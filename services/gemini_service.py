import os
import time
import json
import re
import google.generativeai as genai

# Global configuration flag
_configured = False
_last_key = None

def configure_gemini():
    """
    Configures the Gemini API client.
    """
    global _configured, _last_key
    api_key = os.getenv("GEMINI_API_KEY")
    if _configured and _last_key == api_key:
        return True

    if not api_key:
        print("WARNING: GEMINI_API_KEY not found in environment. Gemini functions will fail.")
        return False

    try:
        genai.configure(api_key=api_key)
        _configured = True
        _last_key = api_key
        return True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return False


def clean_json_response(text):
    """
    Cleans up markdown wrappers (```json ... ```) and thinking blocks (<think>...</think>)
    from the response text so it can be parsed as pure JSON.
    """
    text = text.strip()
    # Remove <think>...</think> blocks emitted by reasoning models
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE).strip()
    # Remove markdown code fences
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    # Trim to the outermost JSON object
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        text = text[start_idx:end_idx + 1]
    return text


def _parse_retry_delay(error_str):
    """
    Extracts the recommended retry delay (seconds) from a Gemini API error message.
    Returns the parsed delay as an integer (rounded up), or None if not found.
    """
    # Pattern 1: "Please retry in 35.367259382s"
    match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_str, re.IGNORECASE)
    if match:
        return int(float(match.group(1))) + 1
    # Pattern 2: "seconds: 35" inside retry_delay block
    match = re.search(r'seconds:\s*(\d+)', error_str)
    if match:
        return int(match.group(1)) + 1
    return None


def generate_text(prompt, system_instruction=None, temperature=0.7, retries=7, delay=2):
    """
    Queries Gemini API to generate text with automatic model fallback.
    - 404 (model not found): skip immediately to next model, no retries
    - Daily quota (limit: 0 or limit: 20 exhausted): skip immediately to next model
    - Per-minute rate limit (429): wait the suggested delay, then retry
    - Other errors: exponential backoff retry
    """
    if not configure_gemini():
        raise ValueError("Gemini API is not configured. Please set GEMINI_API_KEY in .env.")

    preferred_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Confirmed available models on this API key (via list_models()).
    # Ordered: fastest/lightest first to minimize latency. Higher-quality models as fallback.
    fallback_sequence = [
        "gemini-3.1-flash-lite",    # fastest, ~1.2s, high quota
        "gemini-flash-lite-latest", # rolling lite alias
        "gemini-2.5-flash-lite",    # lite version
        "gemini-2.5-flash",         # higher quality, slower (~8s)
        "gemini-2.0-flash-lite",    # older lite
        "gemini-2.0-flash",         # older stable
        "gemini-flash-latest",      # rolling flash alias
        "gemini-3.5-flash",         # newer model
    ]

    # Ensure preferred model is first, then append the rest without duplicates
    models_to_try = [preferred_model]
    for m in fallback_sequence:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for model_name in models_to_try:
        print(f"Attempting content generation using model: {model_name}")
        skip_model = False
        for attempt in range(retries):
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={"temperature": temperature},
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
                else:
                    raise Exception("Empty response from Gemini API.")

            except Exception as e:
                error_str = str(e)
                last_error = e

                is_not_found = "404" in error_str or "not found" in error_str.lower()
                is_rate_limit = "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower()

                # Daily quota: limit is fully exhausted (limit: 0) or today's cap hit (limit: 20)
                is_daily_quota = (
                    is_rate_limit
                    and "GenerateRequestsPerDayPerProjectPerModel" in error_str
                    and ("limit: 0" in error_str or "limit: 20" in error_str)
                )

                print(f"Model {model_name} failed (attempt {attempt + 1}/{retries}): {e}")

                if is_not_found:
                    # Model doesn't exist — skip immediately, don't waste retries
                    print(f"Model {model_name} not found. Skipping to next model...")
                    skip_model = True
                    break

                if is_daily_quota:
                    print(f"Daily quota exhausted for {model_name}. Switching to next model...")
                    skip_model = True
                    break

                if is_rate_limit:
                    # Per-minute throttle — wait the suggested delay then retry
                    parsed_delay = _parse_retry_delay(error_str)
                    sleep_time = (parsed_delay + 5) if parsed_delay else 60
                else:
                    # Other errors — exponential backoff
                    sleep_time = delay * (2 ** attempt)

                if attempt < retries - 1:
                    print(f"Waiting {sleep_time}s before retry {attempt + 2}/{retries}...")
                    time.sleep(sleep_time)
                else:
                    print(f"All retries exhausted for {model_name}. Switching to next model...")
                    skip_model = True
                    break

        if skip_model:
            continue

    if last_error:
        raise last_error
    raise Exception("All attempted Gemini models failed or hit quota limits.")


def generate_json(prompt, system_instruction=None, temperature=0.2, retries=7, delay=2):
    """
    Queries Gemini API and returns a parsed JSON dict.
    Handles markdown fences, thinking blocks, trailing commas, and optional json5 fallback.
    """
    json_prompt = (
        f"{prompt}\n\n"
        "IMPORTANT: Return your response strictly as a valid JSON object. "
        "Do NOT add markdown backticks, code fences, explanation text, "
        "or any formatting outside the JSON object itself."
    )

    response_text = generate_text(
        prompt=json_prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        retries=retries,
        delay=delay
    )

    cleaned = clean_json_response(response_text)

    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError as e:
        print(f"JSON parse error. Raw response:\n{response_text}")
        # Fallback 1: strip trailing commas before ] or }
        try:
            cleaned_fallback = re.sub(r',\s*([\]}])', r'\1', cleaned)
            return json.loads(cleaned_fallback, strict=False)
        except Exception:
            pass
        # Fallback 2: json5 lenient parser if installed
        try:
            import json5
            return json5.loads(cleaned)
        except Exception:
            pass
        raise e
