# Changelog

All notable changes to **FinPilot AI** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.8.1] - 2026-10-25

### Telegram Bot Real Financial Actions & Debt Management
- **End-to-End Real Action Execution (Replaces Manual Tracking Advice)**:
  - Fixed Telegram AI CFO so financial requests ("Add a debt of 1000rs...", "My friend owes me ₹5,000", "Mark loan as repaid") trigger real authenticated actions rather than manual tracking advice.
  - Integrated Telegram update handler directly with `AgentIntentParser`, `PendingAction` staging, and `ActionExecutor`.
  - Enforced inline keyboard confirmation (`[✅ Confirm & Execute]` / `[❌ Cancel]`) with verified database persistence.
  - Read-after-write verification: post-confirmation responses return the persisted record details (`Record ID`, `Type`, `Counterparty`, `Principal`, `Interest Rate`, `Status`).
- **Comprehensive Natural-Language Debt Operations**:
  - **Payables**: *"I borrowed ₹10,000 from my brother"*, *"Add a debt of ₹1,000 to my friend at 1% monthly interest"* creates payable liabilities.
  - **Receivables (Money Lent)**: *"My friend owes me ₹5,000"* creates tracked receivable records.
  - **Listing Debts & Receivables**: *"Show all money I have lent to others"* queries active receivables ledger; *"What are my debts?"* queries active liabilities ledger.
  - **Repayments**: *"Mark the ₹1,000 loan as repaid"* locates the active loan, updates `status="repaid"`, sets `remaining_months=0`, and confirms persistence.
- **Strict Disambiguation & Clarification Workflow**:
  - Ambiguous interest rates without frequency (e.g., *"with interest of 1%"*) prompt a clarification question asking whether 1% is monthly or annual, with interactive option buttons.
  - Missing counterparties or principal amounts trigger targeted questions without inventing details or guessing.
- **Database Schema Extensions (`liabilities` table)**:
  - Added `debt_type` (`payable` / `receivable`), `counterparty`, `interest_period` (`annual` / `monthly`), `status` (`active` / `repaid` / `closed`), `loan_date`, `due_date`, `repayment_frequency`, `notes`.
  - Alembic migration `d03f52189b34_extend_liabilities_with_debt_tracking.py` + automatic runtime SQLite column check on startup.
- **Safety, Isolation & Unsupported Action Identification**:
  - Cross-user mutation prevention: users can only view, stage, and confirm their own financial actions.
  - Duplicate message deduplication via `TelegramProcessedUpdate` and idempotent pending action status transitions.
  - Unsupported actions (e.g. live broker stock trades, direct UPI bank transfers) clearly identified with policy explanations rather than falsely claimed executions.
- **Automated Verification**:
  - Added `test_telegram_cfo_financial_actions.py` covering all 9 operational requirements.
  - 181 backend tests passing (100%).

## [2.8.0] - 2026-10-25

### Telegram Bot Integration with Global AI CFO
- **Official Telegram Bot API Integration (`app/telegram`)**:
  - Direct HTTP client (`TelegramClient`) using `httpx` wrapping Telegram Bot API with resilient retry handling and test spying.
  - Secret token authentication for production webhooks via `X-Telegram-Bot-Api-Secret-Token` header.
  - Autonomous long-polling runner (`python -m app.telegram.polling`) with pre-flight webhook cleanup to prevent concurrent webhook/polling collisions.
  - Incoming update deduplication (`TelegramProcessedUpdate`) safeguarding against duplicate executions on network retries.
- **Cryptographically Secure Account Linking Workflow**:
  - Single-use 8-character cryptographic token (`FP-XXXX-XXXX`) generated from FinPilot Web Settings with strict 15-minute expiration.
  - Invalidation of previous unused codes upon re-generation.
  - Atomic code consumption and 1-to-1 FinPilot user mapping in database (`TelegramAccountLink`).
  - One-click deep linking (`https://t.me/<bot_username>?start=<code>`) and manual `/link <code>` command.
  - Private chat enforcement: strictly refuses commands and linking in group chats or channels.
  - On-demand unlinking from web dashboard (`POST /telegram/unlink`) or Telegram chat (`/unlink`).
- **Complete Global AI CFO Conversational Integration**:
  - Direct message routing through existing `FinancialAgent.process_message(..., channel="telegram")`.
  - Reuses all verified financial services, deterministic calculation engines, and persistent memory.
  - Supports financial summaries, monthly spending queries, debts & EMI breakdowns, budget queries, goal tracking, investment projections, decision simulations, and tax calculations.
  - Ambiguity resolution with interactive inline buttons (`clarify:<id>:<opt>`).
- **Safe Write Actions & Inline Confirmation Workflow**:
  - Automatic conversion of staged write actions (`PendingAction`) into rich Telegram messages with review parameters and disclaimer.
  - Interactive Inline Keyboards: `[✅ Confirm & Execute]` and `[❌ Cancel]`.
  - Strict ownership verification preventing cross-user action tampering.
  - Execution via `ActionExecutor.confirm_and_execute` with verified database persistence.
  - Inline buttons automatically removed upon execution to eliminate duplicate clicks.
- **Proactive Opt-In Notification Pipeline (`app/telegram/notifications.py`)**:
  - Upcoming recorded bills reminder (due within 3 days).
  - Monthly budget limit warnings (sent at 85% and 100% threshold).
  - Financial goal completion milestones.
  - Composite deduplication keys (`TelegramNotificationLog`) ensuring zero duplicate or repeated notifications.
  - Granular opt-in toggles in Web Settings and `/status` in chat.
