from services.gemini_service import generate_text, generate_json

class BaseAgent:
    def __init__(self, name, system_instruction=None):
        """
        Initializes the base agent with a specific name and optional system-level instructions.
        """
        self.name = name
        self.system_instruction = system_instruction

    def run_text(self, prompt, temperature=0.7):
        """
        Generates text output based on the agent's context and prompt.
        """
        return generate_text(
            prompt=prompt,
            system_instruction=self.system_instruction,
            temperature=temperature
        )

    def run_json(self, prompt, temperature=0.2):
        """
        Generates structured JSON output based on the agent's context and prompt.
        """
        return generate_json(
            prompt=prompt,
            system_instruction=self.system_instruction,
            temperature=temperature
        )
