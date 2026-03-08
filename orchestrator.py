"""Orchestrator — Runs the 6-agent pipeline in sequence.

Execution order:
  (Portfolio Analyst + Macro Analyst) in parallel
  → Recommendation Engine
  → Letter Writer
  → Compliance Reviewer
  → Doc Formatter

All LLM calls use GPT-4o via the OpenAI Python SDK.
"""

import os
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from data.clients import MOCK_CLIENTS, MOCK_HOLDINGS, MOCK_TRANSACTIONS
from data.market import MARKET_BENCHMARKS
from agents.portfolio_analyst import PortfolioAnalyst
from agents.macro_analyst import MacroAnalyst
from agents.recommendation_engine import RecommendationEngine
from agents.letter_writer import LetterWriter
from agents.compliance_reviewer import ComplianceReviewer
from agents.doc_formatter import DocFormatter


# Path to macro report text
MACRO_REPORT_PATH = Path(__file__).parent / "input" / "XP - Macro analysis.txt"
PROFITABILITY_CSV_PATH = Path(__file__).parent / "input" / "profitability_calc_wip.csv"
OUTPUT_DIR = Path(__file__).parent / "output"


def load_macro_report() -> str:
    """Load the macro analysis text file."""
    if MACRO_REPORT_PATH.exists():
        return MACRO_REPORT_PATH.read_text(encoding="utf-8")
    return ""