- **Frontend Settings UI (`SettingsView.tsx`)**:
  - Dedicated Telegram Global AI CFO card.
  - Single-use code generation, live countdown timer, one-click copy, and deep link button.
  - Live status indicator, username attribution, and granular notification toggles.
  - "Send Test Alert" and "Disconnect Telegram" controls.
- **Automated Test Suite (`test_telegram_integration.py`)**:
  - 9 comprehensive test scenarios verifying link code generation, expiration, atomic consumption, non-private chat rejection, update deduplication, CFO action proposals, callback query executions, user isolation, and notification deduplication.
  - 173 total backend tests passing (100%).

## [2.7.0] - 2026-10-25

### Advanced Indian Investment Research, Comparison, Planning & Portfolio Module
- **16-Instrument Statutory Indian Product Registry (`data.py`)**:
  - Covers 5 distinct asset classes: Liquid & Cash (Savings Bank Account with 80TTA, Auto-Sweep FD, Overnight Mutual Funds, Liquid Mutual Funds, Money Market Funds), Fixed Income & Bonds (Bank FDs with DICGC ₹5L coverage, Recurring Deposits, Sovereign T-Bills, AAA Corporate Bond Funds, Gilt Funds), Statutory Small Savings & Retirement (PPF EEE 7.1%, EPF/VPF 8.25%, NPS Tier-1 with 80CCD(1B) and 60% tax-free lump sum), Equities (Nifty 50 Index Fund/ETF, Flexi-Cap Active Fund, Mid & Small Cap Fund, ELSS 3-Year Lock-in, Balanced Advantage Fund), Alternatives (Sovereign Gold Bonds with 2.5% semi-annual coupon and 100% tax-exempt capital gains at maturity, Gold ETFs, listed REITs/InvITs).
  - Explicit provenance tracking for every rate: RBI card rates, AMFI benchmark yields, Gazette of India small-savings notifications, SEBI disclosures, and as-of dates. Zero fabricated quotes.
- **Finance Act 2024 & Section 50AA Deterministic Tax Engine (`engine.py`)**:
  - *Equities & Equity Funds (>65% equity)*: Long-Term Capital Gains (>12 months) taxed at 12.5% on gains exceeding ₹1,25,000 annual exemption limit. Short-Term Capital Gains (<=12 months) taxed at 20% flat.
  - *Debt Mutual Funds (Section 50AA)*: Deemed short-term capital assets, taxed at investor's marginal slab rate (0%, 5%, 10%, 15%, 20%, 30%).
  - *Bank FDs & RDs*: Annual accrued interest taxed at marginal slab rate with 10% TDS notification above ₹40,000 threshold.
  - *PPF & EPF*: 100% EEE tax-exempt status (principal deduction, interest, and maturity corpus).
  - *SGB Special Rules*: 2.5% annual coupon taxed at slab; capital gains on redemption at 8-year maturity with RBI are 100% tax-free under Section 47(viic).
  - *Inflation Adjustment*: Real purchasing power calculated across all instruments.
- **Multiple Scenario Comparison Modes (`/api/v1/investments`)**:
  - `POST /multi-compare` and `POST /compare`: Side-by-side post-tax returns, compounding conventions (quarterly, daily, annual, semi-annual), DICGC protection badge, and lock-in haircuts.
  - `POST /lumpsum-vs-sip`: Month-by-month trajectory points comparing terminal wealth and Rupee-Cost Averaging risk mitigation.
  - `POST /goal-plan`: Asset-allocated goal planner (Equity / Debt / Gold) with cash sufficiency checks against verified bank closing balances to prevent emergency fund depletion or double-counting.
  - `POST /stress-test`: 6 macro shock simulations (Immediate 20% market correction, Severe -35% bear market, Prolonged stagnation, 9.5% inflation shock, Premature emergency exit at Month 6, and 6-month paused SIP) with drawdown % and recovery period estimates.
  - `GET /portfolio-analysis`: Analyzes authenticated user's real `AssetHolding` records, calculates equity/debt/cash/gold breakdown vs target benchmarks, flags concentration risks, and prescribes rebalancing steps.
  - `GET / POST / PUT / DELETE /scenarios`: Full CRUD persistence for hypothetical comparison scenarios with strict user isolation.
- **Frontend Upgrade (`InvestmentsView.tsx`)**:
  - 8-tab clean interface: Product Screener, Multi-Product Compare, Lump Sum vs. SIP, Goal Investment Planner, Risk & Stress Test, Portfolio Allocation, Saved Scenarios, and Educational Glossary.
  - Full TypeScript typing and zero mock data leaks.
- **Backend Quality & Testing (`test_advanced_investments.py`)**:
  - 8 new deterministic test suites verifying product catalog filters, lump-sum compounding, monthly SIP, Finance Act 2024 taxation, cash-sufficiency checks, stress-testing resilience, portfolio analysis, and scenario isolation.
  - Full test suite: 164 passed (100%).

## [2.6.0] - 2026-10-24

