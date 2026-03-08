"""XP AAI Platform — API Server

Lightweight Flask API that exposes deterministic portfolio calculations
(pandas/Python) so Rivet's httpCall nodes can use real computed numbers.

Endpoints:
  GET  /api/health              → Health check
  GET  /api/clients             → List all clients
  POST /api/portfolio-analysis  → Full portfolio analysis (P&L, allocation, benchmarks)
  POST /api/drift-analysis      → Drift vs target allocation per risk profile

Start: python api_server.py
Runs on: http://127.0.0.1:5050
"""

from pathlib import Path
from typing import Optional

from flask import Flask, request, jsonify

from agents.portfolio_analyst import PortfolioAnalyst
from data.clients import MOCK_CLIENTS, MOCK_HOLDINGS
from data.market import (
    MARKET_BENCHMARKS,
    TARGET_ALLOCATIONS,
    CLASS_LABELS,
    PROFILE_LABELS,
)

app = Flask(__name__)

# Path to the profitability CSV (same folder as this file)
CSV_PATH = Path(__file__).parent / "input" / "profitability_calc_wip.csv"


# ── Helpers ──────────────────────────────────────────────────────────────

def find_client(client_id: str) -> Optional[dict]:
    """Look up a client by ID."""
    return next((c for c in MOCK_CLIENTS if c["id"] == client_id), None)


# ── Endpoints ────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """Simple health check."""
    return jsonify({"status": "ok", "service": "XP AAI API"})


@app.route("/api/clients", methods=["GET"])
def list_clients():
    """Return all available clients (id, name, profile)."""
    return jsonify([
        {"id": c["id"], "name": c["name"], "profile": c["profile"]}
        for c in MOCK_CLIENTS
    ])


@app.route("/api/portfolio-analysis", methods=["POST"])
def portfolio_analysis():
    """Run PortfolioAnalyst.run() for a given client and return the full JSON.

    Request body: {"client_id": "cli_007"}
    Returns: Full portfolio analysis with P&L, allocation, benchmarks, alerts.
    """
    data = request.get_json(silent=True) or {}
    client_id = data.get("client_id", "")

    client = find_client(client_id)
    if not client:
        return jsonify({"error": f"Client '{client_id}' not found"}), 404

    holdings = MOCK_HOLDINGS.get(client_id)
    if not holdings:
        return jsonify({"error": f"No holdings for '{client_id}'"}), 404

    # Use the CSV file if it exists
    csv_path = str(CSV_PATH) if CSV_PATH.exists() else None

    # Run the REAL pandas calculations
    analyst = PortfolioAnalyst()
    result = analyst.run(client, holdings, MARKET_BENCHMARKS, csv_path)

    return jsonify(result)


@app.route("/api/drift-analysis", methods=["POST"])
def drift_analysis():
    """Calculate allocation drift vs target for a given client.

    Request body: {"client_id": "cli_007"}
    Returns: Drift per asset class, positions to review, actionable drift flag.
    """
    data = request.get_json(silent=True) or {}
    client_id = data.get("client_id", "")

    client = find_client(client_id)
    if not client:
        return jsonify({"error": f"Client '{client_id}' not found"}), 404

    holdings = MOCK_HOLDINGS.get(client_id)
    if not holdings:
        return jsonify({"error": f"No holdings for '{client_id}'"}), 404

    # First, run portfolio analysis to get current allocation + alerts
    analyst = PortfolioAnalyst()
    portfolio_result = analyst.run(client, holdings, MARKET_BENCHMARKS)

    # Now calculate drift (deterministic math — no LLM)
    profile = client["profile"]
    target = TARGET_ALLOCATIONS.get(profile, TARGET_ALLOCATIONS["moderado"])
    allocation = portfolio_result.get("allocation", {})
    alerts = portfolio_result.get("alerts", [])
    total_aum = client["totalAUM"]

    drift_list = []
    for asset_class, target_pct in target.items():
        current_pct = allocation.get(asset_class, {}).get("weight", 0)
        drift = round(current_pct - target_pct, 2)
        drift_amount = round((drift / 100) * total_aum, 2)
        needs_action = abs(drift) > 5

        drift_list.append({
            "asset_class": asset_class,
            "label": CLASS_LABELS.get(asset_class, asset_class),
            "target_pct": target_pct,
            "current_pct": round(current_pct, 2),
            "drift_pct": drift,
            "drift_amount": drift_amount,
            "needs_action": needs_action,
            "status": (
                "overweight" if drift > 0
                else "underweight" if drift < 0
                else "on_target"
            ),
        })

    positions_to_review = [
        {
            "ticker": a["ticker"],
            "asset": a["asset"],
            "pnl_pct": a["pnl_pct"],
            "type": a["type"],
            "reason": a["message"],
        }
        for a in alerts
    ]

    return jsonify({
        "client_name": client["name"],
        "profile": profile,
        "profile_label": PROFILE_LABELS.get(profile, profile),
        "drift_analysis": drift_list,
        "positions_to_review": positions_to_review,
        "has_actionable_drift": any(d["needs_action"] for d in drift_list),
        "total_aum": total_aum,
    })


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("=" * 55)
    print("  XP AAI Platform — API Server")
    print("=" * 55)
    print()
    print("  Running on: http://127.0.0.1:5050")
    print()
    print("  Endpoints:")
    print("    GET  /api/health")
    print("    GET  /api/clients")
    print('    POST /api/portfolio-analysis  {"client_id": "cli_007"}')
    print('    POST /api/drift-analysis      {"client_id": "cli_007"}')
    print()
    print("=" * 55)
    print()

    app.run(host="127.0.0.1", port=5050, debug=True)