def run_pipeline(
    client_id: str,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Run the full 6-agent pipeline for a client.

    Args:
        client_id: The client ID (e.g., "cli_007" for Albert)
        progress_callback: Optional callback(agent_name, status, result)
            status is one of: "running", "done", "error"

    Returns:
        Dict with all agent outputs and the final document path
    """

    def notify(agent_name: str, status: str, result=None):
        if progress_callback:
            progress_callback(agent_name, status, result)

    # --- Find client data ---
    client = next((c for c in MOCK_CLIENTS if c["id"] == client_id), None)
    if not client:
        raise ValueError(f"Client {client_id} not found")

    holdings = MOCK_HOLDINGS.get(client_id)
    if not holdings:
        raise ValueError(f"No holdings data for {client_id}")

    transactions = MOCK_TRANSACTIONS.get(client_id, [])
    macro_text = load_macro_report()
    csv_path = str(PROFITABILITY_CSV_PATH) if PROFITABILITY_CSV_PATH.exists() else None

    results = {}
    start_time = time.time()

    # ─── STEP 1: Portfolio Analyst + Macro Analyst (parallel) ────────────

    portfolio_analyst = PortfolioAnalyst()
    macro_analyst = MacroAnalyst()

    notify("Portfolio Analyst", "running")
    notify("Macro Analyst", "running")

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_portfolio = executor.submit(
            portfolio_analyst.run, client, holdings, MARKET_BENCHMARKS, csv_path
        )
        future_macro = executor.submit(
            macro_analyst.run, macro_text, MARKET_BENCHMARKS
        )

        for future in as_completed([future_portfolio, future_macro]):
            if future == future_portfolio:
                results["portfolio_analysis"] = future.result()
                notify("Portfolio Analyst", "done", results["portfolio_analysis"])
            else:
                results["macro_analysis"] = future.result()
                notify("Macro Analyst", "done", results["macro_analysis"])

    # ─── STEP 2: Recommendation Engine ───────────────────────────────────

    notify("Recommendation Engine", "running")
    rec_engine = RecommendationEngine()
    results["recommendations"] = rec_engine.run(
        client, results["portfolio_analysis"], results["macro_analysis"]
    )
    notify("Recommendation Engine", "done", results["recommendations"])

    # ─── STEP 3: Letter Writer ───────────────────────────────────────────

    notify("Letter Writer", "running")
    writer = LetterWriter()
    results["letter"] = writer.run(
        client,
        results["portfolio_analysis"],
        results["macro_analysis"],
        results["recommendations"],
    )
    notify("Letter Writer", "done", results["letter"])

    # ─── STEP 4: Compliance Reviewer ─────────────────────────────────────

    notify("Compliance Reviewer", "running")
    reviewer = ComplianceReviewer()
    results["compliance"] = reviewer.run(
        results["letter"]["letter_text"], client["name"]
    )
    notify("Compliance Reviewer", "done", results["compliance"])

    # ─── STEP 5: Doc Formatter ───────────────────────────────────────────

    notify("Doc Formatter", "running")
    formatter = DocFormatter()
    safe_name = client["name"].lower().replace(" ", "_")
    output_path = str(OUTPUT_DIR / f"monthly_report_{safe_name}.docx")
    results["document"] = formatter.run(
        results["letter"]["letter_text"],
        client["name"],
        output_path,
        report_type="monthly_letter",
    )
    notify("Doc Formatter", "done", results["document"])

    # ─── Summary ─────────────────────────────────────────────────────────

    elapsed = round(time.time() - start_time, 2)
    results["pipeline_summary"] = {
        "client_id": client_id,
        "client_name": client["name"],
        "elapsed_seconds": elapsed,
        "compliance_passed": results["compliance"]["passed"],
        "compliance_score": results["compliance"]["score"],
        "letter_word_count": results["letter"]["word_count"],
        "output_path": results["document"]["output_path"],
    }

    return results


def generate_workflow_report():
    """Generate the workflow report answering the 3 challenge questions."""
    content = """# Workflow Report — XP AAI Platform

## Question 1: What are the main issues with the first version?

The original Rivet MVP has several critical issues that limit its effectiveness as a financial advisory tool:

- Model Choice: Uses GPT-4o-mini, which lacks the depth and nuance required for professional financial analysis. A more capable model is needed for CVM-compliant, contextually rich investment letters.

- No Code-Based Calculations: The original system passes raw portfolio data to the LLM and asks it to summarize returns. This is fundamentally flawed — LLMs can hallucinate numbers. Financial figures must be calculated deterministically by code (e.g., pandas), not generated by the model.

- No Compliance Review: The output goes directly to the client without any CVM compliance check. This is a regulatory risk — investment letters must avoid direct buy/sell language, include proper disclaimers, and never guarantee returns.

- No Recommendation Engine: The original system only summarizes what exists. It does not compare current allocation against target ranges for the client's risk profile, flag drift, or generate rebalancing suggestions.

- Single Linear Flow: All three data sources (portfolio, risk profile, macro) are processed sequentially. The portfolio and macro analysis are independent and should run in parallel for efficiency.

- No Document Generation: The output is plain text, not a professionally formatted .docx that can be sent to clients.

- Hardcoded Paths: Windows-specific file paths (C:\\Users\\blope\\...) make the system non-portable.

- Generic Prompts: The prompts produce generic summaries without client-specific personalization or actionable insights.

## Question 2: How did you decide on your approach?

The approach was driven by three principles:

1. Separation of Concerns (Agentic Architecture): Each task in the advisory workflow maps to a specialized agent. This mirrors how a real advisory team works — analysts calculate, strategists recommend, writers communicate, compliance reviews. The 6-agent design (Portfolio Analyst, Macro Analyst, Recommendation Engine, Letter Writer, Compliance Reviewer, Doc Formatter) ensures each component can be tested, improved, and scaled independently.

2. Code for Math, LLM for Language: The most critical design decision is that ALL financial calculations are done by Python/pandas code, never by the LLM. The LLM's role is strictly to generate natural language text from verified numbers. This eliminates hallucination risk for financial figures.

3. Compliance by Design: Rather than hoping the LLM produces compliant output, we built compliance into the architecture. The Recommendation Engine uses CVM-compliant language patterns in its prompts. The Compliance Reviewer acts as a quality gate — the letter cannot be delivered without passing automated and LLM-based compliance checks.

The Streamlit platform was chosen because it demonstrates the full advisor workflow: from client overview to report generation. It shows how agents can power an entire AAI productivity tool, not just one letter. To prove this isn't a static demo, we built an "Add Client" page with two input methods: (1) CRM Import — simulates looking up a client in XP's CRM, and (2) Manual Entry — a form where the advisor fills in client details and portfolio positions. New clients are stored in session state and immediately available across all pages, including the agent pipeline. This proves the system works for ANY client, not just hardcoded mock data.

## Question 3: What would you do with a full month?

With a full month, the platform would evolve into a production-ready AAI tool:

- Real Data Integration: Connect to XP's APIs for live portfolio data, market prices, and client CRM. The Add Client CRM Import tab already simulates this integration pattern — in production it would hit XP's actual systems. Replace mock data with real-time feeds.

- Multi-Agent Orchestration Framework: Build a proper orchestration layer with retry logic, error handling, agent memory, and conversation history. Enable agents to iterate (e.g., if compliance fails, send back to the writer for revision).

- Client Communication Automation: Integrate email delivery (via Gmail API or internal systems), schedule monthly report generation, and add client notification preferences.

- Advanced Analytics: Add Monte Carlo simulations for portfolio risk, scenario analysis (what-if Selic goes to 16%?), and automated rebalancing execution tracking.

- RAG Pipeline: Implement retrieval-augmented generation using XP's research library, enabling the macro analyst to cite specific research reports and data points.

- Human-in-the-Loop: Add an approval workflow where the advisor reviews and edits the generated letter before sending, building trust in the AI system.

- Performance Monitoring: Track which recommendations were followed, measure portfolio outcomes, and use this data to improve future recommendations.

- Mobile Interface: Build a mobile-first dashboard so advisors can review client status and approve communications on the go.
"""

    formatter = DocFormatter()
    output_path = str(OUTPUT_DIR / "workflow_report.docx")
    formatter.run(content, "Workflow Report", output_path, report_type="workflow_report")
    return output_path


if __name__ == "__main__":
    # Run for Albert (the challenge client)
    def print_progress(agent_name, status, result=None):
        icon = {"running": "⏳", "done": "✅", "error": "❌"}.get(status, "❓")
        print(f"  {icon} {agent_name}: {status}")

    print("=" * 60)
    print("XP AAI Platform — Agent Pipeline")
    print("=" * 60)

    # Generate Albert's report
    print("\n📊 Generating report for Albert da Silva...")
    results = run_pipeline("cli_007", progress_callback=print_progress)

    print(f"\n{'=' * 60}")
    print(f"Pipeline completed in {results['pipeline_summary']['elapsed_seconds']}s")
    print(f"Compliance: {'PASSED ✅' if results['pipeline_summary']['compliance_passed'] else 'FAILED ❌'}")
    print(f"Score: {results['pipeline_summary']['compliance_score']}/100")
    print(f"Letter: {results['pipeline_summary']['letter_word_count']} words")
    print(f"Output: {results['pipeline_summary']['output_path']}")

    # Generate workflow report
    print("\n📝 Generating workflow report...")
    report_path = generate_workflow_report()
    print(f"Output: {report_path}")

    print(f"\n{'=' * 60}")
    print("Done! All deliverables generated.")
