import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.telegram import (
    TelegramAccountLink,
    TelegramLinkCode,
    TelegramProcessedUpdate,
    TelegramNotificationLog,
)
from app.schemas.telegram import TelegramNotificationPrefsUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)

LINK_CODE_EXPIRY_MINUTES = 15


class TelegramService:
    """
    Service managing Telegram account linking, code generation, update deduplication,
    and user resolution.
    """

    @staticmethod
    def generate_link_code(db: Session, user_id: str) -> TelegramLinkCode:
        """
        Generate a cryptographically secure, single-use, 15-minute link code for an authenticated user.
        Invalidates any previous unused codes for this user.
        """
        # Invalidate old unused codes
        db.query(TelegramLinkCode).filter(
            TelegramLinkCode.user_id == user_id,
            TelegramLinkCode.is_used == False,
        ).update({"is_used": True})

        # Generate a high-entropy 8-character token (e.g. 4 bytes hex)
        raw_code = secrets.token_hex(4).upper()
        # Formatted readable code: FP-XXXX-XXXX
        code_str = f"FP-{raw_code[:4]}-{raw_code[4:]}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=LINK_CODE_EXPIRY_MINUTES)

        link_code = TelegramLinkCode(
            user_id=user_id,
            code=code_str,
            expires_at=expires_at,
            is_used=False,
        )
        db.add(link_code)
        db.commit()
        db.refresh(link_code)
        return link_code

    @staticmethod
    def verify_and_link(
        db: Session,
        telegram_user_id: str,
        telegram_chat_id: str,
        code_str: str,
        telegram_username: Optional[str] = None,
        telegram_first_name: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Atomically verify and consume a link code, binding the Telegram account to the FinPilot user.
        Rejects expired, already used, or invalid codes.
        """
        clean_code = code_str.strip().upper()
        if not clean_code.startswith("FP-") and len(clean_code) == 8:
            clean_code = f"FP-{clean_code[:4]}-{clean_code[4:]}"

        now = datetime.now(timezone.utc)

        # Lookup unused, non-expired code
        link_code = (
            db.query(TelegramLinkCode)
            .filter(
                TelegramLinkCode.code == clean_code,
                TelegramLinkCode.is_used == False,
            )
            .first()
        )

        if not link_code:
            return False, "Invalid or already consumed link code. Please generate a new code from FinPilot Settings.", None

        # Compare datetime with timezone awareness
        code_exp = link_code.expires_at
        if code_exp.tzinfo is None:
            code_exp = code_exp.replace(tzinfo=timezone.utc)

        if now > code_exp:
            link_code.is_used = True
            db.commit()
            return False, "This link code has expired. Please generate a fresh code in FinPilot Settings (valid for 15 minutes).", None

        # Mark code as consumed atomically
        link_code.is_used = True

        target_user = db.query(User).filter(User.id == link_code.user_id).first()
        if not target_user:
            db.commit()
            return False, "Associated user account could not be found.", None

        # Check if this Telegram account is already bound to someone else
        existing_tg_link = (
            db.query(TelegramAccountLink)
            .filter(TelegramAccountLink.telegram_user_id == str(telegram_user_id))
            .first()
        )
        if existing_tg_link and existing_tg_link.user_id != target_user.id:
            # Rebind from old user to new user
            db.delete(existing_tg_link)
            db.flush()

        # Check if target user already had a link
        user_link = (
            db.query(TelegramAccountLink)
            .filter(TelegramAccountLink.user_id == target_user.id)
            .first()
        )

        if user_link:
            user_link.telegram_user_id = str(telegram_user_id)
            user_link.telegram_chat_id = str(telegram_chat_id)
            user_link.telegram_username = telegram_username
            user_link.telegram_first_name = telegram_first_name
            user_link.is_active = True
            user_link.updated_at = now
        else:
            user_link = TelegramAccountLink(
                user_id=target_user.id,
                telegram_user_id=str(telegram_user_id),
                telegram_chat_id=str(telegram_chat_id),
                telegram_username=telegram_username,
                telegram_first_name=telegram_first_name,
                is_active=True,
            )
            db.add(user_link)

        db.commit()
        return True, f"Account successfully connected! Welcome, {target_user.full_name}.", target_user

    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_user_id: str | int) -> Optional[User]:
        link = (
            db.query(TelegramAccountLink)
            .filter(
                TelegramAccountLink.telegram_user_id == str(telegram_user_id),
                TelegramAccountLink.is_active == True,
            )
            .first()
        )
        if not link:
            return None
        return db.query(User).filter(User.id == link.user_id, User.is_active == True).first()

    @staticmethod
    def get_link_by_user_id(db: Session, user_id: str) -> Optional[TelegramAccountLink]:
        return (
            db.query(TelegramAccountLink)
            .filter(TelegramAccountLink.user_id == user_id, TelegramAccountLink.is_active == True)
            .first()
        )

    @staticmethod
    def unlink_account(db: Session, user_id: str) -> bool:
        link = db.query(TelegramAccountLink).filter(TelegramAccountLink.user_id == user_id).first()
        if not link:
            return False
        db.delete(link)
        db.commit()
        return True

    @staticmethod
    def unlink_by_telegram_id(db: Session, telegram_user_id: str | int) -> bool:
        link = (
            db.query(TelegramAccountLink)
            .filter(TelegramAccountLink.telegram_user_id == str(telegram_user_id))
            .first()
        )
        if not link:
            return False
        db.delete(link)
        db.commit()
        return True

    @staticmethod
    def is_update_processed(db: Session, update_id: int) -> bool:
        exists = (
            db.query(TelegramProcessedUpdate)
            .filter(TelegramProcessedUpdate.update_id == update_id)
            .first()
        )
        return exists is not None

    @staticmethod
    def mark_update_processed(db: Session, update_id: int) -> bool:
        try:
            record = TelegramProcessedUpdate(update_id=update_id)
            db.add(record)
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False

    @staticmethod
    def update_notification_preferences(
        db: Session, user_id: str, prefs: TelegramNotificationPrefsUpdate
    ) -> Optional[TelegramAccountLink]:
        link = db.query(TelegramAccountLink).filter(TelegramAccountLink.user_id == user_id).first()
        if not link:
            return None

        if prefs.notifications_enabled is not None:
            link.notifications_enabled = prefs.notifications_enabled
        if prefs.notify_bills is not None:
            link.notify_bills = prefs.notify_bills
        if prefs.notify_budget is not None:
            link.notify_budget = prefs.notify_budget
        if prefs.notify_goals is not None:
            link.notify_goals = prefs.notify_goals
        if prefs.notify_summary is not None:
            link.notify_summary = prefs.notify_summary

        link.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(link)
        return link


telegram_service = TelegramService()
