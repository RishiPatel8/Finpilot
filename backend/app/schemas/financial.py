from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class FinancialProfileBase(BaseModel):
    age: Optional[int] = Field(default=None, ge=18, le=120)
    dependents: int = Field(default=0, ge=0, le=20)
    monthly_income: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    monthly_expenses: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    risk_tolerance: str = Field(default="moderate")
    emergency_fund_target_months: int = Field(default=6, ge=1, le=36)
    tax_regime_preference: str = Field(default="auto")


class FinancialProfileCreate(FinancialProfileBase):
    pass


class FinancialProfileUpdate(FinancialProfileBase):
    pass


class FinancialProfileResponse(FinancialProfileBase):
    id: str
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    date: date
    amount: Decimal = Field(gt=Decimal("0.00"), description="Amount must be positive")
    type: str = Field(description="income or expense")
    category: str
    description: str
    source: str = "manual"
    is_recurring: bool = False


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: str
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CSVImportRowPreview(BaseModel):
    row_number: int
    date: str
    amount: float
    type: str
    category: str
    description: str
    is_valid: bool
    validation_error: Optional[str] = None
    is_duplicate: bool = False


class CSVImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    preview: List[CSVImportRowPreview]


class CSVImportConfirmRequest(BaseModel):
    transactions: List[TransactionCreate]


class LiabilityBase(BaseModel):
    name: str
    principal: Decimal = Field(gt=Decimal("0.00"), description="Principal balance must be positive")
    interest_rate: Decimal = Field(ge=Decimal("0.00"), le=Decimal("100.00"), description="Annual interest rate percentage (0-100)")
    monthly_emi: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Monthly EMI amount")
    tenure_months: int = Field(default=12, gt=0, description="Total tenure in months")
    remaining_months: int = Field(default=12, ge=0, description="Remaining tenure in months")
    debt_type: str = Field(default="payable", description="payable (borrowed) or receivable (lent)")
    counterparty: Optional[str] = None
    interest_period: str = Field(default="annual", description="annual or monthly")
    status: str = Field(default="active", description="active, repaid, closed")
    loan_date: Optional[date] = None
    due_date: Optional[date] = None
    repayment_frequency: str = "monthly"
    notes: Optional[str] = None


class LiabilityCreate(LiabilityBase):
    pass


class LiabilityResponse(LiabilityBase):
    id: str
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DebtRepaymentPlanRequest(BaseModel):
    extra_monthly_payment: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))


class DebtRepaymentPlanResponse(BaseModel):
    total_debt_principal: Decimal
    total_monthly_emi: Decimal
    extra_payment_applied: Decimal
    avalanche_priority: List[str]
    snowball_priority: List[str]
    strategy_recommendation: str


class AssetHoldingBase(BaseModel):
    name: str
    category: str
    invested_value: Decimal = Field(ge=Decimal("0.00"))
    current_value: Decimal = Field(ge=Decimal("0.00"))
    expected_return_rate: Decimal = Decimal("6.5")
    liquidity_days: int = 1


class AssetHoldingCreate(AssetHoldingBase):
    pass


class AssetHoldingResponse(AssetHoldingBase):
    id: str
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FinancialGoalBase(BaseModel):
    name: str
    category: str = "custom"
    target_amount: Decimal = Field(gt=Decimal("0.00"), description="Target amount must be positive")
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Current amount must be non-negative")
    target_date: date
    priority: str = "medium"


class FinancialGoalCreate(FinancialGoalBase):
    pass


class FinancialGoalResponse(FinancialGoalBase):
    id: str
    user_id: str
    monthly_required: Optional[Decimal] = None
    progress_pct: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_surplus: Decimal
    savings_rate_pct: float
    emergency_fund_current: Decimal
    emergency_fund_target: Decimal
    emergency_fund_months_covered: float
    recent_transactions: List[TransactionResponse]
    goals: List[FinancialGoalResponse]
    monthly_history: List[dict] = Field(default_factory=list)
    statement_coverage: Optional[dict] = None
    is_empty: bool = False
    data_quality: dict = Field(default_factory=dict)


class StatementImportRowItem(BaseModel):
    date: str
    value_date: Optional[str] = None
    description: str
    amount: float
    type: str
    category: str
    raw_type: Optional[str] = None
    is_internal_transfer: bool = False
    reference_number: Optional[str] = None
    balance_after: Optional[float] = None
    source_row: Optional[int] = None
    is_duplicate: bool = False


class StatementImportConfirmRequest(BaseModel):
    filename: str
    file_format: str
    metadata: dict = Field(default_factory=dict)
    transactions: List[StatementImportRowItem]


class StatementBatchResponse(BaseModel):
    id: str
    filename: str
    file_format: str
    total_rows: int
    imported_rows: int
    duplicate_rows: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_credits: Decimal
    total_debits: Decimal
    account_number_masked: Optional[str] = None
    bank_name: Optional[str] = None
    closing_balance: Optional[Decimal] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