### Financial Decision Planner — Real Data Affordability Engine & Scenario Suite
- **Verified Financial Baseline Resolution (`GET /api/v1/scenarios/baseline`)**:
  - Dynamically populates user's monthly income, essential living expenses, discretionary spending, liquid bank savings, active loan EMIs, and recurring commitments from verified database records.
  - Computes exact data completeness score (0-100%) and returns data source attribution for every financial metric.
  - Purged all hardcoded mock numbers (no static ₹61,902, ₹62,141, ₹65,200, or ₹8,00,000).
  - Truth-in-accounting empty state: clearly flags unverified profiles, prompting users to connect statements or enter labeled "User-Provided Assumptions".
- **10 Plain-Language Specialized Decision Planners**:
  - `vehicle`: On-road vehicle purchase with down payment, reducing-balance auto loan, ongoing fuel/maintenance, and registration costs.
  - `house`: Home purchase and mortgage planning with property price, 20-year reducing amortization, DTI tracking, and maintenance.
  - `personal_loan`: Personal loan borrowing evaluation with purpose tracking, tenure, and APR.
  - `expensive_product`: Major product acquisition with cash vs EMI options.
  - `major_trip`: Vacation and travel planning with time horizons, already saved amounts, and monthly SIP targets.
  - `business`: Venture capital and small business expansion with initial capital, monthly operating overhead, and ramp-up revenue delay modeling.
  - `increase_investment`: Stepping up monthly SIP contributions with compound interest wealth accumulation projections.
  - `financial_goal`: Sinking-fund target planning with required monthly savings.
  - `cash_vs_loan`: Rigorous opportunity cost analysis comparing loan interest paid against returns if cash remains invested.
  - `custom`: Flexible custom cash flow commitment modeling.
- **Complete Affordability & Impact Calculations**:
  - *Monthly Cash Flow Impact*: Computes Available Monthly Surplus before vs after decision (`Income - Expenses - Existing Obligations - New Commitment - Ongoing Costs`). Eliminates double-counting of existing loan EMIs.
  - *Savings & Emergency Buffer Impact*: Tracks upfront cash outlay, remaining liquid savings, emergency fund preservation, and remaining months of emergency runway.
  - *Loan Amortization*: Exact reducing-balance EMI, total interest paid, processing fees, and all-inclusive total purchase cost.
  - *3-Way Option Comparison*: Option A (Proposed Plan), Option B (Prudent Lower Cost / Higher Down Payment), Option C (Delay & Save First / Pay Cash) with initial cash, monthly outflow, surplus after, total cost, pros, and trade-offs.
  - *5 Deterministic Stress Tests*: 15% income drop, 15% expense increase, ₹50,000 emergency expense, +1.5% interest rate hike, and 6-month delay.
- **Rule-Based Decision Assessment Banner**:
  - Transparent rule-based verdict categories: `AFFORDABLE`, `TIGHT_CASH_FLOW`, `EMERGENCY_FUND_AT_RISK`, `HIGH_RISK_DEFICIT`, and `DATA_INCOMPLETE`.
  - Plain-English executive summaries and key decision driver bullet points.
- **Decision Persistence & User Isolation**:
  - Save scenario with custom titles (`POST /api/v1/scenarios/save`).
  - Retrieve saved scenarios with strict user isolation (`GET /api/v1/scenarios/saved`, `GET /api/v1/scenarios/{id}`).
  - Rename saved scenario (`PUT /api/v1/scenarios/{id}`).
  - Delete saved scenario (`DELETE /api/v1/scenarios/{id}`).
  - Reopen saved scenarios directly into the simulator form.
- **Frontend Experience (`ScenarioSimulatorView.tsx`)**:
  - Complete 6-step guided layout (Decision Type → Baseline → Details → Results → Alternatives → Stress Tests).
  - Expandable advanced options section (interest rates, tenure, one-time fees).
  - Saved decisions drawer and comparison modal.
  - Integrated `KnowMore` educational popovers for `reducing_interest`, `debt_to_income`, `stress_testing`, and `opportunity_cost`.
  - Zero mock data guarantee.

## [2.5.0] - 2026-10-24

### Plain-Language Financial Education & "Know More" System Across FinPilot AI
- **Centralized Typed Financial Terms Registry (`frontend/src/content/financialTerms.ts`)**:
  - Implemented comprehensive typed dictionary (`FinancialTermDefinition`, `FinancialTermKey`) covering 21 core financial concepts across the application.
  - Standardized 5-part educational structure for every term:
    1. *What it means* (simple everyday language without dense jargon).
    2. *Why it matters* (practical relevance to personal financial security).
    3. *Simple real-life example* (tangible figures denominated in Indian Rupees ₹).
    4. *How FinPilot calculates or uses it* (transparent formulas, verified database fields, or simulation parameters).
    5. *Important limitations or assumptions* (clearly distinguishes estimates and models from guarantees; disclaims professional tax/investment advice).
  - Terms defined: `financial_independence`, `retirement_target`, `investable_assets`, `monthly_investment`, `safe_withdrawal_rate`, `inflation`, `lean_fire`, `regular_fire`, `fat_fire`, `coast_fire`, `required_monthly_investment`, `retirement_shortfall`, `financial_health_score`, `net_worth`, `cash_flow`, `emergency_fund`, `recurring_payment`, `debt_payoff`, `tax_regime`, `asset_allocation`, and `growth_chart`.
