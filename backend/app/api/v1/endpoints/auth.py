from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import FinancialProfile
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    FirebaseLoginRequest,
    LinkAccountRequest
)
from app.core.security import hash_password, verify_password, create_access_token
from app.core.firebase import verify_firebase_id_token
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password) if user_in.password else None,
        full_name=user_in.full_name,
        role=user_in.role,
        auth_provider="local"
    )
    db.add(user)
    db.flush()

    # Create empty financial profile
    profile = FinancialProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not user.hashed_password or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    token = create_access_token(subject=user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/firebase-login", response_model=Token)
def firebase_login(req: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """
    Verifies Firebase ID token server-side and maps Firebase UID to FinPilot user record.
    Enforces explicit account linking when email matches an existing local password user.
    """
    try:
        decoded = verify_firebase_id_token(req.id_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    firebase_uid = decoded.get("uid")
    email = decoded.get("email")
    name = decoded.get("name") or email.split("@")[0]

    if not firebase_uid or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firebase token missing required claims (uid or email)."
        )

    # 1. Lookup by Firebase UID
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user:
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        token = create_access_token(subject=user.id)
        return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))

    # 2. Check if user with this email already exists
    existing_email_user = db.query(User).filter(User.email == email).first()
    if existing_email_user:
        # Explicit Account Linking Enforcement:
        # Do not automatically merge accounts solely because emails match. Require password verification.
        if existing_email_user.hashed_password:
            if not req.link_password:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists. Please provide your existing password to link your Google/Firebase account."
                )
            if not verify_password(req.link_password, existing_email_user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid password. Cannot link Firebase account."
                )
        
        # Link verified
        existing_email_user.firebase_uid = firebase_uid
        existing_email_user.auth_provider = "linked"
        db.commit()
        db.refresh(existing_email_user)
        token = create_access_token(subject=existing_email_user.id)
        return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(existing_email_user))

    # 3. New User creation via Firebase
    new_user = User(
        email=email,
        full_name=name,
        firebase_uid=firebase_uid,
        auth_provider="firebase_google",
        role=req.role or "salaried",
        hashed_password=None
    )
    db.add(new_user)
    db.flush()

    # Create empty financial profile
    profile = FinancialProfile(user_id=new_user.id)
    db.add(profile)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(subject=new_user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post("/link-firebase", response_model=UserResponse)
def link_firebase_account(
    req: LinkAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows an authenticated user to link their Firebase Google account.
    """
    if current_user.hashed_password and not verify_password(req.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password verification."
        )

    try:
        decoded = verify_firebase_id_token(req.id_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    firebase_uid = decoded.get("uid")
    # Verify no other account has this firebase_uid
    existing_link = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if existing_link and existing_link.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This Firebase account is already linked to another FinPilot profile."
        )

    current_user.firebase_uid = firebase_uid
    current_user.auth_provider = "linked"
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.get("/export-data")
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exports all personal and financial data owned by the authenticated user
    in structured JSON format for user data portability and privacy compliance.
    """
    profile_data = None
    if current_user.profile:
        profile_data = {
            "age": current_user.profile.age,
            "dependents": current_user.profile.dependents,
            "monthly_income": float(current_user.profile.monthly_income),
            "monthly_expenses": float(current_user.profile.monthly_expenses),
            "risk_tolerance": current_user.profile.risk_tolerance,
            "emergency_fund_target_months": current_user.profile.emergency_fund_target_months,
            "tax_regime_preference": current_user.profile.tax_regime_preference,
        }

    transactions_data = [
        {
            "id": t.id,
            "date": t.date.isoformat(),
            "amount": float(t.amount),
            "type": t.type,
            "category": t.category,
            "description": t.description,
            "source": t.source,
            "is_recurring": t.is_recurring,
        }
        for t in current_user.transactions
    ]

    liabilities_data = [
        {
            "id": l.id,
            "name": l.name,
            "principal": float(l.principal),
            "interest_rate": float(l.interest_rate),
            "monthly_emi": float(l.monthly_emi),
            "tenure_months": l.tenure_months,
            "remaining_months": l.remaining_months,
        }
        for l in current_user.liabilities
    ]

    assets_data = [
        {
            "id": a.id,
            "name": a.name,
            "category": a.category,
            "invested_value": float(a.invested_value),
            "current_value": float(a.current_value),
            "expected_return_rate": float(a.expected_return_rate),
            "liquidity_days": a.liquidity_days,
        }
        for a in current_user.assets
    ]

    goals_data = [
        {
            "id": g.id,
            "name": g.name,
            "category": g.category,
            "target_amount": float(g.target_amount),
            "current_amount": float(g.current_amount),
            "target_date": g.target_date.isoformat(),
            "priority": g.priority,
        }
        for g in current_user.goals
    ]

    scenarios_data = [
        {
            "id": s.id,
            "title": s.title,
            "scenario_type": s.scenario_type,
            "input_data": s.input_data,
            "result_data": s.result_data,
            "created_at": s.created_at.isoformat(),
        }
        for s in (current_user.scenario_records or [])
    ]

    bank_accounts_data = [
        {
            "id": b.id,
            "institution_name": b.institution_name,
            "account_number_masked": b.account_number_masked,
            "account_type": b.account_type,
            "ifsc_code": b.ifsc_code,
            "current_balance": float(b.current_balance),
            "balance_type": b.balance_type,
            "sync_status": b.sync_status,
            "last_synced_at": b.last_synced_at.isoformat() if b.last_synced_at else None
        }
        for b in (current_user.bank_accounts or [])
    ]

    bank_consents_data = [
        {
            "id": c.id,
            "consent_handle": c.consent_handle,
            "provider": c.provider,
            "status": c.status,
            "valid_to": c.valid_to.isoformat() if c.valid_to else None,
            "fetch_frequency": c.fetch_frequency
        }
        for c in (current_user.bank_consents or [])
    ]

    return {
        "export_timestamp": current_user.created_at.isoformat(),
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "auth_provider": current_user.auth_provider,
            "created_at": current_user.created_at.isoformat(),
        },
        "financial_profile": profile_data,
        "transactions": transactions_data,
        "liabilities": liabilities_data,
        "assets": assets_data,
        "goals": goals_data,
        "saved_scenarios": scenarios_data,
        "bank_accounts": bank_accounts_data,
        "bank_consents": bank_consents_data,
    }


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes user account and all cascaded personal and financial records.
    """
    db.delete(current_user)
    db.commit()

