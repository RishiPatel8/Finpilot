from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import User
from app.models.financial import (
    FinancialProfile,
    AssetHolding,
    Liability,
    FinancialGoal,
    Transaction
)
from app.models.bank import BankAccount
from app.schemas.fire import (
    FireCalculationInput,
    FireCalculationResponse,
    FinancialHealthAssessmentResponse
)
from app.api.deps import get_current_user, get_optional_current_user
from app.finance.fire.engine import FireEngine
from app.finance.fire.health import FinancialHealthEngine

router = APIRouter()


@router.post("/calculate", response_model=FireCalculationResponse)
def calculate_fire_custom(
    inp: FireCalculationInput,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Calculates deterministic FIRE target, retirement age, required SIP,
    strategy comparisons, and multi-scenario decumulation curves.
    """
    return FireEngine.calculate_fire(inp)


@router.get("/profile", response_model=FireCalculationResponse)
def get_user_fire_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes personalized FIRE projections dynamically assembled from the
    authenticated user's financial profile, asset holdings, verified bank balances,
    and liabilities, strictly avoiding double-counting.
    """
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    assets = db.query(AssetHolding).filter(AssetHolding.user_id == current_user.id).all()
    bank_accs = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()
    liabilities = db.query(Liability).filter(Liability.user_id == current_user.id).all()

    # Calculate investable assets
    # Exclude illiquid real_estate from investable retirement assets to prevent false sense of liquidity
    investable_categories = ["liquid_mf", "bond", "fd", "equity_mf", "epf_ppf", "gold", "cash"]
    asset_val = sum(a.current_value for a in assets if a.category in investable_categories) if assets else Decimal("0.00")
    bank_val = sum(b.current_balance for b in bank_accs if b.current_balance > Decimal("0.00")) if bank_accs else Decimal("0.00")
    total_investable = asset_val + bank_val

    # Income & Expenses
    monthly_inc = profile.monthly_income if profile else Decimal("100000.00")
    monthly_exp = profile.monthly_expenses if profile else Decimal("50000.00")
    user_age = profile.age if (profile and profile.age) else 28

    # Estimate monthly investment as surplus or default 35% of income
    monthly_surplus = max(Decimal("0.00"), monthly_inc - monthly_exp)
    monthly_inv = monthly_surplus if monthly_surplus > Decimal("0.00") else (monthly_inc * Decimal("0.35"))

    inp = FireCalculationInput(
        current_age=user_age,
        retirement_age=50,
        life_expectancy_age=85,
        monthly_expenses=monthly_exp,
        essential_expenses_pct=Decimal("70.00"),
        monthly_income=monthly_inc,
        current_investable_assets=total_investable if total_investable > Decimal("0.00") else Decimal("500000.00"),
        monthly_investment=monthly_inv,
        expected_annual_inflation_pct=Decimal("6.00"),
        expected_nominal_return_pct=Decimal("11.00"),
        post_retirement_return_pct=Decimal("8.00"),
        withdrawal_rate_pct=Decimal("3.50"),
        other_retirement_monthly_income=Decimal("0.00"),
        include_primary_residence=False
    )
    return FireEngine.calculate_fire(inp)


@router.get("/health-assessment", response_model=FinancialHealthAssessmentResponse)
def get_user_financial_health_assessment(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a comprehensive 8-pillar financial health assessment with scoring,
    benchmarking, status labels, and a 12-month prioritized actionable checklist.
    Supports authenticated users and guest mode with representative baselines.
    """
    if current_user:
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
        assets = db.query(AssetHolding).filter(AssetHolding.user_id == current_user.id).all()
        bank_accs = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()
        liabilities = db.query(Liability).filter(Liability.user_id == current_user.id).all()
        goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == current_user.id).all()

        # Liquid assets (cash, savings bank accounts, liquid mutual funds, short FDs)
        liquid_cats = ["liquid_mf", "cash", "fd"]
        liquid_asset_sum = sum(a.current_value for a in assets if a.category in liquid_cats) if assets else Decimal("0.00")
        bank_sum = sum(b.current_balance for b in bank_accs if b.current_balance > Decimal("0.00")) if bank_accs else Decimal("0.00")
        total_liquid = liquid_asset_sum + bank_sum

        # All investable assets
        investable_cats = ["liquid_mf", "bond", "fd", "equity_mf", "epf_ppf", "gold", "cash"]
        investable_sum = (sum(a.current_value for a in assets if a.category in investable_cats) if assets else Decimal("0.00")) + bank_sum

        # Debts & EMIs
        total_debt_principal = sum(l.principal for l in liabilities) if liabilities else Decimal("0.00")
        total_monthly_emi = sum(l.monthly_emi for l in liabilities) if liabilities else Decimal("0.00")

        # Goals tracking
        if goals:
            on_track_count = sum(1 for g in goals if (g.current_amount >= g.target_amount * Decimal("0.80")))
            goals_on_track_pct = float((on_track_count / len(goals)) * 100.0)
        else:
            goals_on_track_pct = 75.0

        # Profile baselines
        user_age = profile.age if (profile and profile.age) else 30
        monthly_inc = profile.monthly_income if profile else Decimal("100000.00")
        monthly_exp = profile.monthly_expenses if profile else Decimal("50000.00")
        emergency_target_months = profile.emergency_fund_target_months if profile else 6
    else:
        # Guest baseline demonstration
        user_age = 29
        monthly_inc = Decimal("145000.00")
        monthly_exp = Decimal("68000.00")
        total_liquid = Decimal("318500.00")
        investable_sum = Decimal("2095000.00")
        total_debt_principal = Decimal("250000.00")
        total_monthly_emi = Decimal("15000.00")
        goals_on_track_pct = 80.0
        emergency_target_months = 6

    # Quick FIRE baseline calculation for progress %
    annual_exp = monthly_exp * Decimal("12.0")
    fire_target_today = (annual_exp / Decimal("0.035")) if annual_exp > Decimal("0.00") else Decimal("15000000.00")
    fire_prog_pct = float(round((investable_sum / fire_target_today * Decimal("100.0")), 1)) if fire_target_today > Decimal("0.00") else 0.0

    fire_res = FireEngine.calculate_fire(FireCalculationInput(
        current_age=user_age or 30,
        retirement_age=50,
        monthly_expenses=monthly_exp if monthly_exp > Decimal("0.00") else Decimal("50000.00"),
        monthly_income=monthly_inc if monthly_inc > Decimal("0.00") else Decimal("100000.00"),
        current_investable_assets=investable_sum,
        monthly_investment=max(Decimal("0.00"), monthly_inc - monthly_exp)
    ))
    fire_shortfall = fire_res.portfolio_surplus_or_shortfall if fire_res.portfolio_surplus_or_shortfall < Decimal("0.00") else Decimal("0.00")

    return FinancialHealthEngine.assess_health(
        age=user_age,
        monthly_income=monthly_inc,
        monthly_expenses=monthly_exp,
        liquid_assets=total_liquid,
        investable_assets=investable_sum,
        total_debt_principal=total_debt_principal,
        total_monthly_emi=total_monthly_emi,
        goals_on_track_pct=goals_on_track_pct,
        fire_progress_pct=fire_prog_pct,
        fire_shortfall=abs(fire_shortfall),
        target_emergency_months=emergency_target_months
    )
