from agents.base_agent import BaseAgent
import json


class MentorAgent(BaseAgent):
    """
    AI Startup Mentor — answers follow-up questions about a startup
    using the full validation report as grounding context.
    Every response is structured: recommendation, reasoning,
    action_steps, and priority_level.
    """

    def __init__(self):
        system_instruction = (
            "You are an expert AI Startup Mentor with 20+ years of experience in venture capital, "
            "product strategy, go-to-market, and startup operations. "
            "You have been given a complete AI-generated validation report for a specific startup idea. "
            "You ONLY answer based on the startup's actual data — never give generic advice. "
            "Every answer must reference specific details from the report (market size, competitors, "
            "personas, scores, SWOT points, etc.). "
            "You are direct, confident, and actionable. No fluff, no filler."
        )
        super().__init__(name="AI Startup Mentor", system_instruction=system_instruction)

    def _build_context(self, report):
        """
        Builds a compact startup context string from the report data dict.
        All values are already parsed Python dicts when passed in.
        """
        mr = report.get('market_research') or {}
        comp = report.get('competitor_analysis') or {}
        persona = report.get('customer_persona') or {}
        revenue = report.get('revenue_model') or {}
        swot = report.get('swot_analysis') or {}
        scores = report.get('feasibility_scores') or {}
        final = report.get('final_report') or {}

        score_data = scores.get('scores', {})

        ctx = f"""
=== STARTUP VALIDATION REPORT CONTEXT ===

STARTUP: {report.get('idea_title', 'Unknown')}
DESCRIPTION: {report.get('idea_description', '')}
OVERALL SCORE: {report.get('overall_score', 0)}/10

--- MARKET RESEARCH ---
Domain: {mr.get('domain', '')}
TAM: {mr.get('market_size', {}).get('TAM', '')}
SAM: {mr.get('market_size', {}).get('SAM', '')}
SOM: {mr.get('market_size', {}).get('SOM', '')}
Demand: {', '.join(mr.get('demand_analysis', []) if isinstance(mr.get('demand_analysis'), list) else [str(mr.get('demand_analysis',''))])}
Trends: {', '.join(mr.get('trends', []))}
Growth Opportunities: {', '.join(mr.get('growth_opportunities', []))}
Market Demand Score: {mr.get('market_demand_score', '')}/10

--- COMPETITOR ANALYSIS ---
Competitors: {', '.join(c.get('name','') for c in comp.get('competitors', []))}
Market Gaps: {', '.join(comp.get('market_gaps', []))}
Differentiation Strategy: {comp.get('differentiation_strategy', '')}
Competition Score: {comp.get('competition_score', '')}/10

--- CUSTOMER PERSONA ---
Target Audience: {persona.get('target_audience', '')}
User Segments: {', '.join(persona.get('user_segments', []))}
Key Pain Points: {', '.join(persona.get('key_pain_points', []))}
Acquisition Channels: {', '.join(ch.get('channel','') for ch in persona.get('acquisition_channels', []) if isinstance(ch, dict))}

--- REVENUE MODEL ---
Monetization Streams: {', '.join(s.get('strategy','') for s in revenue.get('monetization_strategies', []))}
Revenue Projection: {revenue.get('revenue_projection', revenue.get('revenue_potential_projection', ''))}
Sustainability: {revenue.get('sustainability_analysis', '')}
Revenue Score: {revenue.get('revenue_score', '')}/10

--- SWOT ANALYSIS ---
Strengths: {', '.join(swot.get('strengths', []))}
Weaknesses: {', '.join(swot.get('weaknesses', []))}
Opportunities: {', '.join(swot.get('opportunities', []))}
Threats: {', '.join(swot.get('threats', []))}

--- FEASIBILITY SCORES ---
Market Demand: {score_data.get('market_demand', '')}/10
Competition: {score_data.get('competition', '')}/10
Revenue Potential: {score_data.get('revenue_potential', '')}/10
Technical Complexity: {score_data.get('technical_complexity', '')}/10
Scalability: {score_data.get('scalability', '')}/10
Innovation: {score_data.get('innovation', '')}/10
Investment Readiness: {score_data.get('investment_readiness', '')}/10
Score Justification: {scores.get('score_justification', '')}

--- FINAL REPORT ---
Executive Summary: {str(final.get('executive_summary', ''))[:400]}
Key Risks: {', '.join(r.get('risk','') for r in final.get('key_risks', []) if isinstance(r, dict))}
Key Opportunities: {', '.join(final.get('key_opportunities', []) if isinstance(final.get('key_opportunities'), list) else [])}
Conclusion: {str(final.get('conclusion', ''))[:300]}

=== END OF CONTEXT ===
"""
        return ctx.strip()

    def _build_history_prompt(self, history):
        """Formats past messages into a readable conversation string."""
        if not history:
            return ""
        lines = ["\n=== PREVIOUS CONVERSATION ==="]
        for msg in history[-6:]:  # last 6 messages max for context
            role_label = "Founder" if msg['role'] == 'user' else "Mentor"
            lines.append(f"{role_label}: {msg['content']}")
        lines.append("=== END PREVIOUS CONVERSATION ===\n")
        return "\n".join(lines)

    def answer(self, question, report, history=None):
        """
        Generate a mentor response for the given question.
        Returns a structured dict with recommendation, reasoning,
        action_steps (list), and priority_level.
        """
        context = self._build_context(report)
        history_prompt = self._build_history_prompt(history or [])

        prompt = f"""
{context}
{history_prompt}

The startup founder has asked:
"{question}"

Answer ONLY based on the startup report context above. Be specific — reference actual data points,
scores, competitor names, market sizes, SWOT items from the report.

Return ONLY a valid JSON object with exactly these fields:
{{
  "recommendation": "A direct, confident recommendation sentence (1-2 sentences)",
  "reasoning": "Why this recommendation — cite specific data from the report (2-3 sentences)",
  "action_steps": ["Step 1 (specific and actionable)", "Step 2", "Step 3"],
  "priority_level": "High" | "Medium" | "Low"
}}

No markdown. No code fences. Return raw JSON only.
"""
        return self.run_json(prompt, temperature=0.5)
