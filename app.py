"""XP AAI Platform — Streamlit Application

A professional financial advisor platform powered by 6 AI agents.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import os
from datetime import datetime

from data.clients import MOCK_CLIENTS, MOCK_HOLDINGS, MOCK_TRANSACTIONS, COMMUNICATION_LOG
from data.market import (
    MARKET_BENCHMARKS, TARGET_ALLOCATIONS, AAI_PROFILE,
    CLASS_LABELS, CLASS_COLORS, PROFILE_LABELS, STATUS_MAP,
    BENCHMARK_HISTORY, BENCHMARK_LABELS,
)
from orchestrator import run_pipeline, generate_workflow_report

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="XP AAI Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Global */
    .stApp { background-color: #0A1628; }
    section[data-testid="stSidebar"] { background-color: #060E1A; border-right: 1px solid rgba(255,255,255,0.06); }
    .stApp header { background-color: rgba(6,14,26,0.8); backdrop-filter: blur(10px); }

    /* Gold accent */
    .gold { color: #EDB92E; }
    .gold-bg { background: linear-gradient(135deg, #EDB92E 0%, #F5D06B 100%); color: #0A1628; }

    /* Metric cards */
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 18px 20px;
    }
    .metric-label {
        font-size: 11px; color: #8896AB;
        text-transform: uppercase; letter-spacing: 1px;
        margin-bottom: 6px; font-family: monospace;
    }
    .metric-value {
        font-size: 22px; font-weight: 700; color: #F0F4F8;
        font-family: monospace;
    }
    .metric-value.accent { color: #EDB92E; }
    .metric-sub { font-size: 12px; color: #6B7B8F; margin-top: 4px; }

    /* Status badges */
    .status-badge {
        padding: 4px 10px; border-radius: 12px;
        font-size: 11px; font-weight: 600;
        display: inline-block;
    }
    .status-up_to_date { background: rgba(16,185,129,0.15); color: #10B981; }
    .status-needs_follow_up { background: rgba(237,185,46,0.15); color: #EDB92E; }
    .status-overdue { background: rgba(239,68,68,0.15); color: #EF4444; }

    /* Agent status */
    .agent-step {
        padding: 12px 16px; border-radius: 10px; margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.06);
        display: flex; align-items: center; gap: 12px;
    }
    .agent-pending { background: rgba(255,255,255,0.02); }
    .agent-running { background: rgba(237,185,46,0.08); border-color: rgba(237,185,46,0.3); }
    .agent-done { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.3); }

    /* Table styling */
    .dataframe { font-size: 13px !important; }
    .dataframe th { background: rgba(255,255,255,0.06) !important; color: #8896AB !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.5px; }
    .dataframe td { border-color: rgba(255,255,255,0.04) !important; }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Sidebar client list */
    .client-item {
        padding: 10px 14px; border-radius: 8px; margin: 2px 0;
        cursor: pointer; transition: all 0.2s;
        border: 1px solid transparent;
    }
    .client-item:hover { background: rgba(237,185,46,0.06); }
    .client-item.active { background: rgba(237,185,46,0.1); border-color: rgba(237,185,46,0.3); }
</style>
""", unsafe_allow_html=True)

# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def format_brl(value: float) -> str:
    """Format number as Brazilian currency."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_pct(value: float) -> str:
    """Format number as percentage with Brazilian notation."""
    return f"{value:,.2f}%".replace(".", ",")

def get_allocation_data(holdings: list) -> pd.DataFrame:
    """Calculate allocation by asset class."""
    data = {}
    for h in holdings:
        cls = h["class"]
        data[cls] = data.get(cls, 0) + h["weight"]
    rows = [
        {"class": cls, "label": CLASS_LABELS.get(cls, cls), "weight": round(w, 2), "color": CLASS_COLORS.get(cls, "#999")}
        for cls, w in data.items()
    ]
    return pd.DataFrame(rows)

def get_drift_data(client_profile: str, holdings: list, total_aum: float) -> pd.DataFrame:
    """Calculate allocation drift vs target."""
    target = TARGET_ALLOCATIONS.get(client_profile, TARGET_ALLOCATIONS["moderado"])
    current = {}
    for h in holdings:
        current[h["class"]] = current.get(h["class"], 0) + h["weight"]
    rows = []
    for cls, tgt in target.items():
        cur = current.get(cls, 0)
        drift = round(cur - tgt, 2)
        rows.append({
            "class": cls,
            "label": CLASS_LABELS.get(cls, cls),
            "target": tgt,
            "current": round(cur, 2),
            "drift": drift,
            "drift_amount": round((drift / 100) * total_aum, 2),
            "needs_action": abs(drift) > 5,
            "color": CLASS_COLORS.get(cls, "#999"),
        })
    return pd.DataFrame(rows)

def compute_client_monthly_history(holdings, target_12m_return=None):
    """Compute synthetic monthly returns for a client based on their portfolio weights.

    Each asset class in the portfolio is mapped to a market benchmark:
      renda_fixa → CDI, acoes → IBOV, fiis → IFIX,
      internacional → S&P 500 (BRL), cripto → 2× S&P 500 (BRL).
    The weighted combination gives a realistic month-by-month return series.
    If target_12m_return is provided, the series is scaled so the cumulative
    12-month return matches the stored value.
    """
    # Aggregate portfolio weights by asset class
    class_weights = {}
    for h in holdings:
        cls = h["class"]
        class_weights[cls] = class_weights.get(cls, 0) + h["weight"]
    total = sum(class_weights.values())
    if total > 0:
        class_weights = {k: v / total for k, v in class_weights.items()}

    # Map each asset class to its closest benchmark
    bench_map = {
        "renda_fixa": "cdi",
        "acoes": "ibovespa",
        "fiis": "ifix",
        "internacional": "sp500_brl",
        "cripto": "sp500_brl",  # amplified below
    }

    n_months = len(BENCHMARK_HISTORY["months"])
    monthly_returns = []
    for i in range(n_months):
        r = 0
        for cls, w in class_weights.items():
            bench_key = bench_map.get(cls, "cdi")
            bench_r = BENCHMARK_HISTORY[bench_key][i]
            if cls == "cripto":
                bench_r *= 2.0  # crypto is more volatile
            r += w * bench_r
        monthly_returns.append(r)

    # Scale the series so the cumulative 12M matches the stored client return
    if target_12m_return is not None:
        raw_cum = 1.0
        for r in monthly_returns:
            raw_cum *= (1 + r / 100)
        raw_total = (raw_cum - 1) * 100
        if abs(raw_total) > 0.01:
            scale = target_12m_return / raw_total
        else:
            scale = 1.0
        monthly_returns = [r * scale for r in monthly_returns]

    return [round(r, 2) for r in monthly_returns]


def metric_card(label: str, value: str, sub: str = "", accent: bool = False):
    """Render a metric card."""
    accent_class = "accent" if accent else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {accent_class}">{value}</div>
        {f'<div class="metric-sub">{sub}</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────

if "selected_client" not in st.session_state:
    st.session_state.selected_client = None
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = {}
if "agent_statuses" not in st.session_state:
    st.session_state.agent_statuses = {}

# Dynamic client/holdings stores — start with the mock data, grow as user adds clients
if "all_clients" not in st.session_state:
    st.session_state.all_clients = list(MOCK_CLIENTS)  # mutable copy
if "all_holdings" not in st.session_state:
    st.session_state.all_holdings = dict(MOCK_HOLDINGS)  # mutable copy
if "all_transactions" not in st.session_state:
    st.session_state.all_transactions = dict(MOCK_TRANSACTIONS)
if "next_client_num" not in st.session_state:
    st.session_state.next_client_num = len(MOCK_CLIENTS) + 1

# Also patch the orchestrator's data so pipeline works for new clients
from data import clients as _clients_mod
_clients_mod.MOCK_CLIENTS = st.session_state.all_clients
_clients_mod.MOCK_HOLDINGS = st.session_state.all_holdings
_clients_mod.MOCK_TRANSACTIONS = st.session_state.all_transactions

# Simulated CRM database (for the "Import from CRM" feature)
CRM_DATABASE = [
    {"cpf": "123.456.789-00", "name": "Fernando Gomes", "email": "fernando.gomes@email.com", "phone": "(11) 98888-1234", "birthDate": "1978-04-22", "profile": "arrojado", "monthlyIncome": 45000, "investmentGoals": "Crescimento de longo prazo, horizonte 25 anos", "notes": "Empresário do setor de tecnologia."},
    {"cpf": "987.654.321-00", "name": "Juliana Ribeiro", "email": "juliana.ribeiro@email.com", "phone": "(21) 97777-5678", "birthDate": "1965-11-08", "profile": "conservador", "monthlyIncome": 22000, "investmentGoals": "Preservação de capital e renda passiva", "notes": "Aposentada, prioriza segurança."},
    {"cpf": "456.789.123-00", "name": "Thiago Nascimento", "email": "thiago.nasc@empresa.com", "phone": "(11) 96666-9012", "birthDate": "1990-07-15", "profile": "agressivo", "monthlyIncome": 70000, "investmentGoals": "Multiplicar patrimônio rapidamente, aceita risco alto", "notes": "CTO de startup. Conhecimento avançado em cripto."},
    {"cpf": "321.654.987-00", "name": "Beatriz Monteiro", "email": "bia.monteiro@gmail.com", "phone": "(31) 95555-3456", "birthDate": "1982-01-30", "profile": "moderado", "monthlyIncome": 32000, "investmentGoals": "Aposentadoria em 18 anos + reserva de emergência", "notes": "Médica, pouco tempo para acompanhar mercado."},
]

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    # ── Header ─────────────────────────────────────────────
    st.markdown("### 📊 XP AAI Platform")
    st.markdown(
        f"<span style='color:#6B7B8F;font-size:12px'>{AAI_PROFILE['name']} — {AAI_PROFILE['cnpi']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:10px 0 14px 0'>", unsafe_allow_html=True)

    # ── Navigation ─────────────────────────────────────────
    st.markdown(
        "<span style='color:#4B5B6F;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;font-weight:600'>NAVIGATE</span>",
        unsafe_allow_html=True,
    )
    st.markdown("")
    page = st.radio(
        "Navigate",
        [
            "📊  Overview",
            "👤  Client Portfolio",
            "📄  Reports",
            "⚖️  Rebalancing",
            "➕  Add Client",
        ],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:14px 0'>", unsafe_allow_html=True)

    # ── Clients ────────────────────────────────────────────
    n_clients = len(st.session_state.all_clients)
    st.markdown(
        f"<span style='color:#4B5B6F;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;font-weight:600'>CLIENTS ({n_clients})</span>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    for cl in st.session_state.all_clients:
        status_info = STATUS_MAP.get(cl["status"], {})
        status_color = status_info.get("color", "#999")
        status_label = status_info.get("label", cl["status"])
        is_selected = st.session_state.selected_client == cl["id"]

        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                f"{'▸ ' if is_selected else ''}{cl['name']}",
                key=f"client_{cl['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_client = cl["id"]
                st.rerun()
        with col2:
            st.markdown(
                f"<div style='width:8px;height:8px;border-radius:50%;background:{status_color};margin-top:12px' title='{status_label}'></div>",
                unsafe_allow_html=True,
            )

    # ── Footer ─────────────────────────────────────────────
    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:10px 0 8px 0'>", unsafe_allow_html=True)
    total_aum_all = sum(c["totalAUM"] for c in st.session_state.all_clients)
    st.markdown(f"""
    <div style='font-size:10px;color:#4B5B6F;line-height:2'>
        <span style='margin-right:10px'>🟢 Up to date</span>
        <span style='margin-right:10px'>🟡 Follow-up</span>
        <span>🔴 Overdue</span><br>
        <span style='color:#6B7B8F'>Total AUM: {format_brl(total_aum_all)}</span>
    </div>
    """, unsafe_allow_html=True)

# ─── GET SELECTED CLIENT DATA ────────────────────────────────────────────────

selected = st.session_state.selected_client
client = next((c for c in st.session_state.all_clients if c["id"] == selected), None) if selected else None
portfolio = st.session_state.all_holdings.get(selected) if selected else None
transactions = st.session_state.all_transactions.get(selected, []) if selected else []

# ─── PAGE: OVERVIEW (CLIENT DASHBOARD) ───────────────────────────────────────

if page == "📊  Overview":
    st.markdown("## Overview")
    st.markdown(f"<span style='color:#6B7B8F'>Portfolio snapshot — {datetime.now().strftime('%B %Y')}</span>", unsafe_allow_html=True)

    # Top metrics
    total_aum = sum(c["totalAUM"] for c in st.session_state.all_clients)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total AUM", format_brl(total_aum), f"{len(st.session_state.all_clients)} clients", accent=True)
    with col2:
        metric_card("Selic Rate", f"{MARKET_BENCHMARKS['selic']['current']}%", f"Previous: {MARKET_BENCHMARKS['selic']['previous']}%")
    with col3:
        metric_card("CDI (Month)", format_pct(MARKET_BENCHMARKS["cdi"]["monthly"]), f"12M: {format_pct(MARKET_BENCHMARKS['cdi']['twelveMonth'])}")
    with col4:
        metric_card("IBOV (Month)", format_pct(MARKET_BENCHMARKS["ibovespa"]["monthly"]), f"12M: {format_pct(MARKET_BENCHMARKS['ibovespa']['twelveMonth'])}")

    st.markdown("")

    # Benchmarks chart + client list
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Market Benchmarks")

        # Row 1: Index picker + timeframe
        sel_col1, sel_col2 = st.columns([3, 2])
        with sel_col1:
            selected_benchmarks = st.multiselect(
                "Indexes",
                options=list(BENCHMARK_LABELS.keys()),
                default=["cdi", "ibovespa"],
                format_func=lambda x: BENCHMARK_LABELS[x],
                label_visibility="collapsed",
            )
        with sel_col2:
            timeframe = st.radio(
                "Timeframe",
                options=["3M", "6M", "12M"],
                horizontal=True,
                index=2,
                label_visibility="collapsed",
            )

        # Row 2: Optional client portfolio overlay
        client_options_ids = [None] + [c["id"] for c in st.session_state.all_clients]
        client_name_map = {c["id"]: c["name"] for c in st.session_state.all_clients}
        compare_client_id = st.selectbox(
            "Compare with client",
            options=client_options_ids,
            format_func=lambda x: "Compare with a client portfolio →" if x is None else f"📊 {client_name_map[x]}",
            label_visibility="collapsed",
        )

        timeframe_start = {"3M": 9, "6M": 6, "12M": 0}
        start_idx = timeframe_start.get(timeframe, 0)
        display_months = BENCHMARK_HISTORY["months"][start_idx:]
        bench_colors = {"cdi": "#3B82F6", "ibovespa": "#EDB92E", "ifix": "#10B981", "sp500_brl": "#8B5CF6"}

        fig = go.Figure()
        for bench in (selected_benchmarks if selected_benchmarks else ["cdi", "ibovespa"]):
            monthly_returns = BENCHMARK_HISTORY[bench][start_idx:]
            x_labels = ["Start"] + list(display_months)
            y_vals = [0.0]
            running = 1.0
            for r in monthly_returns:
                running *= (1 + r / 100)
                y_vals.append(round((running - 1) * 100, 2))
            fig.add_trace(go.Scatter(
                name=BENCHMARK_LABELS[bench],
                x=x_labels,
                y=y_vals,
                mode="lines+markers",
                line=dict(color=bench_colors.get(bench, "#999"), width=2),
                marker=dict(size=4),
            ))

        # Client portfolio overlay — historical monthly line
        if compare_client_id:
            compare_portfolio = st.session_state.all_holdings.get(compare_client_id)
            if compare_portfolio:
                compare_name = client_name_map[compare_client_id]
                client_monthly = compute_client_monthly_history(
                    compare_portfolio["holdings"],
                    target_12m_return=compare_portfolio.get("twelveMonthReturn"),
                )
                # Trim to selected timeframe
                client_monthly_trimmed = client_monthly[start_idx:]
                # Build cumulative return series (same logic as benchmarks)
                x_labels_client = ["Start"] + list(display_months)
                y_client = [0.0]
                running_c = 1.0
                for r in client_monthly_trimmed:
                    running_c *= (1 + r / 100)
                    y_client.append(round((running_c - 1) * 100, 2))
                fig.add_trace(go.Scatter(
                    name=f"{compare_name} (portfolio)",
                    x=x_labels_client,
                    y=y_client,
                    mode="lines+markers",
                    line=dict(color="#F59E0B", width=2.5, dash="dash"),
                    marker=dict(size=5, symbol="diamond"),
                ))

        fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.12)", line_width=1)
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#8896AB", height=290, margin=dict(l=10, r=10, t=10, b=55),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            yaxis_title="Cumulative Return (%)",
        )
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)", tickangle=-35)
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("#### Client Status")
        for c in st.session_state.all_clients:
            status_info = STATUS_MAP.get(c["status"], {})
            profile_label = PROFILE_LABELS.get(c["profile"], c["profile"])
            col_a, col_b, col_c = st.columns([3, 2, 1])
            with col_a:
                st.markdown(f"**{c['name']}**")
                st.markdown(f"<span style='color:#6B7B8F;font-size:12px'>{profile_label} · {format_brl(c['totalAUM'])}</span>", unsafe_allow_html=True)
            with col_b:
                holdings_data = st.session_state.all_holdings.get(c["id"])
                if holdings_data:
                    ret = holdings_data["monthlyReturn"]
                    color = "#10B981" if ret > 0 else "#EF4444"
                    st.markdown(f"<span style='color:{color};font-family:monospace;font-size:14px'>{format_pct(ret)}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:#6B7B8F;font-size:11px'>this month</span>", unsafe_allow_html=True)
            with col_c:
                st.markdown(f"<span class='status-badge status-{c['status']}'>{status_info.get('label', c['status'])}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color:rgba(255,255,255,0.04);margin:4px 0'>", unsafe_allow_html=True)

# ─── PAGE: CLIENT PORTFOLIO ───────────────────────────────────────────────────

elif page == "👤  Client Portfolio":
    if not client or not portfolio:
        st.markdown("## Client Portfolio")
        st.info("👈 Select a client from the sidebar to view their portfolio details.")
    else:
        st.markdown(f"## {client['name']}")
        st.markdown(f"<span style='color:#6B7B8F'>{PROFILE_LABELS.get(client['profile'], '')} · Client since {client['accountSince']} · Goals: {client['investmentGoals']}</span>", unsafe_allow_html=True)

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("AUM", format_brl(client["totalAUM"]), accent=True)
        with col2:
            metric_card("Monthly Return", format_pct(portfolio["monthlyReturn"]), f"CDI: {format_pct(MARKET_BENCHMARKS['cdi']['monthly'])}")
        with col3:
            metric_card("YTD Return", format_pct(portfolio["ytdReturn"]), f"CDI YTD: {format_pct(MARKET_BENCHMARKS['cdi']['ytd'])}")
        with col4:
            metric_card("12M Return", format_pct(portfolio["twelveMonthReturn"]), f"CDI 12M: {format_pct(MARKET_BENCHMARKS['cdi']['twelveMonth'])}")

        st.markdown("")

        # Allocation chart + investor profile
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Allocation by Asset Class")
            alloc_df = get_allocation_data(portfolio["holdings"])
            fig = px.pie(
                alloc_df, values="weight", names="label",
                color="label",
                color_discrete_map={row["label"]: row["color"] for _, row in alloc_df.iterrows()},
                hole=0.55,
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#8896AB", height=350, margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15),
            )
            fig.update_traces(textinfo="percent+label", textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("#### Investor Profile")
            profile_label = PROFILE_LABELS.get(client["profile"], client["profile"])
            st.markdown(f"""
            - **Profile:** {profile_label}
            - **Goals:** {client['investmentGoals']}
            - **Monthly Income:** {format_brl(client['monthlyIncome'])}
            - **Client Since:** {client['accountSince']}
            - **Last Contact:** {client['lastContact']}
            - **Notes:** {client.get('notes', 'N/A')}
            """)

            # Benchmark comparison — horizontal bar (this month)
            st.markdown("#### Performance vs. Benchmarks")
            st.markdown("<span style='color:#6B7B8F;font-size:11px'>Monthly return comparison</span>", unsafe_allow_html=True)

            port_ret = portfolio["monthlyReturn"]
            comp_data = [
                {"label": "Portfolio", "value": port_ret, "color": "#EDB92E"},
                {"label": "CDI",       "value": MARKET_BENCHMARKS["cdi"]["monthly"],       "color": "#3B82F6"},
                {"label": "IBOV",      "value": MARKET_BENCHMARKS["ibovespa"]["monthly"],  "color": "#10B981"},
                {"label": "IFIX",      "value": MARKET_BENCHMARKS["ifix"]["monthly"],      "color": "#8B5CF6"},
            ]
            fig2 = go.Figure()
            for item in comp_data:
                fig2.add_trace(go.Bar(
                    name=item["label"],
                    x=[item["value"]],
                    y=[item["label"]],
                    orientation="h",
                    marker_color=item["color"],
                    text=f"{item['value']:+.2f}%",
                    textposition="outside",
                    textfont=dict(color=item["color"], size=12),
                    width=0.5,
                ))
            fig2.add_vline(x=0, line_color="rgba(255,255,255,0.15)", line_width=1)
            fig2.update_layout(
                barmode="overlay",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#8896AB", height=220,
                margin=dict(l=10, r=60, t=10, b=20),
                showlegend=False,
                xaxis_title="Return (%)",
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Holdings table
        st.markdown("#### Holdings")
        holdings_df = pd.DataFrame(portfolio["holdings"])
        holdings_df["market_value"] = holdings_df["currentPrice"] * holdings_df["quantity"]
        holdings_df["pnl"] = (holdings_df["currentPrice"] - holdings_df["avgPrice"]) * holdings_df["quantity"]
        holdings_df["pnl_pct"] = ((holdings_df["currentPrice"] / holdings_df["avgPrice"]) - 1) * 100

        display_df = holdings_df[["asset", "ticker", "class", "quantity", "avgPrice", "currentPrice", "pnl", "pnl_pct", "weight"]].copy()
        display_df.columns = ["Asset", "Ticker", "Class", "Qty", "Avg Price", "Current Price", "P&L (R$)", "P&L (%)", "Weight (%)"]
        display_df["Class"] = display_df["Class"].map(CLASS_LABELS)
        display_df["Avg Price"] = display_df["Avg Price"].apply(format_brl)
        display_df["Current Price"] = display_df["Current Price"].apply(format_brl)
        display_df["P&L (R$)"] = display_df["P&L (R$)"].apply(format_brl)
        display_df["P&L (%)"] = display_df["P&L (%)"].apply(lambda x: format_pct(x))
        display_df["Weight (%)"] = display_df["Weight (%)"].apply(lambda x: f"{x:.1f}%")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Transactions
        if transactions:
            st.markdown("#### Recent Transactions — February 2026")
            tx_df = pd.DataFrame(transactions)
            tx_df["date"] = pd.to_datetime(tx_df["date"]).dt.strftime("%d/%m/%Y")
            tx_df["total"] = tx_df["total"].apply(format_brl)
            tx_df["type"] = tx_df["type"].map({"buy": "Buy", "sell": "Sell", "dividend": "Dividend"})
            st.dataframe(
                tx_df[["date", "type", "asset", "ticker", "quantity", "total", "reason"]].rename(
                    columns={"date": "Date", "type": "Type", "asset": "Asset", "ticker": "Ticker", "quantity": "Qty", "total": "Total", "reason": "Reason"}
                ),
                use_container_width=True, hide_index=True,
            )

# ─── PAGE: REPORTS ────────────────────────────────────────────────────────────

elif page == "📄  Reports":
    st.markdown("## Monthly Report Generator")

    if not client or not portfolio:
        st.info("👈 Select a client from the sidebar, then click 'Generate Monthly Report' to run the 6-agent pipeline.")
    else:
        st.markdown(f"**Client:** {client['name']} — {PROFILE_LABELS.get(client['profile'], '')} — {format_brl(client['totalAUM'])}")
        st.markdown("")

        # Agent pipeline visualization
        agents_list = [
            ("Portfolio Analyst", "Calculates returns, P&L and allocation by asset class"),
            ("Macro Analyst", "Extracts Selic, IPCA, GDP and FX projections from XP macro report"),
            ("Recommendation Engine", "Compares allocation vs. targets, flags drift, generates CVM-compliant suggestions"),
            ("Letter Writer", "Generates professional 2-page monthly investment letter"),
            ("Compliance Reviewer", "CVM review — no buy/sell language, disclaimer present"),
            ("Doc Formatter", "Creates professional .docx with XP branding"),
        ]

        col_pipeline, col_output = st.columns([1, 1])

        with col_pipeline:
            st.markdown("#### Agent Pipeline")

            # Status display
            for agent_name, description in agents_list:
                status = st.session_state.agent_statuses.get(f"{selected}_{agent_name}", "pending")
                icon = {"pending": "⏸️", "running": "⏳", "done": "✅", "error": "❌"}.get(status, "⏸️")
                bg = {"pending": "rgba(255,255,255,0.02)", "running": "rgba(237,185,46,0.08)", "done": "rgba(16,185,129,0.08)"}.get(status, "rgba(255,255,255,0.02)")
                border = {"running": "rgba(237,185,46,0.3)", "done": "rgba(16,185,129,0.3)"}.get(status, "rgba(255,255,255,0.06)")

                st.markdown(f"""
                <div style="padding:12px 16px;border-radius:10px;margin-bottom:8px;background:{bg};border:1px solid {border};display:flex;align-items:center;gap:12px">
                    <span style="font-size:18px">{icon}</span>
                    <div>
                        <div style="font-weight:600;font-size:13px">{agent_name}</div>
                        <div style="font-size:11px;color:#6B7B8F">{description}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Generate button
            st.markdown("")
            if st.button("Generate Monthly Report", type="primary", use_container_width=True):
                # Reset statuses
                for agent_name, _ in agents_list:
                    st.session_state.agent_statuses[f"{selected}_{agent_name}"] = "pending"

                progress_container = st.empty()

                def update_progress(agent_name, status, result=None):
                    st.session_state.agent_statuses[f"{selected}_{agent_name}"] = status

                # Run pipeline
                with st.spinner("Running 6-agent pipeline..."):
                    try:
                        results = run_pipeline(selected, progress_callback=update_progress)
                        st.session_state.pipeline_results[selected] = results
                    except Exception as e:
                        st.error(f"Pipeline error: {e}")
                st.rerun()

        with col_output:
            st.markdown("#### Output")
            results = st.session_state.pipeline_results.get(selected)

            if results:
                # Show compliance result
                compliance = results.get("compliance", {})
                passed = compliance.get("passed", False)
                score = compliance.get("score", 0)

                if passed:
                    st.success(f"✅ Compliance: PASSED ({score}/100)")
                else:
                    st.warning(f"⚠️ Compliance: NEEDS REVIEW ({score}/100)")

                # Show violations/warnings
                violations = compliance.get("violations", [])
                warnings = compliance.get("warnings", [])
                if violations:
                    with st.expander(f"Violations ({len(violations)})"):
                        for v in violations:
                            st.markdown(f"- **{v['severity'].upper()}**: {v['message']}")
                if warnings:
                    with st.expander(f"Warnings ({len(warnings)})"):
                        for w in warnings:
                            st.markdown(f"- {w['message']}")

                # Show letter preview
                letter = results.get("letter", {})
                st.markdown("---")
                st.markdown("#### Letter Preview")
                letter_text = letter.get("letter_text", "")
                word_count = letter.get("word_count", 0)
                st.markdown(f"<span style='color:#6B7B8F;font-size:11px'>{word_count} words</span>", unsafe_allow_html=True)

                # Render as a styled document preview
                escaped_text = letter_text.replace("\n", "<br>")
                st.markdown(
                    f"""
                    <div style="
                        background: #ffffff;
                        color: #1a1a1a;
                        border-radius: 8px;
                        padding: 32px 36px;
                        margin: 8px 0 16px 0;
                        max-height: 500px;
                        overflow-y: auto;
                        font-family: 'Georgia', 'Times New Roman', serif;
                        font-size: 14px;
                        line-height: 1.7;
                        border: 1px solid rgba(255,255,255,0.1);
                        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
                    ">{escaped_text}</div>
                    """,
                    unsafe_allow_html=True,
                )

                # Download button
                doc_info = results.get("document", {})
                output_path = doc_info.get("output_path", "")
                if output_path and os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download .docx",
                            data=f.read(),
                            file_name=os.path.basename(output_path),
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )

                # Show agent details in expanders
                st.markdown("---")
                st.markdown("#### Agent Details")

                with st.expander("Portfolio Analyst Output"):
                    pa = results.get("portfolio_analysis", {})
                    st.json({
                        "summary": pa.get("summary"),
                        "returns": pa.get("returns"),
                        "benchmark_comparison": pa.get("benchmark_comparison", {}).get("monthly"),
                        "alerts": pa.get("alerts"),
                    })

                with st.expander("Macro Analyst Output"):
                    ma = results.get("macro_analysis", {})
                    st.json(ma.get("key_projections"))
                    st.markdown(ma.get("analysis_text", ""))

                with st.expander("Recommendation Engine Output"):
                    rec = results.get("recommendations", {})
                    st.markdown(rec.get("recommendation_text", ""))
                    st.json(rec.get("drift_analysis"))

            else:
                st.markdown("<div style='text-align:center;padding:60px;color:#6B7B8F'>Click 'Generate Monthly Report' to run the 6-agent pipeline</div>", unsafe_allow_html=True)

