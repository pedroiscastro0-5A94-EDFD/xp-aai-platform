"""Market benchmarks, target allocations, and AAI profile data."""

# 12 months of historical monthly returns: Mar/25 → Feb/26
BENCHMARK_HISTORY = {
    "months": ["Mar/25", "Apr/25", "May/25", "Jun/25", "Jul/25", "Aug/25", "Sep/25", "Oct/25", "Nov/25", "Dec/25", "Jan/26", "Feb/26"],
    "cdi":      [1.12, 1.09, 1.13, 1.06, 1.08, 1.11, 1.09, 1.07, 1.06, 1.10, 1.08, 1.07],
    "ibovespa": [-3.20, 2.15, -1.80, 4.30, -0.60, 3.10, -2.40, 5.20, 1.80, -1.10, 2.90, 2.30],
    "ifix":     [0.90, 1.20, -0.40, 1.80, 0.60, 0.85, 0.50, 1.10, -0.30, 0.75, 0.80, 0.85],
    "sp500_brl":[-2.10, 4.50, -0.80, 5.20, 2.30, -1.60, 3.80, -0.40, 6.10, 1.20, -2.40, 3.10],
}

BENCHMARK_LABELS = {
    "cdi": "CDI",
    "ibovespa": "IBOV",
    "ifix": "IFIX",
    "sp500_brl": "S&P 500 (BRL)",
}

# February 2026 benchmarks
MARKET_BENCHMARKS = {
    "month": "2026-02",
    "cdi": {"monthly": 1.07, "ytd": 2.15, "twelveMonth": 13.20},
    "ibovespa": {"monthly": 2.30, "ytd": 5.10, "twelveMonth": 18.50},
    "ifix": {"monthly": 0.85, "ytd": 1.90, "twelveMonth": 10.20},
    "sp500_brl": {"monthly": 3.10, "ytd": 7.80, "twelveMonth": 25.30},
    "ipca": {"monthly": 0.45, "ytd": 0.92, "twelveMonth": 5.20},
    "selic": {"current": 14.25, "previous": 13.75},
    "dolar": {"current": 5.85, "monthlyChange": -1.20},
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
