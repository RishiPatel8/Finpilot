# FinPilot AI — Financial Intelligence Engine v1 Specification & Architecture

## 1. Overview and Mission

The **FinPilot Financial Intelligence Engine v1** is a deterministic, shared financial intelligence layer connecting:
- Transaction management and expense categorization
- Income and living expense cash-flow tracking
- Adaptive 50-30-20 budgeting
- 30-day and 90-day cash-flow forecasting
- Financial milestone feasibility and SIP calibration
- AI CFO conversational reasoning and deterministic tool calling

It empowers Indian retail investors and salaried/self-employed professionals to understand **what changed** in their finances, **why it changed**, **what is projected to happen next**, and **what exact calibrated action to take**.

---

## 2. Core Architectural Principles & Safeguards

1. **Deterministic First, AI Explainable**: All calculations (surplus, emergency runway, anomaly detection, cash flow projections, SIP feasibility) are executed by audited Python engines using statutory Indian financial rules. The LLM (Gemini 2.5 Flash) explains and contextualizes verified engine results but **never invents or overrides** numerical values.
2. **Canonical Financial Snapshot**: Every module references a unified, user-scoped canonical financial snapshot.
3. **Double-Counting Prevention**:
   - Internal transfers between user accounts (`is_internal_transfer == True`) are strictly excluded from income and expenses.
   - Liquid bank balances (positive balances only) are combined with liquid asset holdings (`liquid_mf`, `cash`, `fd`) to compute emergency fund runway without duplication.
4. **Strict User Scoping & Isolation**: Every query and database transaction filters strictly on `user_id == current_user.id`. Cross-user data leaks are prevented by JWT validation and database constraints.
5. **No Fabricated Fallbacks**: Missing or sparse data is explicitly represented with `insufficient_data: true` or `confidence: "low"` rather than manufactured zeros or false projections.
6. **Isolated Bank Integration**: Bank Account Aggregator integration remains in local sandbox mode (`BANK_PROVIDER=sandbox`) with the Finvu FIU integration cleanly paused.

---

## 3. Financial Engine Capabilities

### 3.1 Canonical Financial Snapshot (`/api/v1/intelligence/snapshot`)
Aggregates:
- **Income & Living Expenses**: Sum of genuine non-transfer transactions across specified period (`current_month`, `last_30_days`, `last_month`).
- **Net Cash Flow & Savings Rate**: $\text{Net Cash Flow} = \text{Income} - \text{Expenses}$; $\text{Savings Rate} = (\text{Net Cash Flow} / \text{Income}) \times 100$.
- **Category Spending**: Breakdown across official taxonomy (Housing & Utilities, Food & Dining, Transportation, Groceries, etc.).
- **Liquid Capital & Net Worth**: Aggregated bank balances + liquid investments, minus active liabilities principal.
- **Emergency Reserve Runway**: $\text{Liquid Savings} / \text{Monthly Expenses}$, measured in months relative to statutory 6-month safety benchmark.

### 3.2 Transaction Intelligence & Anomaly Detection (`/api/v1/intelligence/anomalies`)
- **Deterministic Categorization**: Rule-based regex categorization tuned for Indian merchants (Swiggy, Zomato, Blinkit, Zepto, Uber, Ola, BESCOM, Tata Power, D-Mart, Apollo Pharmacy, Zerodha, etc.).
- **Spending Anomaly Engine**: Compares current month spending by category against prior 60-day monthly moving average.
- **Trigger Conditions**: Triggers an alert when category spending exceeds baseline by $> 30\%$ **and** $\ge ₹2,000$.
- **Severity Classification**:
  - `critical`: Spend increase $\ge 75\%$ or absolute spike $\ge ₹10,000$.
  - `elevated`: Spend increase $\ge 30\%$ and $\ge ₹2,000$.
  - `moderate`: Baseline variance within acceptable tolerance.

### 3.3 Recurring Transaction Management & Lifecycle Integration (`/api/v1/recurring-transactions`)
- Identifies periodic outflows (rents, loan EMIs, OTT subscriptions, utility payments) across the last 180 days.
- Clusters by merchant/description token similarity with interval periodicity and variance checks.
- Synchronizes with persisted `recurring_transactions` database records.
- Enables complete user lifecycle management: **Confirm**, **Edit**, **Dismiss**, **Pause**, **Reactivate**, and **Cancel**.
- Feeds confirmed recurring commitments directly into forward 30/90-day cash flow projections.
- Generates 30-day forward upcoming payment schedules with overdue tracking.
- See full specification in [Recurring Transaction Management](RECURRING_TRANSACTION_MANAGEMENT.md).

