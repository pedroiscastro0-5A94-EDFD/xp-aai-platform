"""Letter Writer Agent

Takes outputs from the 3 agents above, generates a professional 2-page
monthly letter in Portuguese (BR). Pure prompt engineering with GPT-4o API.
"""

import os
from openai import OpenAI
from data.market import AAI_PROFILE, PROFILE_LABELS


SYSTEM_PROMPT = """You are a senior investment advisor (assessor de investimentos) at XP Investimentos.
Write a monthly investment letter ("carta mensal") in Brazilian Portuguese for a client.

STRUCTURE (max 2 pages, ~600 words):
1. HEADER: Date, "Carta Mensal de Investimentos — [Month/Year]"
2. GREETING: "Prezado(a) [Name]," with a brief personalized opening
3. MARKET CONTEXT: 1-2 paragraphs on the macro environment (Selic, inflation, global factors)
4. PORTFOLIO PERFORMANCE: 1-2 paragraphs on how the portfolio performed, key numbers,
   comparison to benchmarks. USE ONLY THE EXACT NUMBERS PROVIDED — never invent figures.
5. POSITIONING & OUTLOOK: 1 paragraph on current allocation rationale and forward view
6. RECOMMENDATIONS: 1 paragraph with CVM-compliant suggestions (never direct buy/sell)
7. CLOSING: Professional sign-off with availability for meeting

STYLE RULES:
- Formal but warm, like a trusted advisor writing to a valued client
- Use paragraphs, not bullet points (letter format)
- Smooth transitions between sections
- Confident but never arrogant
- CVM-COMPLIANT: Never guarantee returns, never use "compre/venda" language
- Include disclaimer at the end

IMPORTANT: Use ONLY the numbers provided in the data. Never fabricate returns or values.
All financial figures must come from the input data."""


