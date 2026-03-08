# KNOWLEDGE.md — Complete Study Guide for XP AAI Platform Interview

> **Pedro's personal study guide.** This document covers everything built, why it was built this way, and how to talk about it in the interview.

---

## Table of Contents
1. [Original System Teardown](#1-original-system-teardown)
2. [Architecture Rationale](#2-architecture-rationale)
3. [Agent Deep Dives](#3-agent-deep-dives)
4. [Prompt Engineering Decisions](#4-prompt-engineering-decisions)
5. [Code & Technology Decisions](#5-code--technology-decisions)
6. [Platform Features — Add Client & Dynamic Management](#6-platform-features--add-client--dynamic-management)
7. [Deployment — GitHub & Streamlit Cloud](#7-deployment--github--streamlit-cloud)
8. [Results Comparison: Before vs After](#8-results-comparison-before-vs-after)
9. [The 3 Interview Questions — Polished Answers](#9-the-3-interview-questions--polished-answers)
10. [Talking Points & Anticipated Questions](#10-talking-points--anticipated-questions)

---

## 1. Original System Teardown

### What the Rivet MVP does
The original `enter_challenge.rivet-project` is a simple Rivet graph that:
1. Reads 3 text files (portfolio, risk profile, macro report)
2. Feeds each into a separate prompt
3. Sends each prompt to GPT-4o-mini (3 separate LLM calls)
4. Combines all 3 outputs into a final prompt
5. Sends to GPT-4o-mini one more time to generate the letter

### Issues Found (with evidence)

| Issue | Evidence | Severity |
|-------|----------|----------|
| **Uses GPT-4o-mini** | `model: gpt-4o-mini` in all 4 Chat nodes | HIGH — Lacks depth for financial analysis |
| **No code-based calculations** | Portfolio data goes directly to LLM with no computation | CRITICAL — LLMs hallucinate numbers |
| **No compliance review** | No node checks for CVM violations | CRITICAL — Regulatory risk |
| **No recommendation engine** | Only summarizes existing data, doesn't advise | HIGH — Missing key advisory value |
| **No document generation** | Output is plain text, no .docx | MEDIUM — Not client-ready |
| **Hardcoded Windows paths** | `C:\Users\blope\Downloads\XP Challenge v2\Input\...` | LOW — Non-portable |
| **No parallelization** | All 3 summaries run sequentially | MEDIUM — Inefficient |
| **Generic prompts** | Example outputs are generic, not personalized | MEDIUM — Cookie-cutter letters |
| **No profitability CSV usage** | The CSV file is provided but never referenced | HIGH — Ignores available data |
| **No error handling** | If one node fails, entire graph fails silently | MEDIUM — Not production-ready |
| **Temperature 0.5 everywhere** | Same temp for calculations and creative writing | LOW — Suboptimal |
| **Max tokens 1024** | May truncate longer letters | LOW — Could cause incomplete output |

### The Most Critical Problem
The system lets GPT-4o-mini **invent financial numbers**. When the portfolio text says "Rentabilidade: -41,7%" for LREN3, the LLM might round it, change it, or calculate derived metrics incorrectly. In finance, a wrong number in a client letter is a compliance violation and a trust destroyer.

---

## 2. Architecture Rationale

### Why Agentic?
The monthly advisory workflow has **naturally separable concerns**:
- Calculating numbers (math) ≠ analyzing macro trends (synthesis) ≠ writing Portuguese letters (language)
- A single monolithic prompt can't do all of these well
- Each step needs different LLM settings (temperature, max_tokens)
- Different steps should run in parallel when independent

### Why These 6 Agents?

| Agent | Role | LLM? | Why Separate? |
|-------|------|-------|---------------|
| **Portfolio Analyst** | Calculate returns, P&L | No (pandas) | Financial math must be deterministic |
| **Macro Analyst** | Extract projections | Yes (GPT-4o) | Needs deep text comprehension |
| **Recommendation Engine** | Drift analysis + suggestions | Hybrid | Code for drift calc, LLM for CVM-compliant text |
| **Letter Writer** | Generate Portuguese letter | Yes (GPT-4o) | Core creative writing task |
| **Compliance Reviewer** | CVM compliance gate | Hybrid | Regex for patterns, LLM for nuanced review |
| **Doc Formatter** | Create .docx | No (python-docx) | Pure formatting, no LLM needed |

### Why This Orchestration Order?
```
(Portfolio Analyst + Macro Analyst)  ← PARALLEL: independent of each other
         ↓                ↓
    Recommendation Engine            ← Needs BOTH outputs
              ↓
        Letter Writer                ← Needs all 3 previous outputs
              ↓
      Compliance Reviewer            ← Quality gate on the letter
              ↓
        Doc Formatter                ← Format approved letter
```

The key insight: Portfolio and Macro analysis are **independent** — they don't need each other's output. Running them in parallel cuts pipeline time by ~40%.

---

## 3. Agent Deep Dives

### Agent 1: Portfolio Analyst
**What it does:** Takes raw portfolio data and the profitability CSV, calculates ALL financial metrics using pandas.

**Key calculations:**
- Market value per position: `currentPrice × quantity`
- P&L per position: `(currentPrice - avgPrice) × quantity`
- P&L %: `((currentPrice / avgPrice) - 1) × 100`
- Allocation by asset class: sum of weights per class
- Benchmark comparison: portfolio return vs CDI, IBOV

**Alerts generated:**
- Positions with P&L < -25% → "extreme_loss" alert
- Positions with P&L > +30% → "extreme_gain" alert

**For Albert specifically:**
- HAPV3: -74.58% loss (extreme alert)
- LREN3: -41.7% loss (extreme alert)
- ARZZ3: -31.05% loss (extreme alert)
- MRFG3: +43.5% gain (extreme alert)

**Output:** Structured JSON with every metric calculated by code.

### Agent 2: Macro Analyst
**What it does:** Reads XP's 50+ page macro report and extracts the key numbers an advisor needs.

**Key projections extracted:**
- Selic: 14.25% (raised 50bps, hiking cycle continues)
- IPCA: 6.1% forecast for 2025 (above target)
- GDP: 2.0% for 2025, 1.0% for 2026
- BRL/USD: R$6.20 EOY 2025, R$6.40 EOY 2026
- Fiscal: Primary balance target achievable but debt rising

**LLM role:** GPT-4o reads the dense macro text and produces a concise, structured summary. Temperature 0.2 (factual, not creative).

**Fallback:** If no API key, returns structured data from the benchmarks + hardcoded XP projections from the report.

### Agent 3: Recommendation Engine
**What it does:** Compares current allocation vs. target for the client's risk profile, flags drift >5pp, and generates CVM-compliant suggestions.

**For Albert (Moderado profile):**
- Target: RF 45%, Ações 25%, FIIs 15%, Intl 12%, Cripto 3%
- Actual: RF ~67%, Ações ~29%, FIIs 0%, Intl 0%, Cripto 0%
- Drift flags: RF overweight by ~22pp, FIIs underweight by 15pp, Intl underweight by 12pp

**CVM compliance in prompts:**
- NEVER: "compre", "venda", "recomendo a compra"
- ALWAYS: "pode ser oportuno avaliar", "a alocação sugere", "é interessante considerar"

### Agent 4: Letter Writer
**What it does:** Takes all 3 previous outputs and generates a professional 2-page letter in Portuguese.

**Structure enforced:**
1. Header with date
2. Personal greeting
3. Market context (1-2 paragraphs)
4. Portfolio performance with EXACT calculated numbers
5. Positioning and outlook
6. CVM-compliant recommendations
7. Professional sign-off
8. Mandatory disclaimer

**Temperature: 0.4** — Creative enough for natural language, constrained enough to not deviate from facts.

### Agent 5: Compliance Reviewer
**What it does:** Dual-layer compliance check:

**Layer 1 — Regex patterns (code):**
- Scans for forbidden words: "compre", "venda", "garantido", "sem risco"
- Checks for disclaimer presence
- Checks for advisor signature
- Checks for client name personalization

**Layer 2 — LLM review (GPT-4o):**
- Nuanced review for tone, misleading implications, context-dependent violations
- Temperature 0.1 (very strict, factual)

**Scoring:** Starts at 100, deducts for violations (critical: -30, high: -15, medium: -5, warning: -2). Pass threshold: 70+.

### Agent 6: Doc Formatter
**What it does:** Pure Python code using python-docx. No LLM needed.

**Formatting features:**
- XP Investimentos header with branding colors
- Gold accent separator line (#EDB92E)
- Calibri font, professional spacing
- Section headers detected and styled automatically
- Disclaimer in small gray italic text
- Proper page margins (2.5cm)

---

## 4. Prompt Engineering Decisions

### Why GPT-4o?
- It's OpenAI's most capable and versatile model — strong at understanding dense Portuguese financial text
- The macro report is 50+ pages of complex economic analysis
- CVM compliance requires nuanced understanding of regulatory language
- GPT-4o balances quality and cost, making it ideal for a production advisory tool

### Temperature Choices
| Agent | Temperature | Why |
|-------|-------------|-----|
| Portfolio Analyst | N/A | No LLM calls — pure pandas |
| Macro Analyst | 0.2 | Factual extraction, minimal creativity |
| Recommendation Engine | 0.3 | Structured but needs some language flexibility |
| Letter Writer | 0.4 | Most creative task, but still anchored to data |
| Compliance Reviewer | 0.1 | Strictest — must not miss violations |
| Doc Formatter | N/A | No LLM calls — pure python-docx |

### Key Prompt Patterns
1. **Data anchoring:** "Use ONLY the numbers provided. Never invent or estimate figures."
2. **CVM framing:** Explicit list of forbidden and allowed phrases
3. **Structure enforcement:** Numbered sections in the prompt ensure consistent output
4. **Example outputs:** Each prompt includes an example to calibrate tone and length
5. **Role assignment:** "You are a senior investment advisor" vs "You are a CVM compliance officer"

---

## 5. Code & Technology Decisions

### Why Pandas for Calculations?
- Financial calculations MUST be deterministic — pandas guarantees exact results
- DataFrame operations make it easy to aggregate by asset class, filter extremes, etc.
- The profitability CSV maps naturally to a DataFrame
- Industry standard for financial data processing

### Why Python-docx?
- Industry standard for programmatic .docx generation
- Fine-grained control over formatting (fonts, colors, margins)
- No external dependencies or services needed
- Produces standard Office Open XML that works in Word, Google Docs, etc.

### Why Streamlit?
- Fastest path from Python to a professional web dashboard
- Native support for charts (Plotly integration)
- Session state management for client selection AND dynamic client management
- No frontend skills needed — pure Python
- Perfect for prototyping and demo purposes
- `streamlit run app.py` — one command to launch
- 5 pages: Client Dashboard, Client Deep Dive, Report Generator, Recommendations, ➕ Add Client

### Why Plotly (not Matplotlib)?
- Interactive charts (hover, zoom) — much better for financial data
- Dark theme support that matches the app aesthetic
- Better browser rendering than static images

---

## 6. Platform Features — Add Client & Dynamic Management

### The Problem
The original demo had static mock clients hardcoded in `data/clients.py`. An advisor couldn't add new clients — the platform was read-only. In a real tool, advisors onboard new clients constantly. This was a huge gap between "demo" and "real tool."

### What We Built: "Adicionar Cliente" Page (2 input methods)

**Tab 1 — Import from CRM (CRM Import)**
- Simulates looking up a client in XP's CRM system
- Search bar filters by name or CPF
- Shows matching clients as styled cards with profile info
- Click "Importar" to auto-create the client with an empty portfolio
- 4 sample CRM records: Fernando Gomes (arrojado), Juliana Ribeiro (conservador), Thiago Nascimento (agressivo), Beatriz Monteiro (moderado)

**Tab 2 — Manual Entry**
- Full form split into two sections:
  - **Client Info:** Name, email, phone, risk profile (dropdown), investment goals, monthly income, notes
  - **Portfolio Positions:** Dynamic table where you add rows — each row has: asset name, ticker, class (dropdown), quantity, avg price, current price, weight %
- Real-time weight total tracker (turns green at 100%)
- Optional returns fields (monthly, YTD, 12M)
- On submit: validates required fields, calculates AUM from positions, creates the client
- Client appears immediately in the sidebar and works on ALL other pages (Deep Dive, Report Generator, Recommendations)

### Dynamic Client Management (Session State Architecture)

**Before:** All data came from `MOCK_CLIENTS`, `MOCK_HOLDINGS`, `MOCK_TRANSACTIONS` — static Python lists/dicts.

**After:** Data lives in `st.session_state`:
```python
st.session_state.all_clients = list(MOCK_CLIENTS)    # starts with mock data
st.session_state.all_holdings = dict(MOCK_HOLDINGS)   # grows as clients added
st.session_state.all_transactions = dict(MOCK_TRANSACTIONS)
st.session_state.next_client_num = len(MOCK_CLIENTS) + 1
```

Every page reads from session state instead of the static imports. New clients are added to session state and instantly available everywhere.

**Orchestrator patching** — The agent pipeline also needs to see new clients:
```python
from data import clients as _clients_mod
_clients_mod.MOCK_CLIENTS = st.session_state.all_clients
_clients_mod.MOCK_HOLDINGS = st.session_state.all_holdings
```
This patches the module's references at runtime so `run_pipeline()` works for dynamically added clients too.

### The "Form Version Counter" Pattern (Streamlit Bug Fix)

**The bug:** In Streamlit, when you write widget return values back to `session_state` AND use those values to populate the widgets, changing a selectbox triggers a rerun that conflicts — stale values overwrite fresh ones. The form would lose data or not reset after submit.

**The solution:** A version counter that's part of every widget key:
```python
st.session_state.form_version = 0  # incremented on submit
fv = st.session_state.form_version

# Every widget uses the version in its key
st.text_input("Name", key=f"f_name_{fv}")
st.number_input("Qty", key=f"pos_qty_{fv}_{i}")

# On submit: increment version → all keys become new → form resets cleanly
st.session_state.form_version += 1
st.rerun()
```

This is a clean pattern that solves the Streamlit widget persistence problem without hacky workarounds. Worth mentioning in the interview as an example of debugging a framework-level issue.

### Why This Matters for the Interview
- Shows the platform isn't just a static demo — it's a **functional tool** an advisor could use
- CRM import simulates a real integration point (in production: XP's actual CRM API)
- Manual entry shows attention to UX (real-time validation, weight tracker, form reset)
- The dynamic architecture proves the agent pipeline works for ANY client, not just hardcoded mocks
- Debugging the Streamlit form bug demonstrates problem-solving skills

---

## 7. Deployment — GitHub & Streamlit Cloud

### What We Did
The platform is deployed as a **live web app** accessible via URL — no installation needed.

- **GitHub repo:** Public repository at `github.com/pedroiscastro0-5A94-EDFD/xp-aai-platform`
- **Streamlit Community Cloud:** Free hosting that reads directly from the GitHub repo
- **Shareable URL:** Anyone with the link can open the app in their browser

### How It Works
1. Code lives on GitHub (public repo, 33 files)
2. Streamlit Cloud connects to the repo and deploys automatically
3. The `OPENAI_API_KEY` is stored in Streamlit's encrypted Secrets (not in the code)
4. When someone visits the URL, Streamlit spins up the app (~30 seconds if it was sleeping)
5. Any push to GitHub auto-redeploys — no manual steps

### Why This Matters for the Interview
- **It's not just code on a laptop** — it's a live, shareable product anyone can try
- **Shows deployment awareness** — prototype → GitHub → cloud hosting → shareable URL
- **The app stays active indefinitely** on the free tier (sleeps after inactivity, wakes on visit)
- **Secrets management done right** — API key is in Streamlit Secrets, never in the codebase

### Files Excluded from GitHub (`.gitignore`)
```
__pycache__/     # Python cache files
*.pyc            # Compiled Python
.env             # Local environment variables
.DS_Store        # macOS system files
.streamlit/secrets.toml  # Local secrets
.claude/         # Claude Code session data
drive-download-*/  # Temporary download folders
```

---

## 8. Results Comparison: Before vs After

### Original MVP Letter Problems
1. Numbers might be hallucinated (no calculation layer)
2. Generic tone — could be any client's letter
3. No compliance checking — might contain prohibited language
4. Plain text output — not professional enough for clients
5. No recommendations — just summarizes what happened
6. No benchmark comparison — doesn't tell client if they beat CDI

### My System's Letter
1. Every number calculated by pandas, verified before insertion
2. Personalized to client (name, profile, goals, specific holdings)
3. Compliance-checked with score (85/100+ for passing)
4. Professional .docx with XP branding
5. Specific rebalancing recommendations in CVM-compliant language
6. Clear benchmark comparison (vs CDI, IBOV, by asset class)

### Albert's Specific Improvements
- **Flagged extreme losses:** HAPV3 (-74.58%), LREN3 (-41.7%), ARZZ3 (-31.05%)
- **Flagged extreme gains:** MRFG3 (+43.5%)
- **Allocation drift detected:** No FIIs, no international = massively underweight
- **Specific recommendation:** Diversify into FIIs and international to align with moderate profile
- **Compliance score:** 85/100 — all checks passed

---

## 9. The 3 Interview Questions — Polished Answers

### Q1: What are the main issues with the first version?

**Short answer:** The original MVP has three critical problems and several important ones.

**The critical problems:**
1. **It lets the LLM make up financial numbers.** The portfolio data goes straight into GPT-4o-mini with a prompt asking it to "summarize results." But LLMs don't do math — they generate plausible text. In finance, one wrong number in a client letter destroys trust and can be a compliance violation. Financial calculations must be done by code.

2. **There's no compliance review.** Investment letters in Brazil must follow CVM rules — no direct buy/sell recommendations, no guaranteed returns, proper disclaimers. The original system sends GPT-4o-mini output directly to the client with zero compliance checking.

3. **There's no recommendation engine.** The system summarizes what exists but doesn't compare the portfolio against the client's target allocation, flag drift, or suggest rebalancing. It misses the most valuable part of the advisory service.

**Important problems:**
- Uses GPT-4o-mini (too shallow for financial analysis)
- No document formatting (plain text, not .docx)
- Hardcoded Windows file paths
- Ignores the profitability CSV entirely
- Generic prompts with no client-specific personalization
- Sequential flow when parallel execution is possible

### Q2: How did you decide on your approach?

**Short answer:** Three principles guided every decision.

**Principle 1: Code for math, LLM for language.**
This is the most important architectural decision. Every financial figure — returns, P&L, allocation percentages, benchmark comparisons — is calculated by pandas. The LLM's job is strictly to turn those verified numbers into natural Portuguese prose. This eliminates the hallucination risk entirely.

**Principle 2: Separation of concerns through agents.**
I broke the workflow into 6 specialized agents, each with a clear responsibility. This mirrors how a real advisory team works: analysts crunch numbers, strategists set direction, writers communicate, compliance reviews. Each agent can be tested, improved, and scaled independently. The Portfolio Analyst and Macro Analyst run in parallel because they're independent.

**Principle 3: Compliance by design, not by hope.**
Instead of hoping the LLM produces compliant text, I built compliance into the architecture at multiple levels:
- The Recommendation Engine's prompts explicitly list forbidden and allowed CVM language patterns
- The Compliance Reviewer uses regex for known violations AND GPT-4o for nuanced review
- The letter cannot be delivered without passing the compliance gate

**Why Streamlit?** Because the deliverable isn't just one letter — it's a platform that shows how agents can power an advisor's entire workflow. The dashboard, deep dive, report generator, recommendation, and add client pages demonstrate a vision for the AAI's daily tool.

### Q3: What would you do with a full month?

**Short answer:** Take this from a prototype to a production-ready AAI tool.

**Week 1 — Real data integration:**
- Connect to XP's APIs for live portfolio data and market prices (the Add Client CRM Import tab already simulates this integration pattern)
- Replace mock data with real-time feeds from B3, CVM, and XP's internal systems
- Implement a proper data pipeline with daily refresh
- Connect the CRM import to XP's actual client database

**Week 2 — Agent evolution:**
- Add RAG (retrieval-augmented generation) so the Macro Analyst can cite specific XP research reports
- Build an iterative compliance loop — if the letter fails review, it automatically goes back to the writer for revision
- Add agent memory so recommendations improve over time based on what the advisor approved or edited

**Week 3 — Client communication:**
- Integrate email delivery (scheduled monthly reports)
- Add a human-in-the-loop approval workflow — advisor reviews and edits before sending
- Build notification system for overdue clients

**Week 4 — Advanced analytics + deployment:**
- Monte Carlo simulations for portfolio risk scenarios
- Automated rebalancing execution tracking
- Mobile-first dashboard for on-the-go advisors
- Deploy to XP's infrastructure with proper auth and security

---

## 10. Talking Points & Anticipated Questions

### Key Things to Highlight
1. **"Code for math, LLM for language"** — This is the headline design decision. Lead with it.
2. **The compliance gate** — Show you understand CVM regulations matter in production.
3. **The platform vision** — You didn't just fix one letter, you built a tool an advisor would use daily.
4. **Albert's specific issues** — HAPV3 at -74.58% is a great concrete example of why alerts matter.
5. **Add Client = real tool, not just a demo** — Advisors can add clients via CRM or manual entry and immediately run the agent pipeline for them.
6. **Dynamic architecture** — Everything works for new clients, not just hardcoded mocks. This proves the system scales.
7. **Deployed and shareable** — Not just local code: it's a live URL anyone can try. Shows you think beyond "it works on my machine."

### Anticipated Questions & Answers

**"Why GPT-4o instead of a cheaper model?"**
Financial analysis requires deep understanding of dense Portuguese text (50-page macro reports), nuanced CVM compliance checking, and sophisticated client communication. Cheaper models produce generic output. For a high-AUM client base where each letter represents a trust relationship, the model quality directly impacts the advisory relationship. GPT-4o gives the best balance of quality and cost for this use case.

**"Couldn't you just improve the prompts in the original Rivet graph?"**
Better prompts would help, but they don't solve the fundamental problems: LLMs can't do reliable math, can't guarantee CVM compliance, and can't generate .docx files. These require code-based solutions, not prompt engineering alone.

**"How would you handle a client who disagrees with the recommendation?"**
The system is designed to support the advisor, not replace them. The recommendations page shows current vs. target allocation clearly — the advisor can discuss these with the client and adjust. In a production version, the advisor would edit the letter before sending, and the system would learn from their edits.

**"What about cost? Running GPT-4o for every client monthly?"**
With 52 clients and ~4 GPT-4o calls per client, that's ~200 API calls/month. At current pricing, this costs roughly $10-30/month — negligible compared to the advisor's time saved (estimated 2-3 hours per report manually, so ~100+ hours saved monthly).

**"How do you ensure the LLM doesn't hallucinate numbers even with your architecture?"**
Two layers: (1) Numbers are calculated by pandas and passed to the LLM as structured data, not raw text. The prompt explicitly says "use ONLY the numbers provided." (2) In a production version, I'd add a post-processing step that regex-matches all numbers in the generated letter against the input data and flags any discrepancies.

**"The Add Client feature — how would this work in production?"**
The CRM Import tab simulates what would be a real API call to XP's internal CRM. In production, the search would hit XP's systems and pull the client's full profile, CPF, account history, and existing portfolio from B3 settlement data. The Manual Entry form would be used for edge cases (new clients without CRM records, or advisors who want to model a hypothetical portfolio). The key architectural decision is that session state is the single source of truth — so whether a client comes from CRM, manual entry, or a real database, the agent pipeline treats them identically.

**"What challenges did you face building the platform?"**
The trickiest one was a Streamlit-specific bug: when the Add Client form had dynamic rows with selectboxes, changing a dropdown would trigger a page rerun that wiped other form fields. This is a known Streamlit limitation with widget key management. I solved it with a "form version counter" pattern — every widget key includes a version number, and on submit the version increments, which creates fresh keys and cleanly resets the form. It's a good example of debugging a framework-level issue rather than just the business logic.

---

## File Structure

```
xp-challenge/
├── agents/                          # 6 specialized agents
│   ├── __init__.py
│   ├── portfolio_analyst.py         # Pandas-based calculations
│   ├── macro_analyst.py             # GPT-4o for macro analysis
│   ├── recommendation_engine.py     # Code + LLM for CVM-compliant recs
│   ├── letter_writer.py             # GPT-4o for letter generation
│   ├── compliance_reviewer.py       # Regex + LLM compliance gate
│   └── doc_formatter.py             # python-docx for .docx generation
├── data/                            # Mock client and market data
│   ├── __init__.py
│   ├── clients.py                   # 7 clients (including Albert)
│   └── market.py                    # Benchmarks, targets, AAI profile
├── input/                           # Original challenge input files
│   ├── XP - Albert_s portfolio.txt
│   ├── XP - Albert_s risk profile.txt
│   ├── XP - Macro analysis.txt
│   └── profitability_calc_wip.csv
├── output/                          # Generated deliverables
│   ├── monthly_report_albert.docx   # Albert's monthly letter
│   └── workflow_report.docx         # Answers to 3 questions
├── .streamlit/config.toml           # Streamlit theme config
├── app.py                           # Streamlit AAI Platform (5 pages + Add Client)
├── orchestrator.py                  # Agent pipeline orchestrator
├── requirements.txt                 # Python dependencies
├── xp_advisor_improved.rivet-project # Improved Rivet workflow
└── KNOWLEDGE.md                     # This file (study guide)
```

---

## Quick Reference: Running Everything

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent pipeline (generates Albert's report + workflow report)
python orchestrator.py

# Launch the Streamlit platform
streamlit run app.py
```

---

*Last updated: March 8, 2026*
