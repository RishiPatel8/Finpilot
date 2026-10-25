# FinPilot AI — Telegram Bot Integration & Global AI CFO Guide

This document describes the architecture, security guarantees, setup workflow, and operational procedures for FinPilot AI's official Telegram Bot integration.

---

## 1. Architectural Overview

The FinPilot Telegram Bot connects directly to the existing **Global AI CFO** engine. It does **not** create a separate bot assistant or replicate business logic. All financial queries, intent parsing, deterministic engines, pending-action staging, and confirmed database executions pass through the exact same backend services used by the FinPilot web dashboard.

```
                          ┌──────────────────────────────────────┐
                          │         Telegram User (App)          │
                          └──────────────────┬───────────────────┘
                                             │
                       HTTPS Webhook / Long Polling (/getUpdates)
                                             │
                                             ▼
                          ┌──────────────────────────────────────┐
                          │    FinPilot Telegram Module          │
                          │   (Deduplication & Authentication)   │
                          └──────────────────┬───────────────────┘
                                             │
                                             ▼
                          ┌──────────────────────────────────────┐
                          │     Shared Global AI CFO Engine      │
                          │        (app.ai.agent.FinancialAgent) │
                          └──────┬────────────────────────┬──────┘
                                 │                        │
                    Read Queries │                        │ Write Proposals
                                 ▼                        ▼
                   ┌────────────────────────┐  ┌────────────────────────┐
                   │ Deterministic Engines  │  │ ActionPlanner /        │
                   │ (Budget, Tax, Debts,   │  │ PendingAction System   │
                   │  Goals, Scenarios)     │  │ (Confirm/Cancel Stage) │
                   └─────────────┬──────────┘  └──────────┬─────────────┘
                                 │                        │
                                 │      Inline Confirm    │
                                 │      Callback Query    │
                                 │                        ▼
                                 │             ┌────────────────────────┐
                                 │             │     ActionExecutor     │
                                 │             │ (Verified Persistence) │
                                 │             └──────────┬─────────────┘
                                 │                        │
                                 ▼                        ▼
                          ┌──────────────────────────────────────┐
                          │       FinPilot SQLite Database       │
                          └──────────────────────────────────────┘
```

---

## 2. BotFather Setup Instructions

To provision your official Telegram Bot:

1. **Open Telegram** and search for `@BotFather`.
2. Start the chat and send `/newbot`.
3. Provide a friendly name (e.g. `FinPilot AI CFO`).
4. Provide a unique username ending with `bot` (e.g. `finpilot_cfo_bot`).
5. **Copy the HTTP API Token** provided by BotFather (looks like `7123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`).
6. Configure default bot command suggestions by sending `/setcommands` to `@BotFather`:
   ```
   status - View account link and notification status
   link - Connect with a single-use code (/link CODE)
   unlink - Disconnect this chat from FinPilot
   help - View instructions and example queries
   ```
7. Disable group chats (recommended for maximum privacy) via `/setjoingroups` → **Disable**.

---

## 3. Environment Variables Configuration

Add the following configuration to `backend/.env` (or project root `.env`):

```ini
# Telegram Bot Integration
TELEGRAM_BOT_TOKEN=7123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_BOT_USERNAME=finpilot_cfo_bot
TELEGRAM_WEBHOOK_SECRET=your_32_char_cryptographic_secret_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook
TELEGRAM_POLLING_MODE=False
```

> **Security Rules:**
> - Never expose `TELEGRAM_BOT_TOKEN` or `TELEGRAM_WEBHOOK_SECRET` to the frontend.
> - Never commit `.env` containing live tokens to git.
> - FinPilot client automatically masks tokens and suppresses credentials from server logs.

---

## 4. Local Development vs. Production

Telegram Bot API updates can be delivered via **Long Polling** (ideal for local dev) or **HTTPS Webhook** (recommended for production). Telegram forbids running both concurrently on the same bot token.

### Mode A: Local Development via Long Polling
For local offline development without exposing a public HTTPS URL:

```powershell
cd D:\finpilot\backend
& .\.venv\Scripts\python.exe -m app.telegram.polling
```

**Features of FinPilot's Poller:**
- Automatically checks for active webhooks on startup via `getWebhookInfo`.
- Clears conflicting webhooks via `deleteWebhook` before polling.
- Updates offset dynamically with deduplication.
- Handles graceful shutdown (`Ctrl+C`).

### Mode B: Production Webhook Deployment
For production servers with an HTTPS domain (or tunnels like ngrok/Cloudflare during staging):

1. Set your public URL and secret in `.env`:
   ```ini
   TELEGRAM_WEBHOOK_URL=https://api.yourdomain.com/api/v1/telegram/webhook
   TELEGRAM_WEBHOOK_SECRET=a_secure_random_hex_string_32_chars
   ```
