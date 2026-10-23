from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import ChatMessage
from app.ai.adapter import get_ai_provider
from app.api.deps import get_optional_current_user

router = APIRouter()


class ChatQueryRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    content: str
    citations: List[str]
    tool_invocations: List[Dict[str, Any]]
    provider: Optional[str] = "mock"
    model: Optional[str] = "deterministic-mock"
    status: Optional[str] = "success"


class ChatMessageHistoryItem(BaseModel):
    id: str
    sender: str
    content: str
    citations: Optional[List[str]] = None
    created_at: str


@router.get("/provider-status")
def get_provider_status():
    from app.ai.adapter import get_ai_provider_status
    return get_ai_provider_status()


@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(
    req: ChatQueryRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    provider = get_ai_provider()
    
    # Retrieve recent chat history and authorized financial context
    history = []
    user_context = {}

    if current_user:
        past = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).order_by(ChatMessage.created_at.desc()).limit(6).all()
        history = [{"sender": m.sender, "content": m.content} for m in reversed(past)]

        # Authorized financial context injection
        if current_user.profile:
            user_context["monthly_income"] = float(current_user.profile.monthly_income)
            user_context["monthly_expenses"] = float(current_user.profile.monthly_expenses)
        
        # Calculate liquid savings from manual assets
        if current_user.assets:
            liquid_sum = sum(float(a.current_value) for a in current_user.assets if a.category in ["liquid_mf", "cash", "fd"])
            user_context["current_savings"] = liquid_sum

        # Calculate verified savings from linked bank accounts
        if current_user.bank_accounts:
            user_context["bank_accounts"] = [
                {
                    "institution": a.institution_name,
                    "account_masked": a.account_number_masked,
                    "balance": float(a.current_balance),
                    "status": a.sync_status
                }
                for a in current_user.bank_accounts
            ]
            verified_bank_total = sum(float(a.current_balance) for a in current_user.bank_accounts if a.sync_status == "synced")
            user_context["verified_bank_balance"] = verified_bank_total
            if not user_context.get("current_savings") and verified_bank_total > 0:
                user_context["current_savings"] = verified_bank_total

        # Include debts and EMIs if registered
        if current_user.liabilities:
            user_context["total_debt"] = sum(float(l.principal) for l in current_user.liabilities)
            user_context["monthly_emi"] = sum(float(l.monthly_emi) for l in current_user.liabilities)

    resp_dict = provider.generate_response(query=req.message, chat_history=history, user_context=user_context)

    # Persist interaction if authenticated
    if current_user:
        try:
            user_msg = ChatMessage(
                user_id=current_user.id,
                sender="user",
                content=req.message
            )
            asst_msg = ChatMessage(
                user_id=current_user.id,
                sender="assistant",
                content=resp_dict["content"],
                citations=resp_dict["citations"],
                tool_invocations=resp_dict["tool_invocations"]
            )
            db.add(user_msg)
            db.add(asst_msg)
            db.commit()
        except Exception:
            db.rollback()

    return ChatResponse(
        content=resp_dict["content"],
        citations=resp_dict["citations"],
        tool_invocations=resp_dict["tool_invocations"],
        provider=resp_dict.get("provider", "mock"),
        model=resp_dict.get("model", "deterministic-mock"),
        status=resp_dict.get("status", "success")
    )


@router.get("/history", response_model=List[ChatMessageHistoryItem])
def get_chat_history(
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return []
    messages = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).order_by(ChatMessage.created_at.asc()).all()
    return [
        ChatMessageHistoryItem(
            id=m.id,
            sender=m.sender,
            content=m.content,
            citations=m.citations,
            created_at=m.created_at.isoformat()
        )
        for m in messages
    ]
