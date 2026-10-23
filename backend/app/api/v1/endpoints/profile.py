from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import FinancialProfile
from app.schemas.financial import FinancialProfileResponse, FinancialProfileUpdate
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=FinancialProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    if not profile:
        profile = FinancialProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return FinancialProfileResponse.model_validate(profile)


@router.put("", response_model=FinancialProfileResponse)
def update_profile(
    profile_in: FinancialProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    if not profile:
        profile = FinancialProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return FinancialProfileResponse.model_validate(profile)
