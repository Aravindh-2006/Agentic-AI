from agents.base_agent import BaseAgent
import json

class RevenueModelAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are an expert Financial Modeler and Business Strategist. For any startup — established or novel — "
            "you ALWAYS design concise, realistic monetization models. Draw from analogous business models when "
            "the market is nascent. Keep all fields specific and to the point. No placeholders, no empty fields."
        )
        super().__init__(name="Revenue Model Agent", system_instruction=system_instruction)

    def analyze(self, idea_title, idea_description, market_research_data, customer_persona_data):
        # Pass only the key fields, not full JSON blobs
        ctx = (
            f"Domain: {market_research_data.get('domain', '')}\n"
            f"TAM: {market_research_data.get('market_size', {}).get('TAM', '')}\n"
            f"SOM: {market_research_data.get('market_size', {}).get('SOM', '')}\n"
            f"Target audience: {customer_persona_data.get('target_audience', '')}\n"
            f"User segments: {', '.join(customer_persona_data.get('user_segments', []))}\n"
            f"Key pain points: {', '.join(customer_persona_data.get('key_pain_points', []))}"
        )

        prompt = f"""Design the revenue model for this startup idea:
Title: {idea_title}
Description: {idea_description}

Key Context:
{ctx}

Return ONLY a valid JSON object with exactly these fields:
1. "monetization_strategies": List of exactly 2 revenue streams. Each must have:
   - "strategy": Stream name (e.g., "SaaS Subscription", "Marketplace Fee")
   - "description": 1 sentence on how value is captured
2. "pricing_tiers": List of exactly 2 tiers. Each must have:
   - "tier_name": e.g., "Starter", "Pro"
   - "price_point": e.g., "$29/month"
   - "billing_cycle": "monthly" or "annual"
   - "key_features": List of exactly 3 features
3. "revenue_projection": 1 sentence Year-1 estimate with a specific number (e.g., "~$120K ARR from 200 users at $49/month")
4. "sustainability_analysis": 1-2 sentences on margins, LTV vs CAC, and churn risk
5. "revenue_score": integer 1-10

No markdown. Return raw JSON only."""
        return self.run_json(prompt, temperature=0.4)
