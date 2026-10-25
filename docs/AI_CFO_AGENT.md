# FinPilot AI — Autonomous Context-Aware AI CFO Agent

## 1. Executive Summary

FinPilot AI upgrades the AI CFO into an **Autonomous Context-Aware AI CFO Agent**. The agent goes beyond passive question-answering by understanding natural-language financial commands across all application domains (transactions, debts/liabilities, recurring commitments, budgets, savings goals, cash flow, and tax), staging validated financial changes for explicit user confirmation, maintaining multi-layer conversation memory, utilizing statutory RAG knowledge, and learning from user feedback.

Crucially, the agent operates under **strict financial safety boundaries**:
1. All database-modifying commands require explicit, human-confirmed authorization.
2. The agent never executes real-world bank fund transfers, wire payments, or loan disbursements.
3. Every write operation is mediated through a persistent pending-action state machine shared identically between the Web UI and future channels such as Telegram.

---

## 2. System Architecture

```mermaid
graph TD
    User([User on Web or Telegram]) -->|Natural Language Command| Agent[FinancialAgent /api/v1/assistant/chat]
    Agent --> ContextService[FinancialContextService]
    ContextService --> LiveDB[(PostgreSQL / SQLite)]
    Agent --> MemoryService[ConversationMemoryService]
    MemoryService --> AgentMemory[(agent_memories Table)]
    Agent --> IntentParser[AgentIntentParser]
    
    IntentParser -->|Ambiguous Request| Clarify[Ask 1 Focused Clarification Question]
    Clarify --> User
    
    IntentParser -->|Read / Analysis| DeterministicTools[Deterministic Tools & Statutory RAG]
    DeterministicTools --> Response[Grounded Financial Analysis]
    Response --> User
    
    IntentParser -->|Write Command| ActionPlanner[ActionPlanner]
    ActionPlanner -->|Staged Proposal| PendingActions[(agent_pending_actions Table)]
    ActionPlanner -->|Preview Card + Disclaimer| User
    
    User -->|Explicit Confirm| ActionExecutor[ActionExecutor /actions/{id}/confirm]
    User -->|Cancel| ActionExecutorCancel[ActionExecutor /actions/{id}/cancel]
    
    ActionExecutor --> VerifyAuth{Authorized & Valid?}
    VerifyAuth -->|Yes| AuthoritativeService[Authoritative Service / Model]
    AuthoritativeService --> LiveDB
    ActionExecutor -->|Status: Succeeded + Verification| SuccessResult[Persisted Record Confirmation]
    SuccessResult --> User
    
    User -->|Rating / Correction| FeedbackService[FeedbackService /api/v1/assistant/feedback]
    FeedbackService --> AgentFeedback[(agent_feedback Table)]
    FeedbackService -->|Adaptive Ranking| Insights[Proactive Insights Ranking]
```

---

## 3. Supported Financial Domains & Authoritative Data Models

| Domain | Authoritative Model | Key Operations | Read / Write |
| :--- | :--- | :--- | :--- |
| **Transactions** | `Transaction` | Income/Expense tracking, categorization, manual/bank-sync tags | Read & Write (Confirmed) |
| **Debts & Liabilities** | `Liability` | Loans (Personal, Home, Car, Education), EMIs, interest rates, tenure | Read & Write (Confirmed) |
| **Recurring & Subscriptions**| `RecurringTransaction` | Detection review queue, Confirm, Pause, Reactivate, Cancel | Read & Write (Confirmed) |
| **Budgets & Cash Flow** | `FinancialProfile`, `BudgetEngine` | Needs/Wants/Savings allocation, relative percent adjustments | Read & Write (Confirmed) |
| **Savings Goals** | `FinancialGoal`, `InvestmentEngine`| Target amount, target completion dates, SIP projections | Read & Write (Confirmed) |
| **Accounts & Balances** | `BankAccount` | Provider-reported balances, sync logs, AA consent status | Read-Only |
| **Asset Holdings** | `AssetHolding` | Liquid mutual funds, fixed deposits, bonds, EPF/PPF | Read-Only |
| **Tax Planning** | `TaxRecord`, `TaxEngine` | AY 2025-26 New vs Old regime, standard deductions, 80C | Read-Only |
| **FIRE Forecaster** | `FireEngine` | Lean, Regular, Fat, Coast FIRE accumulation & decumulation | Read-Only |
| **Intelligence Snapshots** | `IntelligenceEngine` | Canonical snapshots, 30d cash-flow forecast, anomaly alerts | Read-Only |

