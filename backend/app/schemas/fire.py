from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FireCalculationInput(BaseModel):
    current_age: int = Field(default=28, ge=18, le=80, description="Current age in years")
    retirement_age: int = Field(default=50, ge=25, le=90, description="Desired financial independence / retirement age")
    life_expectancy_age: int = Field(default=85, ge=50, le=110, description="Planning horizon life expectancy")
    monthly_expenses: Decimal = Field(default=Decimal("50000.00"), ge=0, description="Current monthly living expenses")
    essential_expenses_pct: Decimal = Field(default=Decimal("70.00"), ge=10, le=100, description="Percentage of expenses deemed essential (needs)")
    monthly_income: Optional[Decimal] = Field(default=Decimal("100000.00"), ge=0, description="Current monthly take-home income")
    current_investable_assets: Optional[Decimal] = Field(default=Decimal("1500000.00"), ge=0, description="Current investable liquid & market assets (excludes primary residence)")
    monthly_investment: Optional[Decimal] = Field(default=Decimal("35000.00"), ge=0, description="Current recurring monthly investment / SIP")
    expected_annual_inflation_pct: Decimal = Field(default=Decimal("6.00"), ge=0, le=25, description="Expected annual inflation rate (CPI)")
    expected_nominal_return_pct: Decimal = Field(default=Decimal("11.00"), ge=-10, le=35, description="Pre-retirement nominal portfolio return")
    post_retirement_return_pct: Decimal = Field(default=Decimal("8.00"), ge=-5, le=25, description="Post-retirement nominal portfolio return (conservative asset allocation)")
    withdrawal_rate_pct: Decimal = Field(default=Decimal("3.50"), ge=1.0, le=10.0, description="Safe withdrawal rate (SWR), typically 3.0%-4.0% for Indian inflation dynamics")
    other_retirement_monthly_income: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0, description="Guaranteed post-retirement monthly cash flow (pension, annuity, rent)")
    include_primary_residence: bool = Field(default=False, description="Whether to include primary real estate (default False to avoid double-counting)")


class FireStrategySummary(BaseModel):
    strategy_type: str = Field(..., description="lean | regular | fat | coast | custom")
    name: str
    description: str
    monthly_expense_in_retirement: Decimal
    target_corpus_today: Decimal
    target_corpus_at_retirement: Decimal
    projected_fire_age: Optional[int]
    years_to_fire: Optional[float]
    required_monthly_investment: Decimal
    is_achievable_by_target_age: bool
    shortfall_or_surplus_at_retirement: Decimal
    assumptions_and_limitations: str


class FireProjectionPoint(BaseModel):
    age: int
    year: int
    portfolio_conservative: Decimal
    portfolio_base: Decimal
    portfolio_optimistic: Decimal
    annual_contribution: Decimal
    annual_withdrawal: Decimal
    fire_target_curve: Decimal
    is_retired: bool


class FireCalculationResponse(BaseModel):
    current_age: int
    planned_retirement_age: int
    years_to_retirement: int
    current_investable_assets: Decimal
    current_monthly_expenses: Decimal
    annual_expenses_today: Decimal
    savings_rate_pct: float
    safe_withdrawal_rate_pct: float
    real_return_pct: float
    fire_target_today: Decimal
    fire_target_future: Decimal
    fire_progress_pct: float
    projected_fire_age: Optional[int]
    projected_portfolio_at_retirement: Decimal
    portfolio_surplus_or_shortfall: Decimal
    required_monthly_investment: Decimal
    current_monthly_investment: Decimal
    monthly_investment_gap: Decimal
    strategies: List[FireStrategySummary]
    yearly_projections: List[FireProjectionPoint]
    disclaimers: List[str]


class FinancialHealthPillar(BaseModel):
    pillar_id: str
    name: str
    score: int = Field(..., ge=0, le=100)
    weight: float
    status: str = Field(..., description="excellent | good | fair | critical | provisional")
    metric_value: str
    target_benchmark: str
    description: str
    action_priority: str = Field(..., description="immediate | medium_term | long_term")
    recommendation: str


class FinancialHealthAssessmentResponse(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    status: str
    is_provisional: bool
    summary: str
    pillars: List[FinancialHealthPillar]
    actionable_checklist_12_months: List[Dict[str, Any]]
    disclaimer: str
