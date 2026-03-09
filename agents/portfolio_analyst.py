"""Portfolio Analyst Agent

Parses portfolio data, CALCULATES returns with code (pandas),
compares against CDI/IBOV benchmarks. Output: structured JSON.

Key design decision: ALL financial figures are calculated by Python code,
never by the LLM. The LLM is only used for generating narrative text
about the calculated numbers.
"""

import json
import pandas as pd
from typing import Any, Optional


class PortfolioAnalyst:
    """Analyzes client portfolio using code-based calculations."""

    name = "Portfolio Analyst"

    def run(self, client: dict, holdings: dict, benchmarks: dict, profitability_csv: Optional[str] = None) -> dict:
        """
        Analyze a client's portfolio.

        Args:
            client: Client profile dict
            holdings: Client holdings dict with 'holdings' list and return fields
            benchmarks: Market benchmarks dict
            profitability_csv: Optional path to profitability CSV file

        Returns:
            Structured dict with all calculated portfolio metrics
        """
        h_list = holdings.get("holdings", [])

        # --- Build holdings DataFrame ---
        df = pd.DataFrame(h_list)

        # Calculate P&L for each position
        df["market_value"] = df["currentPrice"] * df["quantity"]
        df["cost_basis"] = df["avgPrice"] * df["quantity"]
        df["pnl"] = df["market_value"] - df["cost_basis"]
        df["pnl_pct"] = ((df["currentPrice"] / df["avgPrice"]) - 1) * 100

        # --- Aggregate by asset class ---
        class_agg = (
            df.groupby("class")
            .agg(
                total_market_value=("market_value", "sum"),
                total_cost_basis=("cost_basis", "sum"),
                total_pnl=("pnl", "sum"),
                total_weight=("weight", "sum"),
                num_positions=("asset", "count"),
            )
            .reset_index()
        )
        class_agg["pnl_pct"] = ((class_agg["total_market_value"] / class_agg["total_cost_basis"]) - 1) * 100

        # --- Total portfolio metrics ---
        total_market_value = float(df["market_value"].sum())
        total_cost_basis = float(df["cost_basis"].sum())
        total_pnl = total_market_value - total_cost_basis
        total_pnl_pct = ((total_market_value / total_cost_basis) - 1) * 100 if total_cost_basis > 0 else 0

        # --- Benchmark comparison ---
        monthly_return = holdings.get("monthlyReturn", 0)
        ytd_return = holdings.get("ytdReturn", 0)
        twelve_month_return = holdings.get("twelveMonthReturn", 0)

        cdi_monthly = benchmarks["cdi"]["monthly"]
        cdi_ytd = benchmarks["cdi"]["ytd"]
        cdi_12m = benchmarks["cdi"]["twelveMonth"]
        ibov_monthly = benchmarks["ibovespa"]["monthly"]
        ibov_ytd = benchmarks["ibovespa"]["ytd"]
        ibov_12m = benchmarks["ibovespa"]["twelveMonth"]

        benchmark_comparison = {
            "monthly": {
                "portfolio": monthly_return,
                "cdi": cdi_monthly,
                "ibovespa": ibov_monthly,
                "vs_cdi": round(monthly_return - cdi_monthly, 2),
                "vs_ibovespa": round(monthly_return - ibov_monthly, 2),
                "beats_cdi": monthly_return > cdi_monthly,
                "beats_ibovespa": monthly_return > ibov_monthly,
            },
            "ytd": {
                "portfolio": ytd_return,
                "cdi": cdi_ytd,
                "ibovespa": ibov_ytd,
                "vs_cdi": round(ytd_return - cdi_ytd, 2),
                "vs_ibovespa": round(ytd_return - ibov_ytd, 2),
            },
            "twelve_month": {
                "portfolio": twelve_month_return,
                "cdi": cdi_12m,
                "ibovespa": ibov_12m,
                "vs_cdi": round(twelve_month_return - cdi_12m, 2),
                "vs_ibovespa": round(twelve_month_return - ibov_12m, 2),
            },
        }

        # --- Flag extreme performers ---
        extreme_losers = df[df["pnl_pct"] < -25].sort_values("pnl_pct")
        extreme_winners = df[df["pnl_pct"] > 30].sort_values("pnl_pct", ascending=False)

        alerts = []
        for _, row in extreme_losers.iterrows():
            alerts.append({
                "type": "extreme_loss",
                "ticker": row["ticker"],
                "asset": row["asset"],
                "pnl_pct": round(float(row["pnl_pct"]), 2),
                "market_value": round(float(row["market_value"]), 2),
                "message": f"{row['ticker']} shows a {row['pnl_pct']:.1f}% loss from cost basis — requires review",
            })
        for _, row in extreme_winners.iterrows():
            alerts.append({
                "type": "extreme_gain",
                "ticker": row["ticker"],
                "asset": row["asset"],
                "pnl_pct": round(float(row["pnl_pct"]), 2),
                "market_value": round(float(row["market_value"]), 2),
                "message": f"{row['ticker']} shows a {row['pnl_pct']:.1f}% gain — consider partial profit-taking",
            })

        # --- Read profitability CSV if provided ---
        monthly_price_changes = {}
        if profitability_csv:
            try:
                csv_df = pd.read_csv(profitability_csv)
                csv_df["monthly_change_pct"] = ((csv_df["Current price"] - csv_df["Last month price"]) / csv_df["Last month price"]) * 100
                for _, row in csv_df.iterrows():
                    monthly_price_changes[row["Asset"]] = {
                        "current_price": float(row["Current price"]),
                        "last_month_price": float(row["Last month price"]),
                        "monthly_change_pct": round(float(row["monthly_change_pct"]), 2),
                    }
            except Exception:
                pass

        # --- Build positions detail ---
        positions = []
        for _, row in df.iterrows():
            pos = {
                "asset": row["asset"],
                "ticker": row["ticker"],
                "class": row["class"],
                "quantity": int(row["quantity"]),
                "avg_price": round(float(row["avgPrice"]), 2),
                "current_price": round(float(row["currentPrice"]), 2),
                "market_value": round(float(row["market_value"]), 2),
                "cost_basis": round(float(row["cost_basis"]), 2),
                "pnl": round(float(row["pnl"]), 2),
                "pnl_pct": round(float(row["pnl_pct"]), 2),
                "weight": float(row["weight"]),
            }
            ticker = row["ticker"]
            if ticker in monthly_price_changes:
                pos["monthly_change_pct"] = monthly_price_changes[ticker]["monthly_change_pct"]
            positions.append(pos)

        # --- Build allocation breakdown ---
        allocation = {}
        for _, row in class_agg.iterrows():
            allocation[row["class"]] = {
                "weight": round(float(row["total_weight"]), 2),
                "market_value": round(float(row["total_market_value"]), 2),
                "pnl": round(float(row["total_pnl"]), 2),
                "pnl_pct": round(float(row["pnl_pct"]), 2),
                "num_positions": int(row["num_positions"]),
            }

        return {
            "agent": self.name,
            "reference_month": benchmarks.get("month", "2026-03"),
            "client_name": client["name"],
            "client_profile": client["profile"],
            "total_aum": client["totalAUM"],
            "summary": {
                "total_market_value": round(total_market_value, 2),
                "total_cost_basis": round(total_cost_basis, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
                "num_positions": len(h_list),
                "num_asset_classes": len(class_agg),
            },
            "returns": {
                "monthly": monthly_return,
                "ytd": ytd_return,
                "twelve_month": twelve_month_return,
            },
            "benchmark_comparison": benchmark_comparison,
            "allocation": allocation,
            "positions": positions,
            "alerts": alerts,
            "monthly_price_changes": monthly_price_changes,
        }