---

## 4. Structured Natural-Language Intent Understanding

The agent's intent engine (`AgentIntentParser`) classifies input into 4 distinct execution classes:

### 4.1 Write Commands (Staged via Pending Actions)
- *"Add a personal loan of ₹50,000 at 12% interest for 2 years"* $\to$ `create_debt`
- *"Record ₹3,500 spent on groceries"* $\to$ `create_transaction` (type: expense)
- *"I received ₹45,000 salary today"* $\to$ `create_transaction` (type: income)
- *"Add my electricity bill of ₹2,500, due on the 28th"* $\to$ `create_recurring_commitment`
- *"Pause my gym subscription"* $\to$ `pause_recurring_commitment`
- *"Cancel my Netflix subscription"* $\to$ `cancel_recurring_commitment`
- *"Increase my grocery budget to ₹7,000"* $\to$ `update_budget` (absolute)
- *"Reduce dining out budget by 15%"* $\to$ `update_budget` (relative adjustment)
- *"Create a vacation goal of ₹1,00,000 by December 2026"* $\to$ `create_savings_goal`

### 4.2 Ambiguity Handling & Persistent Clarification State (`agent_pending_clarifications`)
When a command lacks financial specificity, the agent does **not** guess or jump to a questionnaire. It creates a persistent, user- and conversation-scoped `PendingClarification` record and asks one focused clarification question with structured options:

#### Credit Card Loan Disambiguation (e.g. *"add 10000rs has credit card loan"*)
1. **Credit-card outstanding balance** (`create_debt` with 36% APR, 1 month tenure)
2. **Credit-card EMI/loan liability** (`create_debt` with 16% APR, 12 months tenure, calculated EMI)
3. **Loan received as income** (`create_transaction` with type: income, category: "Loan Inflow")
4. **Record a repayment already made** (`create_transaction` with type: expense, category: "Debt Repayment")

#### General Loan Disambiguation (e.g. *"Add ₹1,000 loan to debt"*)
1. **Record a new debt liability** (Personal Loan, ₹1,000 principal)
2. **Record a loan repayment or EMI payment made** (Expense, category: "Debt Repayment")
3. **Record loan disbursement received as income** (Income, category: "Loan Inflow")

#### Clarification Resolution Guarantees
- **Persistent State**: The clarification is stored in `agent_pending_clarifications` with `id`, `user_id`, `conversation_id`, `original_request`, `options` (JSON), `extracted_amount`, `status`, and `expires_at`.
- **Option Matching**: Selecting an option chip transmits `{ clarification_id, option_id }`. Typed replies like `"1"`, `"1. update it"`, `"Option 1"`, or `"Yes, update it."` are normalized (including trailing punctuation stripping) and matched directly against the active clarification.
- **Immediate Action Staging**: Resolving an option transitions the clarification to `resolved` and immediately generates an `Action Proposal` awaiting confirmation without falling back to generic questionnaires.
- **Expiration & Isolation**: Clarifications expire after 15 minutes and cannot be resolved across different conversation IDs or users.

### 4.3 Contextual Pronoun & Relative References
The agent resolves follow-up references such as *"reduce it by 10%"*, *"that loan"*, or *"the same budget"* by inspecting the user's active conversation history and last-tracked entity in `agent_memories`.

