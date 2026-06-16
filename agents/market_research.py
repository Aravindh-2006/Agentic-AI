from agents.base_agent import BaseAgent

class MarketResearchAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are an expert Market Research Analyst. For any startup idea — established, new, or futuristic — "
            "you ALWAYS produce a concise, insight-packed analysis. Extrapolate from adjacent industries when "
            "direct data is unavailable. Keep every point brief and high-signal. No fluff."
        )
        super().__init__(name="Market Research Agent", system_instruction=system_instruction)

    def analyze(self, idea_title, idea_description):
        prompt = f"""Analyze this startup idea and return a JSON object.
Title: {idea_title}
Description: {idea_description}

IMPORTANT: Complete every field even for novel/futuristic concepts. Extrapolate from analogous markets.
Return ONLY a valid JSON object with exactly these fields:

- "domain": Single phrase (e.g., "B2B SaaS", "HealthTech", "DeepTech")
- "demand_analysis": List of exactly 2 short strings (each under 12 words) — why demand exists
- "market_size": object with:
    - "TAM": e.g., "$20B globally by 2028"
    - "SAM": e.g., "$4B in North America & Europe"
    - "SOM": e.g., "$200M realistic 3-year capture"
    - "explanation": 1 sentence on sizing logic
- "trends": List of exactly 2 short trend strings (under 10 words each)
- "growth_opportunities": List of exactly 2 short opportunity strings (under 10 words each)
- "market_demand_score": integer 1-10

No markdown. Return raw JSON only.
"""
        return self.run_json(prompt, temperature=0.4)
