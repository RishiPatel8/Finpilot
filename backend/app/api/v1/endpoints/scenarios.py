from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import (
    FinancialProfile,
    AssetHolding,
    ScenarioRecord,
    Liability,
    RecurringTransaction,
    Transaction
)
from app.models.bank import BankAccount
from app.schemas.scenario import (
    ScenarioInput,
    ScenarioSimulationResult,
    ScenarioBaselineResponse,
    SavedScenarioCreate,
    SavedScenarioUpdate,
    SavedScenarioResponse
)
from app.finance.scenarios.engine import ScenarioEngine
from app.api.deps import get_current_user, get_optional_current_user

router = APIRouter()


@router.get("/baseline", response_model=ScenarioBaselineResponse)
def get_scenario_baseline(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the authenticated user's verified financial baseline from database records.
    Returns honest empty/unverified state if user is unauthenticated or has zero records.
    """
    if not current_user:
        return ScenarioBaselineResponse(
            monthly_income=0.0,
            essential_expenses=0.0,
            discretionary_expenses=0.0,
            total_monthly_expenses=0.0,
            existing_monthly_emi=0.0,
            existing_recurring_commitments=0.0,
            available_monthly_surplus=0.0,
            liquid_savings=0.0,
            emergency_fund_target_months=6.0,
            emergency_fund_target_amount=0.0,
            emergency_runway_months=0.0,
            total_debt=0.0,
            data_sources={},
            is_verified_data=False,
            data_completeness_pct=0,
            missing_fields=[
                "User not logged in",
                "No bank accounts linked",
                "No statement data uploaded"
            ]
        )

    # 1. Profile Data
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    income = float(profile.monthly_income) if profile and profile.monthly_income else 0.0
    expenses = float(profile.monthly_expenses) if profile and profile.monthly_expenses else 0.0
    target_months = float(profile.emergency_fund_target_months) if profile and profile.emergency_fund_target_months else 6.0

    # 2. Bank Accounts & Liquid Assets
    bank_accs = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()
    bank_total = sum(float(b.current_balance or 0.0) for b in bank_accs)

    liquid_holdings = db.query(AssetHolding).filter(
        AssetHolding.user_id == current_user.id,
        AssetHolding.category.in_(["liquid_mf", "cash", "fd"])
    ).all()
    liquid_holdings_total = sum(float(h.current_value or 0.0) for h in liquid_holdings)
    total_liquid_savings = bank_total + liquid_holdings_total

    # 3. Liabilities & EMIs
    liabilities = db.query(Liability).filter(Liability.user_id == current_user.id).all()
    total_debt = sum(float(l.principal or 0.0) for l in liabilities)
    total_monthly_emi = sum(float(l.monthly_emi or 0.0) for l in liabilities)

    # 4. Recurring Commitments
    recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == current_user.id,
        RecurringTransaction.status == "confirmed",
        RecurringTransaction.transaction_type == "expense"
    ).all()
    total_recurring = sum(float(r.amount or 0.0) for r in recurring)

    # 5. Transaction History Check (Essential vs Discretionary)
    ninety_days_ago = date.today() - timedelta(days=90)
    txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= ninety_days_ago,
        Transaction.is_internal_transfer == False
    ).all()

    essential_cats = {"Groceries", "Rent", "Utilities", "Healthcare", "Insurance", "Education", "Bills"}
    essential_sum = 0.0
    discretionary_sum = 0.0

    for t in txns:
        if t.type == "expense" or getattr(t, "raw_type", None) == "debit":
            amt = float(t.amount or 0.0)
            if t.category in essential_cats:
                essential_sum += amt
            else:
                discretionary_sum += amt

    # If transactions exist, normalize to monthly
    if txns:
        essential_expenses = round(essential_sum / 3.0, 2)
        discretionary_expenses = round(discretionary_sum / 3.0, 2)
        if expenses == 0.0:
            expenses = round(essential_expenses + discretionary_expenses, 2)
    else:
        essential_expenses = round(expenses * 0.65, 2)
        discretionary_expenses = round(expenses * 0.35, 2)

    available_surplus = max(0.0, income - expenses - total_monthly_emi - total_recurring)
    emergency_target_amt = round(essential_expenses * target_months, 2)
    emergency_runway = round(total_liquid_savings / expenses, 1) if expenses > 0 else 0.0

    data_sources = {}
    missing_fields = []
    points = 0

    if income > 0:
        data_sources["income"] = f"Financial Profile (₹{income:,.0f}/mo)"
        points += 25
    else:
        missing_fields.append("Monthly net income not recorded")

    if expenses > 0:
        data_sources["expenses"] = f"{'Bank Statements' if txns else 'Financial Profile'} (₹{expenses:,.0f}/mo)"
        points += 25
    else:
        missing_fields.append("Monthly living expenses not recorded")

    if total_liquid_savings > 0 or bank_accs:
        bank_names = ", ".join(set(b.institution_name for b in bank_accs)) if bank_accs else "Asset Holdings"
        data_sources["savings"] = f"{bank_names} (₹{total_liquid_savings:,.0f})"
        points += 25
    else:
        missing_fields.append("No bank accounts or liquid savings connected")

    if liabilities:
        data_sources["liabilities"] = f"{len(liabilities)} Active Loans (₹{total_monthly_emi:,.0f}/mo EMI)"
        points += 25
    else:
        data_sources["liabilities"] = "Zero recorded loan liabilities"
        points += 25

    is_verified = bool(points >= 50 and (bank_total > 0 or txns or (profile and profile.monthly_income > 0)))

    return ScenarioBaselineResponse(
        monthly_income=income,
        essential_expenses=essential_expenses,
        discretionary_expenses=discretionary_expenses,
        total_monthly_expenses=expenses,
        existing_monthly_emi=total_monthly_emi,
        existing_recurring_commitments=total_recurring,
        available_monthly_surplus=available_surplus,
        liquid_savings=total_liquid_savings,
        emergency_fund_target_months=target_months,
        emergency_fund_target_amount=emergency_target_amt,
        emergency_runway_months=emergency_runway,
        total_debt=total_debt,
        data_sources=data_sources,
        is_verified_data=is_verified,
        data_completeness_pct=points,
        missing_fields=missing_fields
    )


@router.post("/simulate", response_model=ScenarioSimulationResult)
def simulate_scenario(
    inp: ScenarioInput,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes multi-variable financial decision simulation.
    Automatically enriches parameters with authenticated user's authorized profile, bank accounts,
    and liabilities when available.
    """
    user_context = {}
    if current_user:
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
        if profile:
            user_context["monthly_income"] = float(profile.monthly_income or 0.0)
            user_context["monthly_expenses"] = float(profile.monthly_expenses or 0.0)
            user_context["emergency_fund_target_months"] = float(profile.emergency_fund_target_months or 6.0)

        # Calculate liquid assets from holdings and verified bank accounts
        liquid_assets = db.query(AssetHolding).filter(
            AssetHolding.user_id == current_user.id,
            AssetHolding.category.in_(["liquid_mf", "cash", "fd"])
        ).all()
        bank_accs = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()

        holding_total = sum(float(a.current_value or 0.0) for a in liquid_assets)
        bank_total = sum(float(b.current_balance or 0.0) for b in bank_accs)
        user_context["current_savings"] = holding_total + bank_total

        # Liabilities
        liabilities = db.query(Liability).filter(Liability.user_id == current_user.id).all()
        user_context["monthly_emi"] = sum(float(l.monthly_emi or 0.0) for l in liabilities)

        # Recurring
        recurring = db.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == current_user.id,
            RecurringTransaction.status == "confirmed",
            RecurringTransaction.transaction_type == "expense"
        ).all()
        user_context["recurring_monthly_expenses"] = sum(float(r.amount or 0.0) for r in recurring)

    result = ScenarioEngine.simulate(inp, user_context)
    return result


