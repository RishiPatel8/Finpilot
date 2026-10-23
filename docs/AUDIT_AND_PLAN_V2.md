# FinPilot AI v2.0 — Comprehensive Audit & Implementation Plan

**Date**: 2026-10-23  
**Workspace**: `d:\finpilot`  
**Milestone**: v2.0 Open-Source Production Website  

---

## 1. Feature Classification Matrix

| Feature / Component | Category | Status Classification | Evidence & Current State |
| :--- | :--- | :--- | :--- |
| **Financial Dashboard** | Frontend / API | **1. Fully functional & verified** | Real-time calculations: Net Worth, Income, Expenses, Surplus, Runway, Recharts trends, Goal progress. Verified with active data. |
| **Financial Decision Simulator** | Frontend / API / Engine | **1. Fully functional & verified** | Multi-variable simulator (`/scenarios/simulate`), emergency runway preservation, alternative trade-off options, scenario history persistence (`/scenarios/save`). |
| **Tax Planner (AY 2025-26)** | Frontend / API / Engine | **1. Fully functional & verified** | Section 115BAC New vs Old regime, standard deduction (₹75k vs ₹50k), Section 87A rebate, high-income surcharge marginal relief, official citations. |
| **Investment Comparator** | Frontend / API / Engine | **1. Fully functional & verified** | Compares Liquid MF, Govt Bonds, Bank FD, Large Cap Equity with horizon filtering, risk levels, and SEBI tax treatment summaries. |
| **Budget & Bank Statements** | Frontend / API / Engine | **1. Fully functional & verified** | 50/30/20 allocation rules, CSV drag-and-drop parsing, duplicate signature detection, category filtering, search. |
| **Financial Goals** | Frontend / API / Engine | **1. Fully functional & verified** | Goal creation, monthly SIP projection, inflation adjustments, progress tracking. |
| **Local JWT Authentication** | Backend / Auth | **1. Fully functional & verified** | Password hashing (bcrypt), JWT generation, token verification, role assignment. |
| **Firebase Auth & Account Linking** | Backend / Auth | **6. Blocked by external credentials in prod** / **1. Verified in dev** | Mock Firebase token rejected in production. Full Google token verification via public certs supported when credentials configured. |
| **Debt Management (Liabilities)** | Frontend / API / Engine | **3. Partially implemented** | `BudgetEngine.debt_repayment_plan` (Avalanche vs Snowball) and `Liability` DB model exist. Missing API router `/liabilities` and frontend Debt Management view. |
| **First-Time User Onboarding** | Frontend / UX | **5. Missing** | New registration creates user but lacks interactive wizard to guide financial profile setup (income, expenses, emergency target, risk). |
| **Profile & Account Settings** | Frontend / API | **3. Partially implemented** | Backend `GET/PUT /profile` exists. Frontend lacks dedicated Settings view for editing profile, viewing account info, data export, or account deletion. |
| **Data Privacy & Account Deletion** | Backend / Security | **5. Missing** | Needs `DELETE /auth/me` and `GET /auth/export-data` for DPDP Act 2023 / GDPR compliance. |
| **AI CFO (Mock Grounded)** | Backend / AI | **1. Fully functional & verified** | Offline deterministic provider with prompt injection defense, authorized profile injection, tools, and regulatory citations. |
| **AI CFO (Gemini Adapter)** | Backend / AI | **6. Blocked by external API key** | `google.genai` adapter with graceful fallback to `MockAIProvider` when unconfigured. |
| **AI CFO (Ollama Adapter)** | Backend / AI | **5. Missing** | Local Ollama endpoint integration not yet implemented in `adapter.py`. |
| **Database Migrations (Alembic)**| Backend / DB | **5. Missing** | Alembic in `requirements.txt`, but `alembic.ini` and migration scripts not yet initialized. |
| **Security Headers & Rate Limiting**| Backend / Security | **5. Missing** | Security headers middleware (CSP, HSTS, X-Frame-Options) and rate-limiting not yet enabled. |
| **Open-Source Repository Files** | DevOps / Docs | **5. Missing** | Missing `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, GitHub issue templates, and CI/CD workflow. |
| **Demo Mode Isolation** | Frontend / UX | **3. Partially implemented** | Currently registers a mock user in DB instead of purely client-side/isolated demo state. |

---

## 2. Prioritized Implementation Roadmap

### Phase A: Core Backend Endpoints & Adapters (Debt, Ollama, Privacy)
1. Implement `backend/app/api/v1/endpoints/liabilities.py` with full CRUD and Avalanche vs Snowball repayment planning.
2. Implement Privacy endpoints in `auth.py`: `GET /auth/export-data` and `DELETE /auth/me`.
3. Implement `OllamaAIProvider` in `backend/app/ai/adapter.py` with graceful fallback.
4. Mount `liabilities` in `backend/app/api/v1/api.py`.
5. Add relationship between `User` and `ScenarioRecord`.
6. Add security headers middleware in `backend/app/main.py`.

### Phase B: Production Database & Alembic Migrations
1. Initialize Alembic configuration in `backend/alembic.ini` and `backend/alembic/env.py`.
2. Generate initial schema migration script.
3. Verify migration script execution on clean test SQLite and PostgreSQL targets.
4. Document migration, backup, and rollback procedures.

### Phase C: Production-Grade Frontend Features
1. **First-Time User Onboarding Wizard**: Step-by-step interactive setup modal on initial signup.
2. **Debt & Liabilities Management View**: Interactive tab for debts, EMIs, and Avalanche vs Snowball comparison.
3. **Profile Settings & Account Management View**: Full profile editing (income, expenses, risk, regime, emergency months) and privacy controls (export data, delete account).
4. **Isolate Demo Mode**: Allow guest users to explore instant demo data without creating fake persistent DB accounts.

### Phase D: Testing & Verification
1. Add backend unit tests for liabilities, debt repayment, Ollama fallback, and privacy export/deletion.
2. Run full pytest suite (confirm 100% pass rate).
3. Run frontend TypeScript build (`npm run build`).
4. Run real-browser visual verification on Desktop and Mobile.

### Phase E: Open-Source Readiness & Documentation
1. Create `.github/workflows/ci.yml` for automated CI testing.
2. Create `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
3. Create GitHub issue templates for bug reports and feature requests.
4. Update `README.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`.
