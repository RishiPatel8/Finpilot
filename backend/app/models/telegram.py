import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class TelegramAccountLink(Base):
    """
    Persistent mapping between an authenticated FinPilot user and their Telegram account.
    Restricted to private chats. Enforces 1-to-1 relationship per FinPilot account.
    """
    __tablename__ = "telegram_account_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    telegram_user_id = Column(String(64), nullable=False, unique=True, index=True)
    telegram_chat_id = Column(String(64), nullable=False, index=True)
    telegram_username = Column(String(128), nullable=True)
    telegram_first_name = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Opt-in Notification Preferences
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    notify_bills = Column(Boolean, default=True, nullable=False)
    notify_budget = Column(Boolean, default=True, nullable=False)
    notify_goals = Column(Boolean, default=True, nullable=False)
    notify_summary = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="telegram_link")


class TelegramLinkCode(Base):
    """
    Cryptographically secure, single-use, time-bound link code.
    Generated on the FinPilot website and consumed via the Telegram Bot.
    """
    __tablename__ = "telegram_link_codes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(32), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="telegram_link_codes")


class TelegramProcessedUpdate(Base):
    """
    Deduplication store for incoming Telegram updates.
    Prevents duplicate execution on webhook or polling network retries.
    """
    __tablename__ = "telegram_processed_updates"

    update_id = Column(Integer, primary_key=True, autoincrement=False)
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class TelegramNotificationLog(Base):
    """
    Log of outbound alerts sent to prevent duplicate notifications.
    """
    __tablename__ = "telegram_notification_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(64), nullable=False, index=True)  # bill_reminder, budget_alert, goal_milestone
    dedup_key = Column(String(128), nullable=False, index=True)  # e.g. bill_reminder_{id}_{due_date}
    details = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "dedup_key", name="uq_telegram_user_dedup_key"),
    )

    user = relationship("User", back_populates="telegram_notifications")
