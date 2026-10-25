from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import ChatMessage
from app.ai.adapter import get_ai_provider, get_ai_provider_status
from app.ai.financial_context import FinancialContextService
from app.ai.agent import FinancialAgent
from app.ai.action_service import ActionExecutor
from app.ai.feedback import FeedbackService
from app.models.agent import PendingAction
from app.schemas.agent import (
    ActionConfirmRequest,
    ActionConfirmResponse,
    ActionCancelResponse,
    FeedbackSubmitRequest,
    FeedbackSubmitResponse,
)
from app.api.deps import get_optional_current_user, get_current_user

router = APIRouter()


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User financial query")
    page_context: Optional[Dict[str, Any]] = Field(default=None, description="Active view/page context metadata")
    conversation_id: Optional[str] = Field(default="default", description="Optional conversation session ID")
    clarification_id: Optional[str] = Field(default=None, description="Optional active clarification ID")
    option_id: Optional[str] = Field(default=None, description="Optional selected option ID")


class ChatResponse(BaseModel):
    content: str
    citations: List[str]
    tool_invocations: List[Dict[str, Any]]
    provider: Optional[str] = "mock"
    model: Optional[str] = "deterministic-mock"
    status: Optional[str] = "success"
    active_page: Optional[str] = "overview"
    pending_action: Optional[Dict[str, Any]] = None
    clarification: Optional[Dict[str, Any]] = None


class ChatMessageHistoryItem(BaseModel):
    id: str
    sender: str
    content: str
    citations: Optional[List[str]] = None
    tool_invocations: Optional[List[Dict[str, Any]]] = None
    created_at: str


class ProactiveInsight(BaseModel):
    id: str
    title: str
    priority: str  # high, medium, low, positive
    category: str
    message: str
    evidence: str
    suggested_prompt: str


@router.get("/provider-status")
def get_status():
    """Inspects the active AI Provider and cloud model readiness."""
    return get_ai_provider_status()


@router.get("/proactive-insights", response_model=List[ProactiveInsight])
def get_proactive_insights(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates personalized, evidence-based proactive financial insights
    when the user opens the AI CFO assistant.
    """
    ctx = FinancialContextService.get_complete_financial_context(current_user, db)
    insights: List[ProactiveInsight] = []

    # 1. Budget Overspending / Category Anomaly Alerts (High Priority)
    anomalies = ctx.get("spending_anomalies", [])
    if anomalies:
        top_anomaly = anomalies[0]
        insights.append(ProactiveInsight(
            id="anomaly_alert",
            title=f"Spending Spike in {top_anomaly['category']}",
            priority="high",
            category="budget",
            message=top_anomaly["explanation"],
            evidence=f"Deviation is {top_anomaly['deviation_pct']:+.1f}% compared to your monthly baseline.",
            suggested_prompt=f"Why did my {top_anomaly['category']} spending increase this month and how can I adjust?"
        ))

    # 2. Upcoming Recurring Commitments within 7-14 Days (Medium Priority)
    rec_items = ctx.get("recurring_commitments", [])
    if rec_items:
        total_rec = ctx.get("recurring_monthly_expenses", 0.0)
        insights.append(ProactiveInsight(
            id="recurring_summary",
            title=f"Monthly Commitments: ₹{total_rec:,.0f}/mo",
            priority="medium",
            category="recurring",
            message=f"You have {len(rec_items)} active recurring subscriptions and obligations.",
            evidence=f"Represents a normalized cash outflow of ₹{total_rec:,.0f} per month.",
            suggested_prompt="What recurring payments do I have next month and which can I pause?"
        ))

    # 3. Emergency Runway Warning or Positive Status
    runway = ctx.get("emergency_runway_months", 0.0)
    if runway < 3.0:
        insights.append(ProactiveInsight(
            id="runway_warning",
            title="Emergency Runway Below Target",
            priority="high",
            category="safety",
            message=f"Liquid reserves cover {runway:.1f} months of expenses (minimum target is 3.0 months).",
            evidence=f"Current liquid reserves: ₹{ctx.get('current_savings', 0):,.0f} vs monthly burn ₹{ctx.get('monthly_expenses', 0):,.0f}.",
            suggested_prompt="How can I optimize my monthly surplus to build a 6-month emergency fund?"
        ))
    else:
        insights.append(ProactiveInsight(
            id="runway_healthy",
            title="Emergency Reserves Strong",
            priority="positive",
            category="safety",
            message=f"Your liquid funds cover {runway:.1f} months of living expenses.",
            evidence=f"Liquid savings: ₹{ctx.get('current_savings', 0):,.0f} provides stable buffer.",
            suggested_prompt="Can I invest part of my monthly surplus into higher-yield instruments?"
        ))

    # 4. Savings Goal Tracking
    goals = ctx.get("active_goals", [])
    if goals:
        first_goal = goals[0]
        insights.append(ProactiveInsight(
            id=f"goal_{first_goal['id']}",
            title=f"Goal Tracking: {first_goal['name']}",
            priority="medium",
            category="goals",
            message=f"Currently {first_goal['progress_pct']}% funded (₹{first_goal['current_amount']:,.0f} of ₹{first_goal['target_amount']:,.0f}).",
            evidence=f"Requires ~₹{first_goal['required_monthly_savings']:,.0f}/month over remaining {first_goal['months_remaining']} months.",
            suggested_prompt=f"Am I on track to achieve my {first_goal['name']} goal on time?"
        ))

    # Rank insights using feedback learning history
    ranked = FeedbackService.rank_proactive_insights(
        insights=[i.model_dump() for i in insights],
        user=current_user,
        db=db
    )
    return [ProactiveInsight(**r) for r in ranked[:4]]


@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(
    req: ChatQueryRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Autonomous Context-Aware AI CFO Agent Chat:
    - Coordinates natural-language intent understanding
    - Whole-application financial context & memory
    - Prepares user-confirmed pending actions for write requests
    - Dispatches read analysis to deterministic engines & statutory RAG
    """
    agent_result = FinancialAgent.process_message(
        message=req.message,
        user=current_user,
        db=db,
        page_context=req.page_context,
        conversation_id=req.conversation_id or "default",
        clarification_id=req.clarification_id,
        option_id=req.option_id
    )

    # Persist interaction to ChatMessage history
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
                content=agent_result["content"],
                citations=agent_result.get("citations", []),
                tool_invocations=agent_result.get("tool_invocations", [])
            )
            db.add(user_msg)
            db.add(asst_msg)
            db.commit()
        except Exception:
            db.rollback()

    active_page = "overview"
    if req.page_context and isinstance(req.page_context, dict):
        active_page = req.page_context.get("page", "overview")

    return ChatResponse(
        content=agent_result["content"],
        citations=agent_result.get("citations", []),
        tool_invocations=agent_result.get("tool_invocations", []),
        provider=agent_result.get("provider", "mock"),
        model=agent_result.get("model", "deterministic-mock"),
        status=agent_result.get("status", "success"),
        active_page=active_page,
        pending_action=agent_result.get("pending_action"),
        clarification=agent_result.get("clarification")
    )


