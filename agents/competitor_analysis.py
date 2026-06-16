from agents.base_agent import BaseAgent
import json

class CompetitorAnalysisAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are an expert Competitor Analyst. For any startup idea — established or completely novel — "
            "you ALWAYS produce a focused competitor analysis. If no direct competitors exist, identify the "
            "closest indirect alternatives or substitute behaviors. Keep every point sharp and specific. "
            "No placeholders, no empty fields."
        )
        super().__init__(name="Competitor Analysis Agent", system_instruction=system_instruction)

    def analyze(self, idea_title, idea_description, market_research_data):
        market_research_json = json.dumps(market_research_data, indent=2)
        prompt = f"""
Analyze the competition for this startup idea:
Title: {idea_title}
Description: {idea_description}

Market Research Context:
{market_research_json}

IMPORTANT: Complete every field even for novel concepts. Use indirect or substitute competitors if needed.
Return ONLY a valid JSON object with exactly these fields:

1. "competitors": List of exactly 2 competitors (direct, indirect, or substitute). Each must have:
   - "name": Company or solution name
   - "strengths": 1 sentence — what they do well
   - "weaknesses": 1 sentence — where they fall short
2. "market_gaps": List of exactly 2 specific unmet needs competitors are missing
3. "differentiation_strategy": 1-2 sentences on how this startup wins
4. "competition_score": integer 1-10 (1 = crowded red ocean, 10 = blue ocean)

No markdown. Return raw JSON only.
"""
        return self.run_json(prompt, temperature=0.4)
