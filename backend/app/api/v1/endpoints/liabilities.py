from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import Liability
from app.schemas.financial import (
    LiabilityCreate,
    LiabilityResponse,
    DebtRepaymentPlanRequest,
    DebtRepaymentPlanResponse,
)
from app.finance.budget.engine import BudgetEngine
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[LiabilityResponse])
def get_liabilities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all debts and liabilities for the authenticated user.
    """
    liabilities = db.query(Liability).filter(
        Liability.user_id == current_user.id
    ).order_by(Liability.interest_rate.desc()).all()
    return [LiabilityResponse.model_validate(l) for l in liabilities]


@router.post("", response_model=LiabilityResponse, status_code=status.HTTP_201_CREATED)
def create_liability(
    liability_in: LiabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new debt or liability record (e.g. Home Loan, Credit Card, Vehicle Loan).
    """
    liability = Liability(
        user_id=current_user.id,
        name=liability_in.name,
        principal=liability_in.principal,
        interest_rate=liability_in.interest_rate,
        monthly_emi=liability_in.monthly_emi,
        tenure_months=liability_in.tenure_months,
        remaining_months=liability_in.remaining_months,
    )
    db.add(liability)
    db.commit()
    db.refresh(liability)
    return LiabilityResponse.model_validate(liability)


@router.delete("/{liability_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_liability(
    liability_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a liability record belonging to the authenticated user.
    """
    liability = db.query(Liability).filter(
        Liability.id == liability_id,
        Liability.user_id == current_user.id
    ).first()
    if not liability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liability record not found")
    db.delete(liability)
    db.commit()


@router.post("/repayment-plan", response_model=DebtRepaymentPlanResponse)
def calculate_repayment_plan(
    req: DebtRepaymentPlanRequest = DebtRepaymentPlanRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculates deterministic Debt Avalanche vs Debt Snowball repayment strategies
    for the authenticated user's active liabilities.
    """
    liabilities = db.query(Liability).filter(Liability.user_id == current_user.id).all()
    debt_items = [
        {
            "name": l.name,
            "principal": l.principal,
            "interest_rate": l.interest_rate,
            "monthly_emi": l.monthly_emi,
            "tenure_months": l.tenure_months,
            "remaining_months": l.remaining_months,
        }
        for l in liabilities
    ]
    result = BudgetEngine.debt_repayment_plan(debt_items, extra_monthly_payment=req.extra_monthly_payment)
    return DebtRepaymentPlanResponse(**result)