2. Register the webhook with Telegram:
   ```bash
   curl -F "url=https://api.yourdomain.com/api/v1/telegram/webhook" \
        -F "secret_token=a_secure_random_hex_string_32_chars" \
        https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
   ```
3. Webhook requests sent by Telegram will include the header:
   ```
   X-Telegram-Bot-Api-Secret-Token: a_secure_random_hex_string_32_chars
   ```
   FinPilot's `/telegram/webhook` endpoint validates this header before processing any update.

---

## 5. Cryptographically Secure Account Linking Workflow

FinPilot guarantees that accounts are **never** linked solely by username or phone number.

1. **User requests a link code:** In FinPilot Web → **Settings** → **Telegram Global AI CFO**, the user clicks **"Generate Single-Use Link Code"**.
2. **Backend issues token:** A cryptographically secure 8-character token (e.g. `FP-A1B2-C3D4`) is generated with a strict 15-minute expiration timestamp. Any previously generated, unused codes for that user are immediately invalidated.
3. **User links via Telegram:**
   - **One-click Deep Link:** The user clicks **"Open in Telegram"**, which opens `https://t.me/<bot_username>?start=FP-A1B2-C3D4`.
   - **Manual Command:** Or the user opens the bot and types:
     ```
     /link FP-A1B2-C3D4
     ```
4. **Atomic Verification:**
   - The backend checks if the code exists, is unused, and has not expired.
   - It marks `is_used = True` atomically within a single transaction.
   - It records the user's `telegram_user_id` and `telegram_chat_id` in `telegram_account_links`.
5. **Private Chat Enforcement:**
   - If a linking attempt or financial command occurs in a group chat, the bot immediately refuses and instructs the user to open a private 1-on-1 chat.
6. **Unlinking:**
   - The user can disconnect anytime from Web Settings or by typing `/unlink` in Telegram.

---

## 6. Real AI CFO Capabilities in Telegram

Once connected, every interaction is powered by the authenticated user's genuine financial data.

### Supported Operations:
- **Financial Summaries & Net Worth:**
  - *"Give me a complete financial summary"*
  - *"How much did I spend this month?"*
  - *"What is my monthly savings rate?"*
- **Debts & Liabilities:**
  - *"What are my debts and total monthly EMI?"*
  - *"Who do I owe money to?"*
  - *"Add loan from HDFC Bank principal 500000 interest 9.5 emi 12500"* (triggers confirmation)
- **Budgets:**
  - *"What is my budget status this month?"*
  - *"Set monthly budget for Groceries to 12000"* (triggers confirmation)
- **Recurring Bills & Subscriptions:**
  - *"Show my upcoming bills"*
  - *"Add monthly subscription Netflix 649"* (triggers confirmation)
- **Financial Goals:**
  - *"Show my goal progress"*
  - *"Add goal Emergency Reserve target 300000 by 2027"* (triggers confirmation)
- **Indian Tax Calculations & Projections:**
  - *"Calculate tax for 1500000 annual income"*
  - *"Simulate buying an electric car for 900000"*

---

## 7. Action Confirmation Workflow & Safety Protocol

For write operations, FinPilot never commits records directly from raw text.

1. **Action Proposal:** The agent parses the parameters and returns a structured proposal with an inline preview.
2. **Inline Buttons:**
   - `[✅ Confirm & Execute]` (`callback_data="confirm:<action_id>"`)
   - `[❌ Cancel]` (`callback_data="cancel:<action_id>"`)
3. **Execution Safety Checks:**
   - Verifies the Telegram user owns the pending action.
   - Verifies the action is in `awaiting_confirmation` status and has not expired (15-min TTL).
   - Transitions state to `executing`, calls `ActionExecutor`, and commits to the database.
   - Removes the inline buttons from the Telegram message (`reply_markup=None`) so the user cannot double-click.

---

## 8. Proactive Opt-In Notifications

FinPilot supports non-intrusive, deduplicated alerts for:
1. **Upcoming Bills:** Alert 3 days before any active recurring payment is due.
2. **Budget Threshold Warnings:** Sent when monthly expenses cross 85% and 100% of the user's budget.
3. **Goal Accomplishments:** Sent when a financial goal reaches 100% of target.

**Deduplication Guarantee:** Every alert is logged with a composite key `(user_id, dedup_key)` in `telegram_notification_logs` to prevent repeated or duplicate alerts.

---

## 9. Verification & Testing

To run the Telegram test suite:

```powershell
cd D:\finpilot\backend
& .\.venv\Scripts\python.exe -m pytest tests/test_telegram_integration.py -v
```

All 9 test scenarios pass with complete coverage of link code generation, expiration, atomic consumption, non-private chat rejection, update deduplication, CFO action proposals, callback query executions, user isolation, and notification deduplication.
