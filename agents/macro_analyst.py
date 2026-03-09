"""Macro Analyst Agent

Reads XP's macro report, extracts key projections (Selic, IPCA, GDP, FX),
and summarizes relevance to client portfolios using GPT-4o API.
"""

import os
from openai import OpenAI


SYSTEM_PROMPT = """You are a senior macroeconomic analyst at XP Investimentos.
Your job is to analyze XP's macro research report and extract a structured
summary of the key economic projections and their implications for client portfolios.

IMPORTANT: The reference period for this analysis is MARCH 2026 (Março/2026).
The macro report provided may be from a prior date — use it as background context,
but always anchor your analysis to the CURRENT market data provided (March 2026).

Output a structured analysis with these sections:
1. KEY PROJECTIONS — Use the current market data numbers for: Selic rate path, IPCA,
   GDP growth, BRL/USD exchange rate, fiscal balance outlook
2. MARKET SENTIMENT — Overall assessment (bullish/neutral/bearish) for each asset class
3. PORTFOLIO IMPLICATIONS — Specific implications for: fixed income, equities, FIIs,
   international exposure, and crypto allocation
4. RISK FACTORS — Top 3-5 risks to monitor

Keep the analysis factual and data-driven. Use the exact numbers from the CURRENT
market data (March 2026). Write in English for internal use.
Be concise — max 400 words total."""


