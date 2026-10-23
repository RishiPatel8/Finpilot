# Changelog

All notable changes to **FinPilot AI** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-10-23

### FIRE Forecasting & Comprehensive Financial Planning Upgrade
- **Deterministic FIRE Calculation Engine**:
  - Implemented `FireEngine` (`backend/app/finance/fire/engine.py`) calculating:
    - Real returns via the exact Fisher equation: $r_{\text{real}} = \frac{1 + r_{\text{nominal}}}{1 + i} - 1$.
    - Today's FIRE target corpus ($\frac{\text{Annual Expenses}}{\text{SWR}}$) and inflation-adjusted future target at retirement age.
    - Compound portfolio future value with monthly investment annuity formulas.
    - Required monthly SIP to bridge retirement portfolio shortfall.
    - Projected FIRE age and years to financial independence.
  - Implemented 4 core FIRE strategies: **Lean FIRE** (70% expenses), **Regular FIRE** (100% lifestyle), **Fat FIRE** (135% expenses), and **Coast FIRE** (compounding to target with zero additional savings).
  - Multi-scenario year-by-year projections: Conservative (-2.5% return, +1.0% inflation), Base (11% return, 6% inflation), and Optimistic (+2.0% return, -0.5% inflation) tracking accumulation and post-retirement withdrawal/depletion.
  - Tested zero returns, negative returns, zero contributions, and edge cases.
- **Rule-Based 8-Pillar Financial Health Assessment**:
  - Implemented `FinancialHealthEngine` (`backend/app/finance/fire/health.py`) evaluating 8 weighted pillars:
    1. Emergency Fund Cushion (15% weight)
    2. Monthly Cash Flow Surplus (15% weight)
    3. Savings Rate Discipline (15% weight)
    4. Debt-to-Income / EMI Burden (15% weight)
    5. Age-Based Portfolio Multiple (10% weight)
    6. Goal Funding Tracking (10% weight)
    7. FIRE Corpus Progress (10% weight)
    8. Retirement Readiness Gap (5% weight)
  - Produces an overall 0-100 score, status verdict, and a 12-month prioritized actionable checklist (Months 1-3 Immediate, Months 4-6 Medium, Months 7-12 Wealth Compounding).
- **Dedicated FIRE Planning Frontend View**:
  - Created `FirePlanningView.tsx` with light fintech aesthetics (`#F6F8FC`, `#FFFFFF`, `#6478E8`).
  - Added KPI summary cards for today's target, future target, projected FIRE age, progress bar, and required SIP.
  - Added interactive sliders and controls for age, retirement age, expenses, investable assets, monthly SIP, inflation, returns, and SWR.
  - Added Recharts interactive multi-scenario accumulation and decumulation chart with retirement reference line.
  - Added instant what-if preset toggles ("+₹10k/mo SIP", "Retire at 45", "7.5% Inflation Stress Test").
  - Added 8-pillar health assessment view with color-coded status badges and 12-month action cards.
- **AI CFO FIRE Assistant Integration**:
  - Registered 3 new deterministic tools in `FinancialToolsRegistry` (`backend/app/ai/tools.py`):
    - `calculate_fire_plan`
    - `compare_fire_strategies`
    - `assess_financial_health`
- **Statutory Retirement Knowledge in RAG**:
  - Expanded `OFFICIAL_FINANCIAL_CORPUS` with Indian retirement knowledge:
    - Safe withdrawal rate dynamics in India (3.0%-3.5% SWR vs 4% US Trinity Study).
    - Section 10(12A) NPS 60% tax-free lump sum and Section 80CCD(1B) ₹50,000 deduction.
    - Section 80TTB ₹50,000 deposit interest deduction for senior citizens.
- **Comprehensive Verification & Testing**:
  - Expanded backend test suite from 60 to **68 passing tests (100% pass rate in 6.63s)** with dedicated `test_fire_engine.py` (8 tests).
  - Clean frontend production build (`vite build` in 5.19s).
  - Playwright browser QA automated verification passing with **0 console errors**.

## [2.1.0] - 2026-10-23

### Bank Connectivity, Cloud LLM & RAG Upgrade
- **Indian Account Aggregator (AA) Bank Connectivity**:
  - Implemented provider-independent `BaseBankAdapter` supporting Setu, Finvu, and deterministic Sandbox AA.
  - Added database models `BankAccount`, `BankConsent`, and `BankSyncLog` with user-level isolation and cascading deletes.
  - Created Alembic migration `b84f3189e472_add_bank_connectivity_tables.py` tested for reversible upgrades and rollbacks.
  - Built frontend `BankAccountsView.tsx` with consent initiation modal, connection status badges, live balance timestamps, and manual sync triggers.
  - Implemented idempotent transaction deduplication using compound index on `provider_txn_ref` and internal transfer detection (`is_internal_transfer = True`).
- **Cloud-Only Gemini LLM Architecture**:
  - Upgraded AI adapter to cloud-only Google Gemini (`gemini-2.5-flash`) via the `google-genai` SDK with explicit provider status introspection (`get_ai_provider_status()`).
  - Purged Ollama imports, configuration, and dependencies from the supported application path.
  - Maintained offline, deterministic `MockAIProvider` for test execution and offline development with zero external cloud dependencies.
- **Statutory Retrieval-Augmented Generation (RAG) System**:
  - Created modular vector store `RAGKnowledgeStore` with hybrid semantic vector search and statutory keyword section boosting.
  - Added official Indian regulatory corpus covering Finance Act 2024, Section 115BAC, Chapter VI-A, Section 44ADA, Section 112A, SEBI liquid funds, DICGC deposit insurance, and RBI Account Aggregator master directions.
  - Implemented cloud embedding provider with `text-embedding-004` (768 dimensions) and offline deterministic normalized unit vector generator.
  - Added prompt injection defense sanitizing input texts.
  - Strictly separated private user transaction data from public statutory vector indexes.
- **Enhanced AI CFO Integration**:
  - Injected verified bank balances and debt summaries into authenticated user context.
  - Integrated deterministic calculation tools (`compare_debt_payoff`, `calculate_tax`, `simulate_scenario`).
  - Added dynamic AI Provider status badge and RAG statutory citation pill tags in chat UI.
- **Comprehensive Automated Testing & Verification**:
  - Expanded test suite to **60 passed tests (100% pass rate in 8.54s)**.
  - Added dedicated test suites: `test_bank_connectivity.py` (3 tests) and `test_rag_system.py` (7 tests).
  - Verified clean browser rendering and zero console errors via Playwright.

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
