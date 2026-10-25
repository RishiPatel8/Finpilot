import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.telegram import TelegramAccountLink, TelegramNotificationLog
from app.models.financial import RecurringTransaction, Transaction, FinancialGoal, FinancialProfile
from app.telegram.client import telegram_client, TelegramClient

logger = logging.getLogger("finpilot.telegram.notifications")


class NotificationDispatcher:
    """
    Outbound notification engine for Telegram bot.
    Dispatches verified, deduplicated alerts for:
    - Upcoming bills (within 3 days)
    - Budget utilization thresholds (85% and 100%)
    - Goal progress milestones
    """

    def __init__(self, client: Optional[TelegramClient] = None):
        self.client = client or telegram_client

    async def dispatch_bill_reminders(self, db: Session, user_id: Optional[str] = None) -> int:
        today = date.today()
        upcoming_cutoff = today + timedelta(days=3)

        query = (
            db.query(TelegramAccountLink, RecurringTransaction)
            .join(RecurringTransaction, RecurringTransaction.user_id == TelegramAccountLink.user_id)
            .filter(
                TelegramAccountLink.is_active == True,
                TelegramAccountLink.notifications_enabled == True,
                TelegramAccountLink.notify_bills == True,
                RecurringTransaction.status.in_(["detected", "confirmed"]),
                RecurringTransaction.next_expected_date >= today,
                RecurringTransaction.next_expected_date <= upcoming_cutoff,
            )
        )
        if user_id:
            query = query.filter(TelegramAccountLink.user_id == user_id)

        records = query.all()
        sent_count = 0

        for link, bill in records:
            due_str = bill.next_expected_date.isoformat() if bill.next_expected_date else today.isoformat()
            dedup_key = f"bill_{bill.id}_{due_str}"

            # Check if already logged
            exists = (
                db.query(TelegramNotificationLog)
                .filter(
                    TelegramNotificationLog.user_id == link.user_id,
                    TelegramNotificationLog.dedup_key == dedup_key,
                )
                .first()
            )
            if exists:
                continue

            text = (
                f"⏰ <b>Upcoming Bill Reminder</b>\n\n"
                f"• <b>Bill / Service:</b> {bill.name}\n"
                f"• <b>Amount Due:</b> ₹{float(bill.amount):,.2f}\n"
                f"• <b>Due Date:</b> {bill.next_expected_date.strftime('%d %B %Y')}\n"
                f"• <b>Frequency:</b> {bill.frequency.title()}\n\n"
                f"<i>Recorded in your FinPilot recurring tracker.</i>"
            )

            try:
                log_entry = TelegramNotificationLog(
                    user_id=link.user_id,
                    notification_type="bill_reminder",
                    dedup_key=dedup_key,
                    details=f"{bill.name} ₹{bill.amount}",
                )
                db.add(log_entry)
                db.commit()

                await self.client.send_message(chat_id=link.telegram_chat_id, text=text)
                sent_count += 1
            except IntegrityError:
                db.rollback()
            except Exception as e:
                db.rollback()
                logger.error("Failed to send bill reminder to %s: %s", link.user_id, e)

        return sent_count

    async def dispatch_budget_alerts(self, db: Session, user_id: Optional[str] = None) -> int:
        today = date.today()
        month_str = today.strftime("%Y-%m")
        start_of_month = date(today.year, today.month, 1)

        query = db.query(TelegramAccountLink, FinancialProfile).join(
            FinancialProfile, FinancialProfile.user_id == TelegramAccountLink.user_id
        ).filter(
            TelegramAccountLink.is_active == True,
            TelegramAccountLink.notifications_enabled == True,
            TelegramAccountLink.notify_budget == True,
        )
        if user_id:
            query = query.filter(TelegramAccountLink.user_id == user_id)

        links_and_profiles = query.all()
        sent_count = 0

        for link, profile in links_and_profiles:
            monthly_budget = float(profile.monthly_expenses or 0.0)
            if monthly_budget <= 0:
                continue

            # Calculate total expenses for current month
            spent_total = (
                db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
                .filter(
                    Transaction.user_id == link.user_id,
                    Transaction.type == "expense",
                    Transaction.date >= start_of_month,
                )
                .scalar()
            )
            spent = float(spent_total or 0.0)
            pct = (spent / monthly_budget) * 100.0

            # Alert if exceeded 100%
            if pct >= 100.0:
                dedup_key = f"budget_exceeded_{month_str}"
                exists = (
                    db.query(TelegramNotificationLog)
                    .filter(
                        TelegramNotificationLog.user_id == link.user_id,
                        TelegramNotificationLog.dedup_key == dedup_key,
                    )
                    .first()
                )
                if not exists:
                    text = (
                        f"🚨 <b>Budget Alert: Monthly Limit Exceeded</b>\n\n"
                        f"You have spent <b>₹{spent:,.2f}</b> of your <b>₹{monthly_budget:,.2f}</b> monthly expense budget ({pct:.1f}%).\n\n"
                        f"Review your recent expenses or ask me <i>\"How much did I spend this month?\"</i> for insights."
                    )
                    try:
                        log_entry = TelegramNotificationLog(
                            user_id=link.user_id,
                            notification_type="budget_exceeded",
                            dedup_key=dedup_key,
                            details=f"Spent ₹{spent:,.2f} / ₹{monthly_budget:,.2f} ({pct:.1f}%)",
                        )
                        db.add(log_entry)
                        db.commit()
                        await self.client.send_message(chat_id=link.telegram_chat_id, text=text)
                        sent_count += 1
                        continue
                    except IntegrityError:
                        db.rollback()

            # Warning if reached 85%
            elif pct >= 85.0:
                dedup_key = f"budget_warning_{month_str}"
                exists = (
                    db.query(TelegramNotificationLog)
                    .filter(
                        TelegramNotificationLog.user_id == link.user_id,
                        TelegramNotificationLog.dedup_key == dedup_key,
                    )
                    .first()
                )
                if not exists:
                    text = (
                        f"⚠️ <b>Budget Warning: 85% Reached</b>\n\n"
                        f"You have spent <b>₹{spent:,.2f}</b> of your <b>₹{monthly_budget:,.2f}</b> monthly limit ({pct:.1f}%).\n"
                        f"Remaining budget for this month: <b>₹{max(0.0, monthly_budget - spent):,.2f}</b>."
                    )
                    try:
                        log_entry = TelegramNotificationLog(
                            user_id=link.user_id,
                            notification_type="budget_warning",
                            dedup_key=dedup_key,
                            details=f"Spent ₹{spent:,.2f} / ₹{monthly_budget:,.2f} ({pct:.1f}%)",
                        )
                        db.add(log_entry)
                        db.commit()
                        await self.client.send_message(chat_id=link.telegram_chat_id, text=text)
                        sent_count += 1
                    except IntegrityError:
                        db.rollback()

        return sent_count

    async def dispatch_goal_milestones(self, db: Session, user_id: Optional[str] = None) -> int:
        query = (
            db.query(TelegramAccountLink, FinancialGoal)
            .join(FinancialGoal, FinancialGoal.user_id == TelegramAccountLink.user_id)
            .filter(
                TelegramAccountLink.is_active == True,
                TelegramAccountLink.notifications_enabled == True,
                TelegramAccountLink.notify_goals == True,
            )
        )
        if user_id:
            query = query.filter(TelegramAccountLink.user_id == user_id)

        records = query.all()
        sent_count = 0

        for link, goal in records:
            target = float(goal.target_amount or 0.0)
            current = float(goal.current_amount or 0.0)
            if target <= 0:
                continue

            ratio = current / target

            if ratio >= 1.0:
                dedup_key = f"goal_reached_{goal.id}"
                exists = (
                    db.query(TelegramNotificationLog)
                    .filter(
                        TelegramNotificationLog.user_id == link.user_id,
                        TelegramNotificationLog.dedup_key == dedup_key,
                    )
                    .first()
                )
                if not exists:
                    text = (
                        f"🎉 <b>Goal Accomplished!</b>\n\n"
                        f"Congratulations! You have reached 100% of your target for <b>{goal.name}</b>:\n"
                        f"• <b>Target Amount:</b> ₹{target:,.2f}\n"
                        f"• <b>Current Saved:</b> ₹{current:,.2f}\n\n"
                        f"Fantastic financial discipline!"
                    )
                    try:
                        log_entry = TelegramNotificationLog(
                            user_id=link.user_id,
                            notification_type="goal_reached",
                            dedup_key=dedup_key,
                            details=f"{goal.name} ₹{current}/₹{target}",
                        )
                        db.add(log_entry)
                        db.commit()
                        await self.client.send_message(chat_id=link.telegram_chat_id, text=text)
                        sent_count += 1
                    except IntegrityError:
                        db.rollback()

        return sent_count

    async def dispatch_all_notifications(self, db: Session, user_id: Optional[str] = None) -> Dict[str, int]:
        bills = await self.dispatch_bill_reminders(db, user_id)
        budgets = await self.dispatch_budget_alerts(db, user_id)
        goals = await self.dispatch_goal_milestones(db, user_id)
        return {"bills": bills, "budgets": budgets, "goals": goals, "total": bills + budgets + goals}


notification_dispatcher = NotificationDispatcher()
