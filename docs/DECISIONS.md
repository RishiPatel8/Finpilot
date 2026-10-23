# FinPilot AI — Architecture & Design Decisions (ADR)

## ADR-001: Decimal Arithmetic for Monetary Calculations
- **Context**: Floating point arithmetic introduces inaccuracies in financial and tax calculations.
- **Decision**: All financial figures (tax, compound interest, balances) must use Python's `decimal.Decimal` or integer paisa representations. The database will store `NUMERIC(14, 2)`.
- **Consequences**: Exact rounding adhering to Indian Income Tax Section 288B (rounding off taxable income and tax to the nearest multiple of ten rupees).

## ADR-002: Provider-Agnostic LLM Adapter & Deterministic Segregation
- **Context**: The AI assistant needs to assist users without being tied to a single proprietary vendor or requiring expensive API keys for core testing.
- **Decision**: Define `BaseAIProvider` protocol. Implement a comprehensive offline `MockAIProvider` that handles common financial queries and tool calling, while allowing seamless plug-in of Gemini (`google-genai`), Ollama, or OpenAI.
- **Consequences**: Core product, continuous integration, and local evaluation work out of the box with zero external API fees.

## ADR-003: Hybrid Storage Fallback (PostgreSQL & SQLite)
- **Context**: Docker may not always be running in all local development environments (e.g., Docker Desktop daemon stopped on Windows).
- **Decision**: Support both PostgreSQL (production/docker-compose) and SQLite (zero-config local dev/test fallback) through SQLAlchemy 2.0 ORM.
- **Consequences**: Developers and users can run and test FinPilot AI immediately even if Docker Desktop is offline.

## ADR-004: Strict User Isolation in Data Access Layer
- **Context**: Financial data is sensitive and private.
- **Decision**: All repositories and database queries filter strictly by `user_id` authenticated via JWT token claims. The API never accepts `user_id` as an untrusted route or payload parameter for private resources.

## ADR-005: Firebase Identity Mapping & Explicit Account Linking Protection
- **Context**: Introducing Firebase Google Sign-In alongside existing email/password authentication creates risk of account takeover if accounts with identical emails are silently merged.
- **Decision**: The backend verifies Firebase ID tokens server-side via official Firebase Admin SDK. When a Google identity matches an existing local email/password account, the server returns HTTP 409 Conflict. The accounts are linked only after the user explicitly verifies their existing password (`/api/v1/auth/link-firebase`).
- **Consequences**: Prevents malicious third-party OAuth takeovers while preserving legacy accounts and historical financial records.

## ADR-006: Deterministic Multi-Scenario Simulation Engine
- **Context**: Users evaluating major purchases (such as cars, homes, or education) need realistic alternatives, emergency runway protection, and debt boundaries rather than generic chatbot answers.
- **Decision**: Centralize all decision simulation logic in `app.finance.scenarios.engine`. Propose 3 deterministic options:
  1. Balanced Down Payment + Auto Loan (retaining 3-month safety runway and capping EMI <= 15% net income).
  2. All-Cash Extended Horizon (100% savings, zero loan interest).
  3. Discretionary Lifestyle Compression (20% non-essential spend cut).
- **Consequences**: Calculations are 100% reproducible, verifiable by tests, and directly usable by both the frontend UI and the AI assistant.
