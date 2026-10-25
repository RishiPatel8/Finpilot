from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class ScenarioBaselineResponse(BaseModel):
    monthly_income: float = 0.0
    essential_expenses: float = 0.0
    discretionary_expenses: float = 0.0
    total_monthly_expenses: float = 0.0
    existing_monthly_emi: float = 0.0
    existing_recurring_commitments: float = 0.0
    available_monthly_surplus: float = 0.0
    liquid_savings: float = 0.0
    emergency_fund_target_months: float = 6.0
    emergency_fund_target_amount: float = 0.0
    emergency_runway_months: float = 0.0
    total_debt: float = 0.0
    data_sources: Dict[str, str] = Field(default_factory=dict)
    is_verified_data: bool = False
    data_completeness_pct: int = 0
    missing_fields: List[str] = Field(default_factory=list)


class ScenarioInput(BaseModel):
    scenario_type: str = Field(
        description="vehicle, house, personal_loan, expensive_product, major_trip, business, investment_increase, financial_goal, cash_vs_loan, custom, major_purchase, increase_savings, expense_reduction, emergency_fund_builder"
    )
    title: Optional[str] = None

    # Financial baseline inputs (defaults derived from user's verified database records)
    monthly_income: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    monthly_expenses: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    current_savings: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    existing_monthly_emi: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    existing_recurring_commitments: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    emergency_fund_target_months: Optional[float] = Field(default=6.0, ge=1.0)

    # Core Purchase / Investment / Loan Parameters
    target_amount: Optional[Decimal] = Field(default=None, ge=Decimal("0"), description="Purchase price or target sum")
    purchase_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    down_payment: Optional[Decimal] = Field(default=None, ge=Decimal("0"))

    # Loan parameters
    loan_interest_rate_pct: Optional[Decimal] = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    loan_tenure_months: Optional[int] = Field(default=None, ge=1, le=480)
    loan_processing_fee_pct: Optional[Decimal] = Field(default=Decimal("1.0"), ge=Decimal("0"), le=Decimal("10"))
    existing_loan_in_budget: bool = Field(default=False, description="Set true if this EMI is already included in monthly expenses to prevent double-counting")

    # Ongoing Ownership & Recurring Changes
    monthly_ongoing_costs: Optional[Decimal] = Field(default=Decimal("0"), ge=Decimal("0"), description="Fuel, maintenance, insurance, subscription")
    upfront_one_time_costs: Optional[Decimal] = Field(default=Decimal("0"), ge=Decimal("0"), description="Stamp duty, registration, booking fees")
    monthly_revenue_gain: Optional[Decimal] = Field(default=Decimal("0"), ge=Decimal("0"), description="Estimated revenue from business or salary hike")

    # Time & Growth Assumptions
    time_horizon_months: Optional[int] = Field(default=None, gt=0, description="Months to achieve goal or loan tenure")
    expected_annual_return_pct: Decimal = Field(default=Decimal("8.0"))
    expected_annual_inflation_pct: Decimal = Field(default=Decimal("6.0"))
    adjust_for_inflation: bool = True

    # Cash vs Loan Specific
    cash_discount_pct: Optional[Decimal] = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("50"))

    # Legacy / Budget specific parameters
    expense_reduction_amount: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    target_savings_rate_pct: Optional[Decimal] = Field(default=None, ge=Decimal("0"), le=Decimal("100"))


class LoanAnalysis(BaseModel):
    purchase_price: float
    down_payment: float
    principal_borrowed: float
    annual_interest_rate_pct: float
    tenure_months: int
    monthly_emi: float
    total_amount_repaid: float
    total_interest_paid: float
    processing_fee_amount: float
    total_cost_of_ownership: float


class SavingsImpact(BaseModel):
    starting_liquid_savings: float
    initial_cash_required: float
    remaining_liquid_savings: float
    emergency_fund_target: float
    emergency_fund_preserved: bool
    baseline_runway_months: float
    projected_runway_months: float
    runway_delta_months: float
    is_partial_data: bool = False


class CashFlowImpact(BaseModel):
    monthly_income: float
    monthly_living_expenses: float
    existing_obligations: float
    available_surplus_before: float
    proposed_new_monthly_payment: float
    additional_ongoing_costs: float
    monthly_revenue_gain: float
    projected_surplus_after: float
    surplus_delta: float
    debt_to_income_before_pct: float
    debt_to_income_after_pct: float


class GoalTimeline(BaseModel):
    target_amount: float
    already_saved: float
    remaining_to_save: float
    target_horizon_months: int
    required_monthly_savings: float
    months_needed_at_current_surplus: Optional[float] = None
    is_achievable_by_target_date: bool


class StressTestResult(BaseModel):
    name: str
    description: str
    projected_surplus: float
    projected_runway_months: float
    verdict: str  # "Manageable", "Strained", "Deficit"
    impact_summary: str


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
    feasibility: str  # "Affordable", "Moderate Risk", "High Risk / Tight Cash Flow"
    initial_cash_required: Optional[Decimal] = None
    projected_surplus: Optional[Decimal] = None
    remaining_savings: Optional[Decimal] = None
    total_estimated_cost: Optional[Decimal] = None
    pros: List[str]
    cons: List[str]
    trade_offs: Optional[str] = None


class ScenarioSimulationResult(BaseModel):
    scenario_type: str
    title: str
    is_feasible: bool
    verdict_category: str = "AFFORDABLE"  # "AFFORDABLE", "TIGHT_CASH_FLOW", "EMERGENCY_FUND_AT_RISK", "HIGH_RISK_DEFICIT", "DATA_INCOMPLETE"
    summary_verdict: str
    detailed_recommendations: List[str] = Field(default_factory=list)

    # Baseline vs Scenario Metrics (backward compatible)
    baseline_surplus: Decimal
    scenario_surplus: Decimal
    required_monthly_allocation: Decimal
    cash_flow_gap: Decimal

    # Emergency runway impact
    baseline_runway_months: float
    projected_runway_months: float

    # Detailed Sub-Analyses
    cash_flow_impact: CashFlowImpact
    savings_impact: SavingsImpact
    loan_analysis: Optional[LoanAnalysis] = None
    goal_timeline: Optional[GoalTimeline] = None

    comparisons: List[ScenarioMetricComparison]
    timeline_projections: List[Dict[str, Any]]
    alternative_options: List[ScenarioAlternativeOption]
    stress_tests: List[StressTestResult] = Field(default_factory=list)
    risks_and_assumptions: List[str]
    missing_information: List[str] = Field(default_factory=list)
    citations: List[str]


class SavedScenarioCreate(BaseModel):
    title: str
    scenario_type: str
    input_data: Dict[str, Any]
    result_data: Dict[str, Any]


class SavedScenarioUpdate(BaseModel):
    title: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    result_data: Optional[Dict[str, Any]] = None


class SavedScenarioResponse(BaseModel):
    id: str
    user_id: str
    title: str
    scenario_type: str
    input_data: Dict[str, Any]
    result_data: Dict[str, Any]
    created_at: str
    model_config = ConfigDict(from_attributes=True)
