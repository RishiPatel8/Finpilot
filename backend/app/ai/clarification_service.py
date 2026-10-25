import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.agent import PendingClarification

logger = logging.getLogger("finpilot.ai.clarification_service")


class ClarificationService:
    """
    Manages persistent, user-scoped and conversation-scoped clarification state machines.
    Guarantees:
    - Stable option IDs across HTTP turns
    - Fast resolution of user numbered/text replies without relying on LLM memory
    - Strict expiration and cross-conversation isolation
    """

    @classmethod
    def create_clarification(
        cls,
        user_id: str,
        conversation_id: str,
        original_request: str,
        clarification_question: str,
        options: List[Dict[str, Any]],
        extracted_amount: Optional[float],
        db: Session,
        ttl_minutes: int = 15
    ) -> PendingClarification:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ttl_minutes)

        # Supersede any previous unresolved clarifications in this conversation
        try:
            db.query(PendingClarification).filter(
                PendingClarification.user_id == user_id,
                PendingClarification.conversation_id == conversation_id,
                PendingClarification.status == "unresolved"
            ).update({"status": "superseded"}, synchronize_session=False)
            db.commit()
        except Exception as e:
            logger.warning(f"Error superseding old clarifications: {e}")
            db.rollback()

        clarification = PendingClarification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
            original_request=original_request,
            clarification_question=clarification_question,
            options=options,
            extracted_amount=extracted_amount,
            status="unresolved",
            created_at=now,
            expires_at=expires_at
        )
        db.add(clarification)
        db.commit()
        db.refresh(clarification)
        return clarification

    @classmethod
    def get_active_clarification(
        cls,
        user_id: str,
        conversation_id: str,
        db: Session
    ) -> Optional[PendingClarification]:
        """
        Returns the active, non-expired pending clarification for this user and conversation.
        If an unresolved clarification has expired, transitions its status to 'expired'.
        """
        clarification = db.query(PendingClarification).filter(
            PendingClarification.user_id == user_id,
            PendingClarification.conversation_id == conversation_id,
            PendingClarification.status == "unresolved"
        ).order_by(PendingClarification.created_at.desc()).first()

        if not clarification:
            return None

        now = datetime.now(timezone.utc)
        expires_at = clarification.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            clarification.status = "expired"
            db.commit()
            return None

        return clarification

    @classmethod
    def match_option(
        cls,
        clarification: PendingClarification,
        message: str,
        option_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Resolves an option from the clarification options list:
        1. Explicit option_id matching
        2. Direct number/ordinal ('1', '1. update it', 'option 1', 'yes, update it')
        3. Semantic keyword matches against option labels and descriptions
        """
        options: List[Dict[str, Any]] = clarification.options or []
        if not options:
            return None

        # 1. Direct option_id match
        if option_id:
            for opt in options:
                if str(opt.get("id")) == str(option_id):
                    return opt

        import re
        m = re.sub(r"[.!?,]+$", "", message.strip().lower()).strip()

        # Check for option number mappings
        # Option 1
        opt1_patterns = [
            "1", "1.", "1. update it", "option 1", "opt 1", "option 1.", "first option",
            "yes, update it", "yes update it", "update it", "confirm", "proceed",
            "yes, please", "yes", "confirm it", "update", "1 please", "option 1 please",
            "sure, update it", "please update it", "confirm option 1", "yes please", "sure"
        ]
        if m in opt1_patterns or m.startswith("1.") or m.startswith("1 "):
            if len(options) >= 1:
                return options[0]

        # Option 2
        opt2_patterns = [
            "2", "2.", "2. update it", "option 2", "opt 2", "option 2.", "second option",
            "2 please", "option 2 please", "confirm option 2"
        ]
        if m in opt2_patterns or m.startswith("2.") or m.startswith("2 "):
            if len(options) >= 2:
                return options[1]

        # Option 3
        opt3_patterns = [
            "3", "3.", "3. update it", "option 3", "opt 3", "option 3.", "third option",
            "3 please", "option 3 please", "confirm option 3"
        ]
        if m in opt3_patterns or m.startswith("3.") or m.startswith("3 "):
            if len(options) >= 3:
                return options[2]

        # Option 4
        opt4_patterns = [
            "4", "4.", "4. update it", "option 4", "opt 4", "option 4.", "fourth option",
            "4 please", "option 4 please", "confirm option 4"
        ]
        if m in opt4_patterns or m.startswith("4.") or m.startswith("4 "):
            if len(options) >= 4:
                return options[3]

        # 3. Match against labels or IDs directly
        for opt in options:
            lbl = opt.get("label", "").lower()
            oid = opt.get("id", "").lower()
            if lbl and (lbl in m or m in lbl):
                return opt
            if oid and oid in m:
                return opt

        # 4. Keyword heuristics for credit card loan choices
        if any(k in m for k in ["outstanding", "statement balance", "credit card balance", "card balance", "total balance"]):
            for opt in options:
                if "balance" in opt.get("id", "") or "balance" in opt.get("label", "").lower():
                    return opt

        if any(k in m for k in ["emi", "loan liability", "card emi", "credit card loan"]):
            for opt in options:
                if "emi" in opt.get("id", "") or "emi" in opt.get("label", "").lower() or "liability" in opt.get("id", ""):
                    return opt

        if any(k in m for k in ["disbursement", "received as income", "inflow", "received"]):
            for opt in options:
                if "inflow" in opt.get("id", "") or "income" in opt.get("label", "").lower():
                    return opt

        if any(k in m for k in ["repayment", "repay", "already paid", "payment made"]):
            for opt in options:
                if "repay" in opt.get("id", "") or "repayment" in opt.get("label", "").lower():
                    return opt

        return None

    @classmethod
    def resolve_clarification(
        cls,
        clarification: PendingClarification,
        selected_option: Dict[str, Any],
        db: Session
    ) -> PendingClarification:
        clarification.status = "resolved"
        clarification.selected_option_id = selected_option.get("id")
        db.commit()
        db.refresh(clarification)
        return clarification

    @classmethod
    def cancel_clarification(
        cls,
        clarification: PendingClarification,
        db: Session
    ) -> PendingClarification:
        clarification.status = "cancelled"
        db.commit()
        db.refresh(clarification)
        return clarification
