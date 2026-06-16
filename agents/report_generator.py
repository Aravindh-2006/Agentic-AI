from agents.base_agent import BaseAgent
import json

class ReportGenerationAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are a Chief Strategy Officer. You compile tight, executive-level startup reports. "
            "Synthesize findings into actionable insights. No filler, no placeholders, no empty fields."
        )
        super().__init__(name="Report Generation Agent", system_instruction=system_instruction)

    def _slim_context(self, market_research, competitor, customer_persona, revenue_model, swot, feasibility):
        """Build a compact context string instead of dumping full JSON."""
        scores = feasibility.get('scores', {})
        return (
            f"Domain: {market_research.get('domain', '')}\n"
            f"Market demand score: {market_research.get('market_demand_score', '')}\n"
            f"TAM: {market_research.get('market_size', {}).get('TAM', '')}\n"
            f"Trends: {', '.join(market_research.get('trends', []))}\n"
            f"Competitors: {', '.join(c.get('name', '') for c in competitor.get('competitors', []))}\n"
            f"Differentiation: {competitor.get('differentiation_strategy', '')}\n"
            f"Market gaps: {', '.join(competitor.get('market_gaps', []))}\n"
            f"Target audience: {customer_persona.get('target_audience', '')}\n"
            f"Key pain points: {', '.join(customer_persona.get('key_pain_points', []))}\n"
            f"Revenue streams: {', '.join(s.get('strategy', '') for s in revenue_model.get('monetization_strategies', []))}\n"
            f"Revenue projection: {revenue_model.get('revenue_projection', '')}\n"
            f"SWOT strengths: {', '.join(swot.get('strengths', []))}\n"
            f"SWOT threats: {', '.join(swot.get('threats', []))}\n"
            f"Overall score: {feasibility.get('overall_score', '')}/10\n"
            f"Score breakdown: market_demand={scores.get('market_demand','')}, "
            f"competition={scores.get('competition','')}, "
            f"revenue={scores.get('revenue_potential','')}, "
            f"scalability={scores.get('scalability','')}, "
            f"innovation={scores.get('innovation','')}\n"
            f"Score justification: {feasibility.get('score_justification', '')}"
        )

    def analyze(self, idea_title, idea_description, market_research, competitor, customer_persona, revenue_model, swot, feasibility):
        ctx = self._slim_context(market_research, competitor, customer_persona, revenue_model, swot, feasibility)

        prompt = f"""Compile the final validation report for:
Title: {idea_title}
Description: {idea_description}

Key Context:
{ctx}

Return ONLY a valid JSON object with exactly these fields:
1. "executive_summary": 2 focused paragraphs — what it does, why the market needs it, viability verdict
2. "key_risks": List of exactly 3 risks. Each must have:
   - "risk": 1 sentence describing the risk
   - "mitigation": 1 sentence of concrete action
3. "key_opportunities": List of exactly 2 biggest opportunities (1 sentence each)
4. "recommendations": List of exactly 3 specific sequential next steps (numbered, actionable)
5. "conclusion": 1 paragraph — proceed, pivot, or stop with clear reasoning

No markdown. Return raw JSON only."""
        return self.run_json(prompt, temperature=0.4)
