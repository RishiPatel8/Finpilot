# Changelog

All notable changes to **FinPilot AI** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-10-23

### Open-Source Production Website Release
- **Debt Management & Accelerated Payoff**:
  - Implemented `/api/v1/liabilities` endpoint with CRUD operations and user isolation.
  - Implemented `POST /api/v1/liabilities/repayment-plan` calculating deterministic **Debt Avalanche** vs **Debt Snowball** payoff priorities with extra prepayment simulations.
  - Built interactive `DebtManagementView.tsx` with KPI summary cards, debt tracking table, and strategy comparisons.
- **First-Time User Onboarding Flow**:
  - Created `OnboardingModal.tsx` 3-step interactive setup wizard (Personal, Income/Expenses, Targets/Risk) guiding newly registered users into an active financial profile.
- **Settings & Data Privacy (DPDP Act 2023 / GDPR)**:
  - Built `SettingsView.tsx` with Financial Profile baseline editor and Account credentials overview.
  - Implemented `GET /api/v1/auth/export-data` for structured JSON data portability.
  - Implemented `DELETE /api/v1/auth/me` for permanent account deletion and database cascade purge.
- **Ollama Local AI Provider Adapter**:
  - Added `OllamaAIProvider` in `backend/app/ai/adapter.py` supporting local models (`llama3`, `mistral`) via HTTP API with automatic fallback to deterministic `MockAIProvider`.
- **Database Migrations with Alembic**:
  - Initialized Alembic configuration (`alembic.ini`, `alembic/env.py`) with automatic schema version tracking.
  - Created initial migration `163b72f67602_initial_schema.py` creating all tables, indexes, and constraints.