class LetterWriter:
    """Generates monthly investment letters in Portuguese."""

    name = "Letter Writer"

    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None

    def run(
        self,
        client: dict,
        portfolio_analysis: dict,
        macro_analysis: dict,
        recommendations: dict,
    ) -> dict:
        """
        Generate the monthly investment letter.

        Args:
            client: Client profile
            portfolio_analysis: PortfolioAnalyst output
            macro_analysis: MacroAnalyst output
            recommendations: RecommendationEngine output

        Returns:
            Dict with the generated letter text
        """
        # Build the context for the letter
        profile_label = PROFILE_LABELS.get(client["profile"], client["profile"])
        returns = portfolio_analysis.get("returns", {})
        benchmark = portfolio_analysis.get("benchmark_comparison", {})
        allocation = portfolio_analysis.get("allocation", {})
        alerts = portfolio_analysis.get("alerts", [])
        key_proj = macro_analysis.get("key_projections", {})

        # Format allocation summary
        alloc_text = ", ".join([
            f"{v.get('weight', 0):.1f}% em {k.replace('_', ' ').title()}"
            for k, v in allocation.items()
        ])

        # Format alerts
        alerts_text = ""
        for a in alerts:
            if a["type"] == "extreme_loss":
                alerts_text += f"- {a['ticker']}: queda de {abs(a['pnl_pct']):.1f}% vs. preço médio\n"
            elif a["type"] == "extreme_gain":
                alerts_text += f"- {a['ticker']}: alta de {a['pnl_pct']:.1f}% vs. preço médio\n"

        # Format monthly stock returns from CSV profitability data
        monthly_changes_text = ""
        positions = portfolio_analysis.get("positions", [])
        for pos in positions:
            mc = pos.get("monthly_change_pct")
            if mc is not None:
                monthly_changes_text += f"- {pos['ticker']} ({pos['asset']}): {mc:+.2f}% last month\n"

        user_prompt = (
            f"Write the monthly letter for:\n"
            f"CLIENT: {client['name']}\n"
            f"PROFILE: {profile_label}\n"
            f"GOALS: {client['investmentGoals']}\n"
            f"AUM: R${client['totalAUM']:,.2f}\n\n"
            f"PORTFOLIO PERFORMANCE:\n"
            f"- Monthly return: {returns.get('monthly', 0):.2f}%\n"
            f"- YTD return: {returns.get('ytd', 0):.2f}%\n"
            f"- 12-month return: {returns.get('twelve_month', 0):.2f}%\n"
            f"- vs CDI (month): {benchmark.get('monthly', {}).get('vs_cdi', 0):+.2f}pp\n"
            f"- vs IBOVESPA (month): {benchmark.get('monthly', {}).get('vs_ibovespa', 0):+.2f}pp\n"
            f"- Current allocation: {alloc_text}\n"
            f"- Number of positions: {portfolio_analysis.get('summary', {}).get('num_positions', 0)}\n\n"
            f"ALERTS:\n{alerts_text or 'None'}\n\n"
            f"MONTHLY STOCK RETURNS (calculated from profitability CSV):\n"
            f"{monthly_changes_text or 'No CSV data available'}\n\n"
            f"MACRO CONTEXT:\n"
            f"- Selic: {key_proj.get('selic', {}).get('current', 14.25)}% ({key_proj.get('selic', {}).get('note', '')})\n"
            f"- IPCA: {key_proj.get('ipca', {}).get('twelve_month', 5.2)}% 12M ({key_proj.get('ipca', {}).get('note', '')})\n"
            f"- GDP: {key_proj.get('gdp', {}).get('forecast_2025', 2.0)}% for 2025\n"
            f"- BRL/USD: R${key_proj.get('fx', {}).get('current', 5.85)}\n\n"
            f"RECOMMENDATIONS (already CVM-compliant):\n"
            f"{recommendations.get('recommendation_text', 'Portfolio aligned with profile.')}\n\n"
            f"ADVISOR: {AAI_PROFILE['name']}, {AAI_PROFILE['cnpi']}\n"
            f"DISCLAIMER: {AAI_PROFILE['disclaimer']}\n\n"
            f"Write the complete letter in Portuguese. Max 600 words."
        )

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=2000,
                    temperature=0.4,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                letter_text = response.choices[0].message.content
            except Exception:
                letter_text = self._generate_fallback_letter(
                    client, portfolio_analysis, macro_analysis, recommendations
                )
        else:
            letter_text = self._generate_fallback_letter(
                client, portfolio_analysis, macro_analysis, recommendations
            )

        return {
            "agent": self.name,
            "client_name": client["name"],
            "letter_text": letter_text,
            "word_count": len(letter_text.split()),
        }

    def _generate_fallback_letter(
        self, client, portfolio_analysis, macro_analysis, recommendations
    ) -> str:
        """Generate letter without API using template."""
        profile_label = PROFILE_LABELS.get(client["profile"], client["profile"])
        returns = portfolio_analysis.get("returns", {})
        benchmark = portfolio_analysis.get("benchmark_comparison", {})
        key_proj = macro_analysis.get("key_projections", {})
        rec_text = recommendations.get("recommendation_text", "")

        monthly_ret = returns.get("monthly", 0)
        cdi_monthly = benchmark.get("monthly", {}).get("cdi", 1.07)
        vs_cdi = benchmark.get("monthly", {}).get("vs_cdi", 0)

        # Build monthly stock returns section from CSV data
        positions = portfolio_analysis.get("positions", [])
        stock_returns_text = ""
        for pos in positions:
            mc = pos.get("monthly_change_pct")
            if mc is not None:
                direction = "valorização" if mc > 0 else "desvalorização"
                stock_returns_text += f"- {pos['ticker']} ({pos['asset']}): {direction} de {abs(mc):.1f}% no mês\n"

        # Build concise recommendations (max 3 most important)
        rec_lines = rec_text.strip().split("\n") if rec_text else []
        rec_concise = "\n".join(rec_lines[:5]) if rec_lines else "Carteira alinhada ao perfil."

        letter = f"""Carta Mensal de Investimentos — Fevereiro/2026
Prezado(a) {client['name']},
Espero que esteja bem. Apresento a seguir o relatório mensal de sua carteira de investimentos, referente ao mês de fevereiro de 2026.
Cenário Macroeconômico
O mês de fevereiro foi marcado por um cenário de cautela nos mercados. O Comitê de Política Monetária (Copom) elevou a taxa Selic para {key_proj.get('selic', {}).get('current', 14.25)}% ao ano, reforçando o compromisso com o controle da inflação, que acumula {key_proj.get('ipca', {}).get('twelve_month', 5.2)}% em 12 meses. A economia brasileira mostra sinais de desaceleração, com projeção de crescimento de {key_proj.get('gdp', {}).get('forecast_2025', 2.0)}% para 2025, ante {key_proj.get('gdp', {}).get('previous_year', 3.6)}% registrado em 2024. O câmbio operou com volatilidade, com o dólar cotado a R${key_proj.get('fx', {}).get('current', 5.85)}.
Desempenho da Carteira
Sua carteira apresentou rentabilidade de {monthly_ret:.2f}% no mês, {"superando" if vs_cdi > 0 else "ficando abaixo do"} o CDI de {cdi_monthly:.2f}% em {abs(vs_cdi):.2f} pontos percentuais. No acumulado do ano, o retorno é de {returns.get('ytd', 0):.2f}%, e nos últimos 12 meses, de {returns.get('twelve_month', 0):.2f}%.
Rentabilidade Mensal das Ações (calculada automaticamente a partir do CSV):
{stock_returns_text}
Posicionamento e Recomendações
{rec_concise}
Diante do cenário atual, seguimos atentos às oportunidades que possam surgir com a evolução do cenário.
Permaneço à disposição para agendarmos uma conversa e discutirmos em mais detalhes o posicionamento de sua carteira.
Atenciosamente,
{AAI_PROFILE['name']}
{AAI_PROFILE['cnpi']}
{AAI_PROFILE['office']}
{AAI_PROFILE['phone']}
---
{AAI_PROFILE['disclaimer']}"""

        return letter
