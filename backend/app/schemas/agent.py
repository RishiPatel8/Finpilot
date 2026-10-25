from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PendingActionPreview(BaseModel):
    title: str
    summary: str
    items: List[Dict[str, str]]
    disclaimer: str = "This will record a financial record in your FinPilot account. It does not execute a real bank transfer, loan application, or payment."


class PendingActionResponse(BaseModel):
    id: str
    action_type: str
    target_entity: str
    status: str
    parameters: Dict[str, Any]
    preview: PendingActionPreview
    created_at: str
    expires_at: str
    executed_at: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    channel: str = "web"


class ActionConfirmRequest(BaseModel):
    idempotency_key: Optional[str] = None


class ActionConfirmResponse(BaseModel):
    status: str  # succeeded, failed, expired, needs_reconfirmation
    action_id: str
    action_type: str
    message: str
    result: Optional[Dict[str, Any]] = None
    verified_at: Optional[str] = None


class ActionCancelResponse(BaseModel):
    status: str
    action_id: str
    message: str


class FeedbackSubmitRequest(BaseModel):
    event_type: str = Field(..., description="rating_feedback, recommendation_accepted, recommendation_rejected, user_correction")
    recommendation_id: Optional[str] = None
    recommendation_type: Optional[str] = None
    rating: Optional[int] = Field(None, ge=-1, le=1)  # -1, 0, 1
    correction_text: Optional[str] = None
    context_snapshot: Optional[Dict[str, Any]] = None


class FeedbackSubmitResponse(BaseModel):
    status: str
    message: str
    feedback_id: str


class ClarificationOption(BaseModel):
    id: str
    label: str
    action_type: Optional[str] = None
    target_entity: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class PendingClarificationResponse(BaseModel):
    id: str
    question: str
    options: List[ClarificationOption]
    original_request: Optional[str] = None
    extracted_amount: Optional[float] = None
    expires_at: Optional[str] = None
    status: str = "unresolved"


class ParsedIntent(BaseModel):
    intent_type: str  # READ_ANALYSIS, WRITE_ACTION, AMBIGUOUS, UNSUPPORTED
    action_type: Optional[str] = None  # create_transaction, create_debt, create_recurring, pause_recurring, cancel_recurring, update_budget, create_goal
    target_entity: Optional[str] = None
    confidence: float = 1.0
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict)
    clarification_question: Optional[str] = None
    clarification_options: Optional[List[str]] = None
    structured_options: Optional[List[Dict[str, Any]]] = None
    is_ambiguous: bool = False