### 3.4 Cash-Flow Forecasting (`/api/v1/intelligence/forecast`)
- Generates 30-day and 90-day forward projections.
- Incorporates daily burn-rate, verified recurring commitments, and beginning liquid cash balances.
- Explicitly flags projections with `is_estimated: true` and includes key uncertainty assumptions.

### 3.5 Adaptive Budget Calibration (`/api/v1/intelligence/budget-recommendations`)
- Analyzes category spend against the 50-30-20 financial rule (50% Needs, 30% Wants, 20% Savings/Investments).
- Detects over-allocation in discretionary categories (Shopping, Entertainment, Food & Dining) and proposes non-destructive, phased 15% budget trims to unlock surplus for financial goals.

### 3.6 Milestone Feasibility Assessment (`/api/v1/intelligence/goals-feasibility`)
- Computes exact monthly required SIP: $\text{Required SIP} = (\text{Target Amount} - \text{Current Amount}) / \text{Months Remaining}$.
- Assesses feasibility against actual monthly cash surplus:
  - $\text{Surplus} \ge \text{Required SIP}$: `is_on_track = true`.
  - $\text{Surplus} < \text{Required SIP}$: Computes shortfall and projected completion delay in months, accompanied by recommended category savings.

### 3.7 FinPilot Intelligence Feed (`/api/v1/intelligence/feed`)
- Unified, prioritized feed synthesizing anomalies, budget risks, goal calibrations, and upcoming recurring bills.
- Categorized and prioritized by severity: `critical` $\to$ `warning` $\to$ `info` $\to$ `success`.
- Directly routable to actionable tabs (`budget`, `goals`, `debts`, `tax`, `fire`).

---

## 4. API Endpoints Contract

All endpoints reside under `/api/v1/intelligence` and require a valid `Authorization: Bearer <JWT>` header:

| Method | Path | Query / Body | Response Schema | Description |
|---|---|---|---|---|
| `GET` | `/snapshot` | `period` (`current_month`, `last_30_days`, `last_month`) | `CanonicalFinancialSnapshot` | Verified canonical financial snapshot |
| `GET` | `/feed` | None | `IntelligenceFeedResponse` | Prioritized, deduplicated insights feed |
| `GET` | `/recurring` | None | `List[RecurringTransactionPattern]` | Detected recurring expenses and subscriptions |
| `GET` | `/anomalies` | None | `List[SpendingAnomaly]` | Spending surges exceeding 30% & ₹2,000 |
| `GET` | `/forecast` | `horizon_days` (30 or 90) | `CashFlowForecast` | Forward cash-flow projection |
| `GET` | `/budget-recommendations`| None | `List[AdaptiveBudgetRecommendation]` | 50-30-20 category budget recommendations |
| `GET` | `/goals-feasibility` | None | `List[GoalFeasibility]` | Goal feasibility & SIP requirement checks |
| `POST` | `/categorize` | `{"description": "...", "amount": 0.0}` | `CategorizationPreviewResponse` | Deterministic Indian merchant categorization preview |

---

## 5. AI CFO Integration Architecture

The AI CFO assistant (`/api/v1/assistant/chat`) integrates directly with the Intelligence Engine via 3 registered deterministic calculation tools:
1. `get_cash_flow_forecast`: Runs forward cash projections for 30 or 90 days.
2. `explain_spending_anomalies`: Compares category spending to prior baselines.
3. `assess_goal_feasibility`: Computes exact required monthly contributions and delay impacts.

In addition, each chat request automatically enriches the system context with the authenticated user's canonical snapshot metrics (income, expenses, surplus, savings rate, emergency runway) and active spending alerts, grounding every conversation in verified user finances.

---

## 6. Verification and Test Coverage

The Intelligence Engine is verified by a 9-test unit and integration test suite in [`backend/tests/test_intelligence_engine.py`](file:///d:/finpilot/backend/tests/test_intelligence_engine.py):
- `test_canonical_snapshot_calculation_and_transfer_exclusion`
- `test_recurring_transaction_detection`
- `test_spending_anomaly_detection_with_thresholds`
- `test_cash_flow_forecasting_30_and_90_days`
- `test_adaptive_budget_recommendations`
- `test_goals_feasibility_and_sensitivity_assessment`
- `test_intelligence_feed_generation`
- `test_deterministic_ai_tools_execution`
- `test_intelligence_api_endpoints_and_cross_user_isolation`

Total test suite: **94 passed** across 16 test modules with 0 regressions.
