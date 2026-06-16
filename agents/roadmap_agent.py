from agents.base_agent import BaseAgent
import json


class RoadmapAgent(BaseAgent):
    """
    Generates a personalized 6-month startup execution roadmap
    using the full validation report as grounding context.
    Output: 7 phases, 6 monthly plans, 4 milestones, risk warnings.
    """

    def __init__(self):
        system_instruction = (
            "You are an expert Startup Execution Strategist with 20+ years of experience "
            "launching and scaling ventures across SaaS, HealthTech, FinTech, and consumer markets. "
            "You generate hyper-personalized execution roadmaps grounded in real validation data. "
            "Every task, goal, and milestone you generate is specific to the startup idea — "
            "never generic template content. All timelines are realistic for a bootstrap or seed-stage team."
        )
        super().__init__(name="Roadmap Generator Agent", system_instruction=system_instruction)

    def _build_context(self, report):
        """Compact context string from the parsed report dict."""
        mr = report.get('market_research') or {}
        comp = report.get('competitor_analysis') or {}
        persona = report.get('customer_persona') or {}
        revenue = report.get('revenue_model') or {}
        swot = report.get('swot_analysis') or {}
        scores = report.get('feasibility_scores') or {}
        final = report.get('final_report') or {}
        score_data = scores.get('scores', {})

        return (
            f"STARTUP: {report.get('idea_title', '')}\n"
            f"DESCRIPTION: {report.get('idea_description', '')}\n"
            f"OVERALL SCORE: {report.get('overall_score', 0)}/10\n"
            f"DOMAIN: {mr.get('domain', '')}\n"
            f"TAM: {mr.get('market_size', {}).get('TAM', '')}\n"
            f"TRENDS: {', '.join(mr.get('trends', []))}\n"
            f"COMPETITORS: {', '.join(c.get('name', '') for c in comp.get('competitors', []))}\n"
            f"MARKET GAPS: {', '.join(comp.get('market_gaps', []))}\n"
            f"TARGET AUDIENCE: {persona.get('target_audience', '')}\n"
            f"KEY PAIN POINTS: {', '.join(persona.get('key_pain_points', []))}\n"
            f"ACQUISITION CHANNELS: {', '.join(ch.get('channel', '') for ch in persona.get('acquisition_channels', []) if isinstance(ch, dict))}\n"
            f"REVENUE STREAMS: {', '.join(s.get('strategy', '') for s in revenue.get('monetization_strategies', []))}\n"
            f"REVENUE PROJECTION: {revenue.get('revenue_projection', revenue.get('revenue_potential_projection', ''))}\n"
            f"PRICING: {', '.join(t.get('tier_name', '') + ' ' + t.get('price_point', '') for t in revenue.get('pricing_tiers', []) if isinstance(t, dict))}\n"
            f"STRENGTHS: {', '.join(swot.get('strengths', []))}\n"
            f"WEAKNESSES: {', '.join(swot.get('weaknesses', []))}\n"
            f"OPPORTUNITIES: {', '.join(swot.get('opportunities', []))}\n"
            f"THREATS: {', '.join(swot.get('threats', []))}\n"
            f"MARKET DEMAND SCORE: {score_data.get('market_demand', '')}/10\n"
            f"COMPETITION SCORE: {score_data.get('competition', '')}/10\n"
            f"TECHNICAL COMPLEXITY: {score_data.get('technical_complexity', '')}/10\n"
            f"SCALABILITY: {score_data.get('scalability', '')}/10\n"
            f"INVESTMENT READINESS: {score_data.get('investment_readiness', '')}/10\n"
            f"KEY RISKS: {', '.join(r.get('risk', '') for r in final.get('key_risks', []) if isinstance(r, dict))}\n"
            f"RECOMMENDATIONS: {', '.join(str(r) for r in final.get('recommendations', []))}\n"
            f"CONCLUSION: {str(final.get('conclusion', ''))[:300]}"
        )

    def generate(self, report):
        """
        Generate the full roadmap for the given parsed report dict.
        Returns a structured dict with phases, monthly_plan, milestones, risk_warnings.
        """
        context = self._build_context(report)

        prompt = f"""
You are generating a PERSONALIZED 6-month startup execution roadmap.
Use ONLY the data below — every item must reference the actual startup, not generic templates.

{context}

Return ONLY a valid JSON object with EXACTLY this structure:

{{
  "phases": [
    {{
      "phase_number": 1,
      "name": "Idea Validation",
      "description": "1-2 sentences specific to this startup",
      "duration": "Weeks 1-2",
      "key_focus": "Single sentence on the main focus",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    {{
      "phase_number": 2,
      "name": "Market Research & Customer Discovery",
      "description": "...",
      "duration": "Weeks 3-4",
      "key_focus": "...",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    {{
      "phase_number": 3,
      "name": "MVP Development",
      "description": "...",
      "duration": "Month 2",
      "key_focus": "...",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    {{
      "phase_number": 4,
      "name": "Beta Launch",
      "description": "...",
      "duration": "Month 3",
      "key_focus": "...",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    {{
      "phase_number": 5,
      "name": "Customer Acquisition",
      "description": "...",
      "duration": "Month 4",
      "key_focus": "...",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    {{
      "phase_number": 6,
      "name": "Revenue Generation",
      "description": "...",
      "duration": "Month 5",
      "key_focus": "...",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    {{
      "phase_number": 7,
      "name": "Scaling & Growth",
      "description": "...",
      "duration": "Month 6+",
      "key_focus": "...",
      "tasks": ["task 1", "task 2", "task 3"]
    }}
  ],
  "monthly_plan": [
    {{
      "month": 1,
      "label": "Month 1",
      "theme": "Short theme title",
      "goals": ["goal 1", "goal 2"],
      "tasks": ["task 1", "task 2", "task 3", "task 4"],
      "deliverables": ["deliverable 1", "deliverable 2"],
      "expected_outcome": "1 sentence on what success looks like",
      "priority": "High"
    }},
    {{
      "month": 2,
      "label": "Month 2",
      "theme": "...",
      "goals": ["goal 1", "goal 2"],
      "tasks": ["task 1", "task 2", "task 3", "task 4"],
      "deliverables": ["deliverable 1", "deliverable 2"],
      "expected_outcome": "...",
      "priority": "High"
    }},
    {{
      "month": 3,
      "label": "Month 3",
      "theme": "...",
      "goals": ["..."],
      "tasks": ["..."],
      "deliverables": ["..."],
      "expected_outcome": "...",
      "priority": "High"
    }},
    {{
      "month": 4,
      "label": "Month 4",
      "theme": "...",
      "goals": ["..."],
      "tasks": ["..."],
      "deliverables": ["..."],
      "expected_outcome": "...",
      "priority": "Medium"
    }},
    {{
      "month": 5,
      "label": "Month 5",
      "theme": "...",
      "goals": ["..."],
      "tasks": ["..."],
      "deliverables": ["..."],
      "expected_outcome": "...",
      "priority": "Medium"
    }},
    {{
      "month": 6,
      "label": "Month 6",
      "theme": "...",
      "goals": ["..."],
      "tasks": ["..."],
      "deliverables": ["..."],
      "expected_outcome": "...",
      "priority": "Medium"
    }}
  ],
  "milestones": [
    {{
      "milestone_number": 1,
      "title": "Complete Customer Validation",
      "description": "Specific milestone description for this startup",
      "target_month": 1,
      "success_metric": "Measurable success indicator"
    }},
    {{
      "milestone_number": 2,
      "title": "Launch MVP",
      "description": "...",
      "target_month": 3,
      "success_metric": "..."
    }},
    {{
      "milestone_number": 3,
      "title": "Acquire First 100 Users",
      "description": "...",
      "target_month": 4,
      "success_metric": "..."
    }},
    {{
      "milestone_number": 4,
      "title": "Generate First Revenue",
      "description": "...",
      "target_month": 5,
      "success_metric": "..."
    }}
  ],
  "risk_warnings": [
    {{
      "risk": "Risk title specific to SWOT threats",
      "severity": "High",
      "phase_affected": "Phase 3",
      "warning": "Specific warning message",
      "mitigation": "Concrete mitigation action"
    }},
    {{
      "risk": "...",
      "severity": "Medium",
      "phase_affected": "Phase 4",
      "warning": "...",
      "mitigation": "..."
    }},
    {{
      "risk": "...",
      "severity": "Medium",
      "phase_affected": "Phase 5",
      "warning": "...",
      "mitigation": "..."
    }}
  ]
}}

RULES:
- Every task/goal/deliverable must be specific to this startup — no generic text
- Reference actual competitor names, customer personas, pricing tiers from the context
- Tasks must be actionable (verbs: "Build", "Interview", "Deploy", "Measure", "Launch")
- priority must be exactly "High", "Medium", or "Low"
- severity must be exactly "High", "Medium", or "Low"
- No markdown. Return raw JSON only.
"""
        return self.run_json(prompt, temperature=0.5)