- **Security Headers Middleware**:
  - Added `add_security_headers` middleware in `main.py` enforcing `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, and `Strict-Transport-Security`.
- **Open-Source Repository Infrastructure**:
  - Added `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`.
  - Added GitHub Actions CI workflow `.github/workflows/ci.yml`.
  - Added GitHub issue templates for bug reports and feature requests, and pull request template.
  - Multi-stage production `frontend/Dockerfile` with Nginx SPA configuration.
- **Comprehensive Testing Suite**:
  - Expanded backend test suite from 44 to **47 passed tests (100% pass rate in 13.48s)**.
  - Verified 0 console errors and clean visual rendering across Desktop (1440x900) and Mobile (390x844).

## [1.1.1] - 2026-10-23

### Security & Financial Correctness Audit Fixes
- **Production Mock Token Shield**:
  - Gated mock Firebase tokens in `backend/app/core/firebase.py` so they are strictly prohibited when `ENVIRONMENT == "production"` or when `ALLOW_MOCK_FIREBASE` is disabled.
  - Added production guard in `frontend/src/services/firebase.ts` throwing explicit configuration exceptions rather than generating mock tokens.
  - Added regression test `test_firebase_mock_token_rejected_in_production`.
- **Surcharge Marginal Relief Precision**:
  - Corrected marginal relief formula in `backend/app/finance/tax/engine.py` for high-earning taxpayers exceeding surcharge thresholds (₹50L, ₹1Cr, ₹2Cr, ₹5Cr).
  - Enforced statutory constraint: `Total tax + surcharge <= (Tax at threshold + Surcharge at threshold) + Excess income`.
  - Added test fixture `test_surcharge_marginal_relief_high_income`.
- **Goal SIP Zero-Return Protection**:
  - Fixed `ZeroDivisionError` edge case in `backend/app/finance/investments/engine.py` when expected return is 0%, falling back to straight linear division.
  - Added test fixture `test_goal_projection_zero_return_edge_case`.
- **AI CFO Adversarial Prompt Defense & Context Disclosure**:
  - Implemented prompt injection / jailbreak protection neutralizing attempts to leak system instructions.
  - Added transparent baseline disclosure distinguishing estimated benchmarks from authenticated user profile records.
  - Added tests `test_connected_ai_cfo_prompt_injection_defense` and `test_connected_ai_cfo_missing_info_estimation_disclosure`.
- **Scenario Persistence & User Data Isolation**:
  - Verified scenario save and list endpoints with user ownership isolation.
  - Added test fixture `test_scenario_persistence_and_user_isolation`.
  - Overall test suite expanded to **44/44 passing tests (100% pass rate in 4.53s)**.

## [1.1.0] - 2026-10-23

### Added
- **Firebase Authentication Integration**:
  - Frontend Firebase Web SDK integration with Google Sign-In popup flow and graceful local development fallback.
  - Backend Firebase Admin token verification (`firebase_admin.auth.verify_id_token`) validating token signature, issuer, audience, and expiry.
  - Internal FinPilot `User` model mapping with `firebase_uid`, `auth_provider`, and nullable `hashed_password`.
  - Strict explicit account linking security: prevents automatic account takeover when a Google Sign-In matches an existing password account; returns `409 Conflict` requiring explicit password confirmation before linking.
  - Safe `.env.example` documenting all Firebase public and admin configuration keys without secrets.
- **Financial Decision Simulator Engine (`/api/v1/scenarios/`)**:
  - Deterministic simulation engine comparing baseline vs. proposed alternative financial scenarios.
  - Major purchase simulation (e.g. ₹8L car purchase in 18 months) modeling 3 strategic execution pathways:
    1. Prudent Down Payment + Auto Loan (preserving 3 months essential emergency runway).
    2. Extended Horizon All-Cash Purchase (accumulating 100% purchase cost without debt).
    3. Discretionary Budget Compression (trimming 20% lifestyle expenses).
  - Savings Boost simulator and Expense Reduction simulator calculating liquidity additions and debt acceleration.
  - Reusable frontend interface (`features/scenarios/ScenarioSimulatorView.tsx`) with dynamic charts, parameter inputs, and scenario persistence to `ScenarioRecord`.
- **Connected AI CFO Experience**:
  - Context-aware financial assistant with direct access to authorized user profile data (net income, living expenses, liquid savings).
  - Deterministic tool calling to financial scenario engines, avoiding model arithmetic hallucination.
  - Multi-option trade-off breakdown distinguishing facts, estimates, assumptions, and debt commitments.
  - Grounded statutory and regulatory citations (SEBI Liquid Fund norms, RBI Auto Loan EMI guidelines, DICGC bank deposit insurance).
- **Test Suite & Verification Enhancements**:
  - Added `test_firebase_auth.py` covering registration, account linking conflict prevention, and invalid token rejection.
  - Added `test_scenario_simulator.py` covering car purchase calculation reproducibility, savings increase, and expense optimization.
  - Added `test_ai_cfo.py` verifying context injection, tool invocation, and multi-turn planning.
  - Test suite expanded from 29 to **38 passing tests (100% pass rate in 3.51s)**.

## [1.0.0] - 2026-10-23

### Added
- **Core Architecture & Infrastructure**:
  - FastAPI backend structure with Pydantic v2 schemas, SQLAlchemy 2.0 ORM, and SQLite/PostgreSQL dual-engine support.
  - Multi-container `docker-compose.yml` for PostgreSQL, FastAPI backend, and React frontend.
  - React 18, TypeScript, Tailwind CSS, Vite frontend with modern dark-mode aesthetic and Lucide icons.
- **Relational Models & Security (Phase 2)**:
  - Models: `User`, `FinancialProfile`, `Transaction`, `Liability`, `AssetHolding`, `FinancialGoal`, `TaxRecord`, `ChatMessage`.
  - Password hashing with Bcrypt and stateless authentication using PyJWT.
  - Strict user ownership validation across all private endpoints.
- **Unified Financial Dashboard (Phase 3)**:
  - Estimated Net Worth, Monthly Surplus, Savings Rate, and 6-Month Emergency Runway meter.
  - Recharts Area chart for monthly cash flow trends.
  - Explicit synthetic demo data toggle (`/api/v1/demo/seed`) with visual banner indicator.
- **Budgeting & Cash Flow Engine (Phase 4)**:
  - Deterministic cash flow analysis and 50/30/20 budget framework.
  - CSV statement parser with column detection, invalid row reporting, and duplicate signature matching.
  - Debt Payoff Optimizer comparing Avalanche (interest-rate optimal) vs Snowball (psychological quick wins).
- **Indian Tax Engine (Phase 5)**:
  - Section 115BAC New Concessional Regime vs Old Tax Regime for AY 2025-26 (Budget 2024 amendments) and AY 2024-25.
  - Verified ₹75,000 standard deduction under New Regime; Section 87A rebate providing zero tax liability for salaried income up to ₹7,75,000.
  - Section 288B rounding off to the nearest multiple of ten rupees.
  - 100% test fixture agreement across 8 edge cases.
- **Investment & Goal Planning Engine (Phase 6)**:
  - Liquid Mutual Funds vs Bonds vs Bank Fixed Deposits suitability comparison (liquidity, credit safety, Section 50AA slab-rate taxation, interest rate sensitivity).
  - Goal contribution planner with inflation adjustments and year-by-year compounding breakdowns.
- **AI Finance Assistant & RAG (Phase 7)**:
  - Provider-independent AI adapter interface with default zero-cost offline `MockAIProvider` and optional Gemini/Ollama plugins.
  - RAG knowledge retriever indexing official Income Tax Act sections, SEBI circulars, and RBI deposit insurance regulations.
  - Structured function/tool calling delegating all calculations to deterministic Python engines.
- **Automated Testing Suite (Phase 8)**:
  - 29 comprehensive Pytest tests with 100% pass rate.
  - Complete Vite production build verification.
