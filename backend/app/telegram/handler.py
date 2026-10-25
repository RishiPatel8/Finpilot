import re
import html
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.agent import PendingAction
from app.ai.agent import FinancialAgent
from app.ai.action_service import ActionExecutor
from app.ai.clarification_service import ClarificationService
from app.telegram.client import telegram_client, TelegramClient
from app.telegram.service import telegram_service
from app.core.config import settings

logger = logging.getLogger("finpilot.telegram.handler")


def format_for_telegram(text: str) -> str:
    """
    Format standard markdown response into Telegram HTML safe string.
    Escapes raw HTML entities and translates bold/italic/code.
    """
    if not text:
        return ""

    # First escape HTML tags
    clean = html.escape(text)

    # Convert headers (### Header) to <b>Header</b>
    clean = re.sub(r"^#{1,6}\s*(.+)$", r"<b>\1</b>", clean, flags=re.MULTILINE)

    # Convert bold **text** to <b>text</b>
    clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", clean)

    # Convert italic *text* or _text_ to <i>text</i>
    clean = re.sub(r"\*(.+?)\*", r"<i>\1</i>", clean)
    clean = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", clean)

    # Convert inline code `code` to <code>code</code>
    clean = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", clean)

    # Convert bullet points
    clean = re.sub(r"^[ \t]*[-*][ \t]+", "• ", clean, flags=re.MULTILINE)

    return clean.strip()


