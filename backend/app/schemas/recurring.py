from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class RecurringTransactionBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    merchant: Optional[str] = Field(default=None, max_length=255)
    transaction_type: str = Field(default="expense", pattern="^(income|expense)$")
    amount: Decimal = Field(gt=Decimal("0.00"))
    category: str = Field(min_length=1, max_length=100)
    frequency: str = Field(default="monthly", pattern="^(weekly|fortnightly|monthly|quarterly|yearly)$")
    next_expected_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    user_notes: Optional[str] = None


class RecurringTransactionCreate(RecurringTransactionBase):
    bank_account_id: Optional[str] = None


class RecurringTransactionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    merchant: Optional[str] = Field(default=None, max_length=255)
    transaction_type: Optional[str] = Field(default=None, pattern="^(income|expense)$")
    amount: Optional[Decimal] = Field(default=None, gt=Decimal("0.00"))
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    frequency: Optional[str] = Field(default=None, pattern="^(weekly|fortnightly|monthly|quarterly|yearly)$")
    next_expected_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    user_notes: Optional[str] = None


class RecurringTransactionConfirmRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(default=None, gt=Decimal("0.00"))
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    frequency: Optional[str] = Field(default=None, pattern="^(weekly|fortnightly|monthly|quarterly|yearly)$")
    next_expected_date: Optional[date] = None
    user_notes: Optional[str] = None


class RecurringTransactionDismissRequest(BaseModel):
    user_feedback: Optional[str] = Field(default=None, max_length=500)


class RecurringTransactionResponse(RecurringTransactionBase):
    id: str
    user_id: str
    bank_account_id: Optional[str] = None
    status: str  # detected, confirmed, paused, dismissed, cancelled
    confidence: str  # high, medium, low
    detection_source: str
    explanation: Optional[str] = None
    last_occurrence_date: Optional[date] = None
    occurrence_count: int
    user_confirmed_at: Optional[datetime] = None
    user_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpcomingOccurrence(BaseModel):
    expected_date: date
    recurring_id: str
    name: str
    merchant: Optional[str] = None
    amount: Decimal
    transaction_type: str  # income, expense
    category: str
    frequency: str
    status: str
    is_overdue: bool
    days_until: int


class UpcomingSummary(BaseModel):
    horizon_days: int
    total_upcoming_expenses: Decimal
    total_upcoming_income: Decimal
    net_upcoming_cash_flow: Decimal
    occurrences: List[UpcomingOccurrence]


class RecurringSummary(BaseModel):
    monthly_recurring_expenses: Decimal
    monthly_recurring_income: Decimal
    net_recurring_cash_flow: Decimal
    active_count: int
    paused_count: int
    pending_review_count: int
    next_upcoming_payment: Optional[UpcomingOccurrence] = None
    next_upcoming_income: Optional[UpcomingOccurrence] = None
