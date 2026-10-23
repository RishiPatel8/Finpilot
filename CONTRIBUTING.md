# Contributing to FinPilot AI

Thank you for your interest in contributing to **FinPilot AI**! We welcome contributions from developers, fintech experts, designers, and financial domain specialists.

---

## Code of Conduct

Please read and abide by our [Code of Conduct](CODE_OF_CONDUCT.md) in all project interactions.

---

## Architectural Principles

Before contributing code, please ensure your changes adhere to our core project tenets:

1. **Deterministic Financial Calculations**: All Indian Income Tax (Section 115BAC), Goal SIP, 50-30-20 budgeting, and debt payoff arithmetic must be computed deterministically in verified Python engines, never hallucinated by LLMs.
2. **User Data Isolation**: Every endpoint and query must strictly enforce server-side user isolation (`WHERE user_id == current_user.id`).
3. **No Developer Portals / No MCP**: FinPilot AI is an open-source, user-facing personal finance website, not a developer API marketplace or MCP server.
4. **Light Fintech Design System**: Maintain the established palette (`#F6F8FC` canvas, `#FFFFFF` cards, `#6478E8` primary accent, soft pastel badges).

---

## Local Development Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running Tests

### Backend Unit & Integration Tests
```bash
python -m pytest backend/tests/ -v
```

### Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
```

---

## Pull Request Guidelines

1. Fork the repository and create your feature branch from `master` (`git checkout -b feature/amazing-feature`).
2. Write unit tests for any new finance engine logic or API endpoints.
3. Verify that `python -m pytest backend/tests/` passes with 100% success.
4. Verify that `npm run build` compiles with 0 TypeScript errors.
5. Commit your changes with clear semantic commit messages (e.g., `feat: ...`, `fix: ...`, `test: ...`, `docs: ...`).
6. Push to your branch and open a Pull Request.

---

## Financial Rule Updates

When updating statutory tax rules, deductions, or SEBI parameters:
- Cite the official statutory reference (e.g., Finance Act 2024, Income Tax Act 1961 Section 115BAC, SEBI Circulars).
- Add regression tests covering numerical boundary conditions and edge cases.
