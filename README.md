# FinPilot AI — Personal Finance Intelligence Platform

[![Version: 2.0.0](https://img.shields.io/badge/Version-2.0.0-blue.svg)]()
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tests: 47/47](https://img.shields.io/badge/Tests-47%20passed%20(100%25)-brightgreen.svg)]()
[![DPDP Act 2023](https://img.shields.io/badge/Compliance-DPDP%20Act%202023-emerald.svg)]()

FinPilot AI is an open-source, production-grade personal finance intelligence platform designed specifically for Indian users—including salaried professionals, freelancers, students, and small business owners. It combines deterministic financial engines (Indian Tax Old vs. New Regime, Cash Flow & Budgeting, Debt Payoff, Goal Planning, Decision Simulation, and Liquid Mutual Funds vs. Bonds vs. FDs) with a grounded AI assistant that operates strictly without model arithmetic hallucinations, citing official statutory sources (Income Tax Act 1961, SEBI, and RBI).

---

## Key Features

1. **Deterministic Indian Tax Engine (AY 2025-26 & AY 2024-25)**:
   - Slabs, Section 115BAC New Regime vs Old Regime, Section 87A rebate (₹0 tax up to ₹7.75L salary), standard deduction (₹75,000 / ₹50,000), 80C, 80D, HRA, home loan interest.
   - Surcharge marginal relief calculations for high earners (> ₹50L) and Section 288B nearest ₹10 rounding off.
   - 100% test-verified mathematical accuracy.

2. **Financial Decision Simulator Engine**:
   - Reusable deterministic scenario simulator for major purchases (e.g. ₹8L-15L car purchase in 18 months), savings increases, and lifestyle cutbacks.
   - Compares 3 execution pathways: Balanced Down Payment + Auto Loan (preserving 3 months emergency runway), All-Cash Extended Horizon, and Budget Lifestyle Compression.
   - Saves scenarios securely to user account with strict user isolation.

3. **Connected AI CFO Assistant**:
   - Context-aware financial assistant with access to authorized user financial profiles.
   - Provider-agnostic adapter supporting local Ollama (`llama3`, `mistral`), Google Gemini (`gemini-1.5-flash`), and offline deterministic execution.
   - Built-in prompt injection defense, authorized context injection, and regulatory citations.

4. **Debt Management & Accelerated Payoff**:
   - Interactive liability tracking: principal, annual interest rate %, tenure, and EMIs.
   - Deterministic **Debt Avalanche** (mathematically optimal, highest interest first) vs **Debt Snowball** (psychological momentum, lowest balance first) prioritization.
   - Extra monthly prepayment simulator.

5. **Budgeting, 50-30-20 & CSV Statement Deduplication**:
   - Monthly cash flow analysis, savings rate, emergency reserve runway (3-12 months).
   - CSV bank statement import (HDFC, ICICI, SBI, Axis, Kotak) with column mapping, duplicate detection, and preview.

6. **Investment Comparison & Goal SIP Planning**:
   - Liquid Mutual Funds vs Bonds vs Fixed Deposits suitability comparison (liquidity, credit risk, tax treatment under Section 50AA).
   - Inflation-adjusted Goal SIP planning with zero-return edge case resilience.

7. **First-Time User Onboarding & Profile Setup**:
   - Guided 3-step interactive onboarding wizard: role, age, dependents, income, living expenses, emergency targets, and risk tolerance.
   - Direct persistence into user financial profile.

8. **Data Privacy, Portability & Account Deletion (DPDP Act 2023)**:
   - Structured JSON data export (`/auth/export-data`) covering profile, transactions, debts, goals, and scenarios.
   - Permanent account deletion (`DELETE /auth/me`) with cascaded database purge.

9. **Production Database & Alembic Migrations**:
   - PostgreSQL support with SQLAlchemy ORM and Alembic migration tracking.
   - Zero destructive auto-schema changes; isolated SQLite support for local dev and testing.

10. **Premium Fintech Light Design System**:
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
