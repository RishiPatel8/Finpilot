from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import FinancialProfile, Transaction, AssetHolding, Liability, FinancialGoal
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_demo_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Seeds realistic synthetic Indian personal finance demo data for the authenticated user.
    """
    # 1. Update Profile
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    if not profile:
        profile = FinancialProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.age = 29
    profile.dependents = 1
    profile.monthly_income = Decimal("145000.00")
    profile.monthly_expenses = Decimal("68000.00")
    profile.risk_tolerance = "moderate"
    profile.emergency_fund_target_months = 6
    profile.tax_regime_preference = "new"

    # 2. Clear old demo data for clean state
    db.query(Transaction).filter(Transaction.user_id == current_user.id).delete()
    db.query(AssetHolding).filter(AssetHolding.user_id == current_user.id).delete()
    db.query(Liability).filter(Liability.user_id == current_user.id).delete()
    db.query(FinancialGoal).filter(FinancialGoal.user_id == current_user.id).delete()

    # 3. Add Realistic Assets
    assets_data = [
        {"name": "Parag Parikh Liquid Fund", "category": "liquid_mf", "invested_value": Decimal("300000.00"), "current_value": Decimal("318500.00"), "expected_return_rate": Decimal("6.8"), "liquidity_days": 1},
        {"name": "HDFC High-Yield Fixed Deposit", "category": "fd", "invested_value": Decimal("200000.00"), "current_value": Decimal("214200.00"), "expected_return_rate": Decimal("7.1"), "liquidity_days": 365},
        {"name": "Nifty 50 Index Mutual Fund", "category": "equity_mf", "invested_value": Decimal("650000.00"), "current_value": Decimal("845000.00"), "expected_return_rate": Decimal("12.5"), "liquidity_days": 3},
        {"name": "Employee Provident Fund (EPF)", "category": "epf_ppf", "invested_value": Decimal("420000.00"), "current_value": Decimal("495000.00"), "expected_return_rate": Decimal("8.25"), "liquidity_days": 1825},
        {"name": "RBI Sovereign Gold Bond (SGB)", "category": "gold", "invested_value": Decimal("150000.00"), "current_value": Decimal("215000.00"), "expected_return_rate": Decimal("9.5"), "liquidity_days": 730},
    ]
    for a in assets_data:
        db.add(AssetHolding(user_id=current_user.id, **a))

    # 4. Add Realistic Liabilities
    liabilities_data = [
        {"name": "SBI Home Loan (Self-Occupied)", "principal": Decimal("3200000.00"), "interest_rate": Decimal("8.55"), "monthly_emi": Decimal("31500.00"), "tenure_months": 240, "remaining_months": 195},
        {"name": "HDFC Regalia Credit Card Balance", "principal": Decimal("24500.00"), "interest_rate": Decimal("42.0"), "monthly_emi": Decimal("24500.00"), "tenure_months": 1, "remaining_months": 1},
    ]
    for l in liabilities_data:
        db.add(Liability(user_id=current_user.id, **l))

    # 5. Add Realistic Goals
    goals_data = [
        {"name": "Emergency Reserve (6 Months)", "category": "emergency_fund", "target_amount": Decimal("450000.00"), "current_amount": Decimal("318500.00"), "target_date": date.today() + timedelta(days=180), "priority": "high"},
        {"name": "Home Down Payment Top-Up", "category": "home", "target_amount": Decimal("1500000.00"), "current_amount": Decimal("400000.00"), "target_date": date.today() + timedelta(days=730), "priority": "high"},
        {"name": "Child Higher Education", "category": "education", "target_amount": Decimal("2500000.00"), "current_amount": Decimal("350000.00"), "target_date": date.today() + timedelta(days=3650), "priority": "medium"},
    ]
    for g in goals_data:
        db.add(FinancialGoal(user_id=current_user.id, **g))

    # 6. Add Realistic Transactions (Past 30 days)
    today = date.today()
    txns_data = [
        {"date": today - timedelta(days=1), "amount": Decimal("145000.00"), "type": "income", "category": "Income", "description": "Monthly Salary Credit (Infosys)", "source": "bank_statement", "is_recurring": True},
        {"date": today - timedelta(days=2), "amount": Decimal("31500.00"), "type": "expense", "category": "Debt & EMI", "description": "SBI Home Loan Auto-Debit", "source": "bank_statement", "is_recurring": True},
        {"date": today - timedelta(days=3), "amount": Decimal("18000.00"), "type": "expense", "category": "Housing", "description": "Apartment Maintenance & Electricity", "source": "bank_statement", "is_recurring": True},
        {"date": today - timedelta(days=4), "amount": Decimal("25000.00"), "type": "expense", "category": "Investment", "description": "Monthly SIP Nifty 50 Index Fund", "source": "bank_statement", "is_recurring": True},
        {"date": today - timedelta(days=5), "amount": Decimal("4200.00"), "type": "expense", "category": "Food & Dining", "description": "Swiggy & Blinkit Groceries", "source": "manual", "is_recurring": False},
        {"date": today - timedelta(days=7), "amount": Decimal("3500.00"), "type": "expense", "category": "Transportation", "description": "Fuel & Fastag Recharge", "source": "manual", "is_recurring": False},
        {"date": today - timedelta(days=10), "amount": Decimal("5800.00"), "type": "expense", "category": "Shopping", "description": "Amazon Purchase - Home Essentials", "source": "manual", "is_recurring": False},
    ]
    for t in txns_data:
        db.add(Transaction(user_id=current_user.id, **t))

    db.commit()
    return {"status": "success", "message": "Synthetic demo data seeded successfully."}