- **Accessible, Reusable "Know More" Component (`frontend/src/components/KnowMore.tsx`)**:
  - Interactive modal dialog with keyboard accessibility (`Escape` key, backdrop dismissal, focus trap, and screen-reader `role="dialog"`).
  - Multiple presentation variants: `badge` (compact pill with book-open icon), `button`, `icon`, and `link` for seamless inline placement next to headings, tables, and metric cards.
  - Mobile-responsive design with touch-friendly layout, clean typography (`Plus Jakarta Sans`), and styling matching FinPilot's light theme (`#6478E8` accent, slate borders, and muted neutral background).
  - Updated `MetricCardProps` in `frontend/src/components/ui/MetricCard.tsx` to support `React.ReactNode` for inline `KnowMore` triggers beside metric titles.
- **Retirement & Financial Freedom Planner Overhaul (`FirePlanningView.tsx`)**:
  - Renamed technical jargon across all headings, metric labels, cards, strategy cards, and buttons:
    - *"FIRE Forecaster & Financial Planning"* → *"Retirement & Financial Freedom Planner"*
    - *"FIRE Target (Today's Value)"* → *"Money You Need to Retire (Today's Value)"*
    - *"Target at Age X"* → *"Money Needed by Age X"*
    - *"Projected FIRE Age"* → *"Estimated Age You Can Retire"*
    - *"FIRE Progress"* → *"Progress Towards Retirement Goal"*
    - *"Monthly Investment"* → *"Amount You Invest Each Month"*
    - *"Investable Assets"* → *"Money Already Available for Investing"*
    - *"Target Retirement Age"* → *"Age You Want to Retire"*
    - *"Safe Withdrawal Rate (SWR)"* → *"Suggested Yearly Withdrawal Rate"*
    - *"Lean FIRE"* → *"Retirement With Basic Expenses (Lean FIRE)"*
    - *"Regular FIRE"* → *"Retirement With Your Current Lifestyle (Regular FIRE)"*
    - *"Fat FIRE"* → *"Retirement With More Spending and Comfort (Fat FIRE)"*
    - *"Coast FIRE"* → *"Investments That May Grow Enough on Their Own (Coast FIRE)"*
    - *"Required SIP"* → *"Monthly Investment Needed"*
    - *"Shortfall"* → *"Amount You Still Need to Build"*
    - *"Reset Baselines"* → *"Reset to Starting Values"*
    - *"Recalculate Projections"* → *"Update My Retirement Estimate"*
    - *"Financial Health (8 Pillars)"* → *"Check My Financial Health"*
  - Growth Chart Renamed: *"How Your Money Could Grow Over Time"* with subtitle *"An estimate of how your savings may grow before retirement and how they may change when you begin using them."*
  - Simplified Chart Legend:
    - *Optimistic* (Higher-return scenario, e.g. 13% pre / 9% post)
    - *Base case* (The main assumptions used in this estimate, 11% pre / 8% post)
    - *Conservative* (Lower-return scenario, 9% pre / 7% post)
- **Whole-Website Plain-Language Integration**:
  - `Sidebar.tsx`: Renamed navigation items to everyday English ("Retirement & Financial Freedom", "Budget & Spending", "Recurring Payments", "Debt Payoff Plan").
  - `DashboardView.tsx`: Added `KnowMore` triggers to Net Worth, Cash Surplus, Emergency Runway, Active Goals, and Cash Flow Trends chart.
  - `BudgetView.tsx`: Added `KnowMore` trigger to 50/30/20 Cash Flow Framework and simplified overspending diagnostics.
  - `RecurringTransactionsView.tsx`: Added `KnowMore` to PageHeader and commitments cards.
  - `DebtManagementView.tsx`: Added `KnowMore` to Avalanche/Snowball strategy cards and payoff timeline.
  - `TaxPlannerView.tsx`: Added `KnowMore` explaining New vs Old tax regime differences and statutory tax rebates.
  - `InvestmentsView.tsx`: Simplified PageHeader to *"Liquid Funds vs Bonds vs Fixed Deposits"* and added `KnowMore`.
  - `BankAccountsView.tsx`: Simplified PageHeader to *"Bank Accounts & Balances"* with `KnowMore`.
  - `GoalsView.tsx`: Simplified PageHeader to *"Financial Goals & Milestones"* with `KnowMore`.
  - `ScenarioSimulatorView.tsx`: Simplified PageHeader to *"Financial Decision Simulator"* with `KnowMore`.
  - `SettingsView.tsx`: Added `KnowMore` explaining baseline income, living expense, and eligible investment baselines.
- **AI CFO Plain-English Conversational Adapter (`backend/app/ai/adapter.py`)**:
  - Updated `MockAIProvider` and `GeminiAIProvider` system prompts to communicate in plain English by default.
  - Avoided dense academic phrasing (e.g. replaced *"Your current investable corpus is insufficient under base-case accumulation model"* with *"Your current investments may not be enough to reach your retirement goal at the moment. You may need to invest more each month, retire later, or adjust your target."*).
  - Added dedicated plain-English translation handler for requests like *"Explain this simply"*, *"simplify"*, or *"in simple words"*.
  - Consistent formatting using Indian Rupees (₹) and real-life examples.
- **Verification & Zero Mock Data Compliance**:
  - Full backend test suite: **143 passed out of 143 tests** (`100%`).
  - Frontend production build: `tsc && vite build` completed in 10.84s with **0 errors**.
  - All calculation engines, database models, and API contracts preserved with 100% fidelity.

## [2.4.0] - 2026-10-24

