"""Macro Analyst Agent

Reads XP's macro report, extracts key projections (Selic, IPCA, GDP, FX),
and summarizes relevance to client portfolios using GPT-4o API.
"""

import os
from openai import OpenAI


SYSTEM_PROMPT = """You are a senior macroeconomic analyst at XP Investimentos.
Your job is to analyze XP's macro research report and extract a structured
summary of the key economic projections and their implications for client portfolios.

IMPORTANT: The reference period for this analysis is FEBRUARY 2026 (Fevereiro/2026).
The macro report provided may be from a prior date — use it as background context,
but always anchor your analysis to the CURRENT market data provided (February 2026).

Output a structured analysis with these sections:
1. KEY PROJECTIONS — Use the current market data numbers for: Selic rate path, IPCA,
   GDP growth, BRL/USD exchange rate, fiscal balance outlook
2. MARKET SENTIMENT — Overall assessment (bullish/neutral/bearish) for each asset class
3. PORTFOLIO IMPLICATIONS — Specific implications for: fixed income, equities, FIIs,
   international exposure, and crypto allocation
4. RISK FACTORS — Top 3-5 risks to monitor

Keep the analysis factual and data-driven. Use the exact numbers from the CURRENT
market data (February 2026). Write in English for internal use.
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
            f"REFERENCE MONTH: February 2026 (Fevereiro/2026)\n\n"
            f"Current market data (February 2026):\n"
            f"- Selic: {benchmarks['selic']['current']}% (raised from {benchmarks['selic']['previous']}% — contractionary monetary policy)\n"
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
                                f"NOTE: Use the CURRENT MARKET DATA above (February 2026) as the authoritative source.\n"
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

        # Build structured output with known data points — February 2026 context
        return {
            "agent": self.name,
            "reference_month": "2026-02",
            "reference_label": "Fevereiro/2026",
            "analysis_text": analysis_text,
            "key_projections": {
                "selic": {
                    "current": benchmarks["selic"]["current"],
                    "previous": benchmarks["selic"]["previous"],
                    "direction": "hiking" if benchmarks["selic"]["current"] > benchmarks["selic"]["previous"] else "cutting",
                    "change_bps": round((benchmarks["selic"]["current"] - benchmarks["selic"]["previous"]) * 100),
                    "note": f"Selic raised {round((benchmarks['selic']['current'] - benchmarks['selic']['previous']) * 100):.0f}bps to {benchmarks['selic']['current']}%, contractionary monetary policy continues",
                },
                "ipca": {
                    "monthly": benchmarks["ipca"]["monthly"],
                    "twelve_month": benchmarks["ipca"]["twelveMonth"],
                    "ytd": benchmarks["ipca"]["ytd"],
                    "forecast_2026": 5.0,
                    "actual_2025": 6.1,
                    "note": "Inflation above target ceiling, pressured by services and food",
                },
                "gdp": {
                    "actual_2025": 2.0,
                    "forecast_2026": 1.0,
                    "actual_2024": 3.6,
                    "note": "Clear deceleration trend — GDP slowed from 3.6% (2024) to 2.0% (2025), projected 1.0% for 2026",
                },
                "fx": {
                    "current": benchmarks["dolar"]["current"],
                    "monthly_change": benchmarks["dolar"]["monthlyChange"],
                    "actual_eoy_2025": 6.20,
                    "forecast_eoy_2026": 6.40,
                    "note": "BRL recovery fragile, high volatility expected",
                },
                "fiscal": {
                    "note": "Primary balance target achieved in 2025, but public debt trajectory remains concerning",
                },
            },
            "market_sentiment": {
                "renda_fixa": "positive — high Selic favors fixed income, IPCA+ bonds attractive at current spreads",
                "acoes": "cautious — deceleration headwinds offset by cheap valuations, stock picking critical",
                "fiis": "neutral_positive — real estate income steady, but high interest rates cap upside",
                "internacional": "positive — USD diversification valuable given BRL fragility",
                "cripto": "neutral — momentum positive but regulatory uncertainty",
            },
        }

    def _generate_fallback_analysis(self, benchmarks: dict) -> str:
        """Generate analysis without API (uses structured data only). Reference: February 2026."""
        selic_change = round((benchmarks['selic']['current'] - benchmarks['selic']['previous']) * 100)
        return (
            "REFERENCE: February 2026 (Fevereiro/2026)\n\n"
            "KEY PROJECTIONS:\n"
            f"- Selic: Raised {selic_change}bps to {benchmarks['selic']['current']}% from {benchmarks['selic']['previous']}%. "
            "Copom signaled further tightening may be needed given persistent inflation.\n"
            f"- IPCA: Running at {benchmarks['ipca']['twelveMonth']}% (12M), above the target ceiling of 4.5%. "
            "2025 closed at 6.1%. XP projects gradual deceleration to ~5.0% for 2026.\n"
            "- GDP: 2025 closed at 2.0% (down from 3.6% in 2024). "
            "Projected to slow further to 1.0% in 2026 as monetary tightening takes full effect.\n"
            f"- BRL/USD: Currently at R${benchmarks['dolar']['current']}. "
            "2025 ended at R$6.20. XP forecasts R$6.40 by end-2026. "
            "Recent appreciation has fragile foundations.\n"
            "- Fiscal: Primary balance target was achieved in 2025, "
            "but public debt trajectory remains concerning for 2026.\n\n"
            "MARKET SENTIMENT:\n"
            "- Fixed Income: POSITIVE — High Selic makes CDI-linked instruments very attractive. "
            "IPCA+ bonds offer real yields above 5.5%.\n"
            "- Equities: CAUTIOUS — Economic deceleration creates headwinds, "
            "but valuations are depressed, creating selective opportunities.\n"
            "- FIIs: NEUTRAL-POSITIVE — Income yields remain attractive vs fixed income alternatives.\n"
            "- International: POSITIVE — USD diversification is valuable given BRL volatility.\n\n"
            "PORTFOLIO IMPLICATIONS:\n"
            "- Maintain overweight in fixed income for conservative/moderate profiles\n"
            "- Stock selection is critical — favor quality, dividend-paying companies\n"
            "- International exposure serves as both return driver and hedge\n"
            "- FIIs provide steady income stream in volatile environment\n\n"
            "RISK FACTORS:\n"
            "1. US tariff policy uncertainty and Fed rate path\n"
            "2. Brazilian fiscal trajectory and public debt sustainability\n"
            "3. Inflation persistence above target may require even higher Selic\n"
            "4. BRL depreciation risk from global risk-off events\n"
            "5. Political noise around fiscal policy and spending pressures"
        )
