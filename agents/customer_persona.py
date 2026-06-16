from agents.base_agent import BaseAgent
import json

class CustomerPersonaAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are an expert User Researcher. For any concept — conventional or futuristic — you ALWAYS "
            "build focused, realistic audience profiles. Reason from the core problem to identify who would "
            "pay for it. Keep every field concise and specific. No placeholder text, no empty fields."
        )
        super().__init__(name="Customer Persona Agent", system_instruction=system_instruction)

    def analyze(self, idea_title, idea_description, market_research_data, competitor_data):
        # Pass only the key fields, not full JSON blobs
        ctx = (
            f"Domain: {market_research_data.get('domain', '')}\n"
            f"Demand: {', '.join(market_research_data.get('demand_analysis', []))}\n"
            f"Trends: {', '.join(market_research_data.get('trends', []))}\n"
            f"Market gaps: {', '.join(competitor_data.get('market_gaps', []))}\n"
            f"Differentiation: {competitor_data.get('differentiation_strategy', '')}"
        )

        prompt = f"""Analyze the target audience for this startup idea:
Title: {idea_title}
Description: {idea_description}

Key Context:
{ctx}

Return ONLY a valid JSON object with exactly these fields:
1. "target_audience": 1-2 sentences on who this is built for and why they need it
2. "user_segments": List of exactly 2 distinct segment labels
3. "persona": A single detailed buyer persona with:
   - "name": Realistic full name
   - "role_or_occupation": Job title or role
   - "demographics": Age, location, income
   - "goals": What they want to achieve (1 sentence)
   - "pain_points": Their biggest frustration (1 sentence)
   - "behavior": Key platforms or tools they use
4. "key_pain_points": List of exactly 3 core pain points this startup addresses
5. "acquisition_channels": List of exactly 2 channels. Each must have:
   - "channel": Channel name
   - "strategy": 1 sentence on how to use it

No markdown. Return raw JSON only."""
        return self.run_json(prompt, temperature=0.4)