class TelegramUpdateHandler:
    """
    Processes incoming Telegram bot updates:
    - Route verification & deduplication
    - Private chat restriction
    - Account linking commands (/start, /link, /unlink)
    - Full Global AI CFO conversation forwarding
    - Inline action confirmation & cancellation with authorization checks
    - Clarification selection
    """

    def __init__(self, client: Optional[TelegramClient] = None):
        self.client = client or telegram_client

    async def handle_update(self, update_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        update_id = update_data.get("update_id")
        if not update_id:
            return {"status": "ignored", "reason": "missing_update_id"}

        # 1. Update Deduplication
        if telegram_service.is_update_processed(db, update_id):
            logger.info("Telegram update %s already processed, ignoring duplicate.", update_id)
            return {"status": "duplicate", "update_id": update_id}

        telegram_service.mark_update_processed(db, update_id)

        # 2. Route Message or Callback Query
        if "message" in update_data:
            return await self.handle_message(update_data["message"], db)
        elif "callback_query" in update_data:
            return await self.handle_callback_query(update_data["callback_query"], db)

        return {"status": "unsupported_update_type"}

    async def handle_message(self, message: Dict[str, Any], db: Session) -> Dict[str, Any]:
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        chat_type = chat.get("type", "private")
        from_user = message.get("from", {})
        tg_user_id = from_user.get("id")
        text = (message.get("text") or "").strip()

        if not chat_id or not tg_user_id:
            return {"status": "invalid_message"}

        # Enforce private chat security
        if chat_type != "private":
            await self.client.send_message(
                chat_id=chat_id,
                text="🔒 <b>FinPilot Security:</b> For your privacy and financial security, FinPilot AI only interacts in private 1-on-1 chats. Please open a direct message with me.",
            )
            return {"status": "rejected_non_private"}

        # 3. Handle Bot Commands
        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd in ["/start", "/start@finpilot_bot"]:
                return await self._handle_start(chat_id, tg_user_id, arg, from_user, db)
            elif cmd == "/link":
                return await self._handle_link(chat_id, tg_user_id, arg, from_user, db)
            elif cmd == "/unlink":
                return await self._handle_unlink(chat_id, tg_user_id, db)
            elif cmd in ["/help", "/commands"]:
                return await self._handle_help(chat_id)
            elif cmd == "/status":
                return await self._handle_status(chat_id, tg_user_id, db)

        # 4. Handle Natural Language Financial Message
        user = telegram_service.get_user_by_telegram_id(db, tg_user_id)
        if not user:
            help_text = (
                "👋 <b>Welcome to FinPilot AI — Global AI CFO</b>\n\n"
                "Your Telegram account is not yet connected to a FinPilot profile.\n\n"
                "<b>To connect your account:</b>\n"
                "1. Sign in to your dashboard on <a href='http://localhost:5173'>FinPilot Web</a>\n"
                "2. Go to <b>Settings</b> → <b>Telegram Bot</b>\n"
                "3. Click <b>'Generate Link Code'</b>\n"
                "4. Send <code>/link &lt;CODE&gt;</code> here in this chat.\n\n"
                "<i>Your link code is single-use and valid for 15 minutes.</i>"
            )
            await self.client.send_message(chat_id=chat_id, text=help_text)
            return {"status": "unauthenticated"}

        # Forward authorized message through real FinancialAgent
        logger.info("Forwarding Telegram message from user %s to FinancialAgent", user.id)
        agent_result = FinancialAgent.process_message(
            message=text,
            user=user,
            db=db,
            conversation_id=f"tg_{chat_id}",
            channel="telegram",
        )

        # 5. Format & Dispatch Response
        return await self._dispatch_agent_response(chat_id, agent_result)

    async def _handle_start(
        self, chat_id: int, tg_user_id: int, payload: str, from_user: Dict[str, Any], db: Session
    ) -> Dict[str, Any]:
        """
        Handle /start or deep linking (/start FP-XXXX-XXXX).
        """
        if payload:
            # User came via deep-link button with code
            success, msg, user = telegram_service.verify_and_link(
                db=db,
                telegram_user_id=str(tg_user_id),
                telegram_chat_id=str(chat_id),
                code_str=payload,
                telegram_username=from_user.get("username"),
                telegram_first_name=from_user.get("first_name"),
            )
            if success and user:
                welcome = (
                    f"🎉 <b>FinPilot Account Linked!</b>\n\n"
                    f"Welcome aboard, <b>{html.escape(user.full_name)}</b> ({html.escape(user.email)}).\n\n"
                    f"I am your <b>Global AI CFO</b>. You can ask me anything about your finances or request actions directly from Telegram:\n\n"
                    f"• <i>\"Give me a complete financial summary\"</i>\n"
                    f"• <i>\"What are my debts and total EMI?\"</i>\n"
                    f"• <i>\"Add an expense of 450 for coffee\"</i>\n"
                    f"• <i>\"Add a monthly subscription Netflix 649\"</i>\n"
                    f"• <i>\"Simulate buying a car for 800000\"</i>\n\n"
                    f"Type /help to see all capabilities."
                )
                await self.client.send_message(chat_id=chat_id, text=welcome)
                return {"status": "linked", "user_id": user.id}
            else:
                err_text = f"❌ <b>Link Failed:</b> {html.escape(msg)}"
                await self.client.send_message(chat_id=chat_id, text=err_text)
                return {"status": "link_error", "message": msg}

        # Regular /start without code
        user = telegram_service.get_user_by_telegram_id(db, tg_user_id)
        if user:
            msg = (
                f"👋 <b>Welcome back, {html.escape(user.full_name)}!</b>\n\n"
                f"Your FinPilot Global AI CFO is active and ready.\n"
                f"Ask me any question or request a financial action. Type /help for guidance."
            )
            await self.client.send_message(chat_id=chat_id, text=msg)
            return {"status": "active_user", "user_id": user.id}
        else:
            msg = (
                "👋 <b>Welcome to FinPilot AI — Global AI CFO</b>\n\n"
                "To link this Telegram account with your FinPilot financial records:\n"
                "1. Go to FinPilot Settings → Telegram Bot\n"
                "2. Generate a secure 15-minute Link Code\n"
                "3. Send <code>/link &lt;CODE&gt;</code> here.\n\n"
                "<i>Your credentials and financial data remain encrypted and private.</i>"
            )
            await self.client.send_message(chat_id=chat_id, text=msg)
            return {"status": "pending_link"}

    async def _handle_link(
        self, chat_id: int, tg_user_id: int, code_str: str, from_user: Dict[str, Any], db: Session
    ) -> Dict[str, Any]:
        if not code_str:
            await self.client.send_message(
                chat_id=chat_id,
                text="ℹ️ <b>Usage:</b> <code>/link &lt;CODE&gt;</code>\n\nExample: <code>/link FP-A1B2-C3D4</code>\nGenerate a code in FinPilot Web Settings.",
            )
            return {"status": "missing_code"}

        success, msg, user = telegram_service.verify_and_link(
            db=db,
            telegram_user_id=str(tg_user_id),
            telegram_chat_id=str(chat_id),
            code_str=code_str,
            telegram_username=from_user.get("username"),
            telegram_first_name=from_user.get("first_name"),
        )
        if success and user:
            welcome = (
                f"✅ <b>Successfully Linked!</b>\n\n"
                f"Connected to FinPilot account: <b>{html.escape(user.full_name)}</b> ({html.escape(user.email)}).\n"
                f"You can now manage your budgets, debts, goals, bills, and simulate decisions directly here."
            )
            await self.client.send_message(chat_id=chat_id, text=welcome)
            return {"status": "linked", "user_id": user.id}
        else:
            await self.client.send_message(
                chat_id=chat_id,
                text=f"❌ <b>Link Failed:</b> {html.escape(msg)}",
            )
            return {"status": "link_failed", "message": msg}

    async def _handle_unlink(self, chat_id: int, tg_user_id: int, db: Session) -> Dict[str, Any]:
        success = telegram_service.unlink_by_telegram_id(db, tg_user_id)
        if success:
            await self.client.send_message(
                chat_id=chat_id,
                text="🔌 <b>Account Unlinked:</b> This Telegram chat is no longer connected to your FinPilot account. No further alerts or commands will be processed.",
            )
            return {"status": "unlinked"}
        else:
            await self.client.send_message(
                chat_id=chat_id,
                text="ℹ️ No active FinPilot account was linked to this Telegram user.",
            )
            return {"status": "not_linked"}

    async def _handle_status(self, chat_id: int, tg_user_id: int, db: Session) -> Dict[str, Any]:
        user = telegram_service.get_user_by_telegram_id(db, tg_user_id)
        if not user:
            await self.client.send_message(
                chat_id=chat_id,
                text="❌ <b>Not Connected:</b> You do not have an active FinPilot account linked. Use /link to connect.",
            )
            return {"status": "disconnected"}

        link = telegram_service.get_link_by_user_id(db, user.id)
        notif_status = "Enabled" if link and link.notifications_enabled else "Disabled"
        text = (
            f"📊 <b>FinPilot Connection Status</b>\n\n"
            f"• <b>Status:</b> 🟢 Connected\n"
            f"• <b>FinPilot User:</b> {html.escape(user.full_name)}\n"
            f"• <b>Email:</b> {html.escape(user.email)}\n"
            f"• <b>Notifications:</b> {notif_status}\n"
            f"  - Bill Reminders: {'✅' if link and link.notify_bills else '❌'}\n"
            f"  - Budget Alerts: {'✅' if link and link.notify_budget else '❌'}\n"
            f"  - Goal Milestones: {'✅' if link and link.notify_goals else '❌'}\n\n"
            f"To manage notification settings, visit the web dashboard or use /unlink to disconnect."
        )
        await self.client.send_message(chat_id=chat_id, text=text)
        return {"status": "connected", "user_id": user.id}

    async def _handle_help(self, chat_id: int) -> Dict[str, Any]:
        help_text = (
            "🤖 <b>FinPilot Global AI CFO — Commands & Capabilities</b>\n\n"
            "<b>Bot Commands:</b>\n"
            "• /status — View account link and notification status\n"
            "• /unlink — Disconnect your Telegram account\n"
            "• /help — Show this help message\n\n"
            "<b>Natural Language Financial Operations:</b>\n"
            "• <b>Summaries:</b> <i>\"Give me a complete financial summary\"</i>, <i>\"How much did I spend this month?\"</i>\n"
            "• <b>Debts:</b> <i>\"Show all my debts and who I need to pay\"</i>, <i>\"Add loan from HDFC of 50000 EMI 4500\"</i>\n"
            "• <b>Budgets:</b> <i>\"Set monthly budget for Dining to 5000\"</i>, <i>\"Check my budget status\"</i>\n"
            "• <b>Recurring Bills:</b> <i>\"Add monthly subscription Netflix 649\"</i>, <i>\"Show upcoming bills\"</i>\n"
            "• <b>Goals:</b> <i>\"Add goal Emergency Fund target 300000 by 2027\"</i>\n"
            "• <b>Simulations:</b> <i>\"Can I afford a vacation of 120000 next month?\"</i>\n"
            "• <b>Taxes:</b> <i>\"Calculate tax for 1400000 income\"</i>\n\n"
            "<i>All write operations present an inline Confirm/Cancel button before modifying your records.</i>"
        )
        await self.client.send_message(chat_id=chat_id, text=help_text)
        return {"status": "help_sent"}

    async def _dispatch_agent_response(self, chat_id: int, agent_res: Dict[str, Any]) -> Dict[str, Any]:
        content = agent_res.get("content", "")
        pending_action = agent_res.get("pending_action")
        clarification = agent_res.get("clarification")

        # 1. Action Proposal with Inline Buttons
        if pending_action and pending_action.get("status") == "awaiting_confirmation":
            action_id = pending_action["id"]
            preview = pending_action.get("preview", {})
            title = preview.get("title", "Financial Action Proposal")
            summary = preview.get("summary", "")
            items = preview.get("items", [])
            disclaimer = preview.get("disclaimer", "Changes will be immediately persisted upon your confirmation.")

            items_text = "\n".join([f"• <b>{html.escape(it.get('label', ''))}</b>: {html.escape(str(it.get('value', '')))}" for it in items])

            msg_text = (
                f"⚡ <b>Action Proposal: {html.escape(title)}</b>\n\n"
                f"{html.escape(summary)}\n\n"
                f"<b>Parameters:</b>\n{items_text}\n\n"
                f"⚠️ <i>{html.escape(disclaimer)}</i>\n\n"
                f"<b>Please confirm or cancel this operation:</b>"
            )

            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Confirm & Execute", "callback_data": f"confirm:{action_id}"},
                        {"text": "❌ Cancel", "callback_data": f"cancel:{action_id}"},
                    ]
                ]
            }

            await self.client.send_message(
                chat_id=chat_id,
                text=msg_text,
                reply_markup=reply_markup,
            )
            return {"status": "action_proposed", "action_id": action_id}

        # 2. Clarification with Option Buttons
        if clarification and clarification.get("options"):
            c_id = clarification["id"]
            q_text = clarification.get("question", "Please select an option:")
            options = clarification.get("options", [])

            keyboard_buttons = []
            for opt in options:
                opt_id = opt.get("id") or opt.get("label", "")
                label = opt.get("label") or opt_id
                keyboard_buttons.append([{"text": label, "callback_data": f"clarify:{c_id}:{opt_id}"}])

            keyboard_buttons.append([{"text": "❌ Cancel", "callback_data": f"clarify_cancel:{c_id}"}])

            reply_markup = {"inline_keyboard": keyboard_buttons}
            formatted_q = format_for_telegram(q_text)

            await self.client.send_message(
                chat_id=chat_id,
                text=formatted_q,
                reply_markup=reply_markup,
            )
            return {"status": "clarification_sent", "clarification_id": c_id}

        # 3. Standard Text Response
        formatted_text = format_for_telegram(content)
        # Avoid empty messages
        if not formatted_text:
            formatted_text = "I have processed your request."

        # Handle Telegram 4096 char limit safely
        if len(formatted_text) > 4000:
            formatted_text = formatted_text[:3990] + "\n\n<i>[Message truncated for Telegram length limit]</i>"

        await self.client.send_message(chat_id=chat_id, text=formatted_text)
        return {"status": "message_sent"}

    async def handle_callback_query(self, cb_query: Dict[str, Any], db: Session) -> Dict[str, Any]:
        cb_id = cb_query.get("id")
        from_user = cb_query.get("from", {})
        tg_user_id = from_user.get("id")
        data = cb_query.get("data") or ""
        msg = cb_query.get("message") or {}
        chat_id = msg.get("chat", {}).get("id")
        message_id = msg.get("message_id")

        if not cb_id or not tg_user_id:
            return {"status": "invalid_callback"}

        user = telegram_service.get_user_by_telegram_id(db, tg_user_id)
        if not user:
            await self.client.answer_callback_query(
                callback_query_id=cb_id,
                text="Unauthorized: Your Telegram account is not linked to FinPilot.",
                show_alert=True,
            )
            return {"status": "unauthorized"}

        # -------------------------------------------------------------
        # Action Confirmation: confirm:<action_id>
        # -------------------------------------------------------------
        if data.startswith("confirm:"):
            action_id = data.split(":", 1)[1]
            # Verify action belongs to authenticated user
            pending = db.query(PendingAction).filter(PendingAction.id == action_id).first()
            if not pending or pending.user_id != user.id:
                await self.client.answer_callback_query(
                    callback_query_id=cb_id,
                    text="Error: You are not authorized to confirm this action.",
                    show_alert=True,
                )
                return {"status": "forbidden"}

            # Execute action with ActionExecutor
            exec_res = ActionExecutor.confirm_and_execute(action_id=action_id, user=user, db=db)
            await self.client.answer_callback_query(
                callback_query_id=cb_id,
                text=exec_res.message[:100],
            )

            # Edit message to remove buttons and show confirmation
            status_icon = "✅" if exec_res.status == "succeeded" else "⚠️"

            record_block = ""
            if exec_res.status == "succeeded" and exec_res.result:
                lines = []
                for k, v in exec_res.result.items():
                    if k == "entity":
                        continue
                    label = k.replace("_", " ").title()
                    if "principal" in k or "amount" in k or "emi" in k:
                        try:
                            val_str = f"₹{float(v):,.2f}"
                        except (ValueError, TypeError):
                            val_str = str(v)
                    elif "interest_rate" in k:
                        period = exec_res.result.get("interest_period", "")
                        val_str = f"{v}% ({period})" if period else f"{v}%"
                    else:
                        val_str = str(v)
                    lines.append(f"• <b>{label}:</b> {html.escape(val_str)}")
                if lines:
                    record_block = "\n\n<b>Persisted Record Details:</b>\n" + "\n".join(lines)

            updated_text = (
                f"{status_icon} <b>Action Confirmed & Executed</b>\n\n"
                f"{html.escape(exec_res.message)}"
                f"{record_block}\n\n"
                f"<i>Status: {exec_res.status} | Verified at: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</i>"
            )

            if chat_id and message_id:
                await self.client.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=updated_text,
                    reply_markup=None,  # Clear buttons to prevent duplicate clicks
                )

            return {"status": "action_executed", "result": exec_res.status}

        # -------------------------------------------------------------
        # Action Cancellation: cancel:<action_id>
        # -------------------------------------------------------------
        elif data.startswith("cancel:"):
            action_id = data.split(":", 1)[1]
            pending = db.query(PendingAction).filter(PendingAction.id == action_id).first()
            if not pending or pending.user_id != user.id:
                await self.client.answer_callback_query(
                    callback_query_id=cb_id,
                    text="Error: You are not authorized to cancel this action.",
                    show_alert=True,
                )
                return {"status": "forbidden"}

            cancel_res = ActionExecutor.cancel_action(action_id=action_id, user=user, db=db)
            await self.client.answer_callback_query(
                callback_query_id=cb_id,
                text="Action safely cancelled.",
            )

            updated_text = (
                "❌ <b>Action Safely Cancelled</b>\n\n"
                "The proposed financial action has been cancelled. No changes were made to your records."
            )

            if chat_id and message_id:
                await self.client.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=updated_text,
                    reply_markup=None,
                )

            return {"status": "action_cancelled"}

        # -------------------------------------------------------------
        # Clarification Option Selection: clarify:<c_id>:<opt_id>
        # -------------------------------------------------------------
        elif data.startswith("clarify:"):
            parts = data.split(":", 2)
            if len(parts) >= 3:
                c_id, opt_id = parts[1], parts[2]
                await self.client.answer_callback_query(callback_query_id=cb_id, text="Processing selection...")

                agent_result = FinancialAgent.process_message(
                    message=opt_id,
                    user=user,
                    db=db,
                    conversation_id=f"tg_{chat_id}",
                    channel="telegram",
                    clarification_id=c_id,
                    option_id=opt_id,
                )

                if chat_id and message_id:
                    await self.client.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"<i>Selection recorded: {html.escape(opt_id)}</i>",
                        reply_markup=None,
                    )

                return await self._dispatch_agent_response(chat_id, agent_result)

        # -------------------------------------------------------------
        # Clarification Cancellation: clarify_cancel:<c_id>
        # -------------------------------------------------------------
        elif data.startswith("clarify_cancel:"):
            await self.client.answer_callback_query(callback_query_id=cb_id, text="Clarification cancelled.")
            if chat_id and message_id:
                await self.client.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="❌ Clarification cancelled. No changes made.",
                    reply_markup=None,
                )
            return {"status": "clarification_cancelled"}

        await self.client.answer_callback_query(callback_query_id=cb_id)
        return {"status": "unknown_callback"}


telegram_handler = TelegramUpdateHandler()
