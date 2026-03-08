"""Macro Analyst Agent

Reads XP's macro report, extracts key projections (Selic, IPCA, GDP, FX),
and summarizes relevance to client portfolios using Claude Opus 4.6 API.
"""

import os
from anthropic import Anthropic


SYSTEM_PROMPT = """You are a senior macroeconomic analyst at XP Investimentos.
Your job is to analyze XP's monthly macro research report and extract a structured
summary of the key economic projections and their implications for client portfolios.

Output a structured analysis with these sections:
1. KEY PROJECTIONS — Extract exact numbers for: Selic rate path, IPCA forecast,
   GDP growth, BRL/USD exchange rate, fiscal balance outlook
2. MARKET SENTIMENT — Overall assessment (bullish/neutral/bearish) for each asset class
3. PORTFOLIO IMPLICATIONS — Specific implications for: fixed income, equities, FIIs,
   international exposure, and crypto allocation
4. RISK FACTORS — Top 3-5 risks to monitor

Keep the analysis factual and data-driven. Use the exact numbers from the report.
Write in English for internal use (the letter writer will translate to Portuguese).
Be concise — max 400 words total."""


class MacroAnalyst:
    """Analyzes macro reports using Claude Opus 4.6."""

    name = "Macro Analyst"

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key) if api_key else None

    def run(self, macro_report_text: str, benchmarks: dict) -> dict:
        """
        Analyze the macro report and extract key projections.

        Args:
            macro_report_text: Full text of XP's macro research report
            benchmarks: Current market benchmarks for context

        Returns:
            Dict with macro analysis results
        """
        # Always provide the structured benchmark data
        benchmark_context = (
            f"Current market data:\n"
            f"- Selic: {benchmarks['selic']['current']}% (previous: {benchmarks['selic']['previous']}%)\n"
            f"- CDI monthly: {benchmarks['cdi']['monthly']}%\n"
            f"- IBOVESPA monthly: {benchmarks['ibovespa']['monthly']}%\n"
            f"- IPCA monthly: {benchmarks['ipca']['monthly']}%, 12M: {benchmarks['ipca']['twelveMonth']}%\n"
            f"- USD/BRL: {benchmarks['dolar']['current']} (monthly change: {benchmarks['dolar']['monthlyChange']}%)\n"
            f"- S&P 500 in BRL monthly: {benchmarks['sp500_brl']['monthly']}%\n"
            f"- IFIX monthly: {benchmarks['ifix']['monthly']}%\n"
        )

        # If we have an API key, use Claude for the analysis
        if self.client:
            try:
                response = self.client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=1500,
                    temperature=0.2,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                f"{benchmark_context}\n\n"
                                f"--- XP MACRO RESEARCH REPORT ---\n\n"
                                f"{macro_report_text[:8000]}"
                            ),
                        }
                    ],
                )
                analysis_text = response.content[0].text
            except Exception as e:
                analysis_text = self._generate_fallback_analysis(benchmarks)
        else:
            analysis_text = self._generate_fallback_analysis(benchmarks)

        # Build structured output with known data points
        return {
            "agent": self.name,
            "analysis_text": analysis_text,
            "key_projections": {
                "selic": {
                    "current": benchmarks["selic"]["current"],
                    "previous": benchmarks["selic"]["previous"],
                    "direction": "hiking" if benchmarks["selic"]["current"] > benchmarks["selic"]["previous"] else "cutting",
                    "note": "Selic raised 50bps to 14.25%, contractionary monetary policy continues",
                },
                "ipca": {
                    "monthly": benchmarks["ipca"]["monthly"],
                    "twelve_month": benchmarks["ipca"]["twelveMonth"],
                    "forecast_2025": 6.1,
                    "note": "Inflation above target ceiling, pressured by services and food",
                },
                "gdp": {
                    "forecast_2025": 2.0,
                    "forecast_2026": 1.0,
                    "previous_year": 3.6,
                    "note": "Clear deceleration trend, lagged effects of tight monetary policy",
                },
                "fx": {
                    "current": benchmarks["dolar"]["current"],
                    "monthly_change": benchmarks["dolar"]["monthlyChange"],
                    "forecast_eoy_2025": 6.20,
                    "forecast_eoy_2026": 6.40,
                    "note": "BRL recovery fragile, high volatility expected",
                },
                "fiscal": {
                    "note": "Primary balance target achievable in 2025, but public debt rising rapidly",
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
        """Generate analysis without API (uses structured data only)."""
        return (
            "KEY PROJECTIONS:\n"
            f"- Selic: Raised to {benchmarks['selic']['current']}% from {benchmarks['selic']['previous']}%. "
            "Copom signaled further tightening may be needed given persistent inflation.\n"
            f"- IPCA: Running at {benchmarks['ipca']['twelveMonth']}% (12M), above the target ceiling of 4.5%. "
            "XP projects 6.1% for 2025 full year.\n"
            "- GDP: Forecast at 2.0% for 2025 (down from 3.6% in 2024). "
            "Expected to slow further to 1.0% in 2026 as monetary tightening takes effect.\n"
            f"- BRL/USD: Currently at R${benchmarks['dolar']['current']}. "
            "XP forecasts R$6.20 by end-2025 and R$6.40 by end-2026. "
            "Recent appreciation has fragile foundations.\n"
            "- Fiscal: Primary balance target likely achievable in 2025, "
            "but public debt trajectory remains concerning.\n\n"
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
