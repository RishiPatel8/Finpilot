import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.financial import ChatMessage
from app.models.agent import PendingAction, PendingClarification
from app.ai.intent_parser import AgentIntentParser
from app.ai.action_service import ActionPlanner, ActionExecutor
from app.ai.clarification_service import ClarificationService
from app.ai.memory import ConversationMemoryService
from app.ai.financial_context import FinancialContextService
from app.ai.adapter import get_ai_provider
from app.ai.tools import AVAILABLE_TOOLS
from app.schemas.agent import (
    ParsedIntent,
    PendingActionResponse,
    PendingActionPreview,
    ActionConfirmResponse,
    ActionCancelResponse,
)

logger = logging.getLogger("finpilot.ai.agent")


def _format_inr(val: float) -> str:
    s = f"{val:.2f}"
    int_part, dec_part = s.split(".")
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted_int = ",".join(groups) + "," + last3
    return f"{formatted_int}.{dec_part}"


class FinancialAgent:
    """
    Autonomous Context-Aware AI CFO Agent:
    - Analyzes full financial context across all supported domains.
    - Resolves contextual memory, past decisions, and pronoun references.
    - Dispatches read-only analysis to deterministic engines and RAG statutory retrieval.
    - Prepares validated pending write actions and requests explicit user confirmation.
    - Resolves active clarifications persistently across HTTP requests.
    - Never modifies the database without verified user authorization.
    """

    @classmethod
    def process_message(
        cls,
        message: str,
        user: Optional[User],
        db: Session,
        page_context: Optional[Dict[str, Any]] = None,
        conversation_id: str = "default",
        channel: str = "web",
        clarification_id: Optional[str] = None,
        option_id: Optional[str] = None
    ) -> Dict[str, Any]:
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()
        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # STEP 1: Direct Action Confirmation or Cancellation ("Confirm" / "Cancel")
        # -------------------------------------------------------------
        if user:
            # Check for active pending action awaiting authorization
            active_pending = db.query(PendingAction).filter(
                PendingAction.user_id == user.id,
                PendingAction.status == "awaiting_confirmation",
                PendingAction.expires_at > now
            ).order_by(PendingAction.created_at.desc()).first()

            if active_pending:
                confirm_indicators = [
                    "confirm", "yes", "proceed", "execute", "create", "create it", "approve",
                    "do it", "go ahead", "ok", "okay", "sure", "yep", "yeah", "save", "save it",
                    "record it", "confirm the creation", "confirm creation", "create debt", "create the debt",
                    "yes, confirm", "yes confirm", "confirm and execute", "please confirm", "confirm please"
                ]
                has_negative = any(neg in msg_lower for neg in ["don't", "dont", "do not", "cancel", "no", "nevermind", "abort", "stop", "reject"])
                import re
                is_confirm = (
                    any(re.search(rf"\b{re.escape(w)}\b", msg_lower) for w in confirm_indicators)
                    and not has_negative
                )

                if is_confirm:
                    res = ActionExecutor.confirm_and_execute(
                        action_id=active_pending.id,
                        user=user,
                        db=db
                    )
                    record_details = ""
                    if res.status == "succeeded" and res.result:
                        items = [f"- **{k.replace('_', ' ').title()}**: {v}" for k, v in res.result.items() if k != "entity"]
                        if items:
                            record_details = "\n\n**Persisted Record Details**:\n" + "\n".join(items)

                    return {
                        "content": f"### Action Confirmed & Verified\n\n{res.message}{record_details}",
                        "citations": ["FinPilot Safe Financial Execution Protocol"],
                        "tool_invocations": [{
                            "tool": "action_executor",
                            "summary": f"Executed action {active_pending.id[:8]} ({active_pending.action_type}) with database verification."
                        }],
                        "pending_action": {
                            "id": active_pending.id,
                            "action_type": active_pending.action_type,
                            "target_entity": active_pending.target_entity,
                            "status": res.status,
                            "parameters": active_pending.parameters,
                            "preview": active_pending.preview,
                            "execution_result": res.result,
                            "expires_at": active_pending.expires_at.isoformat()
                        },
                        "clarification": None,
                        "status": res.status
                    }

                cancel_indicators = ["cancel", "abort", "nevermind", "dont", "don't", "do not", "stop", "reject"]
                is_cancel = any(re.search(rf"\b{re.escape(w)}\b", msg_lower) for w in cancel_indicators) or msg_lower in ["no", "no.", "n"]
                if is_cancel:
                    res = ActionExecutor.cancel_action(
                        action_id=active_pending.id,
                        user=user,
                        db=db
                    )
                    return {
                        "content": "Proposed action has been safely cancelled. No changes were made to your records.",
                        "citations": ["FinPilot Safe Financial Execution Protocol"],
                        "tool_invocations": [{
                            "tool": "action_executor",
                            "summary": f"Safely cancelled pending action {active_pending.id[:8]}"
                        }],
                        "pending_action": {
                            "id": active_pending.id,
                            "action_type": active_pending.action_type,
                            "target_entity": active_pending.target_entity,
                            "status": "cancelled",
                            "parameters": active_pending.parameters,
                            "preview": active_pending.preview,
                            "expires_at": active_pending.expires_at.isoformat()
                        },
                        "clarification": None,
                        "status": "cancelled"
                    }

        # -------------------------------------------------------------
        # STEP 2: Persistent Clarification Resolution (User- and Conversation-Scoped)
        # -------------------------------------------------------------
        if user:
            active_clarification = None
            if clarification_id:
                # Find specified clarification strictly scoped to user and conversation
                active_clarification = db.query(PendingClarification).filter(
                    PendingClarification.id == clarification_id,
                    PendingClarification.user_id == user.id,
                    PendingClarification.conversation_id == conversation_id
                ).first()
            else:
                # Retrieve active clarification for this user and conversation
                active_clarification = ClarificationService.get_active_clarification(
                    user_id=user.id,
                    conversation_id=conversation_id,
                    db=db
                )

            if active_clarification:
                # Verify expiration
                exp = active_clarification.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)

                if now > exp or active_clarification.status == "expired":
                    active_clarification.status = "expired"
                    db.commit()
                    return {
                        "content": (
                            "This clarification has expired (clarifications are active for 15 minutes). "
                            "Please repeat what you would like to record or analyze."
                        ),
                        "citations": ["FinPilot Disambiguation Protocol"],
                        "tool_invocations": [],
                        "pending_action": None,
                        "clarification": None,
                        "status": "clarification_expired"
                    }

                # Check if user cancelled clarification
                if msg_lower in ["cancel", "cancel.", "nevermind", "abort", "no"]:
                    ClarificationService.cancel_clarification(active_clarification, db)
                    return {
                        "content": "Clarification has been cancelled. No changes were made to your financial records.",
                        "citations": ["FinPilot Disambiguation Protocol"],
                        "tool_invocations": [],
                        "pending_action": None,
                        "clarification": None,
                        "status": "cancelled"
                    }

                # Attempt to match option by ID, number ('1', '1. update it'), or text
                matched_opt = ClarificationService.match_option(
                    clarification=active_clarification,
                    message=msg_clean,
                    option_id=option_id
                )

                if matched_opt:
                    ClarificationService.resolve_clarification(active_clarification, matched_opt, db)

                    action_type = matched_opt.get("action_type", "create_debt")
                    target_entity = matched_opt.get("target_entity", "liability")
                    parameters = dict(matched_opt.get("parameters", {}))

                    # Inject extracted amount if missing in parameters
                    if active_clarification.extracted_amount:
                        amt = float(active_clarification.extracted_amount)
                        if action_type == "create_debt":
                            if parameters.get("principal", 0) == 0:
                                parameters["principal"] = amt
                            if parameters.get("monthly_emi", 0) == 0:
                                parameters["monthly_emi"] = amt
                        elif action_type == "create_transaction":
                            if parameters.get("amount", 0) == 0:
                                parameters["amount"] = amt

                    # Stage the persistent PendingAction
                    pending = ActionPlanner.create_pending_action(
                        user=user,
                        action_type=action_type,
                        target_entity=target_entity,
                        parameters=parameters,
                        db=db,
                        channel=channel
                    )

                    prev = pending.preview
                    items_str = "\n".join([f"- **{it['label']}**: {it['value']}" for it in prev.get("items", [])])
                    review_message = (
                        f"### Action Proposal: {prev.get('title', action_type)}\n\n"
                        f"{prev.get('summary', '')}\n\n"
                        f"**Review Details**:\n"
                        f"{items_str}\n\n"
                        f"> [!IMPORTANT]\n"
                        f"> {prev.get('disclaimer', '')}\n\n"
                        f"**Would you like me to confirm and execute this change, or cancel?**"
                    )

                    return {
                        "content": review_message,
                        "citations": ["FinPilot Safe Financial Execution Protocol"],
                        "tool_invocations": [{
                            "tool": "action_planner",
                            "summary": f"Staged {action_type} action awaiting confirmation (ID: {pending.id[:8]}...)"
                        }],
                        "pending_action": {
                            "id": pending.id,
                            "action_type": pending.action_type,
                            "target_entity": pending.target_entity,
                            "status": pending.status,
                            "parameters": pending.parameters,
                            "preview": pending.preview,
                            "expires_at": pending.expires_at.isoformat()
                        },
                        "clarification": None,
                        "status": "awaiting_confirmation"
                    }

        # -------------------------------------------------------------
        # STEP 3: Retrieve Conversation Memory and Context
        # -------------------------------------------------------------
        recent_history = ConversationMemoryService.get_recent_messages(
            user=user,
            db=db,
            limit=8,
            conversation_id=conversation_id
        )

        full_context = FinancialContextService.get_complete_financial_context(
            user=user,
            db=db,
            page_context=page_context
        )

        # -------------------------------------------------------------
        # STEP 4: Parse Natural Language Intent
        # -------------------------------------------------------------
        intent: ParsedIntent = AgentIntentParser.parse(
            message=msg_clean,
            recent_history=recent_history,
            context=full_context
        )

        # -------------------------------------------------------------
        # STEP 5: Handle Unsupported Operations
        # -------------------------------------------------------------
        if intent.intent_type == "UNSUPPORTED":
            return {
                "content": intent.clarification_question,
                "citations": ["FinPilot AI Security & Execution Policy"],
                "tool_invocations": [],
                "pending_action": None,
                "clarification": None,
                "status": "unsupported"
            }

        # -------------------------------------------------------------
        # STEP 6: Handle Ambiguous Requests (Persist Clarification State)
        # -------------------------------------------------------------
        if intent.intent_type == "AMBIGUOUS" and intent.is_ambiguous:
            structured_options = intent.structured_options or [
                {"id": f"opt_{i+1}", "label": opt}
                for i, opt in enumerate(intent.clarification_options or [])
            ]

            clarification_payload = None
            if user:
                amt = intent.extracted_parameters.get("amount")
                persisted = ClarificationService.create_clarification(
                    user_id=user.id,
                    conversation_id=conversation_id,
                    original_request=msg_clean,
                    clarification_question=intent.clarification_question,
                    options=structured_options,
                    extracted_amount=float(amt) if amt is not None else None,
                    db=db
                )
                clarification_payload = {
                    "id": persisted.id,
                    "question": persisted.clarification_question,
                    "options": persisted.options,
                    "expires_at": persisted.expires_at.isoformat()
                }
            else:
                clarification_payload = {
                    "id": "unauthenticated",
                    "question": intent.clarification_question,
                    "options": structured_options,
                    "expires_at": None
                }

            return {
                "content": intent.clarification_question,
                "citations": ["FinPilot Disambiguation Protocol"],
                "tool_invocations": [],
                "pending_action": None,
                "clarification": clarification_payload,
                "status": "needs_clarification"
            }

        # -------------------------------------------------------------
        # STEP 7: Handle Direct WRITE Actions
        # -------------------------------------------------------------
        if intent.intent_type == "WRITE_ACTION" and intent.action_type:
            if not user:
                return {
                    "content": (
                        "To record or modify financial records, please log in to your authenticated FinPilot account. "
                        "Your financial records are strictly isolated and encrypted."
                    ),
                    "citations": ["FinPilot Authentication Protocol"],
                    "tool_invocations": [],
                    "pending_action": None,
                    "clarification": None,
                    "status": "authentication_required"
                }

            # Generate Staged Pending Action
            pending = ActionPlanner.create_pending_action(
                user=user,
                action_type=intent.action_type,
                target_entity=intent.target_entity or "record",
                parameters=intent.extracted_parameters,
                db=db,
                channel=channel
            )

            # Build Formatted Review Message
            prev = pending.preview
            items_str = "\n".join([f"- **{it['label']}**: {it['value']}" for it in prev.get("items", [])])
            review_message = (
                f"### Action Proposal: {prev.get('title', intent.action_type)}\n\n"
                f"{prev.get('summary', '')}\n\n"
                f"**Review Details**:\n"
                f"{items_str}\n\n"
                f"> [!IMPORTANT]\n"
                f"> {prev.get('disclaimer', '')}\n\n"
                f"**Would you like me to confirm and execute this change, or cancel?**"
            )

            # Track in Conversation Memory
            ConversationMemoryService.track_last_entity(
                user=user,
                entity_type=intent.target_entity or "action",
                entity_name=intent.action_type,
                metadata=intent.extracted_parameters,
                db=db
            )

            return {
                "content": review_message,
                "citations": ["FinPilot Safe Financial Execution Protocol"],
                "tool_invocations": [{
                    "tool": "action_planner",
                    "summary": f"Staged {intent.action_type} action awaiting confirmation (ID: {pending.id[:8]}...)"
                }],
                "pending_action": {
                    "id": pending.id,
                    "action_type": pending.action_type,
                    "target_entity": pending.target_entity,
                    "status": pending.status,
                    "parameters": pending.parameters,
                    "preview": pending.preview,
                    "expires_at": pending.expires_at.isoformat()
                },
                "clarification": None,
                "status": "awaiting_confirmation"
            }

        # -------------------------------------------------------------
        # STEP 8: Deterministic Ledger Queries (Receivables & Debts)
        # -------------------------------------------------------------
        if intent.action_type == "list_receivables" and user:
            from app.models.financial import Liability
            receivables = db.query(Liability).filter(
                Liability.user_id == user.id,
                Liability.debt_type == "receivable",
                Liability.status == "active"
            ).all()

            if not receivables:
                content = (
                    "📋 **Money Lent to Others (Receivables)**\n\n"
                    "You currently have no recorded money lent to others.\n\n"
                    "To record money you have lent, you can tell me: *\"My friend owes me ₹5,000\"* or "
                    "*\"I lent ₹10,000 to Rohan at 1% monthly interest\"*."
                )
            else:
                total_rec = sum(float(r.principal or 0.0) for r in receivables)
                items_str = "\n".join([
                    f"• **{r.counterparty or r.name}**: ₹{_format_inr(float(r.principal))} "
                    f"({float(r.interest_rate or 0.0)}% {r.interest_period or 'monthly'}, Status: {(r.status or 'active').title()})"
                    for r in receivables
                ])
                content = (
                    f"📋 **Money Lent to Others (Receivables)**\n\n"
                    f"{items_str}\n\n"
                    f"**Total Outstanding Receivables:** ₹{_format_inr(total_rec)}"
                )

            return {
                "content": content,
                "citations": ["FinPilot Real-Time Debt & Receivables Ledger"],
                "tool_invocations": [{
                    "tool": "receivables_ledger",
                    "summary": f"Retrieved {len(receivables)} active receivable records."
                }],
                "pending_action": None,
                "clarification": None,
                "status": "success",
                "provider": "deterministic-ledger"
            }

        if intent.action_type == "list_debts" and user:
            from app.models.financial import Liability
            debts = db.query(Liability).filter(
                Liability.user_id == user.id,
                Liability.debt_type != "receivable",
                Liability.status != "repaid"
            ).all()

            if not debts:
                content = (
                    "📋 **Active Debts & Liabilities**\n\n"
                    "You have no recorded active debts."
                )
            else:
                total_debt = sum(float(d.principal or 0.0) for d in debts)
                total_emi = sum(float(d.monthly_emi or 0.0) for d in debts)
                items_str = "\n".join([
                    f"• **{d.name}** ({d.counterparty or 'Lender'}): ₹{_format_inr(float(d.principal))} "
                    f"({float(d.interest_rate or 0.0)}% {d.interest_period or 'annual'}, EMI: ₹{_format_inr(float(d.monthly_emi or 0.0))}/mo)"
                    for d in debts
                ])
                content = (
                    f"📋 **Active Debts & Liabilities**\n\n"
                    f"{items_str}\n\n"
                    f"**Total Outstanding Debt:** ₹{_format_inr(total_debt)}\n"
                    f"**Total Monthly EMI:** ₹{_format_inr(total_emi)}/mo"
                )

            return {
                "content": content,
                "citations": ["FinPilot Real-Time Debt & Receivables Ledger"],
                "tool_invocations": [{
                    "tool": "debts_ledger",
                    "summary": f"Retrieved {len(debts)} active liability records."
                }],
                "pending_action": None,
                "clarification": None,
                "status": "success",
                "provider": "deterministic-ledger"
            }

        # -------------------------------------------------------------
        # STEP 9: READ_ANALYSIS: Process through AI Provider with tools & RAG
        # -------------------------------------------------------------
        provider = get_ai_provider()
        res = provider.generate_response(
            query=msg_clean,
            chat_history=recent_history,
            user_context=full_context
        )

        return {
            "content": res.get("content", ""),
            "citations": res.get("citations", []),
            "tool_invocations": res.get("tool_invocations", []),
            "pending_action": None,
            "clarification": None,
            "status": "success",
            "provider": res.get("provider", "mock"),
            "model": res.get("model", "deterministic-mock")
        }