### Real Bank Statement Intelligence & Zero Mock Data Architecture
- **Multi-Format Extraction Pipeline (`StatementPipeline`, `CsvStatementParser`, `XlsxStatementParser`, `PdfStatementParser`)**:
  - Implemented multi-format extraction supporting CSV (auto-detecting `utf-8-sig`, `utf-8`, `latin1`, `cp1252`), XLSX (using `openpyxl`), and PDF statements (using `pypdf`).
  - Added dynamic table header recognition and preamble skipping for Indian banks (HDFC, ICICI, SBI, Axis, Kotak).
  - Preserved source tracking fields on every imported transaction: `value_date`, `reference_number`, `balance_after`, `source_file`, `source_row`, `batch_id`, `account_mask`, `raw_type`.
  - Created `StatementImportBatch` model capturing audit trail: batch ID, user ID, bank name, masked account, date range, total credits, total debits, closing balance, and imported/duplicate counts.
  - Added batch rollback capability via `DELETE /api/v1/statement/batch/{batch_id}` with cascading transaction cleanup.
- **Indian Banking Normalizer & Accounting Rules (`StatementNormalizer`)**:
  - Date normalization supporting `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`, `DD-Mon-YYYY`, and `YYYY-MM-DD`.
  - Currency normalization supporting INR symbols (`₹`, `Rs`, `INR`), Indian comma separation (`1,45,000.00`), `Cr`/`Dr` suffixes, and accounting parentheses negatives `(5,000.00)`.
  - Self-transfer elimination: identifies transfers between own accounts and auto-sweeps (`is_internal_transfer = True`), excluding them from income and living expenses to prevent artificial inflation.
  - Credit card repayment classification: separates credit card bill settlements (`raw_type = "credit_card_payment"`, `category = "Debt & EMI"`) from new consumption expenses.
  - Refund isolation: separates merchant refunds and reversals (`raw_type = "refund"`, `category = "Refund"`) from earned income.
  - Truthful categorization: unknown transactions default to `"Uncategorized"` for explainable user review.
- **Two-Phase Review & Deduplication Pipeline (`/statement/preview`, `/statement/confirm`)**:
  - Deterministic signature hashing based on normalized date, amount, description, and reference number.
  - Detects duplicates intra-batch and across overlapping past statement imports.
  - Two-phase import workflow: preview returns metrics, detected account identifier, bank name, closing balance, coverage days/months, warnings, and transaction table before atomic persistence.
  - Atomic confirmation updates `BankAccount` balance, recalculates `FinancialProfile` observed run-rate, and triggers recurring transaction detection.
- **Strict Zero-Mock-Data Architecture**:
  - Completely purged fake transactions, mock account balances (`acc_demo_hdfc`, `acc_demo_icici`), sample debts, synthetic recurring items, and hardcoded dashboard variance factors from frontend and backend production code.
  - Replaced mock charts with actual month-by-month history aggregated from genuine persisted database transactions.
  - Implemented transparent empty states explaining required inputs (e.g. "No bank accounts linked yet. Upload 3-month statements or connect via Account Aggregator").
  - Production safeguard: `POST /api/v1/demo/seed` strictly returns `HTTP 403 Forbidden` when `ENVIRONMENT=production`.
- **Frontend Statement Import Experience (`StatementUploadModal.tsx`, `Navbar.tsx`, `BudgetView.tsx`, `DashboardView.tsx`)**:
  - Created interactive `StatementUploadModal` with drag-and-drop file upload, format validation, coverage analysis badges, parsing warnings, and transaction review table.
  - Added global "Import Statement" launcher button to top navigation bar.
  - Upgraded `BudgetView` to accept `.csv`, `.xlsx`, `.pdf` and route through unified statement endpoints.
  - Added Statement Coverage Badge and Zero-Mock-Data Onboarding Card to Dashboard.
- **Automated Regression Suite**:
  - Added `backend/tests/test_statement_intelligence.py` (9 tests) covering CSV, XLSX, and PDF parsing, Indian date/currency normalization, internal transfer accounting, credit card bill payments, refund isolation, deduplication, batch rollback, production demo safeguards, and zero-mock-data empty states.
  - All **143 tests passed out of 143 tests** (100% pass rate).
  - Frontend production build (`tsc && vite build`) passed with 0 errors in 7.06s.

## [2.3.0] - 2026-10-24

### Autonomous Context-Aware AI CFO Agent (Whole-App Intelligence & Natural-Language Actions)
- **Persistent Clarification State Machine (`PendingClarification`, `ClarificationService`)**:
  - Implemented persistent, user- and conversation-scoped `PendingClarification` model (`agent_pending_clarifications`) maintaining unique clarification IDs, original queries, stable options, extracted amounts, and expiration timestamps.
  - Socratic ambiguity handling: for credit-card loan ambiguity (e.g. *"add 10000rs has credit card loan"*), presents 4 distinct options (credit-card balance, EMI loan liability, loan inflow, or repayment) with exact ₹10,000 extraction.
  - Option matching: normalized resolution supporting direct option IDs, ordinal numbers (`"1"`, `"1."`), phrase variations (`"1. update it"`, `"Option 1"`, `"Yes, update it."`), and direct button clicks with punctuation stripping.
  - Immediate proposal transition: resolving an option transitions the clarification to `resolved` and stages a validated `PendingAction` proposal card with Confirm/Cancel controls without triggering generic questionnaires.
  - Strict 15-minute expiration enforcement and cross-conversation isolation.
