from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class FinancialProfileBase(BaseModel):
    age: Optional[int] = None
    dependents: int = 0
    monthly_income: Decimal = Field(default=Decimal("0.00"))
    monthly_expenses: Decimal = Field(default=Decimal("0.00"))
    risk_tolerance: str = Field(default="moderate")
    emergency_fund_target_months: int = 6
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
    amount: Decimal
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
    principal: Decimal
    interest_rate: Decimal
    monthly_emi: Decimal
    tenure_months: int
    remaining_months: int


class LiabilityCreate(LiabilityBase):
    pass


class LiabilityResponse(LiabilityBase):
    id: str
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AssetHoldingBase(BaseModel):
    name: str
    category: str
    invested_value: Decimal
    current_value: Decimal
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
    target_amount: Decimal
    current_amount: Decimal = Decimal("0.00")
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