### 4.4 Unsupported External Actions
If the user requests an external payment (*"Wire transfer ₹10,000 to John"* or *"Send money via UPI"*), the agent clearly explains that FinPilot AI is a personal finance record-keeping and planning platform and does not disburse external banking wires.

---

## 5. User-Confirmed Action Execution Lifecycle

All write operations follow a strict, non-bypassable state machine:

```
[User Command]
       ↓
[Draft / Validation]
       ↓
[Awaiting Confirmation]  ──(15 min timeout)──>  [Expired]
       ↓
[User Confirmed]
       ↓
[Executing (DB Transaction)]  ──(Error/Constraint)──>  [Failed (Rollback)]
       ↓
[Persistence Verified]
       ↓
[Succeeded (Audit Record)]
```

### 5.1 Pending Action Attributes (`agent_pending_actions`)
- `id`: Unique UUIDv4 identifier.
- `user_id`: Foreign key strictly tied to the authenticated user.
- `action_type`: Specific typed action (`create_transaction`, `create_debt`, etc.).
- `parameters`: Validated JSON parameters.
- `preview`: Formatted title, summary, key-value items, and safety disclaimer.
- `status`: `awaiting_confirmation`, `executing`, `succeeded`, `cancelled`, `expired`, `failed`.
- `idempotency_key`: Prevents duplicate executions from repeated clicks or retried requests.
- `expires_at`: Enforces a 15-minute validity window.
- `executed_at`: Timestamp of verified persistence.

### 5.2 Mandatory Safety Guarantees
1. **Explicit Consent**: Zero financial writes occur until the user triggers `POST /api/v1/assistant/actions/{id}/confirm`.
2. **User Isolation**: User 2 cannot inspect or confirm User 1's pending actions.
3. **Idempotency**: Retried confirmations on a `succeeded` action return the existing result without duplicating records.
4. **Replay & Expiration Defense**: Expired or cancelled proposals are rejected.
5. **Persistence Verification**: Every handler performs a direct database query verification (`db.query(Entity).filter_by(id=new_id)`) before returning success.

---

## 6. Shared Web & Telegram Action Service

The backend action API is unified across both the browser interface and external bots (such as Telegram):

- `GET /api/v1/assistant/actions/pending`: Fetches open pending actions for the user.
- `POST /api/v1/assistant/actions/{action_id}/confirm`: Confirms and executes the action.
- `POST /api/v1/assistant/actions/{action_id}/cancel`: Cancels the proposal.

Whether a user clicks **"Confirm & Execute"** on the Web UI or an inline confirmation button in a Telegram bot, both interfaces resolve to the exact same persistent `PendingAction` record with shared authorization, validation, and audit logging.

---

## 7. Persistent Conversation Memory & RAG Knowledge

### 7.1 Memory Layers (`agent_memories`)
1. **Active Window**: Recent 8-10 conversation turns from `chat_messages`.
2. **User Preferences**: Long-term explicit settings (`preferred_tax_regime`, `risk_tolerance`, `monthly_savings_target`).
3. **Episodic Memory**: Summaries of prior advice and financial planning sessions.
4. **Entity Resolution Cache**: Last referenced loan, category, or recurring item.
5. **Live Database Truth**: Current balances and transactions are always queried live from the database, preventing stale chat messages from overriding actual balances.

### 7.2 Statutory RAG System (`KnowledgeRetriever`)
- Ingests approved legal and regulatory sources:
  - Income Tax Act, 1961 (Section 115BAC, Chapter VI-A, Section 87A rebate).
  - Finance (No. 2) Act, 2024.
  - SEBI Regulations (Liquid Mutual Fund categorization, 91-day maturity, instant redemption).
  - RBI / DICGC Act, 1961 (₹5,00,000 bank deposit insurance limits).
- Hybrid semantic vector search + keyword boosting with relevance thresholding.
- Injected into assistant answers as transparent citation badges.