@router.get("/actions/pending")
def get_pending_actions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists active, non-expired pending financial actions awaiting authorization."""
    now = datetime.now(timezone.utc)
    actions = db.query(PendingAction).filter(
        PendingAction.user_id == current_user.id,
        PendingAction.status == "awaiting_confirmation",
        PendingAction.expires_at > now
    ).order_by(PendingAction.created_at.desc()).all()

    return [
        {
            "id": a.id,
            "action_type": a.action_type,
            "target_entity": a.target_entity,
            "status": a.status,
            "parameters": a.parameters,
            "preview": a.preview,
            "created_at": a.created_at.isoformat(),
            "expires_at": a.expires_at.isoformat()
        }
        for a in actions
    ]


@router.post("/actions/{action_id}/confirm", response_model=ActionConfirmResponse)
def confirm_action(
    action_id: str,
    body: Optional[ActionConfirmRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes a user-confirmed pending action.
    Used by both Website Confirm button and Telegram inline buttons.
    """
    idempotency_key = body.idempotency_key if body else None
    res = ActionExecutor.confirm_and_execute(
        action_id=action_id,
        user=current_user,
        db=db,
        idempotency_key=idempotency_key
    )

    if res.status == "failed" and res.message == "Action not found or you are not authorized to execute it.":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.message
        )

    return res


@router.post("/actions/{action_id}/cancel", response_model=ActionCancelResponse)
def cancel_action(
    action_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancels a pending financial action safely without modifying any financial records."""
    res = ActionExecutor.cancel_action(
        action_id=action_id,
        user=current_user,
        db=db
    )

    if res.status == "failed" and "not authorized" in res.message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.message
        )

    return res


@router.post("/feedback", response_model=FeedbackSubmitResponse)
def submit_feedback(
    body: FeedbackSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Collects user ratings, corrections, and recommendation outcome feedback."""
    return FeedbackService.record_feedback(
        user=current_user,
        req=body,
        db=db
    )


@router.get("/history", response_model=List[ChatMessageHistoryItem])
def get_chat_history(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Returns conversation history strictly scoped to the authenticated user."""
    if not current_user:
        return []

    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.asc()).limit(50).all()

    return [
        ChatMessageHistoryItem(
            id=m.id,
            sender=m.sender,
            content=m.content,
            citations=m.citations or [],
            tool_invocations=m.tool_invocations or [],
            created_at=m.created_at.isoformat()
        )
        for m in messages
    ]


@router.delete("/history")
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely deletes conversation history for the authenticated user."""
    deleted_count = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).delete(synchronize_session=False)
    db.commit()

    return {
        "status": "success",
        "message": "Conversation history cleared successfully",
        "deleted_count": deleted_count
    }
