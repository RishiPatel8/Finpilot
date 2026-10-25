from typing import List, Optional, Union, Dict, Any
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.financial import InvestmentScenario, StatementImportBatch, AssetHolding
from app.api.deps import get_current_user, get_optional_current_user
from app.schemas.investment import (
    InvestmentCompareRequest,
    InvestmentCompareResponse,
    MultiProductCompareRequest,
    MultiProductCompareResponse,
    InvestmentProductSummary,
    LumpSumVsSipRequest,
    LumpSumVsSipResponse,
    GoalInvestmentPlanRequest,
    GoalInvestmentPlanResponse,
    InvestmentStressTestRequest,
    InvestmentStressTestResponse,
    PortfolioAnalysisResponse,
    InvestmentScenarioCreate,
    InvestmentScenarioUpdate,
    InvestmentScenarioResponse,
)
from app.finance.investments.engine import InvestmentEngine
from app.finance.investments.data import (
    get_all_products,
    filter_products,
    get_product_by_id
)

router = APIRouter()


# -----------------------------------------------------------------------------
# 1. Product Catalog & Registry
# -----------------------------------------------------------------------------
@router.get("/products", response_model=List[InvestmentProductSummary])
def list_investment_products(
    category: str = Query("all", description="Filter by category: liquid, fixed_income, small_savings, equity, alternatives, all"),
    only_guaranteed: bool = Query(False, description="Filter only statutory/capital-guaranteed products"),
    max_lock_in_months: int = Query(999, description="Maximum lock-in duration allowed in months")
):
    """
    Returns verified statutory Indian investment products catalog.
    Provenance derived from RBI, SEBI, AMFI, and Ministry of Finance gazettes.
    """
    products = filter_products(
        category=category,
        only_guaranteed=only_guaranteed,
        max_lock_in_months=max_lock_in_months
    )
    return [InvestmentProductSummary(**p) for p in products]


# -----------------------------------------------------------------------------
# 2. Comparison Endpoints (Dual: Multi-Product Matrix & Backward Compatible)
# -----------------------------------------------------------------------------
@router.post("/compare")
def compare_investments(
    req: Union[MultiProductCompareRequest, InvestmentCompareRequest]
):
    """
    Unified comparison endpoint:
    - If `selected_product_ids` is provided: executes MultiProductCompare engine with post-tax calculations under Finance Act 2024.
    - If legacy payload without `selected_product_ids`: executes legacy 3-way liquid/bond/fd comparison.
    """
    if hasattr(req, "selected_product_ids") and req.selected_product_ids:
        return InvestmentEngine.compare_multi_products(req)
    else:
        # Fallback to legacy schema
        if not isinstance(req, InvestmentCompareRequest):
            # Parse into InvestmentCompareRequest
            req = InvestmentCompareRequest(
                investment_amount=req.investment_amount,
                time_horizon_months=req.time_horizon_months,
                user_tax_slab_pct=getattr(req, "user_tax_slab_pct", Decimal("30.0")),
                expected_inflation_pct=getattr(req, "expected_inflation_pct", Decimal("6.0")),
                can_lock_funds=getattr(req, "can_lock_funds", False),
            )
        return InvestmentEngine.compare_instruments(req)


@router.post("/multi-compare", response_model=MultiProductCompareResponse)
def compare_multiple_products(req: MultiProductCompareRequest):
    """
    Statutory multi-product comparison across 1 to 6 selected Indian instruments.
    Accounts for compounding frequency, Finance Act 2024 capital gains, TER, and DICGC coverage.
    """
    return InvestmentEngine.compare_multi_products(req)


# -----------------------------------------------------------------------------
# 3. Lump Sum vs. SIP Analysis
# -----------------------------------------------------------------------------
@router.post("/lumpsum-vs-sip", response_model=LumpSumVsSipResponse)
def compare_lumpsum_and_sip(req: LumpSumVsSipRequest):
    """
    Compares lump sum deployment vs Systematic Investment Plan (SIP) over target tenure.
    Provides Rupee-Cost Averaging evaluation and month-by-month trajectory points.
    """
    return InvestmentEngine.compare_lumpsum_vs_sip(req)