---

## 8. Feedback Learning & Recommendation Ranking

FinPilot AI implements a **safe, transparent feedback-learning foundation**:

### 8.1 Tracked Events (`agent_feedback`)
- `rating_feedback`: User ratings (+1 helpful, -1 unhelpful) with optional correction text.
- `recommendation_accepted`: User acts on a proactive insight or prompt.
- `recommendation_rejected`: User dismisses an insight.
- `action_confirmed`: User approves a proposed write action.
- `action_cancelled`: User declines a proposed write action.

### 8.2 Adaptive Recommendation Ranking
- The assistant monitors category engagement per user.
- If a user frequently dismisses recurring payment alerts, that category's ranking weight is automatically reduced.
- If a user frequently engages with budget optimization or debt payoff insights, those categories are elevated.
- **Safety Boundary**: Feedback learning affects *recommendation priority* and *response quality scoring*. It **never** grants autonomous write permissions or bypasses user confirmation.

---

## 9. Verification & Test Evidence

### Backend Pytest Suite
```bash
python -m pytest tests/
================== 134 passed, 1 warning in 60.89s (0:01:00) ==================
```
- Clarification workflow regression suite (`tests/test_clarification_workflow.py` - 10 tests):
  - Ambiguous credit card loan clarification generation (₹10,000 extraction).
  - Clarification resolution via option 1 (`"1. update it"`, `"1"`, `"Option 1"`, `"Yes, update it."`).
  - Action proposal staging for Credit Card Outstanding Balance without questionnaires.
  - Direct database persistence verification upon `"Confirm."`.
  - Zero database record creation upon `"Cancel."`.
  - Idempotency defense preventing duplicate records on re-confirmation.
  - Strict cross-conversation and cross-user isolation.
  - Rejection and prompt refresh on expired clarifications.
  - Full HTTP API endpoint integration flow.
- Autonomous agent test suite (`tests/test_autonomous_agent.py` - 14 tests):
  - Intent parser tests (read, unsupported, ambiguous clarification, write commands).
  - Action execution lifecycle (staging, confirmation, persistence, idempotency, cancellation, expiration).
  - Cross-user isolation (User 2 cannot execute User 1's action).
  - Multi-layer conversation memory and preference storage.
  - Feedback recording and recommendation ranking adaptation.
  - End-to-end API endpoints for actions and feedback.
- All 110 prior regression tests across bank connectivity, FIRE forecaster, intelligence engine, recurring management, and tax engine.

### Frontend Production Build
```bash
npm run build
> tsc && vite build
✓ 2407 modules transformed.
dist/index.html                   1.42 kB │ gzip:   0.77 kB
dist/assets/index-DtiuesQA.css   49.70 kB │ gzip:   8.89 kB
dist/assets/index-bCZvfyJd.js   989.45 kB │ gzip: 251.69 kB
✓ built in 6.18s
```

---

## 10. Manual Verification Instructions

1. Start both development servers:
   ```bash
   # Backend
   cd d:\finpilot\backend
   .\.venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000

   # Frontend
   cd d:\finpilot\frontend
   npm run dev
   ```
2. Open `http://localhost:5173` and log in.
3. Open the floating **AI CFO** assistant at the bottom-right corner.
4. Try natural-language commands:
   - Type: `"Record ₹3,500 spent on groceries"` $\to$ Observe the **Action Proposal Card** with details, disclaimer, and Confirm/Cancel buttons. Click **Confirm & Execute** $\to$ Verified persistence badge appears.
   - Type: `"Add ₹1,000 loan to debt"` $\to$ Observe the focused clarification question with 3 options. Click option 1 $\to$ Proposal card generated for debt creation.
   - Type: `"Wire transfer ₹50,000 to my friend"` $\to$ Observe the security boundary explanation.
5. Click the 👍 or 👎 feedback icons on any response to test feedback recording.
