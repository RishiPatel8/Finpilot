from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class ScenarioInput(BaseModel):
    scenario_type: str = Field(
        description="major_purchase, increase_savings, expense_reduction, emergency_fund_builder, instrument_comparison"
    )
    title: Optional[str] = None
    
    # Financial context inputs (defaults can be derived from user profile)
    monthly_income: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    monthly_expenses: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    current_savings: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    
    # Specific Scenario Parameters
    target_amount: Optional[Decimal] = Field(default=None, ge=Decimal("0"), description="Target purchase cost or savings goal")
    time_horizon_months: Optional[int] = Field(default=None, gt=0, description="Months to achieve goal")
    expense_reduction_amount: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    target_savings_rate_pct: Optional[Decimal] = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    
    # Assumptions
    expected_annual_return_pct: Decimal = Field(default=Decimal("7.0"))
    expected_annual_inflation_pct: Decimal = Field(default=Decimal("6.0"))
    adjust_for_inflation: bool = True


class ScenarioMetricComparison(BaseModel):
    metric_name: str
    baseline_value: str
    scenario_value: str
    delta: str
    impact_type: str  # "positive", "neutral", "negative"


class ScenarioAlternativeOption(BaseModel):
    name: str
    description: str
    monthly_commitment: Decimal
    projected_outcome: Decimal
    feasibility: str  # "Fully Feasible", "Requires Budget Adjustment", "Tight Cash Flow"
    pros: List[str]
    cons: List[str]


class ScenarioSimulationResult(BaseModel):
    scenario_type: str
    title: str
    is_feasible: bool
    summary_verdict: str
    
    # Baseline vs Scenario Metrics
    baseline_surplus: Decimal
    scenario_surplus: Decimal
    required_monthly_allocation: Decimal
    cash_flow_gap: Decimal
    
    # Emergency runway impact
    baseline_runway_months: float
    projected_runway_months: float
    
    comparisons: List[ScenarioMetricComparison]
    timeline_projections: List[Dict[str, Any]]
    alternative_options: List[ScenarioAlternativeOption]
    risks_and_assumptions: List[str]
    citations: List[str]


class SavedScenarioCreate(BaseModel):
    title: str
    scenario_type: str
    input_data: Dict[str, Any]
    result_data: Dict[str, Any]


class SavedScenarioResponse(BaseModel):
    id: str
    user_id: str
    title: str
    scenario_type: str
    input_data: Dict[str, Any]
    result_data: Dict[str, Any]
    created_at: str
    model_config = ConfigDict(from_attributes=True)
