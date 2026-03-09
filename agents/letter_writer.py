"""Letter Writer Agent

Takes outputs from the 3 agents above, generates a professional 2-page
monthly letter in Portuguese (BR). Pure prompt engineering with GPT-4o API.
"""

import os
from openai import OpenAI
from data.market import AAI_PROFILE, PROFILE_LABELS


SYSTEM_PROMPT = """You are a senior investment advisor (assessor de investimentos) at XP Investimentos.
Write a monthly investment letter ("carta mensal") in Brazilian Portuguese for a client.

CRITICAL: The reference month is MARCH 2026 (Março/2026). All data provided
is from March 2026. The letter must be dated and contextualized for this month.

KEY CONTEXT FOR MARCH 2026:
- Selic at 15.00% — BCB SIGNALING start of easing cycle (5 cuts of 0.50 p.p. to 12.50%)
- Ibovespa rallied strongly (+20% YTD) driven by massive EM inflows
- BRL appreciated significantly (to ~R$5.10)
- US-Iran tensions pushed oil to ~US$80/barrel
- Presidential campaign heating up (election in Oct 2026)

STRUCTURE (max 2 pages, ~600 words):
1. HEADER: "Carta Mensal de Investimentos — Março/2026"
2. GREETING: "Prezado(a) [Name]," with a brief personalized opening
3. MARKET CONTEXT: 1-2 paragraphs on the macro environment (Selic at 15%, BCB signaling cuts, inflation, global factors)
   — use the exact March 2026 numbers provided
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
All financial figures must come from the input data. The letter is for MARCH 2026."""


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

        # Get Selic details — BCB at 15.00%, signaling cuts to 12.50%
        selic_current = key_proj.get('selic', {}).get('current', 15.00)
        selic_previous = key_proj.get('selic', {}).get('previous', 14.75)
        selic_hike = abs(round((selic_current - selic_previous) * 100))

        user_prompt = (
            f"REFERENCE MONTH: MARCH 2026 (Março/2026)\n\n"
            f"Write the monthly letter for:\n"
            f"CLIENT: {client['name']}\n"
            f"PROFILE: {profile_label}\n"
            f"GOALS: {client['investmentGoals']}\n"
            f"AUM: R${client['totalAUM']:,.2f}\n\n"
            f"PORTFOLIO PERFORMANCE (March 2026):\n"
            f"- Monthly return (Mar/26): {returns.get('monthly', 0):.2f}%\n"
            f"- YTD return (Jan-Mar/26): {returns.get('ytd', 0):.2f}%\n"
            f"- 12-month return: {returns.get('twelve_month', 0):.2f}%\n"
            f"- vs CDI (month): {benchmark.get('monthly', {}).get('vs_cdi', 0):+.2f}pp\n"
            f"- vs IBOVESPA (month): {benchmark.get('monthly', {}).get('vs_ibovespa', 0):+.2f}pp\n"
            f"- Current allocation: {alloc_text}\n"
            f"- Number of positions: {portfolio_analysis.get('summary', {}).get('num_positions', 0)}\n\n"
            f"ALERTS:\n{alerts_text or 'None'}\n\n"
            f"MONTHLY STOCK RETURNS (March 2026):\n"
            f"{monthly_changes_text or 'No CSV data available'}\n\n"
            f"MACRO CONTEXT (March 2026):\n"
            f"- Selic: at {selic_current}% (last hike of {selic_hike}bps from {selic_previous}%) — BCB signaling easing cycle with 5 cuts of 0.50 p.p. to 12.50%\n"
            f"- IPCA: {key_proj.get('ipca', {}).get('twelve_month', 3.95)}% 12M ({key_proj.get('ipca', {}).get('note', '')})\n"
            f"- GDP: 2025 closed at {key_proj.get('gdp', {}).get('actual_2025', 2.3)}%, forecast {key_proj.get('gdp', {}).get('forecast_2026', 2.0)}% for 2026\n"
            f"- BRL/USD: R${key_proj.get('fx', {}).get('current', 5.10)}\n"
            f"- Ibovespa +20% YTD, massive EM inflows\n"
            f"- US-Iran tensions, oil at ~US$80/barrel\n\n"
            f"RECOMMENDATIONS (already CVM-compliant):\n"
            f"{recommendations.get('recommendation_text', 'Portfolio aligned with profile.')}\n\n"
            f"ADVISOR: {AAI_PROFILE['name']}, {AAI_PROFILE['cnpi']}\n"
            f"DISCLAIMER: {AAI_PROFILE['disclaimer']}\n\n"
            f"Write the complete letter in Portuguese for MARCH 2026. Max 600 words."
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
        """Generate letter without API using template. Reference: March 2026."""
        profile_label = PROFILE_LABELS.get(client["profile"], client["profile"])
        returns = portfolio_analysis.get("returns", {})
        benchmark = portfolio_analysis.get("benchmark_comparison", {})
        key_proj = macro_analysis.get("key_projections", {})
        rec_text = recommendations.get("recommendation_text", "")

        monthly_ret = returns.get("monthly", 0)
        cdi_monthly = benchmark.get("monthly", {}).get("cdi", 1.17)
        vs_cdi = benchmark.get("monthly", {}).get("vs_cdi", 0)

        # Selic context — at 15.00%, BCB signaling cuts to 12.50%
        selic_current = key_proj.get('selic', {}).get('current', 15.00)
        selic_previous = key_proj.get('selic', {}).get('previous', 14.75)
        selic_hike = abs(round((selic_current - selic_previous) * 100))

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

        letter = f"""Carta Mensal de Investimentos — Março/2026

Prezado(a) {client['name']},

Espero que esteja bem. Apresento a seguir o relatório mensal de sua carteira de investimentos, com os principais destaques do mês de março de 2026. Como sempre, nosso objetivo é manter você informado sobre o desempenho de seus investimentos e as perspectivas para os próximos meses.

Cenário Macroeconômico

O mês de março de 2026 foi marcado por uma importante mudança na política monetária brasileira. Com a taxa Selic em {selic_current}% ao ano, o Banco Central sinalizou o início de um ciclo de afrouxamento monetário. A XP projeta 5 cortes consecutivos de 0,50 p.p. a partir deste mês, levando a Selic a 12,50% ao final de 2026. A inflação acumula {key_proj.get('ipca', {}).get('twelve_month', 3.95)}% em 12 meses, com projeção de 3,8% para 2026. A economia brasileira encerrou 2025 com crescimento de {key_proj.get('gdp', {}).get('actual_2025', 2.3)}%, e a projeção para 2026 é de {key_proj.get('gdp', {}).get('forecast_2026', 2.0)}%.

No cenário externo, as tensões entre EUA e Irã elevaram o petróleo a cerca de US$80/barril, enquanto fluxos recordes para mercados emergentes impulsionaram o Ibovespa a uma alta acumulada de aproximadamente 20% no ano. O real se apreciou significativamente, com o dólar cotado a R${key_proj.get('fx', {}).get('current', 5.10)}, beneficiado pela rotação global para ativos emergentes.

Desempenho da Carteira

Em março de 2026, sua carteira apresentou rentabilidade de {monthly_ret:.2f}%, {"superando o" if vs_cdi > 0 else "ficando abaixo do"} CDI de {cdi_monthly:.2f}% em {abs(vs_cdi):.2f} pontos percentuais. No acumulado do ano (janeiro-março/2026), o retorno é de {returns.get('ytd', 0):.2f}%, e nos últimos 12 meses, de {returns.get('twelve_month', 0):.2f}%. A perspectiva de início do ciclo de cortes na Selic tende a beneficiar posições em renda fixa prefixada e FIIs, enquanto o forte rali das ações brasileiras contribuiu positivamente para as posições em renda variável.

{f"Rentabilidade Mensal das Ações{chr(10)}{chr(10)}{stock_returns_text}" if stock_returns_text else ""}
Posicionamento e Recomendações

Com base na análise do seu perfil {profile_label} e nas condições atuais de mercado de março de 2026, destacamos os seguintes pontos de atenção:

{rec_concise}

O cenário de queda de juros abre oportunidades em diversas classes de ativos, mas é importante manter a diversificação e atenção aos riscos geopolíticos (tensões EUA-Irã) e eleitorais (campanha presidencial 2026). Seguimos monitorando o mercado e avaliando oportunidades que possam contribuir para a evolução da sua carteira, sempre respeitando seu perfil de risco e objetivos de investimento.

Permaneço à disposição para agendarmos uma conversa e discutirmos em mais detalhes o posicionamento de sua carteira. Não hesite em entrar em contato caso tenha qualquer dúvida.

Atenciosamente,
{AAI_PROFILE['name']}
{AAI_PROFILE['cnpi']}
{AAI_PROFILE['office']}
{AAI_PROFILE['phone']}

---
{AAI_PROFILE['disclaimer']}"""

        return letter
