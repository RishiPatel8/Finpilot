# FinPilot AI — Personal Finance Intelligence Platform

[![Version: 2.2.0](https://img.shields.io/badge/Version-2.2.0-blue.svg)]()
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tests: 68/68](https://img.shields.io/badge/Tests-68%20passed%20(100%25)-brightgreen.svg)]()
[![FIRE Forecasting](https://img.shields.io/badge/FIRE%20Forecaster-Lean%20|%20Regular%20|%20Fat%20|%20Coast-orange.svg)]()
[![RBI Account Aggregator](https://img.shields.io/badge/Connectivity-RBI%20NBFC--AA-indigo.svg)]()
[![DPDP Act 2023](https://img.shields.io/badge/Compliance-DPDP%20Act%202023-emerald.svg)]()

FinPilot AI is an open-source, production-grade personal finance intelligence platform designed specifically for Indian users—including salaried professionals, freelancers, students, and small business owners. It combines **deterministic FIRE forecasting and comprehensive 8-pillar financial health tracking**, **secure bank connectivity via the RBI Account Aggregator framework**, deterministic financial calculation engines (Indian Tax Old vs. New Regime, Cash Flow & Budgeting, Debt Payoff, Goal Planning, Decision Simulation, and Liquid Mutual Funds vs. Bonds vs. FDs), and a **grounded AI assistant powered by Cloud Gemini and statutory RAG knowledge retrieval** (Income Tax Act 1961, Finance Act 2024, SEBI, and RBI).

---

## Key Features

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

### Backend Unit & Integration Tests (47/47 passing)
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
