import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import relationship, backref
from app.db.session import Base


class PendingAction(Base):
    """
    Persistent state machine for AI-proposed financial actions awaiting explicit user authorization.
    State Lifecycle: draft -> awaiting_confirmation -> executing -> succeeded
    Terminal states: cancelled, expired, failed, needs_reconfirmation
    """
    __tablename__ = "agent_pending_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False, index=True)  # create_transaction, create_debt, create_recurring, etc.
    target_entity = Column(String(64), nullable=False)  # transaction, liability, recurring_transaction, profile, goal
    parameters = Column(JSON, nullable=False)  # Validated tool parameters
    preview = Column(JSON, nullable=False)  # Human-readable preview payload {title, summary, items, disclaimer}
    status = Column(String(32), default="awaiting_confirmation", nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    executed_at = Column(DateTime, nullable=True)
    execution_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    channel = Column(String(32), default="web", nullable=False)  # web, telegram, api

    user = relationship("User", backref=backref("pending_actions", cascade="all, delete-orphan", passive_deletes=True))


class AgentMemory(Base):
    """
    Long-term and episodic memory for AI CFO.
    Stores user preferences, conversation turn summaries, and entity references strictly scoped to user_id.
    """
    __tablename__ = "agent_memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(64), default="default", nullable=False, index=True)
    memory_type = Column(String(32), nullable=False, index=True)  # preference, episodic_summary, entity_ref
    key = Column(String(128), nullable=False, index=True)
    value = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "memory_type", "key", name="uq_user_memory_type_key"),
    )

    user = relationship("User", backref=backref("agent_memories", cascade="all, delete-orphan", passive_deletes=True))


class AgentFeedback(Base):
    """
    Feedback collection and evaluation foundation for recommendation ranking and quality scoring.
    """
    __tablename__ = "agent_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # recommendation_shown, recommendation_accepted, recommendation_rejected, user_correction, action_confirmed, action_cancelled, rating_feedback
    recommendation_id = Column(String(64), nullable=True, index=True)
    recommendation_type = Column(String(64), nullable=True, index=True)
    rating = Column(Integer, nullable=True)  # +1 (helpful), -1 (unhelpful)
    correction_text = Column(Text, nullable=True)
    context_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", backref=backref("agent_feedback_events", cascade="all, delete-orphan", passive_deletes=True))


class PendingClarification(Base):
    """
    Persistent state machine for AI CFO clarification workflows.
    Tracks active questions, stable options with unique IDs, original user query,
    and extracted parameters scoped strictly to authenticated user and conversation.
    Status Lifecycle: unresolved -> resolved | expired | cancelled
    """
    __tablename__ = "agent_pending_clarifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(64), default="default", nullable=False, index=True)
    original_request = Column(Text, nullable=False)
    clarification_question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # List of dicts: [{"id": "...", "label": "...", "action_type": "...", ...}]
    extracted_amount = Column(Numeric(14, 2), nullable=True)
    status = Column(String(32), default="unresolved", nullable=False, index=True)  # unresolved, resolved, expired, cancelled
    selected_option_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    user = relationship("User", backref=backref("pending_clarifications", cascade="all, delete-orphan", passive_deletes=True))

