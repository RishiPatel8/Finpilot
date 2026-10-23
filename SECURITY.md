# Security Policy

FinPilot AI takes the security and privacy of user financial data seriously.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Reporting a Vulnerability

If you discover a potential security vulnerability in FinPilot AI, please **DO NOT** create a public GitHub issue.

Instead, please send a responsible disclosure report via email to **security@finpilot.ai** (or contact the project maintainers privately on GitHub).

Please include:
1. Description of the vulnerability.
2. Steps to reproduce or proof-of-concept payload.
3. Potential impact on user data isolation or calculation integrity.
4. Suggested remediation if known.

We will acknowledge receipt within 48 hours and work with you to validate and deploy a patch before public disclosure.

## Security Architecture Principles

- **Zero Client-Side Calculation Trust**: All tax, goal, and debt projections are computed on the server.
- **Strict User Isolation**: Every database query is scoped by `user_id`.
- **Statutory Compliance**: Data portability and account deletion adhere to the Digital Personal Data Protection (DPDP) Act 2023.
- **No Mock Tokens in Production**: Mock authentication tokens are strictly rejected when `ENVIRONMENT=production`.
- **Security Headers**: All API responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, and `Content-Security-Policy`.