# -----------------------------------------------------------------------------
# 4. Goal-Based Investment Planner
# -----------------------------------------------------------------------------
@router.post("/goal-plan", response_model=GoalInvestmentPlanResponse)
def plan_goal(
    req: GoalInvestmentPlanRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates asset-allocated investment plan (Equity / Debt / Gold) for financial milestone.
    Cross-checks liquid balances from verified bank records to prevent double-counting or emergency fund depletion.
    """
    liquid_cash: Optional[Decimal] = None

    if current_user:
        # Compute verified liquid balance from statement batches or liquid assets
        latest_batch = (
            db.query(StatementImportBatch)
            .filter(StatementImportBatch.user_id == current_user.id)
            .order_by(StatementImportBatch.id.desc())
            .first()
        )
        if latest_batch and latest_batch.closing_balance is not None:
            liquid_cash = Decimal(str(latest_batch.closing_balance))
        else:
            # Check liquid holdings
            liquid_holdings = (
                db.query(AssetHolding)
                .filter(AssetHolding.user_id == current_user.id, AssetHolding.category.in_(["liquid_mf", "cash"]))
                .all()
            )
            if liquid_holdings:
                liquid_cash = sum((Decimal(str(h.current_value)) for h in liquid_holdings), Decimal("0.00"))

    return InvestmentEngine.plan_goal_investment(req, verified_liquid_cash=liquid_cash)


# -----------------------------------------------------------------------------
# 5. Stress Testing & Scenario Shock
# -----------------------------------------------------------------------------
@router.post("/stress-test", response_model=InvestmentStressTestResponse)
def stress_test_investments(req: InvestmentStressTestRequest):
    """
    Simulates portfolio resilience against 6 macro shock scenarios:
    Market crash (-20%), Severe bear market (-35%), Stagnation, Inflation shock (9.5%), Premature exit, Paused SIP.
    """
    return InvestmentEngine.stress_test_portfolio(req)


# -----------------------------------------------------------------------------
# 6. Existing Portfolio Analysis
# -----------------------------------------------------------------------------
@router.get("/portfolio-analysis", response_model=PortfolioAnalysisResponse)
def analyze_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyzes authenticated user's real AssetHolding records.
    Computes equity/debt/cash/gold allocation vs target benchmarks, detects concentration risks, and provides rebalancing steps.
    """
    return InvestmentEngine.analyze_existing_portfolio(db, current_user.id)


# -----------------------------------------------------------------------------
# 7. Saved Comparison Scenarios CRUD (Authenticated)
# -----------------------------------------------------------------------------
@router.get("/scenarios", response_model=List[InvestmentScenarioResponse])
def get_user_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists all saved investment comparison scenarios for the authenticated user.
    """
    scenarios = (
        db.query(InvestmentScenario)
        .filter(InvestmentScenario.user_id == current_user.id)
        .order_by(InvestmentScenario.updated_at.desc())
        .all()
    )
    return scenarios


@router.post("/scenarios", response_model=InvestmentScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_user_scenario(
    payload: InvestmentScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves an investment planning/comparison scenario under user's profile.
    Explicitly stored as a hypothetical scenario, NOT an actual trade or purchase.
    """
    scenario = InvestmentScenario(
        user_id=current_user.id,
        name=payload.name,
        scenario_mode=payload.scenario_mode,
        notes=payload.notes,
        inputs=payload.inputs,
        results_summary=payload.results_summary,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.put("/scenarios/{scenario_id}", response_model=InvestmentScenarioResponse)
def update_user_scenario(
    scenario_id: str,
    payload: InvestmentScenarioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates an existing saved scenario (rename, update notes, or update inputs).
    """
    scenario = (
        db.query(InvestmentScenario)
        .filter(InvestmentScenario.id == scenario_id, InvestmentScenario.user_id == current_user.id)
        .first()
    )
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")

    if payload.name is not None:
        scenario.name = payload.name
    if payload.notes is not None:
        scenario.notes = payload.notes
    if payload.inputs is not None:
        scenario.inputs = payload.inputs
    if payload.results_summary is not None:
        scenario.results_summary = payload.results_summary

    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_200_OK)
def delete_user_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes a saved scenario belonging to the authenticated user.
    """
    scenario = (
        db.query(InvestmentScenario)
        .filter(InvestmentScenario.id == scenario_id, InvestmentScenario.user_id == current_user.id)
        .first()
    )
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")

    db.delete(scenario)
    db.commit()
    return {"status": "deleted", "id": scenario_id}
