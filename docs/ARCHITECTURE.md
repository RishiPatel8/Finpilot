# FinPilot AI — Architecture & Design

## 1. System Overview

FinPilot AI is an explainable personal finance platform tailored for Indian individuals and small-business owners.
The system separates **deterministic financial computations** (Tax, Budget, Investment projections) from **generative AI/LLM components** (Assistant, Explainability, RAG) to guarantee mathematical accuracy, regulatory compliance, and zero hallucination of monetary numbers.

```mermaid
flowchart TD
    User([User Browser]) <--> FE[Frontend: React + Vite + Tailwind + Recharts]
    FE <-->|REST API + JWT Auth| BE[Backend: FastAPI]
    
    subgraph Backend Services
        BE --> Auth[Auth & Security Engine: Bcrypt + JWT]
        BE --> FinTax[Tax Engine: Slabs, Rebates, FY 24-25 / AY 25-26]
        BE --> FinBudget[Budget & Cash Flow Engine: CSV Import, Categories]
        BE --> FinInvest[Investment & Goal Planner: Liquid MF vs Bonds vs FD]
        BE --> AIAdapter[AI Orchestration: Provider-Independent Adapter]
    end

    subgraph Data & Storage
        BE --> DB[(PostgreSQL / SQLite Storage)]
        AIAdapter --> RAG[(Knowledge Base / Vector Store)]
    end

    subgraph External LLM (Optional)
        AIAdapter -.->|Structured Tool Calling| LLM[Gemini / Ollama / OpenAI / Mock]
    end
```

## 2. Core Architectural Principles

1. **Deterministic Financial Safety**:
   - Arithmetic, tax calculations, loan amortization, and compounding are executed by tested Python algorithms with fixed precision (`Decimal` arithmetic).
   - The LLM never computes tax brackets or returns from scratch; it orchestrates deterministic tools and explains outputs clearly with citations.

2. **Decoupled AI Engine**:
   - Pluggable AI adapter (`BaseAIProvider`) supporting `MockProvider` (offline, zero-cost, instant testing), `GeminiProvider`, `OllamaProvider`, and `OpenAIProvider`.
   - Core product is 100% operational without external paid API keys.

3. **Strict Data Ownership & Security**:
   - All financial endpoints enforce user ownership (`user_id` derived strictly from JWT authentication claims, never from client body or path tampering).
   - Passwords hashed with bcrypt; secrets managed via environment variables.

4. **Multi-Environment Ready**:
   - Supports Docker Compose containerization (PostgreSQL + FastAPI + Vite).
   - Supports standalone local execution (Python venv + SQLite fallback) for environments where the Docker daemon is temporarily inactive.