# ─── PAGE: REBALANCING ────────────────────────────────────────────────────────

elif page == "⚖️  Rebalancing":
    st.markdown("## Rebalancing")

    if not client or not portfolio:
        st.info("👈 Select a client from the sidebar to view rebalancing recommendations.")
    else:
        st.markdown(f"**Client:** {client['name']} — {PROFILE_LABELS.get(client['profile'], '')} — {format_brl(client['totalAUM'])}")
        st.markdown("")

        drift_df = get_drift_data(client["profile"], portfolio["holdings"], client["totalAUM"])

        # ── Drift chart (full width) ──────────────────────────────────────
        st.markdown("#### Allocation Drift vs. Target")
        st.markdown(
            "<span style='color:#6B7B8F;font-size:12px'>How far each asset class is from its target weight. "
            "Red = overweight (too much), blue = underweight (too little). "
            "Action required outside the ±5pp dashed lines.</span>",
            unsafe_allow_html=True,
        )

        drift_colors = [
            "#EF4444" if d > 5 else "#3B82F6" if d < -5 else "#6B7B8F"
            for d in drift_df["drift"]
        ]
        drift_fig = go.Figure()
        drift_fig.add_trace(go.Bar(
            x=drift_df["label"],
            y=drift_df["drift"],
            marker_color=drift_colors,
            text=[f"{d:+.1f}pp" for d in drift_df["drift"]],
            textposition="outside",
            textfont=dict(size=12),
            hovertemplate="<b>%{x}</b><br>Drift: %{y:+.1f}pp<br><extra></extra>",
            width=0.5,
        ))

        # Threshold lines at ±5pp
        drift_fig.add_hline(y=5,  line_dash="dot", line_color="rgba(239,68,68,0.45)", line_width=1.5)
        drift_fig.add_hline(y=-5, line_dash="dot", line_color="rgba(59,130,246,0.45)", line_width=1.5)
        drift_fig.add_hline(y=0,  line_color="rgba(255,255,255,0.15)", line_width=1)

        y_range = max(abs(drift_df["drift"].max()), abs(drift_df["drift"].min()), 8) + 4
        drift_fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#8896AB", height=320,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=False,
            yaxis_title="Drift (pp vs. target)",
            yaxis=dict(range=[-y_range, y_range], zeroline=False, gridcolor="rgba(255,255,255,0.06)"),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(drift_fig, use_container_width=True)

        # ── Summary table + actions ───────────────────────────────────────
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Current vs. Target")
            for _, row in drift_df.iterrows():
                drift = row["drift"]
                bar_color = "#EF4444" if drift > 5 else "#3B82F6" if drift < -5 else "#10B981"
                status_icon = "🔴" if drift > 5 else "🔵" if drift < -5 else "✅"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;padding:9px 14px;border-radius:8px;background:rgba(255,255,255,0.02);margin-bottom:5px;border-left:3px solid {bar_color}">
                    <div>
                        <span style="font-size:13px">{status_icon} <strong>{row['label']}</strong></span><br>
                        <span style="font-size:11px;color:#6B7B8F">Target {row['target']}% → Current {row['current']}%</span>
                    </div>
                    <span style="font-family:monospace;color:{bar_color};font-weight:700">{drift:+.1f}pp</span>
                </div>
                """, unsafe_allow_html=True)

        with col_right:
            if any(drift_df["needs_action"]):
                st.markdown("#### Action Required")
                for _, row in drift_df[drift_df["needs_action"]].iterrows():
                    direction = "Reduce" if row["drift"] > 0 else "Increase"
                    amount = abs(row["drift_amount"])
                    icon = "🔻" if row["drift"] > 0 else "🔺"
                    st.markdown(f"""
                    <div style="padding:10px 14px;border-radius:8px;background:rgba(255,255,255,0.02);margin-bottom:6px;border:1px solid rgba(255,255,255,0.08)">
                        <div style="font-weight:600">{icon} {row['label']}</div>
                        <div style="font-size:12px;color:#8896AB;margin-top:2px">{direction} by ~{format_brl(amount)}</div>
                        <div style="font-size:11px;color:#6B7B8F">Drift: {row['drift']:+.1f}pp</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("#### Action Required")
                st.markdown("<span style='color:#10B981'>✅ Portfolio is within target ranges. No rebalancing needed.</span>", unsafe_allow_html=True)

        # Position-level alerts
        st.markdown("---")
        st.markdown("#### Position Alerts")
        holdings_df = pd.DataFrame(portfolio["holdings"])
        holdings_df["pnl_pct"] = ((holdings_df["currentPrice"] / holdings_df["avgPrice"]) - 1) * 100

        extreme = holdings_df[(holdings_df["pnl_pct"] < -25) | (holdings_df["pnl_pct"] > 30)].sort_values("pnl_pct")
        if len(extreme) > 0:
            for _, row in extreme.iterrows():
                pnl = row["pnl_pct"]
                color = "#EF4444" if pnl < 0 else "#10B981"
                icon = "🔴" if pnl < 0 else "🟢"
                label = "EXTREME LOSS" if pnl < -25 else "STRONG GAIN"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-radius:8px;background:rgba(255,255,255,0.02);margin-bottom:6px;border:1px solid rgba(255,255,255,0.06)">
                    <div style="display:flex;align-items:center;gap:10px">
                        <span style="font-size:16px">{icon}</span>
                        <div>
                            <div style="font-weight:600">{row['asset']} ({row['ticker']})</div>
                            <div style="font-size:11px;color:#6B7B8F">{CLASS_LABELS.get(row['class'], '')} · Weight: {row['weight']:.1f}%</div>
                        </div>
                    </div>
                    <div style="text-align:right">
                        <div style="font-family:monospace;color:{color};font-size:16px;font-weight:700">{pnl:+.1f}%</div>
                        <div style="font-size:10px;color:{color};font-weight:600">{label}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#6B7B8F'>No extreme positions detected. All holdings within normal ranges.</span>", unsafe_allow_html=True)

