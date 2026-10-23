from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import FinancialProfile, AssetHolding, ScenarioRecord
from app.schemas.scenario import (
    ScenarioInput,
    ScenarioSimulationResult,
    SavedScenarioCreate,
    SavedScenarioResponse
)
from app.finance.scenarios.engine import ScenarioEngine
from app.api.deps import get_current_user, get_optional_current_user

router = APIRouter()


@router.post("/simulate", response_model=ScenarioSimulationResult)
def simulate_scenario(
    inp: ScenarioInput,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes multi-variable financial decision simulation.
    Automatically enriches parameters with authenticated user's authorized profile when available.
    """
    user_context = {}
    if current_user:
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
        if profile:
            user_context["monthly_income"] = float(profile.monthly_income)
            user_context["monthly_expenses"] = float(profile.monthly_expenses)
        
        # Calculate liquid assets for current savings
        liquid_assets = db.query(AssetHolding).filter(
            AssetHolding.user_id == current_user.id,
            AssetHolding.category.in_(["liquid_mf", "cash", "fd"])
        ).all()
        user_context["current_savings"] = float(sum(a.current_value for a in liquid_assets)) if liquid_assets else 0.0

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
