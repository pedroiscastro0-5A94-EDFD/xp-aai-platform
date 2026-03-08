"""Recommendation Engine Agent

Compares current allocation vs. target ranges for each risk profile,
flags drift >5%, flags individual stocks with extreme returns.
Combines code logic + Claude Opus 4.6 API for recommendation text.
Uses CVM-compliant language only.
"""

import os
from anthropic import Anthropic
from data.market import TARGET_ALLOCATIONS, CLASS_LABELS, PROFILE_LABELS


SYSTEM_PROMPT = """You are a CVM-compliant investment advisor at XP Investimentos.
Generate rebalancing recommendations based on the portfolio drift analysis provided.

CRITICAL CVM COMPLIANCE RULES — you MUST follow these:
- NEVER use direct buy/sell language ("compre", "venda", "recomendo a compra")
- Instead use: "a alocação pode ser ajustada", "o posicionamento sugere uma revisão",
  "é oportuno avaliar", "pode ser interessante considerar"
- NEVER guarantee returns or imply certainty
- Always mention that past performance does not guarantee future results
- Frame everything as analysis and positioning, not as direct recommendations
- Use passive voice and conditional language

Generate 3-5 specific, actionable recommendations in Portuguese.
Each recommendation should reference specific asset classes and the drift analysis.
Keep it concise — max 300 words total."""


class RecommendationEngine:
    """Generates CVM-compliant portfolio recommendations."""

    name = "Recommendation Engine"

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key) if api_key else None

    def run(
        self,
        client: dict,
        portfolio_analysis: dict,
        macro_analysis: dict,
    ) -> dict:
        """
        Generate rebalancing recommendations.

        Args:
            client: Client profile dict
            portfolio_analysis: Output from PortfolioAnalyst
            macro_analysis: Output from MacroAnalyst

        Returns:
            Dict with drift analysis and recommendations
        """
        profile = client["profile"]
        target = TARGET_ALLOCATIONS.get(profile, TARGET_ALLOCATIONS["moderado"])
        allocation = portfolio_analysis.get("allocation", {})
        alerts = portfolio_analysis.get("alerts", [])
        total_aum = client["totalAUM"]

        # --- Calculate drift for each asset class ---
        drift_analysis = []
        for asset_class, target_pct in target.items():
            current_pct = allocation.get(asset_class, {}).get("weight", 0)
            drift = round(current_pct - target_pct, 2)
            drift_amount = round((drift / 100) * total_aum, 2)
            needs_action = abs(drift) > 5

            drift_analysis.append({
                "asset_class": asset_class,
                "label": CLASS_LABELS.get(asset_class, asset_class),
                "target_pct": target_pct,
                "current_pct": round(current_pct, 2),
                "drift_pct": drift,
                "drift_amount": drift_amount,
                "needs_action": needs_action,
                "status": "overweight" if drift > 0 else "underweight" if drift < 0 else "on_target",
            })

        # --- Identify positions needing attention ---
        positions_to_review = []
        for alert in alerts:
            positions_to_review.append({
                "ticker": alert["ticker"],
                "asset": alert["asset"],
                "pnl_pct": alert["pnl_pct"],
                "type": alert["type"],
                "reason": alert["message"],
            })

        # --- Generate recommendation text ---
        drift_summary = "\n".join([
            f"- {d['label']}: target {d['target_pct']}%, current {d['current_pct']}%, "
            f"drift {d['drift_pct']:+.1f}pp ({'NEEDS ACTION' if d['needs_action'] else 'OK'})"
            for d in drift_analysis
        ])

        alerts_summary = "\n".join([
            f"- {a['ticker']}: {a['pnl_pct']:+.1f}% P&L ({a['type']})"
            for a in positions_to_review
        ]) or "No extreme positions flagged."

        macro_sentiment = ""
        if "market_sentiment" in macro_analysis:
            for cls, sentiment in macro_analysis["market_sentiment"].items():
                macro_sentiment += f"- {CLASS_LABELS.get(cls, cls)}: {sentiment}\n"

        # Use Claude for recommendation text if available
        if self.client:
            try:
                user_prompt = (
                    f"Client: {client['name']}, Profile: {PROFILE_LABELS.get(profile, profile)}\n"
                    f"Investment Goals: {client['investmentGoals']}\n"
                    f"Total AUM: R${total_aum:,.2f}\n\n"
                    f"DRIFT ANALYSIS:\n{drift_summary}\n\n"
                    f"POSITION ALERTS:\n{alerts_summary}\n\n"
                    f"MACRO SENTIMENT:\n{macro_sentiment}\n\n"
                    f"Generate CVM-compliant rebalancing recommendations in Portuguese."
                )
                response = self.client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=1000,
                    temperature=0.3,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                recommendation_text = response.content[0].text
            except Exception:
                recommendation_text = self._generate_fallback_recommendations(
                    client, drift_analysis, positions_to_review, profile
                )
        else:
            recommendation_text = self._generate_fallback_recommendations(
                client, drift_analysis, positions_to_review, profile
            )

        return {
            "agent": self.name,
            "client_name": client["name"],
            "profile": profile,
            "profile_label": PROFILE_LABELS.get(profile, profile),
            "drift_analysis": drift_analysis,
            "positions_to_review": positions_to_review,
            "has_actionable_drift": any(d["needs_action"] for d in drift_analysis),
            "recommendation_text": recommendation_text,
            "total_aum": total_aum,
        }

    def _generate_fallback_recommendations(
        self, client: dict, drift: list, alerts: list, profile: str
    ) -> str:
        """Generate recommendations without API."""
        recs = []
        profile_label = PROFILE_LABELS.get(profile, profile)

        for d in drift:
            if d["needs_action"]:
                if d["drift_pct"] > 0:
                    recs.append(
                        f"A alocação em {d['label']} encontra-se acima do target para o perfil "
                        f"{profile_label} ({d['current_pct']:.1f}% vs. {d['target_pct']}% alvo). "
                        f"Pode ser oportuno avaliar uma redução gradual de aproximadamente "
                        f"R${abs(d['drift_amount']):,.0f} nesta classe."
                    )
                else:
                    recs.append(
                        f"A alocação em {d['label']} está abaixo do nível sugerido para o perfil "
                        f"{profile_label} ({d['current_pct']:.1f}% vs. {d['target_pct']}% alvo). "
                        f"Considerando o cenário atual, pode ser interessante avaliar um "
                        f"incremento de aproximadamente R${abs(d['drift_amount']):,.0f}."
                    )

        for a in alerts:
            if a["type"] == "extreme_loss":
                recs.append(
                    f"A posição em {a['asset']} ({a['ticker']}) apresenta uma desvalorização de "
                    f"{a['pnl_pct']:.1f}% em relação ao preço médio. É recomendável uma "
                    f"revisão desta posição à luz da tese original de investimento."
                )
            elif a["type"] == "extreme_gain":
                recs.append(
                    f"A posição em {a['asset']} ({a['ticker']}) acumula valorização de "
                    f"{a['pnl_pct']:.1f}%. Pode ser oportuno considerar uma realização "
                    f"parcial de lucros para reequilibrar o portfólio."
                )

        if not recs:
            recs.append(
                f"A carteira de {client['name']} encontra-se alinhada ao perfil "
                f"{profile_label}. Sugerimos manter o posicionamento atual e "
                f"acompanhar a evolução do cenário macroeconômico."
            )

        return "\n\n".join(recs)
