import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Boolean, DateTime, Date, Numeric, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    dependents = Column(Integer, default=0, nullable=False)
    monthly_income = Column(Numeric(14, 2), default=0.00, nullable=False)
    monthly_expenses = Column(Numeric(14, 2), default=0.00, nullable=False)
    risk_tolerance = Column(String(50), default="moderate", nullable=False)  # conservative, moderate, aggressive
    emergency_fund_target_months = Column(Integer, default=6, nullable=False)
    tax_regime_preference = Column(String(20), default="auto", nullable=False)  # auto, new, old
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="profile")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, default=date.today, nullable=False, index=True)
    amount = Column(Numeric(14, 2), nullable=False)
    type = Column(String(20), nullable=False)  # income, expense
    category = Column(String(100), nullable=False, index=True)  # Housing, Food, Transport, Investment, Tax, etc.
    description = Column(String(255), nullable=False)
    source = Column(String(100), default="manual", nullable=False)  # manual, csv_import, bank_statement
    is_recurring = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="transactions")


class Liability(Base):
    __tablename__ = "liabilities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Home Loan, Education Loan, Car Loan, Credit Card
    principal = Column(Numeric(14, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)  # Annual interest rate percentage e.g. 8.5%
    monthly_emi = Column(Numeric(14, 2), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    remaining_months = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="liabilities")


class AssetHolding(Base):
    __tablename__ = "asset_holdings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Parag Parikh Liquid Fund, RBI Floating Rate Bond, SBI 3-Yr FD, EPF, etc.
    category = Column(String(50), nullable=False)  # liquid_mf, bond, fd, equity_mf, epf_ppf, gold, real_estate, cash
    invested_value = Column(Numeric(14, 2), nullable=False)
    current_value = Column(Numeric(14, 2), nullable=False)
    expected_return_rate = Column(Numeric(5, 2), default=6.5, nullable=False)
    liquidity_days = Column(Integer, default=1, nullable=False)  # 0 = instant, 1 = T+1, >365 = locked
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="assets")


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Emergency Reserve, Home Down Payment, Higher Education, Retirement
    category = Column(String(50), default="custom", nullable=False)
    target_amount = Column(Numeric(14, 2), nullable=False)
    current_amount = Column(Numeric(14, 2), default=0.00, nullable=False)
    target_date = Column(Date, nullable=False)
    priority = Column(String(20), default="medium", nullable=False)  # high, medium, low
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="goals")


class TaxRecord(Base):
    __tablename__ = "tax_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_year = Column(String(20), nullable=False, index=True)  # AY 2025-26, AY 2024-25
    gross_income = Column(Numeric(14, 2), nullable=False)
    total_deductions = Column(Numeric(14, 2), default=0.00, nullable=False)
    regime = Column(String(20), nullable=False)  # new, old
    calculated_tax = Column(Numeric(14, 2), nullable=False)
    calculation_details = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="tax_records")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)
    tool_invocations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="chat_messages")


class ScenarioRecord(Base):
    __tablename__ = "scenario_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    scenario_type = Column(String(50), nullable=False)
    input_data = Column(JSON, nullable=False)
    result_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="scenario_records")
