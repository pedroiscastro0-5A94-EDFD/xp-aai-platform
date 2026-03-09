"""Market benchmarks, target allocations, and AAI profile data."""

# 12 months of historical monthly returns: Apr/25 → Mar/26
# Context: Selic rose to 15.00% through 2025, BCB signals cutting cycle in Mar/26.
#           Ibovespa +20% YTD, BRL appreciated to ~R$5.10, massive EM inflows.
BENCHMARK_HISTORY = {
    "months": ["Apr/25", "May/25", "Jun/25", "Jul/25", "Aug/25", "Sep/25", "Oct/25", "Nov/25", "Dec/25", "Jan/26", "Feb/26", "Mar/26"],
    "cdi":      [1.02, 1.05, 1.07, 1.08, 1.10, 1.12, 1.14, 1.15, 1.17, 1.18, 1.17, 1.16],
    "ibovespa": [1.80, -2.50, 3.20, -1.50, -3.00, -2.80, 4.50, 1.20, -1.50, 7.20, 6.50, 5.00],
    "ifix":     [0.80, -0.30, 1.20, 0.50, 0.30, -0.50, 0.80, 0.40, 0.60, 2.50, 2.20, 2.80],
    "sp500_brl":[3.50, -1.50, 4.00, 1.80, -2.50, 2.80, -1.20, 5.00, 0.50, -3.00, -1.50, -2.00],
}

BENCHMARK_LABELS = {
    "cdi": "CDI",
    "ibovespa": "IBOV",
    "ifix": "IFIX",
    "sp500_brl": "S&P 500 (BRL)",
}

# March 2026 benchmarks
# Source: XP Macro Mensal (5 de março de 2026)
# Key events: BCB signals start of cutting cycle in March, Ibovespa +20% YTD,
#   massive EM inflows, BRL appreciated to ~R$5.10, US-Iran tensions.
MARKET_BENCHMARKS = {
    "month": "2026-03",
    "cdi": {"monthly": 1.16, "ytd": 3.53, "twelveMonth": 14.50},
    "ibovespa": {"monthly": 5.00, "ytd": 19.80, "twelveMonth": 22.50},
    "ifix": {"monthly": 2.80, "ytd": 7.70, "twelveMonth": 12.80},
    "sp500_brl": {"monthly": -2.00, "ytd": -6.40, "twelveMonth": 8.50},
    "ipca": {"monthly": 0.35, "ytd": 1.50, "twelveMonth": 3.95},
    "selic": {"current": 14.50, "previous": 15.00},
    "dolar": {"current": 5.10, "monthlyChange": -2.30},
}

# Target allocation ranges by risk profile (percentage)
TARGET_ALLOCATIONS = {
    "conservador": {"renda_fixa": 60, "multimercado": 10, "acoes": 10, "fiis": 10, "internacional": 8, "cripto": 2},
    "moderado":    {"renda_fixa": 35, "multimercado": 10, "acoes": 25, "fiis": 15, "internacional": 12, "cripto": 3},
    "arrojado":    {"renda_fixa": 10, "multimercado": 15, "acoes": 35, "fiis": 15, "internacional": 18, "cripto": 7},
    "agressivo":   {"renda_fixa": 5,  "multimercado": 10, "acoes": 40, "fiis": 10, "internacional": 25, "cripto": 10},
}

# Financial advisor profile
AAI_PROFILE = {
    "name": "Carlos Eduardo Martins",
    "cnpi": "CNPI-T 12345",
    "email": "carlos.martins@xpi.com.br",
    "phone": "(11) 91234-5678",
    "office": "XP Investimentos - Faria Lima",
    "totalClients": 52,
    "totalAUM": 18430000,
    "signature": (
        "Carlos Eduardo Martins\n"
        "Assessor de Investimentos\n"
        "CNPI-T 12345\n"
        "XP Investimentos\n"
        "(11) 91234-5678"
    ),
    "disclaimer": (
        "Este material é informativo e não constitui recomendação de investimento. "
        "Rentabilidade passada não é garantia de retorno futuro. "
        "Investimentos envolvem riscos, inclusive de perda do capital investido."
    ),
}

# Asset class display labels and colors
CLASS_LABELS = {
    "renda_fixa": "Fixed Income",
    "multimercado": "Multi-Market",
    "acoes": "Equities",
    "fiis": "REITs",
    "internacional": "International",
    "cripto": "Crypto",
}

CLASS_COLORS = {
    "renda_fixa": "#3B82F6",
    "multimercado": "#EC4899",
    "acoes": "#EDB92E",
    "fiis": "#10B981",
    "internacional": "#8B5CF6",
    "cripto": "#F97316",
}

PROFILE_LABELS = {
    "conservador": "Conservative",
    "moderado": "Moderate",
    "arrojado": "Aggressive",
    "agressivo": "Very Aggressive",
}

STATUS_MAP = {
    "up_to_date": {"label": "Up to date", "color": "#10B981"},
    "needs_follow_up": {"label": "Follow-up", "color": "#EDB92E"},
    "overdue": {"label": "Overdue", "color": "#EF4444"},
}
