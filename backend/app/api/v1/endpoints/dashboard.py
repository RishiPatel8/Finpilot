from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.user import User
from app.models.financial import FinancialProfile, Transaction, AssetHolding, Liability, FinancialGoal
from app.models.bank import BankAccount
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
    
    # Assets, Bank Balances & Liabilities
    assets = db.query(AssetHolding).filter(AssetHolding.user_id == current_user.id).all()
    bank_accs = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()
    liabilities = db.query(Liability).filter(Liability.user_id == current_user.id).all()

    asset_total = sum(a.current_value for a in assets) if assets else Decimal("0.00")
    bank_total = sum(b.current_balance for b in bank_accs if b.current_balance > Decimal("0.00")) if bank_accs else Decimal("0.00")
    total_assets = asset_total + bank_total
    total_liabilities = sum(l.principal for l in liabilities) if liabilities else Decimal("0.00")
    net_worth = total_assets - total_liabilities

    # Transactions analysis across user's history
    all_user_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.is_internal_transfer == False
    ).order_by(Transaction.date.asc()).all()

    total_txns_count = len(all_user_txns)
    statement_coverage = None
    monthly_history = []

    # Calculate real month-by-month history
    if all_user_txns:
        min_date = all_user_txns[0].date
        max_date = all_user_txns[-1].date
        cov_days = (max_date - min_date).days + 1
        statement_coverage = {
            "start_date": str(min_date),
            "end_date": str(max_date),
            "days": cov_days,
            "coverage_months": round(cov_days / 30.0, 1),
            "total_transactions": total_txns_count
        }

        # Group by Year-Month
        month_buckets: dict = {}
        for t in all_user_txns:
            m_key = t.date.strftime("%Y-%m")
            if m_key not in month_buckets:
                month_buckets[m_key] = {"income": Decimal("0.00"), "expenses": Decimal("0.00")}
            if t.type == "income":
                month_buckets[m_key]["income"] += t.amount
            elif t.type == "expense":
                month_buckets[m_key]["expenses"] += t.amount

        # Sort chronological and take up to last 6 distinct months
        sorted_m = sorted(month_buckets.keys())[-6:]
        for m in sorted_m:
            inc = month_buckets[m]["income"]
            exp = month_buckets[m]["expenses"]
            # Convert YYYY-MM to readable label e.g. "Jan", "Feb"
            try:
                dt_obj = date.fromisoformat(f"{m}-01")
                m_label = dt_obj.strftime("%b")
            except Exception:
                m_label = m

            monthly_history.append({
                "month_key": m,
                "month": m_label,
                "income": float(inc),
                "expenses": float(exp),
                "surplus": float(inc - exp),
            })

    # Current month's transactions
    today = date.today()
    month_start = date(today.year, today.month, 1)

    income_sum = sum((t.amount for t in all_user_txns if t.type == "income" and t.date >= month_start), Decimal("0.00"))
    expense_sum = sum((t.amount for t in all_user_txns if t.type == "expense" and t.date >= month_start), Decimal("0.00"))

    # If transactions for current calendar month are 0, use observed monthly average or profile baseline
    if income_sum > Decimal("0.00"):
        monthly_income = income_sum
    elif all_user_txns:
        # Calculate average monthly income from observed transactions
        total_income = sum((t.amount for t in all_user_txns if t.type == "income"), Decimal("0.00"))
        months_span = Decimal(str(max(1.0, statement_coverage["coverage_months"]))) if statement_coverage else Decimal("1.0")
        monthly_income = (total_income / months_span).quantize(Decimal("1.00"))
    else:
        monthly_income = profile.monthly_income if profile else Decimal("0.00")

    if expense_sum > Decimal("0.00"):
        monthly_expenses = expense_sum
    elif all_user_txns:
        total_expenses = sum((t.amount for t in all_user_txns if t.type == "expense"), Decimal("0.00"))
        months_span = Decimal(str(max(1.0, statement_coverage["coverage_months"]))) if statement_coverage else Decimal("1.0")
        monthly_expenses = (total_expenses / months_span).quantize(Decimal("1.00"))
    else:
        monthly_expenses = profile.monthly_expenses if profile else Decimal("0.00")

    # Calculate liquid assets for emergency fund (liquid assets + verified bank balances)
    liquid_categories = ["liquid_mf", "cash", "fd"]
    asset_liquid = sum(a.current_value for a in assets if a.category in liquid_categories) if assets else Decimal("0.00")
    emergency_current = asset_liquid + bank_total

    target_months = profile.emergency_fund_target_months if profile else 6
    cash_flow = BudgetEngine.analyze_cash_flow(monthly_income, monthly_expenses, emergency_current, target_months=target_months)

    # Recent transactions
    recent_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc(), Transaction.created_at.desc()).limit(10).all()

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

    is_empty = (total_txns_count == 0 and total_assets == Decimal("0.00") and total_liabilities == Decimal("0.00") and monthly_income == Decimal("0.00"))
    data_quality = {
        "has_statements": total_txns_count > 0,
        "has_bank_accounts": len(bank_accs) > 0,
        "has_liabilities": len(liabilities) > 0,
        "has_assets": len(assets) > 0,
        "total_transactions": total_txns_count,
        "statement_months": statement_coverage["coverage_months"] if statement_coverage else 0.0
    }

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
        goals=goal_resps,
        monthly_history=monthly_history,
        statement_coverage=statement_coverage,
        is_empty=is_empty,
        data_quality=data_quality
    )