# ─── PAGE: ADD CLIENT ─────────────────────────────────────────────────────────

elif page == "➕  Add Client":
    st.markdown("## Add New Client")
    st.markdown("<span style='color:#6B7B8F'>Add a client via CRM import or manual entry</span>", unsafe_allow_html=True)
    st.markdown("")

    tab_crm, tab_manual = st.tabs(["🔗 Import from CRM", "✏️ Manual Entry"])

    # ─── TAB 1: CRM IMPORT ───────────────────────────────────────────────
    with tab_crm:
        st.markdown("#### Search XP CRM")
        st.markdown("<span style='color:#6B7B8F;font-size:12px'>Simulated CRM lookup — search by client name or CPF</span>", unsafe_allow_html=True)
        st.markdown("")

        crm_query = st.text_input("Search by name or CPF", placeholder="e.g. Fernando or 123.456...")

        if crm_query:
            q = crm_query.lower().strip()
            matches = [r for r in CRM_DATABASE if q in r["name"].lower() or q in r["cpf"]]

            if not matches:
                st.warning("No matching clients found in CRM. Try a different name or CPF.")
            else:
                for idx, record in enumerate(matches):
                    profile_label = PROFILE_LABELS.get(record["profile"], record["profile"])
                    st.markdown(f"""
                    <div style="padding:16px 20px;border-radius:12px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);margin-bottom:12px">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <div>
                                <div style="font-weight:700;font-size:16px">{record['name']}</div>
                                <div style="font-size:12px;color:#6B7B8F;margin-top:4px">CPF: {record['cpf']} · {profile_label} · {record['email']}</div>
                                <div style="font-size:12px;color:#8896AB;margin-top:2px">Goals: {record['investmentGoals']}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Import {record['name']}", key=f"crm_import_{idx}", type="primary"):
                        # Create new client from CRM data
                        num = st.session_state.next_client_num
                        new_id = f"cli_{num:03d}"
                        st.session_state.next_client_num = num + 1

                        new_client = {
                            "id": new_id,
                            "name": record["name"],
                            "email": record["email"],
                            "phone": record["phone"],
                            "birthDate": record["birthDate"],
                            "cpf": record["cpf"][:3] + ".***.***-" + record["cpf"][-2:],
                            "profile": record["profile"],
                            "investmentGoals": record["investmentGoals"],
                            "monthlyIncome": record["monthlyIncome"],
                            "totalAUM": 0,
                            "accountSince": datetime.now().strftime("%Y-%m-%d"),
                            "lastContact": datetime.now().strftime("%Y-%m-%d"),
                            "nextReview": datetime.now().strftime("%Y-%m-%d"),
                            "status": "needs_follow_up",
                            "notes": record["notes"] + " (Imported from CRM)",
                        }

                        # Empty portfolio — advisor will fill in later
                        new_holdings = {
                            "holdings": [],
                            "monthlyReturn": 0.0,
                            "ytdReturn": 0.0,
                            "twelveMonthReturn": 0.0,
                        }

                        st.session_state.all_clients.append(new_client)
                        st.session_state.all_holdings[new_id] = new_holdings
                        st.session_state.all_transactions[new_id] = []
                        st.session_state.selected_client = new_id

                        st.success(f"✅ {record['name']} imported! Select them in the sidebar to add their portfolio.")
                        st.rerun()
        else:
            st.markdown("")
            st.markdown("<span style='color:#6B7B8F'>Available in CRM simulation:</span>", unsafe_allow_html=True)
            for r in CRM_DATABASE:
                st.markdown(f"- **{r['name']}** — {r['cpf']} — {PROFILE_LABELS.get(r['profile'], '')}")

    # ─── TAB 2: MANUAL ENTRY ─────────────────────────────────────────────
    with tab_manual:
        st.markdown("#### Client Information")
        st.markdown("")

        # Track how many portfolio rows to show
        if "num_positions" not in st.session_state:
            st.session_state.num_positions = 1
        # Form version counter — incremented on submit to reset all widget keys
        if "form_version" not in st.session_state:
            st.session_state.form_version = 0
        # Success message flag
        if "client_added_msg" not in st.session_state:
            st.session_state.client_added_msg = None

        # Show success message from previous submit (persists across rerun)
        if st.session_state.client_added_msg:
            st.success(st.session_state.client_added_msg)
            st.session_state.client_added_msg = None

        fv = st.session_state.form_version  # short alias for key prefix

        # Client info section
        col_a, col_b = st.columns(2)
        with col_a:
            f_name = st.text_input("Full Name *", placeholder="João da Silva", key=f"f_name_{fv}")
            f_email = st.text_input("Email", placeholder="joao@email.com", key=f"f_email_{fv}")
            f_phone = st.text_input("Phone", placeholder="(11) 99999-9999", key=f"f_phone_{fv}")
            f_profile = st.selectbox("Risk Profile *", ["moderado", "conservador", "arrojado", "agressivo"], format_func=lambda x: PROFILE_LABELS.get(x, x), key=f"f_profile_{fv}")

        with col_b:
            f_goals = st.text_input("Investment Goals *", placeholder="Aposentadoria em 20 anos", key=f"f_goals_{fv}")
            f_income = st.number_input("Monthly Income (R$)", min_value=0, value=0, step=1000, key=f"f_income_{fv}")
            f_notes = st.text_area("Notes", placeholder="Client preferences, special requests...", height=100, key=f"f_notes_{fv}")

        # Portfolio section
        st.markdown("---")
        st.markdown("#### Portfolio Positions")
        st.markdown("<span style='color:#6B7B8F;font-size:12px'>Add each asset in the client's portfolio. Weight (%) should add up to 100.</span>", unsafe_allow_html=True)
        st.markdown("")

        # Column headers
        header_cols = st.columns([2, 1.2, 1.2, 1, 1.2, 1.2, 0.8])
        header_cols[0].markdown("**Asset Name**")
        header_cols[1].markdown("**Ticker**")
        header_cols[2].markdown("**Class**")
        header_cols[3].markdown("**Qty**")
        header_cols[4].markdown("**Avg Price**")
        header_cols[5].markdown("**Current Price**")
        header_cols[6].markdown("**Weight %**")

        class_options = list(CLASS_LABELS.keys())

        # Render each position row — widgets use unique keys, values read at submit
        for i in range(st.session_state.num_positions):
            cols = st.columns([2, 1.2, 1.2, 1, 1.2, 1.2, 0.8])
            cols[0].text_input("asset", key=f"pos_asset_{fv}_{i}", label_visibility="collapsed", placeholder="Tesouro IPCA+")
            cols[1].text_input("ticker", key=f"pos_ticker_{fv}_{i}", label_visibility="collapsed", placeholder="NTNB35")
            cols[2].selectbox("class", class_options, key=f"pos_class_{fv}_{i}", label_visibility="collapsed", format_func=lambda x: CLASS_LABELS.get(x, x))
            cols[3].number_input("qty", value=0, min_value=0, key=f"pos_qty_{fv}_{i}", label_visibility="collapsed")
            cols[4].number_input("avg", value=0.0, min_value=0.0, step=0.01, key=f"pos_avg_{fv}_{i}", label_visibility="collapsed")
            cols[5].number_input("cur", value=0.0, min_value=0.0, step=0.01, key=f"pos_cur_{fv}_{i}", label_visibility="collapsed")
            cols[6].number_input("w", value=0.0, min_value=0.0, max_value=100.0, step=0.1, key=f"pos_w_{fv}_{i}", label_visibility="collapsed")

        # Add / Remove position buttons
        btn_col1, btn_col2, _ = st.columns([1, 1, 4])
        with btn_col1:
            if st.button("➕ Add Position", use_container_width=True):
                st.session_state.num_positions += 1
                st.rerun()
        with btn_col2:
            if st.session_state.num_positions > 1:
                if st.button("🗑️ Remove Last", use_container_width=True):
                    st.session_state.num_positions -= 1
                    st.rerun()

        # Weight total check — read directly from widget keys
        total_weight = sum(
            st.session_state.get(f"pos_w_{fv}_{i}", 0.0)
            for i in range(st.session_state.num_positions)
        )
        weight_color = "#10B981" if abs(total_weight - 100) < 1 else "#EF4444" if total_weight > 0 else "#6B7B8F"
        st.markdown(f"<div style='text-align:right;font-family:monospace;color:{weight_color};font-size:13px;margin-top:4px'>Total weight: {total_weight:.1f}%</div>", unsafe_allow_html=True)

        # Returns section
        st.markdown("")
        st.markdown("#### Returns (optional)")
        ret_cols = st.columns(3)
        f_monthly = ret_cols[0].number_input("Monthly Return (%)", value=0.0, step=0.01, key=f"f_monthly_{fv}")
        f_ytd = ret_cols[1].number_input("YTD Return (%)", value=0.0, step=0.01, key=f"f_ytd_{fv}")
        f_12m = ret_cols[2].number_input("12-Month Return (%)", value=0.0, step=0.01, key=f"f_12m_{fv}")

        # Submit button
        st.markdown("---")
        if st.button("Create Client", type="primary", use_container_width=True):
            # Validation
            errors = []
            if not f_name.strip():
                errors.append("Client name is required")
            if not f_goals.strip():
                errors.append("Investment goals are required")

            # Read positions from widget keys
            positions = []
            for i in range(st.session_state.num_positions):
                pos = {
                    "asset": st.session_state.get(f"pos_asset_{fv}_{i}", "").strip(),
                    "ticker": st.session_state.get(f"pos_ticker_{fv}_{i}", "").strip(),
                    "class": st.session_state.get(f"pos_class_{fv}_{i}", "renda_fixa"),
                    "quantity": st.session_state.get(f"pos_qty_{fv}_{i}", 0),
                    "avgPrice": st.session_state.get(f"pos_avg_{fv}_{i}", 0.0),
                    "currentPrice": st.session_state.get(f"pos_cur_{fv}_{i}", 0.0),
                    "weight": st.session_state.get(f"pos_w_{fv}_{i}", 0.0),
                }
                if pos["asset"] and pos["ticker"]:
                    positions.append(pos)

            if not positions:
                errors.append("Add at least one portfolio position with asset name and ticker")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                # Calculate total AUM from positions
                total_aum = sum(p["currentPrice"] * p["quantity"] for p in positions)

                # Create the client
                num = st.session_state.next_client_num
                new_id = f"cli_{num:03d}"
                st.session_state.next_client_num = num + 1

                new_client = {
                    "id": new_id,
                    "name": f_name.strip(),
                    "email": f_email.strip() or f"{f_name.strip().lower().replace(' ', '.')}@email.com",
                    "phone": f_phone.strip(),
                    "birthDate": "1985-01-01",
                    "cpf": "***.***.***-00",
                    "profile": f_profile,
                    "investmentGoals": f_goals.strip(),
                    "monthlyIncome": f_income,
                    "totalAUM": total_aum if total_aum > 0 else f_income * 10,
                    "accountSince": datetime.now().strftime("%Y-%m-%d"),
                    "lastContact": datetime.now().strftime("%Y-%m-%d"),
                    "nextReview": datetime.now().strftime("%Y-%m-%d"),
                    "status": "up_to_date",
                    "notes": f_notes.strip() or "Added manually via platform.",
                }

                new_holdings = {
                    "holdings": positions,
                    "monthlyReturn": f_monthly,
                    "ytdReturn": f_ytd,
                    "twelveMonthReturn": f_12m,
                }

                st.session_state.all_clients.append(new_client)
                st.session_state.all_holdings[new_id] = new_holdings
                st.session_state.all_transactions[new_id] = []
                st.session_state.selected_client = new_id

                # Reset form: increment version so all widget keys are fresh
                st.session_state.form_version += 1
                st.session_state.num_positions = 1
                st.session_state.client_added_msg = f"✅ {f_name.strip()} added! AUM: {format_brl(new_client['totalAUM'])}"
                st.balloons()
                st.rerun()
