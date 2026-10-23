from typing import List
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import FinancialGoal
from app.schemas.financial import FinancialGoalCreate, FinancialGoalResponse
from app.schemas.investment import GoalProjectionRequest, GoalProjectionResponse
from app.finance.investments.engine import InvestmentEngine
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[FinancialGoalResponse])
def get_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == current_user.id).order_by(FinancialGoal.target_date.asc()).all()
    results = []
    today = date.today()

    for g in goals:
        # Calculate months remaining
        months_left = max(1, (g.target_date.year - today.year) * 12 + (g.target_date.month - today.month))
        proj = InvestmentEngine.project_goal(GoalProjectionRequest(
            goal_name=g.name,
            target_amount=g.target_amount,
            current_amount=g.current_amount,
            time_horizon_months=months_left,
            adjust_for_inflation=False
        ))
        progress = float((g.current_amount / g.target_amount * 100)) if g.target_amount > 0 else 0.0

        resp = FinancialGoalResponse(
            id=g.id,
            user_id=g.user_id,
            name=g.name,
            category=g.category,
            target_amount=g.target_amount,
            current_amount=g.current_amount,
            target_date=g.target_date,
            priority=g.priority,
            monthly_required=proj.required_monthly_sip,
            progress_pct=round(min(100.0, progress), 1),
            created_at=g.created_at
        )
        results.append(resp)

    return results


@router.post("", response_model=FinancialGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_in: FinancialGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    g = FinancialGoal(
        user_id=current_user.id,
        name=goal_in.name,
        category=goal_in.category,
        target_amount=goal_in.target_amount,
        current_amount=goal_in.current_amount,
        target_date=goal_in.target_date,
        priority=goal_in.priority
    )
    db.add(g)
    db.commit()
    db.refresh(g)

    today = date.today()
    months_left = max(1, (g.target_date.year - today.year) * 12 + (g.target_date.month - today.month))
    proj = InvestmentEngine.project_goal(GoalProjectionRequest(
        goal_name=g.name,
        target_amount=g.target_amount,
        current_amount=g.current_amount,
        time_horizon_months=months_left,
        adjust_for_inflation=False
    ))
    progress = float((g.current_amount / g.target_amount * 100)) if g.target_amount > 0 else 0.0

    return FinancialGoalResponse(
        id=g.id,
        user_id=g.user_id,
        name=g.name,
        category=g.category,
        target_amount=g.target_amount,
        current_amount=g.current_amount,
        target_date=g.target_date,
        priority=g.priority,
        monthly_required=proj.required_monthly_sip,
        progress_pct=round(min(100.0, progress), 1),
        created_at=g.created_at
    )


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    goal = db.query(FinancialGoal).filter(FinancialGoal.id == goal_id, FinancialGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    db.delete(goal)
    db.commit()


@router.post("/project", response_model=GoalProjectionResponse)
def project_goal(req: GoalProjectionRequest):
    return InvestmentEngine.project_goal(req)
