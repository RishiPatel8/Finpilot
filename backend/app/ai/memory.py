import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.agent import AgentMemory
from app.models.financial import ChatMessage

logger = logging.getLogger("finpilot.ai.memory")


class ConversationMemoryService:
    """
    Multi-layer conversation memory service:
    1. Active window: Recent chat turns from ChatMessage table.
    2. Preference memory: User-specific preferences (risk tolerance, tax regime, budget limits).
    3. Episodic memory: Summaries of concluded financial planning sessions.
    4. Entity resolution: Resolves pronouns and contextual follow-ups ("that loan", "increase it by 10%").
    All memory records are strictly isolated by user_id.
    """

    @classmethod
    def get_recent_messages(
        cls,
        user: Optional[User],
        db: Session,
        limit: int = 10,
        conversation_id: str = "default"
    ) -> List[Dict[str, str]]:
        if not user:
            return []
        past = db.query(ChatMessage).filter(
            ChatMessage.user_id == user.id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

        return [{"sender": m.sender, "content": m.content} for m in reversed(past)]

    @classmethod
    def set_user_preference(
        cls,
        user: User,
        key: str,
        value: str,
        db: Session,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMemory:
        mem = db.query(AgentMemory).filter(
            AgentMemory.user_id == user.id,
            AgentMemory.memory_type == "preference",
            AgentMemory.key == key
        ).first()

        now = datetime.now(timezone.utc)
        if mem:
            mem.value = value
            mem.metadata_json = metadata
            mem.updated_at = now
        else:
            mem = AgentMemory(
                user_id=user.id,
                memory_type="preference",
                key=key,
                value=value,
                metadata_json=metadata,
                created_at=now,
                updated_at=now
            )
            db.add(mem)

        db.commit()
        db.refresh(mem)
        return mem

    @classmethod
    def get_user_preferences(cls, user: Optional[User], db: Session) -> Dict[str, str]:
        if not user:
            return {}
        records = db.query(AgentMemory).filter(
            AgentMemory.user_id == user.id,
            AgentMemory.memory_type == "preference"
        ).all()
        return {r.key: r.value for r in records}

    @classmethod
    def track_last_entity(
        cls,
        user: User,
        entity_type: str,
        entity_name: str,
        metadata: Dict[str, Any],
        db: Session
    ):
        cls.set_user_preference(
            user=user,
            key=f"last_{entity_type}",
            value=entity_name,
            db=db,
            metadata=metadata
        )

    @classmethod
    def get_last_entity(cls, user: Optional[User], entity_type: str, db: Session) -> Optional[Dict[str, Any]]:
        if not user:
            return None
        mem = db.query(AgentMemory).filter(
            AgentMemory.user_id == user.id,
            AgentMemory.memory_type == "preference",
            AgentMemory.key == f"last_{entity_type}"
        ).first()
        if mem:
            return {
                "name": mem.value,
                "metadata": mem.metadata_json or {}
            }
        return None

    @classmethod
    def save_episodic_summary(
        cls,
        user: User,
        conversation_id: str,
        summary: str,
        db: Session,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMemory:
        now = datetime.now(timezone.utc)
        key = f"summary_{int(now.timestamp())}"
        mem = AgentMemory(
            user_id=user.id,
            conversation_id=conversation_id,
            memory_type="episodic_summary",
            key=key,
            value=summary,
            metadata_json=metadata,
            created_at=now,
            updated_at=now
        )
        db.add(mem)
        db.commit()
        db.refresh(mem)
        return mem

    @classmethod
    def clear_all_memory(cls, user: User, db: Session) -> int:
        count = db.query(AgentMemory).filter(AgentMemory.user_id == user.id).delete()
        db.commit()
        return count
