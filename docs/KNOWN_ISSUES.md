# FinPilot AI — Known Issues, Prerequisites & Limitations

## External Configuration Prerequisites

1. **Firebase Authentication Console Setup**:
   - For production deployment or live Google OAuth:
     - Navigate to [Firebase Console](https://console.firebase.google.com/) and create/select a project.
     - In **Authentication > Sign-in method**, enable **Google** and **Email/Password**.
     - In **Authentication > Settings > Authorized domains**, ensure `localhost`, `127.0.0.1`, and your production domain are added.
     - In **Project Settings > General > Web apps**, copy `apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, and `appId` into `frontend/.env`.
     - In **Project Settings > Service accounts**, generate a new private key and place it at `backend/firebase-service-account.json` or set `FIREBASE_CREDENTIALS_PATH`.
   - *Offline / Zero-Config Dev Mode*: Both frontend and backend feature a built-in mock fallback for offline automated testing and local preview without external credentials.

2. **Host Docker Daemon Status**:
   - The host system has Docker CLI installed, but the Docker Desktop daemon service is currently stopped on Windows.
   - *Mitigation*: Both `docker-compose.yml` and native local development configurations (Python 3.14 + SQLite + Vite dev server) are provided so the application runs and tests reliably in both containerized and direct host environments.

3. **External LLM Provider Credentials**:
   - Optional: set `GEMINI_API_KEY` in `backend/.env` to use Google Gemini 2.5 Flash.
   - By default, `FinPilot AI` utilizes `MockAIProvider` with full RAG knowledge search and deterministic financial tool execution, ensuring zero-cost operation and zero test failures.

4. **Tax Scope & Financial Advisory Disclaimer**:
   - Covers Indian resident individuals (Salaried, Freelancers, Small Business / Presumptive 44AD/44ADA) under Assessment Year 2025-26 (Budget 2024 revisions) and AY 2024-25.
   - Non-resident taxation (NRI Section 115) and complex capital gains with pre-2001 indexation require professional Chartered Accountant review.
   - FinPilot AI provides deterministic educational scenario modeling and does not represent personalized SEBI-registered investment advice or guarantee future investment returns.
