# FinPilot AI — Personal Finance Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tests: 38/38](https://img.shields.io/badge/Tests-38%20passed-brightgreen.svg)]()

FinPilot AI is an explainable personal finance intelligence platform for Indian users—including salaried professionals, freelancers, students, and small business owners. It combines deterministic financial engines (Indian Tax Old vs. New Regime, Cash Flow & Budgeting, Goal Planning, Decision Simulation, and Liquid Mutual Funds vs. Bonds vs. FDs) with a conversational AI assistant that provides calculation-grounded answers with citations to the Income Tax Act and SEBI/RBI regulations.

---

## Key Features

1. **Firebase Authentication & Secure Identity**:
   - Google Sign-In via Firebase Web SDK alongside traditional email/password authentication.
   - Server-side verification via official Firebase Admin SDK (token signature, issuer, audience, and expiry).
   - Strict explicit account linking: prevents automatic account takeover when a Google Sign-In matches an existing password account; returns `409 Conflict` requiring explicit password confirmation before linking.
   - User ownership checks on every private endpoint; client user IDs are never trusted.

2. **Financial Decision Simulator Engine**:
   - Reusable deterministic scenario simulator for major purchases (e.g. ₹8L-15L car purchase in 18 months), savings increases, and lifestyle cutbacks.
   - Compares 3 execution pathways: Balanced Down Payment + Auto Loan (preserving 3 months emergency runway), All-Cash Extended Horizon, and Budget Lifestyle Compression.
   - Saves scenarios securely to user account with full parameter reproducibility.

3. **Connected AI CFO**:
   - Context-aware financial assistant with direct access to authorized user profile data (net income, living expenses, liquid savings).
   - Tool calling to deterministic financial scenario engines, avoiding model arithmetic hallucination.
   - Explains trade-offs across liquidity, debt interest, and goal delays.
   - Cites official regulatory sources (SEBI Liquid Fund norms, RBI Auto Loan EMI guidelines, DICGC bank deposit insurance).

4. **Deterministic Indian Tax Planner**:
   - Assessment Year 2025-26 (FY 2024-25 Budget 2024 revisions) & AY 2024-25 comparisons.
   - Slabs, Section 115BAC New Regime vs Old Regime, Section 87A rebate, standard deduction (₹75,000 / ₹50,000), 80C, 80D, HRA, NPS 80CCD(1B), home loan interest.
   - 100% test-verified mathematical accuracy with Section 288B rounding off.

5. **Budgeting & Cash Flow Engine**:
   - Monthly cash flow analysis, savings rate, emergency reserve runway (3-12 months).
   - CSV bank statement import with column mapping, duplicate detection, and preview.
   - Debt repayment optimization (Avalanche vs Snowball).

6. **Investment Comparison & Goal Planning**:
   - Liquid Mutual Funds vs Bonds vs Fixed Deposits suitability comparison (liquidity, credit risk, tax treatment under Section 50AA, interest rate sensitivity).
   - Goal progress calculators: Emergency Fund, Car/Home Purchase, Higher Education, Retirement.

7. **Unified Responsive Dashboard**:
   - Real data persistence + one-click demo data mode.
   - Interactive charts (Recharts), financial meters, and dark-mode UI.

---

## Quickstart

### Prerequisites
- Node.js v18+ (tested with v24)
- Python 3.12+ (tested with v3.14)
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
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 2. Frontend
```powershell
cd frontend
npm install
npm run dev
```

---

## Running the Automated Test Suite

Run all 38 unit, integration, and security tests:
```powershell
$env:PYTHONPATH="backend"; python -m pytest backend/tests -v
```

Run frontend production build verification:
```powershell
cd frontend
npm run build
```

---

## Firebase Console Setup (Optional for Live Production)

1. In [Firebase Console](https://console.firebase.google.com/), enable **Google** and **Email/Password** under Authentication.
2. Add `localhost` and `127.0.0.1` to Authorized Domains.
3. Place web app configuration in `frontend/.env`:
   ```env
   VITE_FIREBASE_API_KEY=your-api-key
   VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your-project-id
   ```
4. Place private key at `backend/firebase-service-account.json` or set `FIREBASE_CREDENTIALS_PATH`.
*(Note: FinPilot AI includes offline mock fallback mode for zero-config local development and automated CI testing).*

---

## Project Structure

```
finpilot/
├── backend/
│   ├── app/
│   │   ├── ai/            # AI CFO adapter, RAG knowledge retriever, tools
│   │   ├── api/v1/        # REST endpoints (auth, scenarios, assistant, tax, etc.)
│   │   ├── core/          # Security, PyJWT, Firebase Admin SDK integration
│   │   ├── db/            # Database session & models
│   │   ├── finance/       # Deterministic tax, budget, investment, scenario engines
│   │   ├── models/        # SQLAlchemy 2.0 ORM models
│   │   └── schemas/       # Pydantic v2 validation models
│   └── tests/             # 38 pytest test cases
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI, Sidebar, Navbar, AuthModal
│   │   ├── features/      # Scenarios, Assistant, Tax, Investments, Budget, Goals
│   │   └── services/      # Axios API client, Firebase Web SDK
├── docs/                  # ARCHITECTURE, DECISIONS, PROJECT_STATUS, KNOWN_ISSUES
├── docker-compose.yml     # Multi-container orchestration
└── .env.example           # Safe environment variables template
```

## Security & Privacy
- Zero plaintext password storage (Bcrypt).
- Firebase ID token server-side cryptographic verification via official Firebase Admin SDK.
- Explicit account linking preventing silent account takeovers.
- Strict user ownership validation on all private financial resources.
- LLM prompts are sanitized; no sensitive credentials or financial records leaked to external providers.
