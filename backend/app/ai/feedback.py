import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.user import User
from app.models.agent import AgentFeedback
from app.schemas.agent import FeedbackSubmitRequest, FeedbackSubmitResponse

logger = logging.getLogger("finpilot.ai.feedback")


class FeedbackService:
    """
    Feedback and evaluation foundation for AI CFO recommendations.
    Provides:
    - User rating tracking (+1 / -1) and correction recording.
    - Proactive recommendation ranking based on past acceptance/dismissal signals.
    - Zero autonomous financial write authority.
    """

    @classmethod
    def record_feedback(
        cls,
        user: User,
        req: FeedbackSubmitRequest,
        db: Session
    ) -> FeedbackSubmitResponse:
        now = datetime.now(timezone.utc)
        fb = AgentFeedback(
            user_id=user.id,
            event_type=req.event_type,
            recommendation_id=req.recommendation_id,
            recommendation_type=req.recommendation_type,
            rating=req.rating,
            correction_text=req.correction_text,
            context_snapshot=req.context_snapshot,
            created_at=now
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

        logger.info(f"Recorded feedback {fb.id} (type: {fb.event_type}) for user {user.id}")
        return FeedbackSubmitResponse(
            status="success",
            message="Feedback recorded successfully. Thank you for helping improve FinPilot AI.",
            feedback_id=fb.id
        )

    @classmethod
    def rank_proactive_insights(
        cls,
        insights: List[Dict[str, Any]],
        user: Optional[User],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Ranks proactive insights based on user interaction history.
        Deprioritizes categories the user frequently rejects, and boosts categories the user accepts.
        """
        if not user or not insights:
            return insights

        # Calculate acceptance/rejection score per category for this user
        case_stmt = case(
            (AgentFeedback.event_type == "recommendation_accepted", 1),
            (AgentFeedback.event_type == "recommendation_rejected", -1),
            else_=0
        )
        stats = db.query(
            AgentFeedback.recommendation_type,
            func.sum(case_stmt).label("net_score")
        ).filter(
            AgentFeedback.user_id == user.id,
            AgentFeedback.recommendation_type.isnot(None)
        ).group_by(AgentFeedback.recommendation_type).all()

        score_map = {cat: (score or 0) for cat, score in stats}

        def compute_sort_key(item: Dict[str, Any]) -> float:
            base_priority = {
                "high": 60.0,
                "medium": 40.0,
                "positive": 30.0,
                "low": 20.0
            }.get(item.get("priority", "medium"), 30.0)

            category = item.get("category", "")
            learned_affinity = score_map.get(category, 0) * 25.0

            return base_priority + learned_affinity

        return sorted(insights, key=compute_sort_key, reverse=True)
