from agents.base_agent import BaseAgent
import json

class FeasibilityScoringAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are an expert Venture Capital Analyst. For any startup concept you ALWAYS produce a complete "
            "numerical feasibility scorecard. All scores must be floats between 0.0 and 10.0, never strings."
        )
        super().__init__(name="Feasibility Scoring Agent", system_instruction=system_instruction)

    def _slim_context(self, market_research, competitor, customer_persona, revenue_model, swot):
        """Build a compact context string instead of dumping full JSON."""
        scores_summary = (
            f"Domain: {market_research.get('domain', '')}\n"
            f"Market demand score: {market_research.get('market_demand_score', '')}\n"
            f"Market size TAM: {market_research.get('market_size', {}).get('TAM', '')}\n"
            f"Competition score: {competitor.get('competition_score', '')}\n"
            f"Differentiation: {competitor.get('differentiation_strategy', '')}\n"
            f"Target audience: {customer_persona.get('target_audience', '')}\n"
            f"Revenue score: {revenue_model.get('revenue_score', '')}\n"
            f"Revenue streams: {', '.join(s.get('strategy', '') for s in revenue_model.get('monetization_strategies', []))}\n"
            f"Strengths: {', '.join(swot.get('strengths', []))}\n"
            f"Weaknesses: {', '.join(swot.get('weaknesses', []))}\n"
            f"Opportunities: {', '.join(swot.get('opportunities', []))}\n"
            f"Threats: {', '.join(swot.get('threats', []))}"
        )
        return scores_summary

    def analyze(self, idea_title, idea_description, market_research, competitor, customer_persona, revenue_model, swot):
        ctx = self._slim_context(market_research, competitor, customer_persona, revenue_model, swot)

        prompt = f"""Score the feasibility of this startup idea:
Title: {idea_title}
Description: {idea_description}

Key Context:
{ctx}

Provide a float score 0.0–10.0 for each category (higher = more favorable):
- market_demand: customer need strength and TAM
- competition: 10=blue ocean, 1=brutal red ocean
- revenue_potential: margins and LTV power
- technical_complexity: 10=easy to build, 1=needs R&D breakthrough
- scalability: 10=zero marginal cost, 1=labor intensive
- innovation: 10=first-of-its-kind, 1=pure copycat
- investment_readiness: 10=VC-ready, 1=pre-concept

Return ONLY a valid JSON object with exactly these fields:
- "scores": object with 7 numeric keys (market_demand, competition, revenue_potential, technical_complexity, scalability, innovation, investment_readiness)
- "explanations": object with same 7 keys, each a 1-sentence justification
- "overall_score": float — weighted average of the 7 scores
- "score_justification": 2-3 sentences on the overall rating

No markdown. Return raw JSON only."""
        return self.run_json(prompt, temperature=0.3)
