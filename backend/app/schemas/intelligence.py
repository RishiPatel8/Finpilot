from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class CanonicalFinancialSnapshot(BaseModel):
    user_id: str
    snapshot_timestamp: datetime
    period: str  # current_month, last_30_days, rolling_90_days
    start_date: date
    end_date: date
    income: Decimal = Field(ge=Decimal("0.00"))
    expenses: Decimal = Field(ge=Decimal("0.00"))
    net_cash_flow: Decimal
    savings_rate_pct: float
    category_spending: Dict[str, Decimal]
    liquid_savings: Decimal = Field(ge=Decimal("0.00"))
    total_assets: Decimal = Field(ge=Decimal("0.00"))
    total_liabilities: Decimal = Field(ge=Decimal("0.00"))
    net_worth: Decimal
    emergency_runway_months: float
    total_transactions_count: int = Field(ge=0)
    data_quality_flags: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class RecurringTransactionPattern(BaseModel):
    id: str
    merchant_or_desc: str
    category: str
    estimated_amount: Decimal = Field(gt=Decimal("0.00"))
    frequency: str = "monthly"  # monthly, weekly, quarterly, annual
    next_expected_date: Optional[date] = None
    occurrence_count: int = Field(ge=1)
    confidence: str = "medium"  # high, medium, low
    is_confirmed: bool = False


class SpendingAnomaly(BaseModel):
    id: str
    category: str
    current_period_spend: Decimal
    baseline_spend: Decimal
    variance_amount: Decimal
    variance_pct: float
    severity: str = "moderate"  # moderate, elevated, critical
    explanation: str


class CashFlowForecast(BaseModel):
    horizon_days: int = 30
    projected_income: Decimal
    projected_expenses: Decimal
    projected_net: Decimal
    projected_ending_cash: Optional[Decimal] = None
    daily_burn_rate: Decimal
    key_drivers: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    confidence: str = "medium"
    insufficient_data: bool = False


class AdaptiveBudgetRecommendation(BaseModel):
    category: str
    historical_average: Decimal
    current_budget: Optional[Decimal] = None
    recommended_budget: Decimal
    rationale: str
    potential_savings: Decimal = Field(default=Decimal("0.00"))


class GoalFeasibility(BaseModel):
    goal_id: str
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date
    required_monthly_sip: Decimal
    current_projected_monthly_savings: Decimal
    is_on_track: bool
    projected_completion_date: Optional[date] = None
    delay_months: int = 0
    remedial_actions: List[str] = Field(default_factory=list)


class FinancialInsight(BaseModel):
    id: str
    category: str  # spending, budget, recurring, goal, cash_flow, savings, anomaly
    title: str
    summary: str
    detail: str
    severity: str = "info"  # info, success, warning, critical
    confidence: str = "high"  # high, medium, low
    metric_value: Optional[str] = None
    baseline_value: Optional[str] = None
    action_label: Optional[str] = None
    action_tab: Optional[str] = None  # budget, debts, goals, tax, fire, scenarios
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IntelligenceFeedResponse(BaseModel):
    insights: List[FinancialInsight]
    total_insights: int
    high_priority_count: int
    data_quality_summary: Dict[str, Any]
    generated_at: datetime


class CategorizationPreviewRequest(BaseModel):
    description: str
    amount: Optional[Decimal] = None


class CategorizationPreviewResponse(BaseModel):
    description: str
    suggested_category: str
    confidence: str
    matched_rule: str
