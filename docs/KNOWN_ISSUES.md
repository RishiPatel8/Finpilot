# FinPilot AI — Known Issues & Limitations

## Known Limitations

1. **Host Docker Daemon Status**:
   - The host system has Docker CLI 29.7.2 installed, but the Docker Desktop daemon service is currently stopped or not responding to named pipe `//./pipe/dockerDesktopLinuxEngine`.
   - *Mitigation*: Both `docker-compose.yml` and native local development configurations (Python 3.12 + SQLite + Vite dev server) are provided so the application runs and tests reliably in both containerized and direct host environments.

2. **Tax Scope (Initial Version)**:
   - Covers Indian resident individuals (Salaried, Freelancers, Small Business / Presumptive 44AD/44ADA) under Assessment Year 2025-26 (Financial Year 2024-25) and AY 2024-25.
   - Non-resident taxation (NRI Section 115) and capital gains with indexation pre-2001 are flagged for professional chartered accountant review.

3. **Financial Disclaimer**:
   - FinPilot AI provides educational analysis and scenario planning. It does not provide SEBI-registered personalized investment advice or guarantee market returns.
