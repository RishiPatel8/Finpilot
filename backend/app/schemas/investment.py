from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# -----------------------------------------------------------------------------
# 1. Product Catalog & Registry Schemas
# -----------------------------------------------------------------------------

class InvestmentProductSummary(BaseModel):
    id: str
    name: str
    category: str
    asset_class: str
    indicative_annual_yield_pct: Decimal
    rate_type: str  # guaranteed, indicative, scenario_benchmark
    compounding_frequency: str
    recommended_horizon: str
    minimum_investment: Decimal
    minimum_sip_amount: Optional[Decimal] = None
    maximum_annual_investment: Optional[Decimal] = None
    lock_in_months: int
    liquidity_rating: str  # instant, t_plus_1, t_plus_2, on_maturity, with_penalty, locked
    liquidity_mechanism: str
    credit_risk_level: str
    market_risk_level: str
    duration_risk_level: str
    dicgc_insured: bool
    dicgc_limit: Decimal
    exit_penalty_rules: str
    tax_treatment_summary: str
    tax_category: str
    ter_pct: Decimal
    data_provenance: str
    regulatory_authority: str
    as_of_date: str
    suitability: str


# -----------------------------------------------------------------------------
# 2. Multi-Product Comparison Schemas
# -----------------------------------------------------------------------------

class MultiProductCompareRequest(BaseModel):
    selected_product_ids: List[str] = Field(min_length=1, max_length=6, description="List of 1 to 6 product IDs to compare")
    investment_mode: str = Field(default="lump_sum", description="'lump_sum' or 'monthly_sip'")
    investment_amount: Decimal = Field(gt=Decimal("0"), description="Lump sum amount or monthly SIP contribution in ₹")
    time_horizon_months: int = Field(gt=0, description="Duration in months")
    user_tax_slab_pct: Decimal = Field(default=Decimal("30.0"), description="Investor's marginal income tax slab percentage (0, 5, 10, 15, 20, 30)")
    expected_inflation_pct: Decimal = Field(default=Decimal("6.0"), description="Annual inflation rate")
    can_lock_funds: bool = Field(default=False, description="Whether investor can lock funds without premature withdrawal")
    custom_return_overrides: Optional[Dict[str, Decimal]] = Field(default=None, description="Optional custom annual return assumption overrides per product ID")


class MultiProductCompareItem(BaseModel):
    product_id: str
    name: str
    category: str
    asset_class: str
    rate_used_pct: Decimal
    rate_type: str
    compounding_frequency: str
    invested_principal: Decimal
    gross_maturity_value: Decimal
    estimated_gain: Decimal
    estimated_fees_ter: Decimal
    estimated_tax: Decimal
    tax_rules_applied: str
    net_post_tax_proceeds: Decimal
    net_annualized_cagr_pct: Decimal
    inflation_adjusted_value: Decimal
    is_locked: bool
    lock_in_months: int
    liquidity_rating: str
    liquidity_mechanism: str
    credit_risk_level: str
    market_risk_level: str
    dicgc_insured: bool
    dicgc_coverage_amount: Decimal
    premature_exit_penalty: str
    premature_exit_haircut_estimate: Decimal
    data_provenance: str
    as_of_date: str
    pros: List[str]
    cons: List[str]
    suitability_verdict: str


class MultiProductCompareResponse(BaseModel):
    investment_mode: str
    investment_amount: Decimal
    time_horizon_months: int
    user_tax_slab_pct: Decimal
    inflation_rate_pct: Decimal
    items: List[MultiProductCompareItem]
    top_recommendation: str
    rationale: str
    regulatory_disclaimer: str


# -----------------------------------------------------------------------------
# 3. Lump Sum vs. SIP Schemas
# -----------------------------------------------------------------------------

class LumpSumVsSipRequest(BaseModel):
    product_id: str = Field(default="nifty50_index_fund")
    lump_sum_amount: Decimal = Field(gt=Decimal("0"))
    monthly_sip_amount: Decimal = Field(gt=Decimal("0"))
    time_horizon_months: int = Field(gt=0)
    expected_annual_return_pct: Decimal = Field(default=Decimal("12.0"))
    expected_annual_inflation_pct: Decimal = Field(default=Decimal("6.0"))
    user_tax_slab_pct: Decimal = Field(default=Decimal("30.0"))


class LumpSumVsSipSchedulePoint(BaseModel):
    month: int
    lump_sum_value: Decimal
    lump_sum_invested: Decimal
    sip_value: Decimal
    sip_invested: Decimal


class LumpSumVsSipResponse(BaseModel):
    product_name: str
    time_horizon_months: int
    expected_return_pct: Decimal
    lump_sum_total_invested: Decimal
    lump_sum_gross_value: Decimal
    lump_sum_net_post_tax: Decimal
    lump_sum_real_purchasing_power: Decimal
    sip_total_invested: Decimal
    sip_gross_value: Decimal
    sip_net_post_tax: Decimal
    sip_real_purchasing_power: Decimal
    rupee_cost_averaging_verdict: str
    schedule: List[LumpSumVsSipSchedulePoint]
    recommendation: str


