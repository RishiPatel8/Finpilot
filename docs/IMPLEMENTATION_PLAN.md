# FinPilot AI — Implementation Plan

## Phase 1: Foundation & Docker Environment
- [ ] Scaffold backend directory structure with FastAPI, Pydantic, SQLAlchemy 2.0, Alembic.
- [ ] Scaffold frontend with React 18+, TypeScript, Vite, Tailwind CSS, Lucide icons, Recharts.
- [ ] Configure `docker-compose.yml`, backend Dockerfile, frontend Dockerfile, nginx or direct dev server.
- [ ] Implement backend `/health` and `/api/v1/health` endpoints returning system status, DB connection status, and version.
- [ ] Create Python virtual environment (`py -3.12 -m venv backend/.venv`) and install dependencies for local execution and testing.
- [ ] Verify frontend build and local dev server.

## Phase 2: Relational DB & Authentication
- [ ] Database setup (SQLAlchemy declarative models, Alembic migrations).
- [ ] Models: `User`, `FinancialProfile`, `IncomeRecord`, `Transaction`, `Liability`, `AssetHolding`, `FinancialGoal`, `TaxRecord`, `ChatMessage`.
- [ ] Security: Password hashing (passlib/bcrypt), JWT token generation and validation.
- [ ] API endpoints: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`.
- [ ] Tests for auth, registration, token verification, and tenant isolation.

## Phase 3: Unified Dashboard & UI Foundation
- [ ] Modern, high-aesthetic layout with sidebar, navigation, theme, metrics cards, charts.
- [ ] Dashboard views: Net Worth, Cash Flow, Spending breakdown, Goals progress, Emergency Fund meter.
- [ ] Toggle for Synthetic Demo Data vs Live User Data.
- [ ] Accessible, responsive design.

## Phase 4: Budgeting & Savings Engine
- [ ] Core deterministic engine (`app/finance/budget/`): Income aggregation, category analysis, savings rate, emergency reserve runway (3-6-12 months).
- [ ] CSV Transaction Import service: Column mapping, deduplication, invalid row reporting, preview before committing.
- [ ] Budget vs Actual variance analytics and debt payoff scenarios (Avalanche vs Snowball).
- [ ] Unit & integration tests for budget calculations and CSV parsing.

## Phase 5: Indian Tax Engine (FY 2024-25 / AY 2025-26)
- [ ] Versioned rule definitions: New Tax Regime (Section 115BAC amended) vs Old Tax Regime.
- [ ] Slabs, Standard Deduction (₹75,000 for salaried under New Regime, ₹50,000 Old Regime), 87A rebate, 80C, 80D, HRA, 80CCD(1B) NPS, 24(b) home loan interest.
- [ ] Surcharge and 4% Health & Education Cess.
- [ ] Regime comparison matrix with step-by-step breakdown and recommendation with citations to Income Tax Act.
- [ ] Exhaustive test suite for boundary values (₹3L, ₹7L, ₹7.75L, ₹10L, ₹15L, ₹50L surcharge boundaries).

## Phase 6: Investment Comparison & Goal Planning Engine
- [ ] Liquid Mutual Funds vs Bonds vs Fixed Deposits comparison calculator.
- [ ] Risk, liquidity, taxability (Section 50AA for debt funds post April 2023 at slab rate), credit risk, interest rate risk.
- [ ] Compound interest, SIP, lump sum, inflation-adjusted future value equations (`Decimal` precision).
- [ ] Goal planning: Target date contribution requirements (Emergency Fund, Home Downpayment, Retirement, Education).
- [ ] Tests for financial calculations.

## Phase 7: AI Finance Assistant & RAG Orchestration
- [ ] Provider-agnostic LLM interface (`BaseLLMProvider`).
- [ ] Default offline `MockProvider` + support for Gemini / Ollama / OpenAI.
- [ ] Tool orchestrator mapping user queries to deterministic calculators (`calculate_tax`, `compare_investments`, `analyze_budget`).
- [ ] Grounded RAG knowledge base of Indian financial rules with citations.
- [ ] Privacy safeguards: strip PII/tokens, refuse unauthorized calculations.

## Phase 8: Testing, Hardening & Security Audit
- [ ] Pytest test suite covering all engines and API endpoints.
- [ ] Frontend test / lint / build verification.
- [ ] Security testing: tenant isolation (User A cannot read User B's transactions or tax records), SQL injection resistance, rate limiting.

## Phase 9: Documentation & Deployment
- [ ] Finalize README.md with quickstart guide for both Docker and local setups.
- [ ] Update CHANGELOG.md, ARCHITECTURE.md, and PROJECT_STATUS.md with verified outcomes.
