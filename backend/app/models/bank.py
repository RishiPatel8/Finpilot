import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class BankConsent(Base):
    __tablename__ = "bank_consents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_handle = Column(String(128), unique=True, index=True, nullable=False)
    consent_id = Column(String(128), unique=True, index=True, nullable=True)
    provider = Column(String(50), default="sandbox", nullable=False)  # sandbox, setu, finvu
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, ACTIVE, REVOKED, EXPIRED, REJECTED
    fip_ids = Column(JSON, nullable=True)  # List of bank identifiers
    fi_types = Column(JSON, default=lambda: ["DEPOSIT"], nullable=False)
    valid_from = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    valid_to = Column(DateTime, nullable=False)
    fetch_frequency = Column(String(20), default="DAILY", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="bank_consents")
    accounts = relationship("BankAccount", back_populates="consent")


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_id = Column(String(36), ForeignKey("bank_consents.id", ondelete="SET NULL"), nullable=True, index=True)
    institution_name = Column(String(100), nullable=False)  # HDFC Bank, ICICI Bank, SBI, etc.
    account_number_masked = Column(String(50), nullable=False)  # XXXX-XXXX-4921
    account_type = Column(String(50), default="savings", nullable=False)  # savings, current, deposit
    ifsc_code = Column(String(20), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    current_balance = Column(Numeric(14, 2), default=0.00, nullable=False)
    balance_type = Column(String(30), default="provider_reported", nullable=False)  # provider_reported, calculated, cached
    balance_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    sync_status = Column(String(30), default="synced", nullable=False)  # synced, pending, failed, stale
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="bank_accounts")
    consent = relationship("BankConsent", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="bank_account", cascade="all, delete-orphan")
    sync_logs = relationship("BankSyncLog", back_populates="account", cascade="all, delete-orphan")


class BankSyncLog(Base):
    __tablename__ = "bank_sync_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    sync_status = Column(String(20), nullable=False)  # SUCCESS, FAILED, PARTIAL
    records_synced = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    synced_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
    account = relationship("BankAccount", back_populates="sync_logs")
