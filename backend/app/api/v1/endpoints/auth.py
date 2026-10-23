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
