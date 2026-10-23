# FinPilot AI v2.1 Upgrade Plan: Bank Connectivity, Cloud LLM & RAG

## 1. Baseline Audit & Environment State

- **Current Git Commit**: `2dc2cc8` on branch `master` (working tree clean).
- **Backend Test Suite**: 47/47 tests passed (100%) in 15.62s (`pytest`).
- **Frontend Build**: Vite v5.4.21 + TypeScript compiled cleanly in 17.71s with zero errors (`dist/assets` output valid).
- **Database Status**:
  - Primary development engine: SQLite (`finpilot.db`).
  - Production engine: PostgreSQL supported via SQLAlchemy 2.x and Alembic migration `163b72f67602_initial_schema.py`.
- **Existing LLM & AI Status**:
  - `adapter.py` contains `MockAIProvider`, `GeminiAIProvider`, and `OllamaAIProvider`.
  - Ollama is present but must be removed in v2.1 per cloud-only non-negotiable requirements.
  - `google-genai` (v2.33.0) is installed.
- **Existing RAG Status**:
  - `backend/app/rag/knowledge.py` contains in-memory statutory documents (Income Tax Act 1961, Finance Act 2024, SEBI circulars, DICGC norms) and a token-overlap keyword search engine.
  - Needs upgrade to a formal, extensible RAG pipeline with vector embeddings, semantic search, metadata filtering (jurisdiction, effective date), citation linking, and document ingestion without exposing private user data.
- **Existing Bank Integration Status**:
  - No bank account connectivity or Account Aggregator models currently exist in the database or UI.
  - Transactions are currently created manually or via CSV statement uploads.
  - Needs an Indian Account Aggregator (AA) adapter architecture (Setu / Finvu standard), sandbox flow, consent management, idempotent sync, and balance freshness indicators.

---

## 2. Identified Gaps & Risk Analysis

| Subsystem | Current State (v2.0) | Target State (v2.1) | Risk & Mitigation |
| :--- | :--- | :--- | :--- |
| **LLM Provider** | Gemini + Ollama local model | Cloud-only Gemini (default: `gemini-2.5-flash`), zero Ollama dependencies | **Risk**: Hard dependency on live API key causing test breakages. **Mitigation**: Preserve deterministic `MockAIProvider` for test/offline mode; explicit provider status and timeouts. |
| **Bank Connectivity** | CSV imports and manual entries only | Account Aggregator (AA) adapter with Setu/Finvu compatibility, consent tracking, sandbox connector | **Risk**: Fake bank logins or credential capture violates security principles. **Mitigation**: Strictly consent-based redirect/handle flow; no bank credentials ever stored; clear sandbox labeling. |
| **Transaction Sync & Balances** | Single transaction table without provider sync metadata | Linked bank accounts, consent sessions, sync logs, transaction deduplication cursors | **Risk**: Duplicate transaction imports on sync retry. **Mitigation**: Unique compound index on `(bank_account_id, provider_txn_ref)` with idempotent upserts. |
| **RAG Knowledge System** | 5 static dict documents with token overlap | Modular RAG pipeline: document ingestion, metadata filtering, chunking, semantic vector search / pgvector fallback, citations | **Risk**: Private user financial transactions leaking into shared knowledge vector index. **Mitigation**: Strict separation—RAG indexes only public statutory docs; user context injected at query time via authenticated scope. |
| **AI Advisor Integration** | Context strings in prompt | Multi-source AI CFO: authenticated financial context + deterministic tools + retrieved RAG citations + Cloud Gemini | **Risk**: Hallucinated financial numbers or fake account actions. **Mitigation**: Financial engines remain strictly deterministic; LLM acts as explainer and synthesizer. |

---

## 3. Implementation Phases

### Phase 1: Cloud-Only LLM Architecture
1. Purge `OllamaAIProvider`, Ollama settings, Ollama tests, and documentation from the application path.
2. Upgrade `GeminiAIProvider` using `google-genai` and robust fallback handling.
3. Validate API key handling, explicit provider status (`ready`, `missing_key`, `fallback_mock`, `error`), and timeout controls (15s).
4. Update `Settings` in `config.py` and `.env.example`.

### Phase 2: Bank Integration Architecture (Indian Account Aggregator)
1. Document Indian Account Aggregator ecosystem (Setu AA, Finvu AA, RBI NBFC-AA master directions).
2. Create provider-independent backend interface `BaseBankAdapter`:
   - Account discovery, consent creation & status tracking, callback handling, balance fetching, transaction sync, consent revocation.
3. Implement `SandboxAccountAggregatorAdapter` with realistic Indian banks (HDFC, ICICI, SBI, Axis) for sandbox/development.
4. Database Models:
   - `BankAccount`: Linked account with masked account number, IFSC, account type, balance, last sync timestamp.
   - `BankConsent`: Consent handle, consent ID, status (`PENDING`, `ACTIVE`, `REVOKED`, `EXPIRED`), valid_from, valid_to, fetch frequency.
   - `BankSyncLog`: Sync status, records fetched, errors.
5. Extend `Transaction` model with `bank_account_id` and `provider_txn_ref` for idempotent deduplication.
6. Create Alembic migration script for bank tables and test migration upgrade/downgrade.
7. Frontend: Create `BankAccountsView.tsx` with consent initiation modal, connection status badge, manual sync button, and revoke button.

### Phase 3: RAG Knowledge System
1. Knowledge Corpus: Authoritative Indian regulatory guidelines (Income Tax Act 1961, Finance Act 2024, RBI DICGC guidelines, SEBI Liquid Mutual Fund circulars, RBI Master Directions on Account Aggregators).
2. Vector Store Abstraction:
   - Ingestion pipeline with text chunking, document hashing, version tracking, and effective dates.
   - Semantic retrieval service supporting Cloud Embeddings (`text-embedding-004`) with cosine similarity and deterministic fallback when offline.
   - Source citation enforcement: each retrieval item includes `title`, `source`, `section_ref`, `url`, and `confidence_score`.
3. Strict data isolation: Knowledge store is completely separate from user transaction data.

### Phase 4: Integrated AI Financial Advisor (AI CFO)
1. Extend AI CFO tools to include linked bank account balances and recent synchronized transactions.
2. Pass grounded RAG evidence and deterministic calculation outputs to Gemini.
3. Ensure responses clearly distinguish:
   - Verified account balances from bank sync.
   - Deterministic calculation results.
   - Statutory rules cited from RAG.
   - Financial planning assumptions.

### Phase 5: Financial Security, Privacy & Compliance
1. User-level authorization on all bank and sync endpoints (`current_user.id`).
2. Data retention and consent revocation workflows: revoking consent disables synchronization and marks consent as `REVOKED`.
3. Account deletion cascade: deleting an account cascades to all linked bank records, consent handles, and transactions.
4. Export data: Include linked bank metadata (masked) and synchronized transactions in DPDP export.

### Phase 6: Automated Testing & Verification
1. Unit and contract tests for `SandboxAccountAggregatorAdapter`.
2. Tests for consent lifecycle: create, poll, approve, sync, revoke, expire.
3. Idempotent transaction sync and duplicate avoidance tests.
4. Cloud LLM adapter tests: Gemini initialization, missing key, provider error, timeout fallback.
5. RAG retrieval tests: semantic search, effective date filtering, source citation format, prompt injection defense.
6. Alembic migration upgrade and rollback tests.
7. Frontend production build and browser verification across new routes.

### Phase 7: Documentation & Release
1. Update `README.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`, `SECURITY.md`, and `.env.example`.
2. Provide step-by-step Bank Integration Guide and RAG Setup Guide.