class MacroAnalyst:
    """Analyzes macro reports using GPT-4o."""

    name = "Macro Analyst"

    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None

    def run(self, macro_report_text: str, benchmarks: dict) -> dict:
        """
        Analyze the macro report and extract key projections.

        Args:
            macro_report_text: Full text of XP's macro research report
            benchmarks: Current market benchmarks for context

        Returns:
            Dict with macro analysis results
        """
        # Always provide the structured benchmark data with clear date reference
        benchmark_context = (
            f"REFERENCE MONTH: March 2026 (Março/2026)\n\n"
            f"Current market data (March 2026):\n"
            f"- Selic: {benchmarks['selic']['current']}% (last hike from {benchmarks['selic']['previous']}%) — BCB signaling start of easing cycle with 5 cuts of 0.50 p.p. to 12.50%\n"
            f"- CDI monthly: {benchmarks['cdi']['monthly']}%\n"
            f"- CDI YTD: {benchmarks['cdi']['ytd']}%, 12M: {benchmarks['cdi']['twelveMonth']}%\n"
            f"- IBOVESPA monthly: {benchmarks['ibovespa']['monthly']}%, YTD: {benchmarks['ibovespa']['ytd']}%, 12M: {benchmarks['ibovespa']['twelveMonth']}%\n"
            f"- IPCA monthly: {benchmarks['ipca']['monthly']}%, 12M: {benchmarks['ipca']['twelveMonth']}%\n"
            f"- USD/BRL: {benchmarks['dolar']['current']} (monthly change: {benchmarks['dolar']['monthlyChange']}%)\n"
            f"- S&P 500 in BRL monthly: {benchmarks['sp500_brl']['monthly']}%, YTD: {benchmarks['sp500_brl']['ytd']}%, 12M: {benchmarks['sp500_brl']['twelveMonth']}%\n"
            f"- IFIX monthly: {benchmarks['ifix']['monthly']}%, YTD: {benchmarks['ifix']['ytd']}%, 12M: {benchmarks['ifix']['twelveMonth']}%\n"
        )

        # If we have an API key, use GPT-4o for the analysis
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=1500,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": (
                                f"{benchmark_context}\n\n"
                                f"--- XP MACRO RESEARCH REPORT (background context — may be from a prior date) ---\n"
                                f"NOTE: Use the CURRENT MARKET DATA above (March 2026) as the authoritative source.\n"
                                f"The report below provides economic analysis context.\n\n"
                                f"{macro_report_text[:8000]}"
                            ),
                        },
                    ],
                )
                analysis_text = response.choices[0].message.content
            except Exception as e:
                analysis_text = self._generate_fallback_analysis(benchmarks)
        else:
            analysis_text = self._generate_fallback_analysis(benchmarks)

        # Build structured output with known data points — March 2026 context
        return {
            "agent": self.name,
            "reference_month": "2026-03",
            "reference_label": "Março/2026",
            "analysis_text": analysis_text,
            "key_projections": {
                "selic": {
                    "current": benchmarks["selic"]["current"],
                    "previous": benchmarks["selic"]["previous"],
                    "direction": "signaling_cuts",
                    "change_bps": round((benchmarks["selic"]["current"] - benchmarks["selic"]["previous"]) * 100),
                    "target_eoy_2026": 12.50,
                    "note": f"Selic at {benchmarks['selic']['current']}% (last hike of {round((benchmarks['selic']['current'] - benchmarks['selic']['previous']) * 100):.0f}bps from {benchmarks['selic']['previous']}%). BCB signaling 5 consecutive cuts of 0.50 p.p. starting March, targeting 12.50% by year-end.",
                },
                "ipca": {
                    "monthly": benchmarks["ipca"]["monthly"],
                    "twelve_month": benchmarks["ipca"]["twelveMonth"],
                    "ytd": benchmarks["ipca"]["ytd"],
                    "forecast_2026": 3.8,
                    "forecast_2027": 4.0,
                    "actual_2025": 4.3,
                    "note": "Inflation benign short-term, but oil prices are upside risk. IPCA-15 Feb at 0.84% surprised but quality was OK.",
                },
                "gdp": {
                    "actual_2025": 2.3,
                    "forecast_2026": 2.0,
                    "forecast_2027": 1.2,
                    "actual_2024": 3.4,
                    "note": "Economy decelerated to 2.3% in 2025, recovery expected in H1 2026 from fiscal/credit stimuli, projected 2.0% for 2026",
                },
                "fx": {
                    "current": benchmarks["dolar"]["current"],
                    "monthly_change": benchmarks["dolar"]["monthlyChange"],
                    "actual_eoy_2025": 5.49,
                    "forecast_eoy_2026": 5.60,
                    "forecast_eoy_2027": 5.80,
                    "note": "BRL appreciated to ~R$5.10, structural models suggest R$5.00 is fair value, but political/fiscal risks ahead",
                },
                "fiscal": {
                    "note": "Revenue strong short-term, oil helping. Primary deficit of 0.4% GDP in 2026. Public debt rising to 83.4% GDP.",
                },
            },
            "market_sentiment": {
                "renda_fixa": "positive — still-high Selic favors CDI-linked instruments, IPCA+ bonds attractive as inflation declines",
                "acoes": "positive — Ibovespa +20% YTD, massive EM inflows, but valuations getting stretched",
                "fiis": "positive — rate cutting cycle benefits FIIs, income yields attractive",
                "internacional": "cautious — BRL appreciation reducing returns in BRL terms, US-Iran tensions add uncertainty",
                "cripto": "neutral — momentum positive but regulatory and geopolitical uncertainty",
            },
        }

    def _generate_fallback_analysis(self, benchmarks: dict) -> str:
        """Generate analysis without API (uses structured data only). Reference: March 2026."""
        selic_hike = abs(round((benchmarks['selic']['current'] - benchmarks['selic']['previous']) * 100))
        return (
            "REFERENCE: March 2026 (Março/2026)\n\n"
            "KEY PROJECTIONS:\n"
            f"- Selic: Currently at {benchmarks['selic']['current']}% (last hike of {selic_hike}bps from {benchmarks['selic']['previous']}%). "
            "BCB signaling start of easing cycle. XP projects 5 consecutive cuts of 0.50 p.p. to reach 12.50% by year-end.\n"
            f"- IPCA: Running at {benchmarks['ipca']['twelveMonth']}% (12M), declining from 4.3% in 2025. "
            "XP projects 3.8% for 2026 and 4.0% for 2027. Oil prices are upside risk.\n"
            "- GDP: 2025 closed at 2.3% (down from 3.4% in 2024). "
            "Fiscal/credit stimuli should support 2.0% growth in 2026. Expected 1.2% in 2027.\n"
            f"- BRL/USD: Currently at R${benchmarks['dolar']['current']}. Appreciated from R$5.49 at end-2025. "
            "XP forecasts R$5.60 by end-2026, R$5.80 by end-2027.\n"
            "- Fiscal: Revenue strong, oil helping. Primary deficit at 0.4% of GDP for 2026. "
            "Public debt rising to 83.4% GDP.\n\n"
            "MARKET CONTEXT:\n"
            "- Ibovespa accumulated +20% YTD driven by massive EM inflows\n"
            "- US-Iran conflict pushed oil to ~US$80/barrel (+30% YTD)\n"
            "- Record EM capital flows, investors rotating out of US assets\n\n"
            "MARKET SENTIMENT:\n"
            "- Fixed Income: POSITIVE — Still-high Selic, rate cuts benefit bond prices.\n"
            "- Equities: POSITIVE — Strong rally, EM inflows, but watch for stretched valuations.\n"
            "- FIIs: POSITIVE — Rate cutting cycle benefits real estate.\n"
            "- International: CAUTIOUS — BRL appreciation reducing USD returns.\n\n"
            "PORTFOLIO IMPLICATIONS:\n"
            "- Fixed income remains core, shift toward IPCA+ as rate cuts begin\n"
            "- Equities benefiting from EM rotation but be selective\n"
            "- FIIs attractive as rate cuts start\n"
            "- International: reduced urgency given BRL strength, maintain for diversification\n\n"
            "RISK FACTORS:\n"
            "1. US-Iran conflict and oil price persistence (upside risk to inflation)\n"
            "2. Presidential campaign — fiscal promises could increase risk premia\n"
            "3. Global EM flow reversal if risk appetite shifts\n"
            "4. Oil at US$80 could force gasoline hikes, adding ~0.70 p.p. to IPCA\n"
            "5. Public debt trajectory — DBGG at 83.4% GDP in 2026"
        )
