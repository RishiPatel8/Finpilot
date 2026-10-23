from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.user import User
from app.models.financial import FinancialProfile, Transaction, AssetHolding, Liability, FinancialGoal
from app.schemas.financial import DashboardSummaryResponse, TransactionResponse, FinancialGoalResponse
from app.api.deps import get_current_user
from app.finance.budget.engine import BudgetEngine

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    
    # Assets & Liabilities
    assets = db.query(AssetHolding).filter(AssetHolding.user_id == current_user.id).all()
    liabilities = db.query(Liability).filter(Liability.user_id == current_user.id).all()

    total_assets = sum(a.current_value for a in assets) if assets else Decimal("0.00")
    total_liabilities = sum(l.principal for l in liabilities) if liabilities else Decimal("0.00")
    net_worth = total_assets - total_liabilities

    # Current month's transactions
    today = date.today()
    month_start = date(today.year, today.month, 1)

    income_sum = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "income",
        Transaction.date >= month_start
    ).scalar() or Decimal("0.00")

    expense_sum = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.date >= month_start
    ).scalar() or Decimal("0.00")

    # If transactions for current month are 0, use profile baseline
    monthly_income = income_sum if income_sum > Decimal("0") else (profile.monthly_income if profile else Decimal("0.00"))
    monthly_expenses = expense_sum if expense_sum > Decimal("0") else (profile.monthly_expenses if profile else Decimal("0.00"))

    # Calculate liquid assets for emergency fund
    liquid_categories = ["liquid_mf", "cash", "fd"]
    emergency_current = sum(a.current_value for a in assets if a.category in liquid_categories) if assets else Decimal("0.00")

    target_months = profile.emergency_fund_target_months if profile else 6
    cash_flow = BudgetEngine.analyze_cash_flow(monthly_income, monthly_expenses, emergency_current, target_months=target_months)

    # Recent transactions
    recent_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc(), Transaction.created_at.desc()).limit(5).all()

    # Goals
    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == current_user.id).all()
    goal_resps = []
    for g in goals:
        prog = float(g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0.0
        goal_resps.append(FinancialGoalResponse(
            id=g.id,
            user_id=g.user_id,
            name=g.name,
            category=g.category,
            target_amount=g.target_amount,
            current_amount=g.current_amount,
            target_date=g.target_date,
            priority=g.priority,
            progress_pct=round(min(100.0, prog), 1),
            created_at=g.created_at
        ))

    return DashboardSummaryResponse(
        net_worth=net_worth,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_surplus=cash_flow["monthly_surplus"],
        savings_rate_pct=cash_flow["savings_rate_pct"],
        emergency_fund_current=emergency_current,
        emergency_fund_target=cash_flow["emergency_fund_target"],
        emergency_fund_months_covered=cash_flow["emergency_fund_months_covered"],
        recent_transactions=[TransactionResponse.model_validate(t) for t in recent_txns],
        goals=goal_resps
    )
