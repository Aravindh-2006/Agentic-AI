from agents.base_agent import BaseAgent
import json

class SWOTAnalysisAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are an expert Business Strategy Consultant. For any startup concept — conventional or futuristic — "
            "you ALWAYS deliver a sharp, idea-specific SWOT analysis. Every point must be directly tied to the "
            "startup's mechanics, users, and market. No generic clichés, no empty fields."
        )
        super().__init__(name="SWOT Analysis Agent", system_instruction=system_instruction)

    def _slim_context(self, market_research, competitor, customer_persona, revenue_model):
        """Build a compact context string instead of dumping full JSON."""
        return (
            f"Domain: {market_research.get('domain', '')}\n"
            f"Market demand score: {market_research.get('market_demand_score', '')}\n"
            f"Trends: {', '.join(market_research.get('trends', []))}\n"
            f"Competitors: {', '.join(c.get('name', '') for c in competitor.get('competitors', []))}\n"
            f"Competition score: {competitor.get('competition_score', '')}\n"
            f"Market gaps: {', '.join(competitor.get('market_gaps', []))}\n"
            f"Target audience: {customer_persona.get('target_audience', '')}\n"
            f"Key pain points: {', '.join(customer_persona.get('key_pain_points', []))}\n"
            f"Revenue streams: {', '.join(s.get('strategy', '') for s in revenue_model.get('monetization_strategies', []))}\n"
            f"Revenue score: {revenue_model.get('revenue_score', '')}"
        )

    def analyze(self, idea_title, idea_description, market_research, competitor, customer_persona, revenue_model):
        ctx = self._slim_context(market_research, competitor, customer_persona, revenue_model)

        prompt = f"""Perform a SWOT Analysis for this startup idea:
Title: {idea_title}
Description: {idea_description}

Key Context:
{ctx}

Return ONLY a valid JSON object with exactly these fields:
1. "strengths": List of exactly 3 internal strengths unique to this startup (each under 15 words)
2. "weaknesses": List of exactly 3 internal weaknesses or execution challenges (each under 15 words)
3. "opportunities": List of exactly 3 external market opportunities to exploit (each under 15 words)
4. "threats": List of exactly 3 external threats or risks to monitor (each under 15 words)

No markdown. Return raw JSON only."""
        return self.run_json(prompt, temperature=0.4)
