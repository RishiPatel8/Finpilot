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
