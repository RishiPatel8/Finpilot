# FinPilot AI — Recurring Transaction Management v1 Specification

## 1. Executive Summary & Objective

The **Recurring Transaction Management v1** module bridges AI pattern detection and user-controlled financial tracking. It converts detected subscriptions, bill payments, and salaries into verified, user-controlled financial commitments.

Users can:
1. **Review AI Detections**: Inspect recurring patterns identified by the Intelligence Engine with confidence indicators and explainable historical evidence.
2. **Confirm & Edit**: Confirm detected recurring transactions with optional 1-click edits (customizing title, amount, frequency, category, next due date, and notes).
3. **Dismiss False Positives**: Dismiss non-recurring charges with optional structured feedback without modifying underlying historical transactions.
4. **Lifecycle Control**: Pause, reactivate, or permanently cancel confirmed commitments.
5. **30-Day Forward Payment Schedule**: View chronological upcoming outflows and inflows with overdue tracking and days-remaining badges.
6. **Forecast & Health Grounding**: Feed verified recurring obligations into forward 30/90-day cash flow projections and the AI CFO assistant without double-counting.

---

## 2. Data Model & Database Migration

### 2.1 Database Schema (`recurring_transactions`)
Defined in [`backend/app/models/financial.py`](file:///d:/finpilot/backend/app/models/financial.py):

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | Primary Key, UUID | Unique recurring item identifier |
| `user_id` | `VARCHAR(36)` | Foreign Key `users.id` (CASCADE), Indexed | Owner user ID |
| `bank_account_id` | `VARCHAR(36)` | Foreign Key `bank_accounts.id` (SET NULL), Nullable | Linked bank account |
| `name` | `VARCHAR(255)` | Not Null | User-visible title (e.g., "Netflix India") |
| `merchant` | `VARCHAR(255)` | Nullable | Underlying merchant/counterparty |
| `transaction_type` | `VARCHAR(20)` | Not Null, Default: `'expense'` | `'expense'` or `'income'` |
| `amount` | `NUMERIC(14, 2)` | Not Null, $> 0$ | Expected payment/inflow amount in INR |
| `category` | `VARCHAR(100)` | Not Null, Indexed | Financial category |
| `frequency` | `VARCHAR(30)` | Not Null, Default: `'monthly'` | `'weekly'`, `'fortnightly'`, `'monthly'`, `'quarterly'`, `'yearly'` |
| `status` | `VARCHAR(30)` | Not Null, Default: `'detected'`, Indexed | `'detected'`, `'confirmed'`, `'paused'`, `'dismissed'`, `'cancelled'` |
| `confidence` | `VARCHAR(20)` | Not Null, Default: `'medium'` | `'high'`, `'medium'`, `'low'` |
| `detection_source` | `VARCHAR(50)` | Not Null, Default: `'intelligence_engine'` | `'intelligence_engine'`, `'manual'`, `'rule_match'` |
| `explanation` | `TEXT` | Nullable | Why the item was identified as recurring |
| `next_expected_date`| `DATE` | Nullable, Indexed | Next scheduled due date |
| `start_date` | `DATE` | Nullable | Subscription/commitment inception date |
| `end_date` | `DATE` | Nullable | Final expiration or cancellation date |
| `last_occurrence_date`| `DATE` | Nullable | Most recent transaction date |
| `occurrence_count` | `INTEGER` | Not Null, Default: `1` | Historical occurrence count |
| `user_confirmed_at` | `DATETIME` | Nullable | Timestamp when user confirmed |
| `user_feedback` | `TEXT` | Nullable | User reason if dismissed |
| `user_notes` | `TEXT` | Nullable | Optional user private notes |
| `created_at` | `DATETIME` | Not Null, UTC | Record creation timestamp |
| `updated_at` | `DATETIME` | Not Null, UTC | Last modification timestamp |

### 2.2 Reversible Migration
Alembic migration: [`backend/alembic/versions/c92e742810a1_add_recurring_transactions_table.py`](file:///d:/finpilot/backend/alembic/versions/c92e742810a1_add_recurring_transactions_table.py).
- Upgrades table with foreign keys and compound indexes on `user_id`, `status`, `category`, and `next_expected_date`.
- Downgrades cleanly by dropping indexes and table.

---

## 3. Recurring Lifecycle & State Transitions

```
                    [Transaction History]
                              |
                              v (Pattern Detection)
                        +------------+
                        |  DETECTED  |
                        +------------+
                         /     |    \
           (User Dismiss)      |     \ (User Confirm)
               /               |      \
              v                |       v
       +-----------+           |  +-------------+
       | DISMISSED |           |  |  CONFIRMED  | <------+
       +-----------+           |  +-------------+        |
                               |      /       \          |
                               | (Pause)    (Cancel)  (Reactivate)
                               |   /             \       |
                               v  v               v      |
                           +--------+         +-----------+
                           | PAUSED |         | CANCELLED |
                           +--------+         +-----------+
```

### Transition Rules:
1. **`detected` $\to$ `confirmed`**: Promotes AI prediction to a verified obligation; sets `user_confirmed_at`; marks source transactions with `is_recurring = True`.
2. **`detected` $\to$ `dismissed`**: Silences detection; stores optional user feedback; permanently excludes pattern from re-appearing in review queue.
3. **`confirmed` $\to$ `paused`**: Temporarily removes commitment from active cash-flow projections and upcoming schedule while retaining history.
4. **`paused` $\to$ `confirmed`**: Re-activates commitment; automatically advances overdue `next_expected_date` to upcoming forward dates.
5. **`confirmed` / `paused` $\to$ `cancelled`**: Sets `end_date = today` and marks cancelled. Cannot be reactivated directly (requires creating a new item).

---

## 4. API Specification (`/api/v1/recurring-transactions`)

All routes require `Authorization: Bearer <JWT>` and enforce strict user scoping:

| Method | Endpoint | Query / Body | Response Schema | Description |
|---|---|---|---|---|
| `GET` | `/` | `status`, `transaction_type` | `List[RecurringTransactionResponse]` | List user's recurring records |
| `GET` | `/detections` | None | `List[RecurringTransactionResponse]` | Scan history & return unreviewed detected items |
| `GET` | `/summary` | None | `RecurringSummary` | Monthly recurring totals, active counts, and next payments |
| `GET` | `/upcoming` | `horizon_days` (default 30) | `UpcomingSummary` | Chronological forward occurrence schedule |
| `GET` | `/{id}` | None | `RecurringTransactionResponse` | Get single recurring record |
| `POST` | `/` | `RecurringTransactionCreate` | `RecurringTransactionResponse` | Manually add a recurring item |
| `POST` | `/{id}/confirm` | `RecurringTransactionConfirmRequest` | `RecurringTransactionResponse` | Confirm detection with optional adjustments |
| `PATCH` | `/{id}` | `RecurringTransactionUpdate` | `RecurringTransactionResponse` | Edit recurring record details |
| `POST` | `/{id}/dismiss` | `RecurringTransactionDismissRequest` | `RecurringTransactionResponse` | Dismiss detection with optional feedback |
| `POST` | `/{id}/pause` | None | `RecurringTransactionResponse` | Pause active recurring item |
| `POST` | `/{id}/reactivate` | None | `RecurringTransactionResponse` | Reactivate paused recurring item |
| `POST` | `/{id}/cancel` | None | `RecurringTransactionResponse` | Permanently cancel recurring item |

---

## 5. Forecast & Double-Counting Safeguards

### 5.1 Cash-Flow Forecasting Integration
In [`backend/app/finance/intelligence/engine.py`](file:///d:/finpilot/backend/app/finance/intelligence/engine.py):
1. **Confirmed Priority**: If confirmed records exist in `recurring_transactions`, they supersede unconfirmed detection heuristics.
2. **Monthly Normalization**: Frequencies are converted accurately to monthly equivalents:
   - Weekly: $\times 52 / 12$
   - Fortnightly: $\times 26 / 12$
   - Monthly: $\times 1$
   - Quarterly: $/ 3$
   - Yearly: $/ 12$
3. **Double-Counting Prevention**: Reconciles confirmed recurring obligations with recent historical averages:
   $$\text{Non-Recurring Burn} = \max(0, \text{Snapshot Living Expenses} - \text{Confirmed Recurring Expenses})$$
   $$\text{Projected Expenses} = (\text{Recurring Expenses} \times \text{Horizon Fraction}) + (\text{Non-Recurring Burn} \times \text{Horizon Fraction})$$
4. **Exclusion of Non-Active States**: `paused`, `dismissed`, and `cancelled` items are strictly excluded from forward projections.

### 5.2 Upcoming Occurrence Scheduler
In [`backend/app/finance/recurring/service.py`](file:///d:/finpilot/backend/app/finance/recurring/service.py):
- Uses calendar month arithmetic (`_add_months`) handling month length variations (e.g. January 31 $\to$ February 28/29).
- Tracks `is_overdue = True` if an expected date has passed without recorded payment, keeping overdue bills visible until reconciled.

---

## 6. AI CFO Integration

Registered in [`backend/app/ai/tools.py`](file:///d:/finpilot/backend/app/ai/tools.py):
- **Tool**: `get_recurring_commitments(items, total_monthly_expenses, simulated_pause_amount)`
- Evaluates:
  - Total monthly commitment and percentage of living expenses.
  - Category breakdown (EMIs, housing, subscriptions, utilities).
  - Financial impact simulation: calculates annualized freed cash surplus if a user pauses or cancels an expense.
- **Context Injection**: `/api/v1/assistant/chat` injects the user's active confirmed recurring list into LLM system prompts so questions like *"How much do I spend on subscriptions?"* or *"What happens if I pause Netflix?"* cite real user figures.

---

## 7. Verification & Automated Test Coverage

Tested across **17 test modules** with **102 tests passing (100% pass rate)**:
- [`backend/tests/test_recurring_management.py`](file:///d:/finpilot/backend/tests/test_recurring_management.py):
  1. `test_sync_and_get_detections`
  2. `test_confirm_detection_with_edits`
  3. `test_dismiss_detection_persistence`
  4. `test_pause_reactivate_cancel_lifecycle`
  5. `test_upcoming_occurrences_calculation`
  6. `test_recurring_summary_and_forecast_integration`
  7. `test_ai_cfo_recurring_commitments_tool`
  8. `test_recurring_api_endpoints_and_cross_user_isolation`
- Frontend production build: `npm run build` compiled cleanly in 4.58s with 0 TypeScript errors.
