from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.finance.intelligence.engine import IntelligenceEngine
from app.schemas.intelligence import (
    CanonicalFinancialSnapshot,
    RecurringTransactionPattern,
    SpendingAnomaly,
    CashFlowForecast,
    AdaptiveBudgetRecommendation,
    GoalFeasibility,
    IntelligenceFeedResponse,
    CategorizationPreviewRequest,
    CategorizationPreviewResponse
)

router = APIRouter()


@router.get("/snapshot", response_model=CanonicalFinancialSnapshot)
def get_canonical_snapshot(
    period: str = Query("current_month", pattern="^(current_month|last_30_days|last_month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns user-scoped, verified canonical financial snapshot
    aggregating income, expenses, category spending, liquid savings, and net worth.
    """
    return IntelligenceEngine.get_canonical_snapshot(current_user, db, period=period)


@router.get("/feed", response_model=IntelligenceFeedResponse)
def get_intelligence_feed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns prioritized, deduplicated financial insights across anomalies,
    budget limits, upcoming recurring commitments, and savings milestones.
    """
    return IntelligenceEngine.generate_intelligence_feed(current_user, db)


@router.get("/recurring", response_model=List[RecurringTransactionPattern])
def get_recurring_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detects recurring transaction patterns (EMIs, rent, utilities, subscriptions).
    """
    return IntelligenceEngine.detect_recurring_transactions(current_user, db)


@router.get("/anomalies", response_model=List[SpendingAnomaly])
def get_spending_anomalies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detects categories with abnormal spending surges compared to prior moving baselines.
    """
    return IntelligenceEngine.detect_spending_anomalies(current_user, db)


@router.get("/forecast", response_model=CashFlowForecast)
def get_cash_flow_forecast(
    horizon_days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Projects upcoming 30/90-day cash flow based on confirmed income run-rate
    and known recurring commitments.
    """
    return IntelligenceEngine.forecast_cash_flow(current_user, db, horizon_days=horizon_days)


@router.get("/budget-recommendations", response_model=List[AdaptiveBudgetRecommendation])
def get_budget_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns adaptive budget ceiling recommendations aligned with the 50-30-20 framework.
    """
    return IntelligenceEngine.compute_adaptive_budget_recommendations(current_user, db)


@router.get("/goals-feasibility", response_model=List[GoalFeasibility])
def get_goals_feasibility(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assesses goal timelines against active monthly cash flow surplus, identifying delays and sensitivity levers.
    """
    return IntelligenceEngine.assess_goals_feasibility(current_user, db)


@router.post("/categorize", response_model=CategorizationPreviewResponse)
def preview_categorization(
    req: CategorizationPreviewRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Deterministically classifies a transaction description into an Indian financial category.
    """
    return IntelligenceEngine.preview_categorization(req.description)
