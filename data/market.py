"""Market benchmarks, target allocations, and AAI profile data."""

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
    "conservador": {"renda_fixa": 70, "acoes": 10, "fiis": 10, "internacional": 8, "cripto": 2},
    "moderado":    {"renda_fixa": 45, "acoes": 25, "fiis": 15, "internacional": 12, "cripto": 3},
    "arrojado":    {"renda_fixa": 20, "acoes": 40, "fiis": 15, "internacional": 18, "cripto": 7},
    "agressivo":   {"renda_fixa": 10, "acoes": 45, "fiis": 10, "internacional": 25, "cripto": 10},
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
    "renda_fixa": "Renda Fixa",
    "acoes": "Ações",
    "fiis": "FIIs",
    "internacional": "Internacional",
    "cripto": "Cripto",
}

CLASS_COLORS = {
    "renda_fixa": "#3B82F6",
    "acoes": "#EDB92E",
    "fiis": "#10B981",
    "internacional": "#8B5CF6",
    "cripto": "#F97316",
}

PROFILE_LABELS = {
    "conservador": "Conservador",
    "moderado": "Moderado",
    "arrojado": "Arrojado",
    "agressivo": "Agressivo",
}

STATUS_MAP = {
    "up_to_date": {"label": "Em dia", "color": "#10B981"},
    "needs_follow_up": {"label": "Follow-up", "color": "#EDB92E"},
    "overdue": {"label": "Atrasado", "color": "#EF4444"},
}
