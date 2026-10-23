# Changelog

All notable changes to **FinPilot AI** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