- **Frontend Formatted Markdown & Option Chips (`GlobalAICFO.tsx`)**:
  - Replaced raw text output with rich structured rendering (`FormattedMessage`, `renderFormattedInline`) eliminating literal `**` or `###` syntax.
  - Interactive clarification option chips with structured `clarification_id` and `option_id` request payloads.
  - Added `finpilot:financial-data-updated` event dispatch on confirmed actions to automatically refresh data tables across all tabs.
- **Natural-Language Financial Intent Understanding (`AgentIntentParser`)**:
  - Implemented structured parsing for financial commands and questions, distinguishing read-only analysis, write actions, ambiguous commands, and unsupported external banking transfers.
  - Fixed amount extractor regex preventing premature digit truncation on unformatted numeric strings (e.g., `10000` accurately extracted as `10000.0`).
  - Contextual reference resolution: resolves follow-ups like *"reduce it by 15%"* and *"that loan"* using recent conversation turns and tracked entity references.
- **User-Confirmed Action Execution & Pending Actions System (`ActionPlanner`, `ActionExecutor`)**:
  - Implemented persistent `PendingAction` model with lifecycle state machine: `draft -> awaiting_confirmation -> executing -> succeeded` (terminal: `cancelled`, `expired`, `failed`).
  - Staged write operations generate rich preview cards with key-value breakdowns, 15-minute expiration windows, and clear financial safety disclaimers.
  - Every database write requires explicit user authorization (`POST /api/v1/assistant/actions/{id}/confirm`).
  - Strict idempotency protection against duplicate submissions, expiration defense, and database rollback on failure.
  - Direct persistence verification before confirming success.
- **Shared Web and Telegram Action Service**:
  - Implemented unified backend endpoints (`GET /actions/pending`, `POST /actions/{id}/confirm`, `POST /actions/{id}/cancel`). Both Web UI buttons and Telegram inline bot buttons invoke the exact same persistent records with strict user isolation.
- **Multi-Layer Conversation Memory (`ConversationMemoryService`)**:
  - Implemented `AgentMemory` model supporting 5 memory layers: active chat window, long-term user preferences (tax regime, risk tolerance), episodic summaries of past planning sessions, entity tracking, and live database facts.
  - Scoped strictly to authenticated `user_id` with complete cross-user isolation.
- **Feedback Learning & Adaptive Recommendation Ranking (`FeedbackService`)**:
  - Implemented `AgentFeedback` model tracking ratings (+1 / -1), user corrections, recommendation outcomes (accepted / rejected), and action confirmations.
  - Dynamically adapts proactive insight ranking: frequently dismissed categories are de-emphasized while engaged categories are boosted. Zero autonomous write permissions are granted via feedback.
- **Frontend Action Card & Feedback UI (`GlobalAICFO.tsx`)**:
  - Rendered interactive **Pending Action Proposal Cards** inside the floating chat panel with preview tables, safety disclaimers, and Confirm / Cancel buttons.
  - Added clarification option chips for 1-click answers to ambiguous queries.
  - Added thumbs up / down feedback controls on assistant responses with persistent feedback logging.
- **Automated Regression Suite**:
  - Added `backend/tests/test_clarification_workflow.py` (10 new tests) and `backend/tests/test_autonomous_agent.py` (14 new tests) covering intent parsing, credit-card loan ambiguity resolution, action staging, confirmation, idempotency, cancellation, expiration, memory isolation, feedback ranking, and API endpoints.
  - Total backend tests: **134 passed out of 134 tests** (100% pass rate).
  - Frontend production build: compiled cleanly with 0 errors in 6.18s.

### Global AI CFO 2.0 (Universal Context-Aware Financial Assistant)
- **Persistent Floating UI & Multi-Mode Panel (`GlobalAICFO.tsx`)**:
  - Added floating launcher button fixed at bottom-right of every application page with live proactive alert counter badge.
  - Interactive multi-mode viewport support: standard docked sidebar (420px), expanded analysis view (680px), and distraction-free fullscreen mode.
  - Active page contextual awareness with route badges (e.g. `Viewing: Debts & EMIs`, `Viewing: Recurring Payments`).
  - Route-aware quick prompt suggestions tailoring actions to user's current workflow.
  - Proactive financial insights carousel with one-click diagnostic queries.
  - Expandable tool execution badges revealing exact arithmetic inputs, outputs, and statutory citations.
  - In-panel conversation history clearing with cross-user isolation.
- **Unified Financial Context Service (`FinancialContextService`)**:
  - Implemented `backend/app/ai/financial_context.py` gathering verified data across user profile, linked bank accounts, transactions (90d), confirmed recurring commitments, liabilities/EMIs, asset holdings, goals, active anomalies, and 30-day cash-flow forecasts.
  - Injected seamlessly into assistant chat reasoning pipeline (`/api/v1/assistant/chat`).
- **Deterministic Affordability & Cross-Feature Tool Registry**:
  - Implemented `evaluate_affordability` in `backend/app/ai/tools.py` calculating post-commitment surplus, new Debt-to-Income (DTI) ratio against RBI benchmarks, and revised emergency runway.
  - Added deterministic tools: `get_financial_overview`, `get_account_balances`, `get_net_worth`, `query_transactions`, `summarize_income_and_expenses`, `analyze_spending_by_category`, `get_budget_performance`, `find_overspending`, `get_upcoming_obligations`, and `analyze_emergency_runway`.
