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
    source = Column(String(100), default="manual", nullable=False)  # manual, csv_import, bank_sync, bank_statement
    bank_account_id = Column(String(36), ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    provider_txn_ref = Column(String(128), unique=True, nullable=True, index=True)
    is_internal_transfer = Column(Boolean, default=False, nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)
    value_date = Column(Date, nullable=True)
    reference_number = Column(String(128), nullable=True, index=True)
    balance_after = Column(Numeric(14, 2), nullable=True)
    source_file = Column(String(255), nullable=True)
    source_row = Column(Integer, nullable=True)
    batch_id = Column(String(36), nullable=True, index=True)
    account_mask = Column(String(30), nullable=True)
    raw_type = Column(String(30), nullable=True)  # debit, credit, refund, transfer, fee, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="transactions")
    bank_account = relationship("BankAccount", back_populates="transactions")


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

    # Extended peer-to-peer debt and loan tracking
    debt_type = Column(String(32), default="payable", nullable=False)  # payable (borrowed), receivable (lent)
    counterparty = Column(String(255), nullable=True)  # Name of friend, brother, lender, etc.
    interest_period = Column(String(20), default="annual", nullable=False)  # annual, monthly
    status = Column(String(32), default="active", nullable=False)  # active, repaid, closed
    loan_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    repayment_frequency = Column(String(32), default="monthly", nullable=False)  # monthly, lump_sum
    notes = Column(Text, nullable=True)

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


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(String(36), ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    merchant = Column(String(255), nullable=True)
    transaction_type = Column(String(20), default="expense", nullable=False)  # income, expense
    amount = Column(Numeric(14, 2), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    frequency = Column(String(30), default="monthly", nullable=False)  # weekly, fortnightly, monthly, quarterly, yearly
    status = Column(String(30), default="detected", nullable=False, index=True)  # detected, confirmed, paused, dismissed, cancelled
    confidence = Column(String(20), default="medium", nullable=False)  # high, medium, low
    detection_source = Column(String(50), default="intelligence_engine", nullable=False)
    explanation = Column(Text, nullable=True)

    next_expected_date = Column(Date, nullable=True, index=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    last_occurrence_date = Column(Date, nullable=True)
    occurrence_count = Column(Integer, default=1, nullable=False)

    user_confirmed_at = Column(DateTime, nullable=True)
    user_feedback = Column(Text, nullable=True)
    user_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="recurring_transactions")
    bank_account = relationship("BankAccount")


class StatementImportBatch(Base):
    __tablename__ = "statement_import_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(20), nullable=False)  # csv, xlsx, pdf
    total_rows = Column(Integer, default=0, nullable=False)
    imported_rows = Column(Integer, default=0, nullable=False)
    duplicate_rows = Column(Integer, default=0, nullable=False)
    skipped_rows = Column(Integer, default=0, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    total_credits = Column(Numeric(14, 2), default=0.00, nullable=False)
    total_debits = Column(Numeric(14, 2), default=0.00, nullable=False)
    account_number_masked = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    closing_balance = Column(Numeric(14, 2), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="statement_batches")


class InvestmentScenario(Base):
    __tablename__ = "investment_scenarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    scenario_mode = Column(String(50), default="multi_product", nullable=False)  # multi_product, lumpsum_vs_sip, goal_plan, stress_test, portfolio_analysis
    notes = Column(Text, nullable=True)
    inputs = Column(JSON, nullable=False)
    results_summary = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="investment_scenarios")