# -----------------------------------------------------------------------------
# 4. Goal Investment Planner Schemas
# -----------------------------------------------------------------------------

class GoalInvestmentPlanRequest(BaseModel):
    goal_name: str
    target_amount: Decimal = Field(gt=Decimal("0"))
    time_horizon_months: int = Field(gt=0)
    current_amount_allocated: Decimal = Field(default=Decimal("0.00"))
    risk_profile: str = Field(default="moderate", description="conservative, moderate, aggressive")
    expected_annual_inflation_pct: Decimal = Field(default=Decimal("6.0"))
    adjust_for_inflation: bool = True
    user_tax_slab_pct: Decimal = Field(default=Decimal("30.0"))


class GoalAllocationSlice(BaseModel):
    asset_class: str
    target_percentage: Decimal
    allocated_sip: Decimal
    allocated_lump_sum: Decimal
    suggested_product: str
    indicative_rate_pct: Decimal


class GoalInvestmentPlanResponse(BaseModel):
    goal_name: str
    nominal_target: Decimal
    inflation_adjusted_target: Decimal
    time_horizon_months: int
    current_amount_allocated: Decimal
    required_monthly_sip: Decimal
    required_lump_sum_alternative: Decimal
    expected_blended_cagr_pct: Decimal
    allocation_breakdown: List[GoalAllocationSlice]
    cash_sufficiency_notice: str
    verified_liquid_cash_available: Optional[Decimal] = None
    is_fully_funded: bool
    disclaimer: str


# -----------------------------------------------------------------------------
# 5. Stress Testing & Scenario Shock Schemas
# -----------------------------------------------------------------------------

class PortfolioStressItem(BaseModel):
    product_id: str
    amount_invested: Decimal


class InvestmentStressTestRequest(BaseModel):
    portfolio_items: List[PortfolioStressItem]
    time_horizon_months: int = Field(default=36)
    stress_scenario: str = Field(
        default="market_crash_20",
        description="market_crash_20, severe_recession_35, prolonged_stagnation, high_inflation_shock, premature_emergency_exit, paused_sip_6mo"
    )
    monthly_sip_amount: Decimal = Field(default=Decimal("0.00"))


class InvestmentStressTestResponse(BaseModel):
    stress_scenario: str
    scenario_title: str
    scenario_description: str
    total_capital_deployed: Decimal
    baseline_projected_value: Decimal
    stressed_projected_value: Decimal
    drawdown_amount: Decimal
    drawdown_pct: Decimal
    estimated_recovery_months: int
    resilience_rating: str  # High, Moderate, Vulnerable
    vulnerable_assets: List[str]
    cushioning_assets: List[str]
    safeguard_recommendations: List[str]
    disclaimer: str


# -----------------------------------------------------------------------------
# 6. Portfolio Analysis Schemas
# -----------------------------------------------------------------------------

class AssetCategorySlice(BaseModel):
    category: str
    label: str
    total_value: Decimal
    percentage: Decimal
    target_percentage: Decimal
    difference_pct: Decimal


class PortfolioAnalysisResponse(BaseModel):
    total_portfolio_value: Decimal
    categories_breakdown: List[AssetCategorySlice]
    equity_exposure_pct: Decimal
    debt_fixed_income_pct: Decimal
    liquid_cash_pct: Decimal
    gold_alternatives_pct: Decimal
    risk_profile: str
    risk_alignment_verdict: str
    concentration_risks: List[str]
    rebalancing_recommendations: List[str]
    data_source: str


# -----------------------------------------------------------------------------
# 7. Saved Comparison Scenarios Schemas (CRUD)
# -----------------------------------------------------------------------------

class InvestmentScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scenario_mode: str = Field(default="multi_product")
    notes: Optional[str] = None
    inputs: Dict[str, Any]
    results_summary: Dict[str, Any]


class InvestmentScenarioUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    results_summary: Optional[Dict[str, Any]] = None


class InvestmentScenarioResponse(BaseModel):
    id: str
    user_id: str
    name: str
    scenario_mode: str
    notes: Optional[str] = None
    inputs: Dict[str, Any]
    results_summary: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# 8. Backward-Compatible Legacy Schemas
# -----------------------------------------------------------------------------

class InvestmentOptionComparison(BaseModel):
    category: str
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
    investment_amount: Decimal = Field(gt=Decimal("0"))
    time_horizon_months: int = Field(gt=0)
    user_tax_slab_pct: Decimal = Field(default=Decimal("30.0"))
    expected_inflation_pct: Decimal = Field(default=Decimal("6.0"))
    can_lock_funds: bool = Field(default=False)
    risk_tolerance: str = Field(default="moderate")


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
