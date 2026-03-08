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
    st.markdown("### 📊 XP AAI Platform")
    st.markdown(f"<span style='color:#6B7B8F;font-size:12px'>{AAI_PROFILE['name']} — {AAI_PROFILE['cnpi']}</span>", unsafe_allow_html=True)
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        ["Client Dashboard", "Client Deep Dive", "Report Generator", "Recommendations", "➕ Add Client"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("<span style='color:#6B7B8F;font-size:11px;text-transform:uppercase;letter-spacing:1px'>Clients</span>", unsafe_allow_html=True)

    for cl in st.session_state.all_clients:
        status_info = STATUS_MAP.get(cl["status"], {})
        status_color = status_info.get("color", "#999")
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
            st.markdown(f"<div style='width:8px;height:8px;border-radius:50%;background:{status_color};margin-top:12px'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"<span style='color:#6B7B8F;font-size:10px'>AUM Total: {format_brl(sum(c['totalAUM'] for c in st.session_state.all_clients))}</span>", unsafe_allow_html=True)

# ─── GET SELECTED CLIENT DATA ────────────────────────────────────────────────

selected = st.session_state.selected_client
client = next((c for c in st.session_state.all_clients if c["id"] == selected), None) if selected else None
portfolio = st.session_state.all_holdings.get(selected) if selected else None
transactions = st.session_state.all_transactions.get(selected, []) if selected else []

# ─── PAGE: CLIENT DASHBOARD ──────────────────────────────────────────────────

if page == "Client Dashboard":
    st.markdown("## Client Dashboard")
    st.markdown(f"<span style='color:#6B7B8F'>Overview — {datetime.now().strftime('%B %Y')}</span>", unsafe_allow_html=True)

    # Top metrics
    total_aum = sum(c["totalAUM"] for c in st.session_state.all_clients)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total AUM", format_brl(total_aum), f"{len(st.session_state.all_clients)} clients", accent=True)
    with col2:
        metric_card("Selic", f"{MARKET_BENCHMARKS['selic']['current']}%", f"Previous: {MARKET_BENCHMARKS['selic']['previous']}%")
    with col3:
        metric_card("CDI Month", format_pct(MARKET_BENCHMARKS["cdi"]["monthly"]), f"12M: {format_pct(MARKET_BENCHMARKS['cdi']['twelveMonth'])}")
    with col4:
        metric_card("IBOV Month", format_pct(MARKET_BENCHMARKS["ibovespa"]["monthly"]), f"12M: {format_pct(MARKET_BENCHMARKS['ibovespa']['twelveMonth'])}")

    st.markdown("")

    # Benchmarks chart + client list
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Benchmarks — February 2026")
        bench_df = pd.DataFrame([
            {"Benchmark": "CDI", "Monthly": MARKET_BENCHMARKS["cdi"]["monthly"], "YTD": MARKET_BENCHMARKS["cdi"]["ytd"]},
            {"Benchmark": "IBOV", "Monthly": MARKET_BENCHMARKS["ibovespa"]["monthly"], "YTD": MARKET_BENCHMARKS["ibovespa"]["ytd"]},
            {"Benchmark": "IFIX", "Monthly": MARKET_BENCHMARKS["ifix"]["monthly"], "YTD": MARKET_BENCHMARKS["ifix"]["ytd"]},
            {"Benchmark": "S&P BRL", "Monthly": MARKET_BENCHMARKS["sp500_brl"]["monthly"], "YTD": MARKET_BENCHMARKS["sp500_brl"]["ytd"]},
        ])
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Monthly", x=bench_df["Benchmark"], y=bench_df["Monthly"], marker_color="#EDB92E"))
        fig.add_trace(go.Bar(name="YTD", x=bench_df["Benchmark"], y=bench_df["YTD"], marker_color="#3B82F6"))
        fig.update_layout(
            barmode="group", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#8896AB", height=300, margin=dict(l=20, r=20, t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
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
                    st.markdown(f"<span style='color:#6B7B8F;font-size:11px'>monthly</span>", unsafe_allow_html=True)
            with col_c:
                st.markdown(f"<span class='status-badge status-{c['status']}'>{status_info.get('label', c['status'])}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color:rgba(255,255,255,0.04);margin:4px 0'>", unsafe_allow_html=True)

# ─── PAGE: CLIENT DEEP DIVE ──────────────────────────────────────────────────

elif page == "Client Deep Dive":
    if not client or not portfolio:
        st.markdown("## Client Deep Dive")
        st.info("Select a client from the sidebar to view portfolio details.")
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

        # Allocation chart + Risk profile
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Allocation by Class")
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

            # Benchmark comparison bar
            st.markdown("#### Performance vs. Benchmarks")
            bench_data = pd.DataFrame([
                {"Indicator": "Portfolio", "Return": portfolio["monthlyReturn"]},
                {"Indicator": "CDI", "Return": MARKET_BENCHMARKS["cdi"]["monthly"]},
                {"Indicator": "IBOV", "Return": MARKET_BENCHMARKS["ibovespa"]["monthly"]},
                {"Indicator": "IFIX", "Return": MARKET_BENCHMARKS["ifix"]["monthly"]},
            ])
            fig2 = px.bar(
                bench_data, x="Indicator", y="Return",
                color="Indicator",
                color_discrete_map={"Portfolio": "#EDB92E", "CDI": "#3B82F6", "IBOV": "#10B981", "IFIX": "#8B5CF6"},
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#8896AB", height=250, margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
            )
            fig2.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
            fig2.update_yaxes(gridcolor="rgba(255,255,255,0.06)", title="Return (%)")
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

# ─── PAGE: REPORT GENERATOR ──────────────────────────────────────────────────

elif page == "Report Generator":
    st.markdown("## Report Generator")

    if not client or not portfolio:
        st.info("Select a client from the sidebar, then click 'Generate Monthly Report' to run the 6-agent pipeline.")
    else:
        st.markdown(f"**Client:** {client['name']} — {PROFILE_LABELS.get(client['profile'], '')} — {format_brl(client['totalAUM'])}")
        st.markdown("")

        # Agent pipeline visualization
        agents_list = [
            ("Portfolio Analyst", "Calculates returns, P&L and allocation by class using pandas"),
            ("Macro Analyst", "Extracts Selic, IPCA, GDP and FX projections from XP macro report"),
            ("Recommendation Engine", "Compares allocation vs. targets, flags drift, generates CVM-compliant suggestions"),
            ("Letter Writer", "Generates professional 2-page monthly letter in Portuguese"),
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
                with st.spinner("Running agent pipeline..."):
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
                    st.success(f"Compliance: PASSED ({score}/100)")
                else:
                    st.warning(f"Compliance: NEEDS REVIEW ({score}/100)")

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
                st.markdown(f"<span style='color:#6B7B8F;font-size:11px'>{letter.get('word_count', 0)} words</span>", unsafe_allow_html=True)

                with st.container(height=400):
                    st.markdown(letter_text)

                # Download button
                doc_info = results.get("document", {})
                output_path = doc_info.get("output_path", "")
                if output_path and os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Download .docx",
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

# ─── PAGE: RECOMMENDATIONS ───────────────────────────────────────────────────

elif page == "Recommendations":
    st.markdown("## Recommendations")

    if not client or not portfolio:
        st.info("Select a client from the sidebar to view rebalancing recommendations.")
    else:
        st.markdown(f"**Client:** {client['name']} — {PROFILE_LABELS.get(client['profile'], '')} — {format_brl(client['totalAUM'])}")
        st.markdown("")

        drift_df = get_drift_data(client["profile"], portfolio["holdings"], client["totalAUM"])

        # Current vs Target allocation chart
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Current vs. Target Allocation")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Current", x=drift_df["label"], y=drift_df["current"],
                marker_color=[CLASS_COLORS.get(c, "#999") for c in drift_df["class"]],
                opacity=0.8,
            ))
            fig.add_trace(go.Bar(
                name="Target", x=drift_df["label"], y=drift_df["target"],
                marker_color=[CLASS_COLORS.get(c, "#999") for c in drift_df["class"]],
                opacity=0.3,
            ))
            fig.update_layout(
                barmode="group", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#8896AB", height=350, margin=dict(l=20, r=20, t=20, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15),
                yaxis_title="Allocation (%)",
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("#### Drift Analysis")
            for _, row in drift_df.iterrows():
                drift = row["drift"]
                color = "#EF4444" if drift > 5 else "#10B981" if drift < -5 else "#6B7B8F"
                action = "OVERWEIGHT" if drift > 5 else "UNDERWEIGHT" if drift < -5 else "OK"
                action_color = color

                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-radius:8px;background:rgba(255,255,255,0.02);margin-bottom:6px;border-left:3px solid {row['color']}">
                    <div>
                        <div style="font-weight:600;font-size:13px">{row['label']}</div>
                        <div style="font-size:11px;color:#6B7B8F">Target: {row['target']}% · Current: {row['current']}%</div>
                    </div>
                    <div style="text-align:right">
                        <div style="font-family:monospace;color:{color};font-weight:600">{drift:+.1f}pp</div>
                        <div style="font-size:10px;color:{action_color};font-weight:600">{action}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if any(drift_df["needs_action"]):
                st.markdown("")
                st.markdown("#### Rebalancing Required")
                for _, row in drift_df[drift_df["needs_action"]].iterrows():
                    direction = "reduce" if row["drift"] > 0 else "increase"
                    amount = abs(row["drift_amount"])
                    st.markdown(f"- **{row['label']}**: {direction} by ~{format_brl(amount)} ({abs(row['drift']):+.1f}pp drift)")

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

elif page == "➕ Add Client":
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
