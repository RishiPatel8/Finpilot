# FinPilot AI — Personal Finance Intelligence Platform

[![Version: 2.8.0](https://img.shields.io/badge/Version-2.8.0-blue.svg)]()
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg)](https://www.typescriptlang.org/)
[![Telegram Bot CFO](https://img.shields.io/badge/Telegram%20Bot-Global%20AI%20CFO%20|%20Inline%20Actions-2CA5E0.svg)](docs/TELEGRAM_INTEGRATION.md)
[![Investments & Portfolio](https://img.shields.io/badge/Investments%20&%20Portfolio-16%20Indian%20Instruments%20|%20FA%202024-blueviolet.svg)]()
[![Decision Planner](https://img.shields.io/badge/Decision%20Planner-10%20Scenarios%20|%20Deterministic-blueviolet.svg)]()
[![Tests: 173/173](https://img.shields.io/badge/Tests-173%20passed%20(100%25)-brightgreen.svg)]()
[![Zero Mock Data](https://img.shields.io/badge/Mock%20Data-ZERO%20(100%25%20Data--Driven)-success.svg)]()
[![Plain-Language Finance](https://img.shields.io/badge/Financial%20Literacy-Plain%20Language%20%26%20Know%20More-success.svg)]()
[![Statement Intelligence](https://img.shields.io/badge/Statements-CSV%20|%20XLSX%20|%20PDF-purple.svg)]()
[![Autonomous AI CFO Agent](https://img.shields.io/badge/AI%20CFO%20Agent-Autonomous%20&%20Confirmed-purple.svg)]()
[![Intelligence Engine v1](https://img.shields.io/badge/Intelligence%20Engine-v1%20Deterministic-blueviolet.svg)]()
[![Recurring Transactions](https://img.shields.io/badge/Recurring%20&%20Bills-v1%20User--Controlled-teal.svg)]()
[![FIRE Forecasting](https://img.shields.io/badge/FIRE%20Forecaster-Lean%20|%20Regular%20|%20Fat%20|%20Coast-orange.svg)]()
[![RBI Account Aggregator](https://img.shields.io/badge/Connectivity-RBI%20NBFC--AA%20(Paused%20/%20Sandbox)-indigo.svg)]()
[![DPDP Act 2023](https://img.shields.io/badge/Compliance-DPDP%20Act%202023-emerald.svg)]()

FinPilot AI is an open-source, production-grade personal finance intelligence platform designed specifically for Indian users—including salaried professionals, freelancers, students, and small business owners. It combines the **Global AI CFO Telegram Bot Integration (cryptographically secure single-use account linking, real conversational intelligence, interactive inline Confirm/Cancel buttons, and proactive bill/budget/goal alerts)**, **Financial Decision Planner (evaluating real life decisions with verified cash flow baseline, 10 specialized scenarios, reducing-balance loan amortization, 3-way option comparisons, and 5 sensitivity stress tests)**, **Plain-Language Financial Education & Centralized Know More System**, **Genuine Bank Statement Intelligence Pipeline (multi-format CSV/XLSX/PDF extraction, Indian currency & date normalization, double-counting elimination, and duplicate detection)**, **Zero-Mock-Data Architecture (strictly data-driven dashboards, truth-in-accounting empty states, and production demo safeguards)**, **Autonomous Context-Aware AI CFO Agent (natural-language commands, user-confirmed write execution, multi-layer conversation memory, feedback learning, and whole-app intelligence)**, **Financial Intelligence Engine v1**, **user-controlled Recurring Transaction Management & Forward Scheduling**, **deterministic FIRE forecasting and comprehensive 8-pillar financial health tracking**, and a **grounded AI assistant powered by Cloud Gemini and statutory RAG knowledge retrieval**.

---

## Key Features

1. **Telegram Global AI CFO & Mobile Action Layer ([Full Setup Guide](docs/TELEGRAM_INTEGRATION.md))**:
   - **Direct CFO Interaction**: Query spending, budgets, debt liabilities, and goal progress, calculate taxes, and simulate life decisions directly from private Telegram chats.
   - **Real Financial Actions & Debt Management**: Executes real authenticated ledger mutations rather than manual advice. Supports borrowing (*"I borrowed ₹10,000 from my brother"*), money lent (*"My friend owes me ₹5,000"*), listings (*"Show all money I have lent to others"*, *"What are my debts?"*), and repayments (*"Mark the ₹1,000 loan as repaid"*).
   - **Disambiguation Without Guessing**: Ambiguous interest rates without frequency (e.g., *"at 1% interest"*) prompt a clarification question asking if it is monthly or annual with interactive option buttons. Missing counterparties or amounts trigger targeted questions.
   - **Read-After-Write Verification**: Post-confirmation messages return the persisted record details (`Record ID`, `Type`, `Counterparty`, `Principal`, `Interest Rate`, `Status`).
   - **Cryptographic Account Linking**: Single-use 15-minute codes (`FP-XXXX-XXXX`) generated securely in Web Settings. Zero linkage via raw phone numbers or public usernames alone.
   - **Interactive Inline Buttons**: Action proposals provide `[✅ Confirm & Execute]` and `[❌ Cancel]` buttons; verifies ownership, authorization, and idempotency, removing buttons upon execution to eliminate duplicate records.
   - **Dual Delivery Support**: Local development through long polling (`python -m app.telegram.polling`) and production via secret-token secured HTTPS webhook (`X-Telegram-Bot-Api-Secret-Token`).
   - **Proactive Opt-In Alerts**: Upcoming recorded bills (3 days prior), monthly budget limits (at 85% & 100%), and goal milestone celebrations with deduplicated dispatch logs.

2. **Real Data Financial Decision Planner & Affordability Suite**:
   - **User Baseline Auto-Resolution (`GET /api/v1/scenarios/baseline`)**: Pulls actual monthly income, essential expenses, discretionary spend, liquid bank balances, active loan EMIs, and recurring commitments from verified DB records. Zero mock data leak.
   - **10 Plain-Language Decision Types**: Buy a car/bike, buy a house / mortgage down payment, personal loan, expensive product, major trip, business expansion, investment SIP increase, financial goal, paying cash vs taking loan, and custom decisions.
   - **Complete Affordability Analysis**: Evaluates monthly cash flow surplus before vs after decision, eliminates EMI double-counting, measures emergency runway impact, and computes exact reducing-balance loan amortization.
   - **3-Way Options Comparison**: Option A (Proposed Plan), Option B (Prudent Lower Cost / Higher Down Payment), Option C (Delay & Save First / Pay Cash).
   - **5 Deterministic Stress Tests**: 15% income drop, 15% expense surge, ₹50,000 emergency shock, +1.5% interest rate hike, and 6-month delay.
   - **Scenario Persistence**: Save, rename, reopen, and delete decisions with strict user isolation.

1. **Plain-Language Financial Education & Centralized "Know More" Feature**:
   - **Accessible `KnowMore` Dialog**: Reusable, keyboard-navigable (`Escape`, focus trapping, ARIA dialog) component available as badges, buttons, and links across every page.
   - **Standardized 5-Part Explanation Structure**: For each term, provides (1) What it means, (2) Why it matters, (3) Real-life example in Indian Rupees (₹), (4) How FinPilot calculates or uses it, and (5) Important limitations or assumptions.
   - **Typed Content Registry (`financialTerms.ts`)**: 21 curated, deterministic definitions with zero LLM latency or hallucination risk for static financial concepts.
   - **Simplified Retirement & Financial Freedom Planner**: Replaced confusing terms (FIRE target, SWR, investable assets, required SIP, decumulation) with natural phrases ("Money You Need to Retire", "Suggested Yearly Withdrawal Rate", "Amount You Invest Each Month").
   - **"How Your Money Could Grow Over Time"**: Re-engineered chart titles, subtitles, and scenario legends with explicit return rates (Optimistic, Base Case, Conservative).
   - **Plain-English AI CFO**: Conversational assistant communicates in everyday English, avoids dense finance jargon, supports *"Explain this simply"*, and formats examples with ₹.

2. **Genuine Bank Statement Intelligence & Zero Mock Data Architecture**:
   - **Multi-Format Extraction Pipeline**: Direct upload, text/table extraction, and parsing for Indian bank statements across CSV (with encoding auto-detection), XLSX (`openpyxl`), and PDF (`pypdf`).
   - **Indian Banking Normalization**: Handles Indian date standards (`DD/MM/YYYY`, `DD-Mon-YYYY`, `YYYY-MM-DD`), INR formatting (`₹`, comma separators `1,45,000.00`, `Dr`/`Cr` indicators, parenthetical negatives `(5,000.00)`).
   - **Strict Accounting Integrity**:
     - *Self-transfers*: Detects transfers between user's own accounts (`is_internal_transfer = True`) and excludes them from income/expense calculations to eliminate double-counting.
     - *Credit Card Bill Repayments*: Categorized under `Debt & EMI` as balance settlements rather than new consumption expenses.
     - *Merchant Refunds*: Tagged as reversals/refunds rather than inflated earned income.
     - *Uncertain Fallback*: Unrecognized transactions default to `"Uncategorized"` for transparent user review rather than speculative misclassification.
   - **Intra-Batch & Cross-Import Deduplication**: Deterministic signature generation based on normalized date, amount, description, and reference number, preventing duplicate records across overlapping statement periods.
   - **Two-Phase Import Safety**: Interactive modal preview showing parsed totals, detected accounts, date coverage, warnings, and transaction tables before atomic database confirmation (`/api/v1/statement/confirm`).
   - **Zero Mock Data Guarantee**: Completely purged sample balances, fake liability items, hardcoded chart series, and synthetic variance factors from production code. When data is not yet linked or uploaded, widgets display truthful, transparent empty states explaining required inputs.
   - **Production Safeguards**: Seeding endpoints (`POST /api/v1/demo/seed`) are strictly blocked in production environments with HTTP 403 Forbidden.
   - **Natural-Language Financial Actions**: Understands and stages write commands ("Record ₹3,500 spent on groceries", "Add a personal loan of ₹50,000", "Pause my gym subscription", "Reduce dining budget by 15%").
   - **Mandatory User Confirmation Layer**: Staged pending actions (`draft -> awaiting_confirmation -> executing -> succeeded`) require explicit user authorization before modifying records.
   - **Shared Web & Telegram API Architecture**: Identical backend pending-action endpoints (`/actions/pending`, `/actions/{id}/confirm`, `/actions/{id}/cancel`) supporting browser UI and Telegram bot integration with idempotency protection.
   - **Socratic Ambiguity Handling**: Detects ambiguous financial commands (e.g. *"Add ₹1,000 loan to debt"*) and returns a single focused clarification question with selectable options.
   - **Multi-Layer Conversation Memory**: Manages active chat history, long-term user preferences (tax regime, risk tolerance), episodic summaries of planning sessions, and live database facts with strict user isolation.
   - **Feedback Learning & Adaptive Ranking**: Collects ratings and corrections, dynamically ranking proactive insights based on user engagement history without autonomous write permissions.
   - **Statutory RAG System**: Grounds financial advice with citations from Income Tax Act 1961, Finance Act 2024, SEBI, and DICGC.
   - See [AI CFO Agent Architecture](file:///docs/AI_CFO_AGENT.md).

2. **Global Floating UI & Multi-Mode Assistant**:
   - **Persistent Floating UI**: Accessible from every page via a floating launcher button at bottom-right with real-time proactive alert indicators.
   - **Multi-Mode Expandable Panel**: Docked sidebar (420px), expanded analysis console (680px), or distraction-free fullscreen mode without navigating away from the active workflow.
   - **Active Page Awareness**: Ingests route context (`page_context`) to provide contextual quick prompt chips and relevant advice based on the page in view (e.g., Debts, Budget, Recurring).
   - **Unified Financial Context Service**: Automatically pulls verified bank balances, 90-day transactions, liabilities/EMIs, confirmed recurring commitments, goals, active anomalies, and 30-day cash-flow forecasts.
   - **Deterministic Affordability Decision Matrix**: Evaluates multi-variable scenarios (e.g., *"Can I afford a ₹25,000 monthly EMI?"*) calculating post-commitment surplus, new Debt-to-Income (DTI) ratio, and emergency runway months.
   - **Proactive Insights & Transparent Badges**: Surges proactive financial alerts with 1-click follow-up queries, alongside interactive tool execution badges detailing verified formulas and citations.
   - See [AI CFO Architecture](file:///docs/AI_CFO_ARCHITECTURE.md).

2. **Recurring Transaction Management & 30-Day Forward Scheduler**:
   - **AI Review Queue**: Review subscriptions, bills, and recurring salary inflows detected by the Intelligence Engine.
   - **Lifecycle Management**: Confirm (with optional inline edits), Dismiss (with feedback preventing re-appearance), Pause, Reactivate, or Cancel commitments.
   - **Upcoming 30-Day Payment Schedule**: Chronological calendar of forward recurring obligations with overdue badges, days-remaining counters, and income/expense styling.
   - **Forecast Grounding**: Confirmed recurring obligations take precedence in forward 30/90-day cash flow projections with strict double-counting safeguards.
   - **AI CFO Subscription Tools**: Direct `get_recurring_commitments` tool calling and context injection for grounded advice on pausing or trimming subscriptions.
   - See [Recurring Transaction Management Specification](docs/RECURRING_TRANSACTION_MANAGEMENT.md).

2. **Financial Intelligence Engine v1 & Unified Feed**:
   - **Canonical Financial Snapshot**: User-scoped aggregation of genuine income, living expenses, category breakdowns, liquid bank + asset holdings, and emergency runway months. Excludes internal transfers (`is_internal_transfer == True`) to eliminate double-counting.
   - **Spending Anomaly Detection**: Compares current category spend against prior 60-day monthly baselines; detects surges exceeding 30% and ₹2,000 with explainable metrics.
   - **Cash-Flow Forecasting**: 30-day and 90-day forward projections incorporating historical run-rate, detected recurring commitments, and starting cash reserves.
   - **Adaptive 50-30-20 Budget Calibration**: Identifies discretionary overspend and suggests phased 15% trims to unlock goal surplus without disrupting lifestyle.
   - **Milestone Feasibility & SIP Calibration**: Calculates required monthly investments, completion timelines, and actionable sensitivity recommendations.
   - **Prioritized Intelligence Feed**: Directly embedded into the primary dashboard with critical/warning/info severity styling and one-click navigation to actionable workflows.
   - See [Intelligence Engine Architecture](docs/INTELLIGENCE_ENGINE.md).

1. **Deterministic FIRE Forecaster & Financial Independence Planning**:
   - Exact compound mathematics and Fisher equation real returns: $r_{\text{real}} = \frac{1 + r_{\text{nominal}}}{1 + i} - 1$.
   - Today's FIRE corpus target and inflation-adjusted future targets.
   - 4 Core FIRE strategies: **Lean FIRE** (needs only), **Regular FIRE** (current lifestyle), **Fat FIRE** (luxury cushion), and **Coast FIRE** (compounding to retirement with zero additional contributions).
   - Multi-scenario accumulation and decumulation tracking under Conservative, Base, and Optimistic return profiles.
   - Excludes illiquid primary residence to prevent double-counting.
   - See [FIRE Methodology](file:///docs/FIRE_METHODOLOGY.md) and [FIRE Implementation Plan](file:///docs/FIRE_PLANNING_IMPLEMENTATION_PLAN.md).

2. **Transparent 8-Pillar Financial Health Assessment**:
   - Mathematically evaluated 0-100 scoring across 8 pillars: Emergency Fund, Cash Flow Surplus, Savings Rate, Debt-to-Income, Age Portfolio Multiple, Goal Funding, FIRE Progress, and Retirement Readiness.
   - Zero black-box AI scores: explicit formulas and statutory benchmarks.
   - 12-month prioritized actionable checklist (Immediate, Medium-term, and Long-term).

3. **Indian Bank Connectivity via Account Aggregator (AA)**:
   - Integrates via RBI-regulated Account Aggregator architecture (Setu, Finvu, and deterministic Sandbox AA).
   - Zero bank credentials stored: connects via explicit, time-bound electronic user consent.
   - Automated transaction sync with compound index deduplication (`provider_txn_ref`).
   - Internal transfer detection (`is_internal_transfer = True`) to prevent double-counting transfers between own accounts.
   - Provider-reported vs cached balance timestamps with staleness indicators.
   - See [Bank Integration Guide](file:///docs/BANK_INTEGRATION_GUIDE.md) and [Account Aggregator Evaluation](file:///docs/ACCOUNT_AGGREGATOR_EVALUATION.md).

2. **Statutory RAG Knowledge System**:
   - Modular vector store (`RAGKnowledgeStore`) with hybrid semantic vector search and statutory keyword section boosting.
   - Verified official corpus: Finance (No. 2) Act 2024, Section 115BAC, Chapter VI-A (80C, 80D, 24(b)), Section 44ADA (freelancers), Section 112A (equity LTCG), SEBI liquid funds (91-day maturity, instant redemption), DICGC deposit insurance (₹5 Lakh cover), and RBI AA Master Directions.
   - Cloud embedding provider (`text-embedding-004`) with offline deterministic unit vector fallback.
   - Strict data isolation: private user financial records are never indexed into the public legal vector store.
   - See [RAG Setup Guide](file:///docs/RAG_SETUP_GUIDE.md).

3. **Cloud-Only Gemini AI CFO Assistant**:
   - Grounded conversational financial advisor powered by Google Gemini (`gemini-2.5-flash`) via `google-genai`.
   - Provider-independent backend adapter with live status introspection and deterministic fallback engine for offline execution and testing.
   - Incorporates authenticated user financial context (verified bank balances, income, living expenses, debts, and EMIs).
   - Injects deterministic financial tools (`calculate_tax`, `compare_investments`, `simulate_scenario`, `compare_debt_payoff`).
   - Cites official statutory sources and displays citation pills in chat UI.

4. **Deterministic Indian Tax Engine (AY 2025-26 & AY 2024-25)**:
   - Section 115BAC New Regime vs Old Regime, Section 87A rebate (₹0 tax up to ₹7.75L salary), enhanced standard deduction (₹75,000), 80C, 80D, HRA, home loan interest.
   - Surcharge marginal relief calculations for high earners (> ₹50L) and Section 288B nearest ₹10 rounding off.
   - 100% test-verified mathematical accuracy.

5. **Financial Decision Simulator Engine**:
   - Reusable deterministic scenario simulator for major purchases (e.g. ₹8L-15L car purchase in 18 months), savings increases, and lifestyle cutbacks.
   - Compares 3 execution pathways: Balanced Down Payment + Auto Loan (preserving 3 months emergency runway), All-Cash Extended Horizon, and Budget Lifestyle Compression.
   - Saves scenarios securely to user account with strict user isolation.

6. **Debt Management & Accelerated Payoff**:
   - Interactive liability tracking: principal, annual interest rate %, tenure, and EMIs.
   - Deterministic **Debt Avalanche** (mathematically optimal, highest interest first) vs **Debt Snowball** (psychological momentum, lowest balance first) prioritization.
   - Extra monthly prepayment simulator.

7. **Budgeting, 50-30-20 & CSV Statement Deduplication**:
   - Monthly cash flow analysis, savings rate, emergency reserve runway (3-12 months).
   - CSV bank statement import (HDFC, ICICI, SBI, Axis, Kotak) with column mapping, duplicate detection, and preview.

8. **Investment Comparison & Goal SIP Planning**:
   - Liquid Mutual Funds vs Bonds vs Fixed Deposits suitability comparison (liquidity, credit risk, tax treatment under Section 50AA).
   - Inflation-adjusted Goal SIP planning with zero-return edge case resilience.

9. **First-Time User Onboarding & Profile Setup**:
   - Guided 3-step interactive onboarding wizard: role, age, dependents, income, living expenses, emergency targets, and risk tolerance.
   - Direct persistence into user financial profile.

10. **Data Privacy, Portability & Account Deletion (DPDP Act 2023)**:
    - Structured JSON data export (`/auth/export-data`) covering profile, transactions, debts, goals, scenarios, and linked bank accounts.
    - Permanent account deletion (`DELETE /auth/me`) with cascading database purge and consent revocation.

11. **Production Database & Alembic Migrations**:
    - PostgreSQL support with SQLAlchemy ORM and Alembic migration tracking.
    - Zero destructive auto-schema changes; isolated SQLite support for local dev and testing.

12. **Premium Fintech Light Design System**:
    - `#F6F8FC` canvas, crisp `#FFFFFF` cards, `#6478E8` indigo brand accent, soft pastel badges (lavender, mint, blue, peach).
    - Fully responsive on Desktop (1440px) and Mobile (390px).

---

## Quickstart

### Prerequisites
- Node.js v18+ (tested with v20+)
- Python 3.11+ (tested with v3.14)
- Git

### Running Locally

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/finpilot.git
   cd finpilot
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   cp ../.env.example .env
   python -m alembic upgrade head
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Frontend Setup**:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## Running Tests

### Backend Unit & Integration Tests (94/94 passing)
```bash
python -m pytest backend/tests/ -v
```

### Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
```

---

## Docker Compose Setup

Run PostgreSQL, FastAPI backend, and Nginx frontend in isolated containers:
```bash
docker compose up -d
```
- Frontend: `http://localhost:5173`
- Backend API & Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

## Open-Source Community Guidelines

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Project Status & Test Log](docs/PROJECT_STATUS.md)

---

## Recommended License

FinPilot AI is open-source software. We recommend licensing under the **Apache License 2.0** (or **MIT License**), which allows broad community adoption and commercial use while protecting contributors.
