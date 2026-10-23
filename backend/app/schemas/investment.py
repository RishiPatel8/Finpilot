from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class InvestmentOptionComparison(BaseModel):
    category: str  # "liquid_mf", "bond", "fd"
    display_name: str
    indicative_annual_yield_pct: Decimal
    recommended_time_horizon: str
    liquidity_mechanism: str
    credit_risk_level: str
    interest_rate_risk: str
    tax_treatment_summary: str
    exit_load_or_penalty: str
    pros: List[str]
    cons: List[str]
    suitability_verdict: str
    projected_maturity_value: Decimal
    inflation_adjusted_value: Decimal


class InvestmentCompareRequest(BaseModel):
    investment_amount: Decimal = Field(gt=Decimal("0"), description="Principal amount to invest")
    time_horizon_months: int = Field(gt=0, description="Duration in months")
    user_tax_slab_pct: Decimal = Field(default=Decimal("30.0"), description="Investor's marginal tax slab percentage")
    expected_inflation_pct: Decimal = Field(default=Decimal("6.0"), description="Expected annual inflation rate")
    can_lock_funds: bool = Field(default=False, description="Whether investor can commit to locking funds without premature withdrawal")
    risk_tolerance: str = Field(default="moderate", description="conservative, moderate, aggressive")


class InvestmentCompareResponse(BaseModel):
    principal_amount: Decimal
    time_horizon_months: int
    inflation_rate_pct: Decimal
    comparisons: List[InvestmentOptionComparison]
    top_recommendation: str
    rationale: str
    disclaimer: str


class GoalProjectionRequest(BaseModel):
    goal_name: str
    target_amount: Decimal = Field(gt=Decimal("0"))
    current_amount: Decimal = Field(default=Decimal("0.00"))
    time_horizon_months: int = Field(gt=0)
    expected_annual_return_pct: Decimal = Field(default=Decimal("8.0"))
    expected_annual_inflation_pct: Decimal = Field(default=Decimal("6.0"))
    adjust_for_inflation: bool = True


class GoalProjectionResponse(BaseModel):
    goal_name: str
    nominal_target_amount: Decimal
    inflation_adjusted_target: Decimal
    current_amount: Decimal
    time_horizon_months: int
    required_monthly_sip: Decimal
    total_investment_contributed: Decimal
    projected_wealth_gain: Decimal
    breakdown_by_year: List[dict]