- **Proactive Insights & Isolated Conversation Endpoints**:
  - Added `GET /api/v1/assistant/proactive-insights` delivering prioritized financial alerts (surplus allocation, high DTI warnings, upcoming bill clusters, overspending spikes).
  - Added `DELETE /api/v1/assistant/history` with strict user-scoping.
- **Automated Regression Test Suite**:
  - Created `backend/tests/test_global_ai_cfo.py` with 8 test cases verifying context assembly, affordability matrix, forward obligations, chat endpoint integration, proactive alerts, and history isolation.
  - Full backend test suite: **110 passed out of 110 tests** (100% pass rate).
  - Frontend production build: verified cleanly with 0 TypeScript/Vite errors.

### Recurring Transaction Management v1
- **Persistent Recurring Transactions Model & Migration**:
  - Implemented `RecurringTransaction` model in `backend/app/models/financial.py` supporting fields for user scoping, title, merchant, amount, type (income/expense), category, frequency (weekly, fortnightly, monthly, quarterly, yearly), status (`detected`, `confirmed`, `paused`, `dismissed`, `cancelled`), confidence, explanation, next expected date, user confirmation timestamp, user feedback, and private notes.
  - Added reversible Alembic migration `c92e742810a1_add_recurring_transactions_table.py` with indexes on `user_id`, `status`, `category`, and `next_expected_date`.
- **Review Queue, Lifecycle Transitions & Feedback**:
  - Implemented `RecurringTransactionService` in `backend/app/finance/recurring/service.py` to synchronize detected patterns from the Intelligence Engine with persistent records without automatically converting predictions into confirmed obligations.
  - Implemented safe user lifecycle state transitions: **Confirm** (with optional inline edits), **Dismiss** (with structured feedback reason, preventing reappearance), **Pause**, **Reactivate**, and **Cancel** (with protection against reactivating cancelled items).
  - Linked confirmed recurring records to underlying historical transactions (`Transaction.is_recurring = True`).
- **Upcoming 30-Day Occurrence Scheduler**:
  - Built forward calculation engine projecting upcoming recurring outflows and inflows across configurable horizons (30 to 180 days).
  - Accurately handles month length variations (Jan 31 $\to$ Feb 28/29), leap years, and overdue states (`is_overdue = True`) without fabricating transactions.
- **Forecast & Intelligence Engine Reconciled Integration**:
  - Integrated confirmed recurring records into `forecast_cash_flow`: user-confirmed recurring amounts take precedence over unconfirmed detection estimates.
  - Built double-counting safeguard: reconciles confirmed recurring obligations with historical living expenses so fixed commitments and run-rate do not artificially inflate projected expenses.
  - Updated `generate_intelligence_feed` recurring alerts to route directly to `action_tab="recurring"`.
- **Authenticated REST API Endpoints (`/api/v1/recurring-transactions`)**:
  - Exposes 10 endpoints: `GET /`, `GET /detections`, `GET /summary`, `GET /upcoming`, `GET /{id}`, `POST /`, `POST /{id}/confirm`, `PATCH /{id}`, `POST /{id}/dismiss`, `POST /{id}/pause`, `POST /{id}/reactivate`, `POST /{id}/cancel`.
- **Dedicated Frontend Interface & Navigation**:
  - Built `RecurringTransactionsView.tsx` with summary metric cards (monthly expenses, monthly income, net recurring cash flow, review queue count), interactive detection review queue cards, confirmed records management table with status filtering, and chronological 30-day upcoming activity schedule.
  - Added modals for manual creation, item editing/confirmation, and structured dismissal feedback.
  - Added `'recurring'` tab to `Sidebar.tsx` and `App.tsx`.
- **AI CFO Recurring Tools & Context Enrichment**:
  - Added `get_recurring_commitments` tool to `backend/app/ai/tools.py` calculating monthly recurring totals, expense percentage, and pause impact simulation.
  - Enriched `/assistant/chat` context with user's confirmed recurring list.
- **Automated Regression Suite**:
  - Added `backend/tests/test_recurring_management.py` (8 new tests) covering detection sync, confirmation with edits, dismissal persistence, pause/reactivate/cancel lifecycle, upcoming occurrence scheduler, forecast integration, and cross-user isolation.
  - Total backend tests: **102 passed** across 17 test modules (100% pass rate).
  - Frontend production build: compiled cleanly with 0 errors in 4.58s.

### Financial Intelligence Engine v1 (Shared Intelligence Layer)
- **Deterministic Shared Financial Intelligence Engine**:
  - Implemented `IntelligenceEngine` (`backend/app/finance/intelligence/engine.py`) connecting transaction management, cash-flow forecasting, adaptive budgeting, savings goals, financial health assessment, and the AI CFO assistant.
  - Built `get_canonical_snapshot()` producing user-scoped verified financial snapshots aggregating genuine income, expenses, category spending, liquid bank + asset reserves, net worth, and emergency fund runway months.
  - Implemented strict double-counting prevention: internal transfers (`is_internal_transfer == True`) are strictly excluded from income and expense aggregates.
  - Implemented `detect_recurring_transactions()` using merchant token similarity, interval periodicity (weekly, monthly, quarterly), and amount variance checks (<25%).
  - Implemented `detect_spending_anomalies()` comparing current month category spend against prior 60-day moving baselines, triggering anomalies for surges exceeding >30% and >₹2,000.
  - Implemented `forecast_cash_flow()` projecting 30-day and 90-day cash surplus and daily burn rate with ending liquid cash balances and uncertainty assumptions.
  - Implemented `compute_adaptive_budget_recommendations()` applying the 50-30-20 framework to suggest phased 15% discretionary reductions (Food & Dining, Shopping, Entertainment) to free up surplus for goal SIPs.
  - Implemented `assess_goals_feasibility()` computing exact required monthly contributions, completion timeline delays, and actionable remedial sensitivities.
  - Implemented `preview_categorization()` providing deterministic regex classification for Indian merchants and categories.