@router.post("/save", response_model=SavedScenarioResponse, status_code=status.HTTP_201_CREATED)
def save_scenario(
    req: SavedScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves an authorized financial simulation to the user's account history.
    """
    record = ScenarioRecord(
        user_id=current_user.id,
        title=req.title,
        scenario_type=req.scenario_type,
        input_data=req.input_data,
        result_data=req.result_data
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return SavedScenarioResponse(
        id=record.id,
        user_id=record.user_id,
        title=record.title,
        scenario_type=record.scenario_type,
        input_data=record.input_data,
        result_data=record.result_data,
        created_at=record.created_at.isoformat()
    )


@router.get("", response_model=List[SavedScenarioResponse])
def get_saved_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all scenarios saved by the authenticated user.
    """
    records = db.query(ScenarioRecord).filter(
        ScenarioRecord.user_id == current_user.id
    ).order_by(ScenarioRecord.created_at.desc()).all()

    return [
        SavedScenarioResponse(
            id=r.id,
            user_id=r.user_id,
            title=r.title,
            scenario_type=r.scenario_type,
            input_data=r.input_data,
            result_data=r.result_data,
            created_at=r.created_at.isoformat()
        )
        for r in records
    ]


@router.get("/{scenario_id}", response_model=SavedScenarioResponse)
def get_saved_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a single saved scenario by ID for reopening.
    """
    record = db.query(ScenarioRecord).filter(
        ScenarioRecord.id == scenario_id,
        ScenarioRecord.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario record not found")

    return SavedScenarioResponse(
        id=record.id,
        user_id=record.user_id,
        title=record.title,
        scenario_type=record.scenario_type,
        input_data=record.input_data,
        result_data=record.result_data,
        created_at=record.created_at.isoformat()
    )


@router.put("/{scenario_id}", response_model=SavedScenarioResponse)
def update_saved_scenario(
    scenario_id: str,
    req: SavedScenarioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Renames or updates an existing saved scenario.
    """
    record = db.query(ScenarioRecord).filter(
        ScenarioRecord.id == scenario_id,
        ScenarioRecord.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario record not found")

    if req.title is not None:
        record.title = req.title
    if req.input_data is not None:
        record.input_data = req.input_data
    if req.result_data is not None:
        record.result_data = req.result_data

    db.commit()
    db.refresh(record)

    return SavedScenarioResponse(
        id=record.id,
        user_id=record.user_id,
        title=record.title,
        scenario_type=record.scenario_type,
        input_data=record.input_data,
        result_data=record.result_data,
        created_at=record.created_at.isoformat()
    )


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(ScenarioRecord).filter(
        ScenarioRecord.id == scenario_id,
        ScenarioRecord.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario record not found")
    db.delete(record)
    db.commit()
