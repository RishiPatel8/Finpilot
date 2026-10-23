# FinPilot AI — Personal Finance Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)

FinPilot AI is an explainable personal finance intelligence platform for Indian users—including salaried professionals, freelancers, students, and small business owners. It combines deterministic financial engines (Indian Tax Old vs. New Regime, Cash Flow & Budgeting, Goal Planning, and Liquid Mutual Funds vs. Bonds vs. FDs) with a conversational AI assistant that provides calculation-grounded answers with citations to the Income Tax Act and SEBI/RBI regulations.

---

## Key Features

1. **Deterministic Indian Tax Planner**:
   - Assessment Year 2025-26 (FY 2024-25) & AY 2024-25 comparisons.
   - Slabs, Section 115BAC New Regime vs Old Regime, Section 87A rebate, standard deduction (₹75,000 / ₹50,000), 80C, 80D, HRA, NPS 80CCD(1B), home loan interest.
   - 100% test-verified mathematical accuracy with Section 288B rounding off.

2. **Budgeting & Cash Flow Engine**:
   - Monthly cash flow analysis, savings rate, emergency reserve runway (3-12 months).
   - CSV bank statement import with column mapping, duplicate detection, and preview.
   - Debt repayment optimization (Avalanche vs Snowball).

3. **Investment Comparison & Goal Planning**:
   - Liquid Mutual Funds vs Bonds vs Fixed Deposits suitability comparison (liquidity, credit risk, tax treatment under Section 50AA, interest rate sensitivity).
   - Goal progress calculators: Emergency Fund, Home Purchase, Higher Education, Retirement.

4. **Conversational AI Financial Assistant**:
   - Provider-agnostic adapter (offline mock, Gemini, Ollama, OpenAI).
   - Structured tool execution so calculations are always computed deterministically.
   - Grounded responses with official citations.

5. **Unified Responsive Dashboard**:
   - Real data persistence + one-click demo data mode.
   - Interactive charts (Recharts), financial meters, and clean UI.

---

## Quickstart

### Prerequisites
- Node.js v18+ (tested with v24)
- Python 3.12+
- Docker & Docker Compose (optional for containerized run)

### Running with Docker Compose
```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`

### Running Locally (Native Windows / Linux)

#### 1. Backend
```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend
```powershell
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
finpilot/
├── backend/            # FastAPI, SQLAlchemy 2, Pydantic, Alembic, Finance Engines
├── frontend/           # React 18, TypeScript, Vite, Tailwind CSS, Lucide, Recharts
├── docs/               # Architecture, decisions, project status, known issues
├── docker-compose.yml  # Multi-container orchestration
└── .env.example        # Environment variable template
```

## Security & Privacy
- Zero plaintext password storage (Bcrypt).
- Strict user ownership validation on all private financial resources.
- LLM prompts are sanitized; no sensitive credentials or financial records leaked to external providers.