- **FinPilot Intelligence Feed & UI Integration**:
  - Added the **FinPilot Intelligence Feed** directly onto `DashboardView.tsx`, featuring severity badges (critical, warning, info, success), metrics, confidence ratings, and direct routing buttons (`onNavigateToTab`) to relevant budget, debt, goal, and tax views.
  - Added empty and loading states to ensure graceful rendering across sparse, normal, and demo data modes.
- **AI CFO Assistant Intelligence Tools & Context Grounding**:
  - Registered 3 new deterministic tools (`get_cash_flow_forecast`, `explain_spending_anomalies`, `assess_goal_feasibility`) in `backend/app/ai/tools.py`.
  - Enriched AI CFO conversational context in `/api/v1/assistant/chat` with authenticated user canonical snapshot metrics (income, expenses, cash surplus, savings rate, emergency runway) and active spending alerts.
  - Added suggested intelligence questions to `AssistantView.tsx` ("Why did I spend more this month?", "What is my projected cash flow?", "Am I on track for my savings goals?").
- **Authenticated REST API Endpoints (`/api/v1/intelligence`)**:
  - Added 8 user-scoped endpoints: `/snapshot`, `/feed`, `/recurring`, `/anomalies`, `/forecast`, `/budget-recommendations`, `/goals-feasibility`, `/categorize`.
- **Unit and Integration Test Suite**:
  - Added `backend/tests/test_intelligence_engine.py` (9 new tests) covering snapshot math, transfer exclusion, anomaly detection, recurring detection, forecasting, adaptive budgeting, goal feasibility, AI tools, and cross-user isolation.
  - Total test suite: **94 passed** across 16 test modules (0 failures, 100% pass rate).
  - Frontend production build: `tsc && vite build` compiled with 0 errors in 5.56s.

### Financial Metric Parity, Assistant Persistence & Isolated Bank Sandbox
- **Account Aggregator Isolation & Safe Pausing**:
  - Safely isolated live Finvu FIU account aggregator integration while preserving complete adapter implementation (`FinvuAccountAggregatorAdapter`), routes (`/Consent/Notification`, `/FI/Notification`, `/webhook`), and ReBIT JWS security.
  - Activated offline `sandbox` bank provider in local development for zero-dependency execution.
  - Added clear UI disclosure banner on `BankAccountsView.tsx` distinguishing sandbox simulated bank records from live account aggregator data.
- **Dashboard & FIRE Engine Parity**:
  - Updated `get_dashboard_summary()` (`backend/app/api/v1/endpoints/dashboard.py`) to query and sum linked `BankAccount` balances into `total_assets`, `net_worth`, and `emergency_fund_current`, synchronizing dashboard metrics with the FIRE forecasting engine.
- **Dynamic User Profile in FIRE Planning**:
  - Updated `FirePlanningView.tsx` to mount and fetch the authenticated user's real figures via `GET /api/v1/fire/profile`, dynamically synchronizing age, retirement targets, monthly expenses, investable assets, and SIP with real database state.
  - Standardized authentication in FIRE view using `apiRequest` and `getAuthToken()`.
- **Persistent AI CFO Conversation Context**:
  - Enhanced `AssistantView.tsx` to automatically fetch persisted chat messages from `GET /api/v1/assistant/history` on mount, restoring multi-turn conversation context across session reloads.
- **Dynamic Cash Flow Runway Chart**:
  - Replaced hardcoded calendar months in `DashboardView.tsx` with a dynamic 6-month calculation ending in the current month.
- **Decision Simulator Liquid Savings Parity**:
  - Updated `simulate_scenario()` (`backend/app/api/v1/endpoints/scenarios.py`) to query and sum linked `BankAccount` balances alongside asset holdings into `user_context["current_savings"]`.
  - Added auto-population of authenticated user profile metrics on mount in `ScenarioSimulatorView.tsx`.
- **Manual Cash Flow & Transaction Entry**:
  - Added "+ Add Transaction" modal to `frontend/src/features/budget/BudgetView.tsx` with date, type, amount, category, and description inputs, enabling direct entry for non-CSV and cash transactions.
- **Strict Financial Schema Validation Bounds**:
  - Enforced positive value constraints (`gt=0`, `ge=0`) on transactions, liabilities, goals, and age bounds (18-120) in `backend/app/schemas/financial.py` using Pydantic `Field`.
- **Automated Cross-User Isolation & Boundary Test Suite**:
  - Added `backend/tests/test_cross_user_isolation.py` proving that User A's goals, transactions, liabilities, saved scenarios, and bank accounts cannot be accessed or deleted by User B (returning 404/401 with zero cross-user exposure).
- **Verification & Launch Gates**:
  - Backend pytest suite: **85 passed** across 15 test modules (100% pass rate).
  - Frontend production build: `tsc && vite build` compiled cleanly in 5.76s with zero errors.

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
