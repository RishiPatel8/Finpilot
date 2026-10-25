import pytest
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.agent import PendingAction, AgentMemory, AgentFeedback
from app.models.financial import (
    Transaction,
    Liability,
    RecurringTransaction,
    FinancialGoal,
    FinancialProfile,
)
from app.ai.intent_parser import AgentIntentParser
from app.ai.action_service import ActionPlanner, ActionExecutor
from app.ai.memory import ConversationMemoryService
from app.ai.feedback import FeedbackService
from app.ai.agent import FinancialAgent
from app.schemas.agent import FeedbackSubmitRequest


def test_intent_parser_read_analysis():
    intent = AgentIntentParser.parse("What is my net worth and monthly cash flow?")
    assert intent.intent_type == "READ_ANALYSIS"
    assert intent.is_ambiguous is False


def test_intent_parser_unsupported_external_transfer():
    intent = AgentIntentParser.parse("Wire transfer ₹10,000 to John's bank account")
    assert intent.intent_type == "UNSUPPORTED"
    assert "do not execute direct bank fund transfers" in intent.clarification_question.lower()


def test_intent_parser_ambiguous_loan_command():
    intent = AgentIntentParser.parse("Add ₹1,000 loan to debt")
    assert intent.intent_type == "AMBIGUOUS"
    assert intent.is_ambiguous is True
    assert "which option do you mean" in intent.clarification_question.lower()
    assert len(intent.clarification_options) == 3
    assert any("new debt liability" in opt.lower() for opt in intent.clarification_options)


def test_intent_parser_ambiguity_clarification_resolution():
    history = [
        {"sender": "user", "content": "Add ₹1,000 loan to debt"},
        {"sender": "assistant", "content": "You mentioned adding a ₹1,000 loan. Which option do you mean? 1. Record new debt liability..."}
    ]
    intent = AgentIntentParser.parse("1", recent_history=history)
    assert intent.intent_type == "WRITE_ACTION"
    assert intent.action_type == "create_debt"
    assert intent.target_entity == "liability"
    assert intent.extracted_parameters["principal"] == 1000.0


def test_intent_parser_write_commands():
    # 1. Expense transaction
    i_exp = AgentIntentParser.parse("Record ₹3,500 spent on groceries")
    assert i_exp.intent_type == "WRITE_ACTION"
    assert i_exp.action_type == "create_transaction"
    assert i_exp.extracted_parameters["amount"] == 3500.0
    assert i_exp.extracted_parameters["type"] == "expense"
    assert i_exp.extracted_parameters["category"] == "Groceries"

    # 2. Income transaction
    i_inc = AgentIntentParser.parse("I received ₹45,000 salary today")
    assert i_inc.intent_type == "WRITE_ACTION"
    assert i_inc.action_type == "create_transaction"
    assert i_inc.extracted_parameters["amount"] == 45000.0
    assert i_inc.extracted_parameters["type"] == "income"

    # 3. Recurring commitment
    i_rec = AgentIntentParser.parse("Add my electricity bill of ₹2,500, due on the 28th")
    assert i_rec.intent_type == "WRITE_ACTION"
    assert i_rec.action_type == "create_recurring_commitment"
    assert i_rec.extracted_parameters["amount"] == 2500.0
    assert "electricity" in i_rec.extracted_parameters["name"].lower()

    # 4. Pause recurring
    i_pause = AgentIntentParser.parse("Pause my gym subscription")
    assert i_pause.intent_type == "WRITE_ACTION"
    assert i_pause.action_type == "pause_recurring_commitment"
    assert "gym" in i_pause.extracted_parameters["name"].lower()

    # 5. Budget adjustment with relative percentage
    hist = [{"sender": "assistant", "content": "Your Grocery spending was ₹6,000 this month."}]
    i_bgt = AgentIntentParser.parse("Reduce it by 15%", recent_history=hist)
    assert i_bgt.intent_type == "WRITE_ACTION"
    assert i_bgt.action_type == "update_budget"
    assert i_bgt.extracted_parameters["adjustment_pct"] == -15.0


def test_pending_action_creation_and_preview(db_session):
    user = User(
        email="planner_test@example.com",
        full_name="Planner Test User",
        role="salaried"
    )
    db_session.add(user)
    db_session.commit()

    params = {
        "name": "Auto Loan",
        "principal": 350000.0,
        "interest_rate": 8.5,
        "monthly_emi": 11500.0,
        "tenure_months": 36
    }
    pending = ActionPlanner.create_pending_action(
        user=user,
        action_type="create_debt",
        target_entity="liability",
        parameters=params,
        db=db_session
    )

    assert pending.id is not None
    assert pending.status == "awaiting_confirmation"
    assert pending.preview["title"] == "Create Debt Record: Auto Loan"
    assert pending.expires_at > pending.created_at
    assert "does not execute a real bank transfer" in pending.preview["disclaimer"]


def test_action_execution_successful_persistence(db_session):
    user = User(
        email="executor_test@example.com",
        full_name="Executor Test User",
        role="salaried"
    )
    db_session.add(user)
    db_session.commit()

    # Stage an expense transaction
    pending = ActionPlanner.create_pending_action(
        user=user,
        action_type="create_transaction",
        target_entity="transaction",
        parameters={
            "amount": 2500.0,
            "type": "expense",
            "category": "Utilities",
            "description": "Broadband Internet Bill"
        },
        db=db_session
    )

    # Confirm and execute
    res = ActionExecutor.confirm_and_execute(
        action_id=pending.id,
        user=user,
        db=db_session
    )

    assert res.status == "succeeded"
    assert res.result["entity"] == "transaction"
    txn_id = res.result["id"]

    # Verify directly in Transaction table
    persisted_txn = db_session.query(Transaction).filter_by(id=txn_id, user_id=user.id).first()
    assert persisted_txn is not None
    assert float(persisted_txn.amount) == 2500.0
    assert persisted_txn.description == "Broadband Internet Bill"
    assert persisted_txn.source == "ai_agent"


def test_action_execution_idempotency(db_session):
    user = User(
        email="idempotent_test@example.com",
        full_name="Idempotent User",
        role="salaried"
    )
    db_session.add(user)
    db_session.commit()

    pending = ActionPlanner.create_pending_action(
        user=user,
        action_type="create_debt",
        target_entity="liability",
        parameters={
            "name": "Personal Loan",
            "principal": 50000.0,
            "interest_rate": 11.0,
            "monthly_emi": 4400.0,
            "tenure_months": 12
        },
        db=db_session
    )

    # First execution
    res1 = ActionExecutor.confirm_and_execute(pending.id, user, db_session)
    assert res1.status == "succeeded"

    # Second execution (replayed click or duplicate network request)
    res2 = ActionExecutor.confirm_and_execute(pending.id, user, db_session)
    assert res2.status == "succeeded"
    assert "already executed" in res2.message

    # Ensure only 1 record was created in Liability table
    liabs = db_session.query(Liability).filter_by(user_id=user.id).all()
    assert len(liabs) == 1


def test_action_cancellation(db_session):
    user = User(
        email="cancel_test@example.com",
        full_name="Cancel User",
        role="salaried"
    )
    db_session.add(user)
    db_session.commit()

    pending = ActionPlanner.create_pending_action(
        user=user,
        action_type="create_transaction",
        target_entity="transaction",
        parameters={"amount": 999.0, "type": "expense"},
        db=db_session
    )

    cancel_res = ActionExecutor.cancel_action(pending.id, user, db_session)
    assert cancel_res.status == "cancelled"

    # Cannot execute cancelled action
    exec_res = ActionExecutor.confirm_and_execute(pending.id, user, db_session)
    assert exec_res.status == "cancelled"

    # Zero transactions created
    assert db_session.query(Transaction).filter_by(user_id=user.id).count() == 0


def test_action_expiration(db_session):
    user = User(
        email="expired_test@example.com",
        full_name="Expired User",
        role="salaried"
    )
    db_session.add(user)
    db_session.commit()

    pending = ActionPlanner.create_pending_action(
        user=user,
        action_type="create_transaction",
        target_entity="transaction",
        parameters={"amount": 500.0},
        db=db_session
    )

    # Force expiration timestamp into the past
    pending.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    res = ActionExecutor.confirm_and_execute(pending.id, user, db_session)
    assert res.status == "expired"
    assert "expired" in res.message.lower()


def test_cross_user_action_isolation(db_session):
    user1 = User(email="user1_act@example.com", full_name="User 1")
    user2 = User(email="user2_act@example.com", full_name="User 2")
    db_session.add_all([user1, user2])
    db_session.commit()

    pending = ActionPlanner.create_pending_action(
        user=user1,
        action_type="create_debt",
        target_entity="liability",
        parameters={"name": "User 1 Loan", "principal": 100000.0},
        db=db_session
    )

    # User 2 attempts to confirm User 1's pending action
    res = ActionExecutor.confirm_and_execute(pending.id, user2, db_session)
    assert res.status == "failed"
    assert "not authorized" in res.message


def test_conversation_memory_service(db_session):
    user1 = User(email="mem_u1@example.com", full_name="Memory User 1")
    user2 = User(email="mem_u2@example.com", full_name="Memory User 2")
    db_session.add_all([user1, user2])
    db_session.commit()

    # User 1 sets preferences and tracks entities
    ConversationMemoryService.set_user_preference(user1, "preferred_tax_regime", "new", db_session)
    ConversationMemoryService.track_last_entity(user1, "loan", "Home Loan", {"rate": 8.5}, db_session)

    # Retrieve User 1 memory
    u1_prefs = ConversationMemoryService.get_user_preferences(user1, db_session)
    assert u1_prefs.get("preferred_tax_regime") == "new"

    last_loan = ConversationMemoryService.get_last_entity(user1, "loan", db_session)
    assert last_loan["name"] == "Home Loan"
    assert last_loan["metadata"]["rate"] == 8.5

    # User 2 isolation check (must see empty preferences)
    u2_prefs = ConversationMemoryService.get_user_preferences(user2, db_session)
    assert len(u2_prefs) == 0
    assert ConversationMemoryService.get_last_entity(user2, "loan", db_session) is None


def test_feedback_service_and_ranking(db_session):
    user = User(email="feedback_u@example.com", full_name="Feedback User")
    db_session.add(user)
    db_session.commit()

    # Record acceptance and rejection events
    FeedbackService.record_feedback(
        user=user,
        req=FeedbackSubmitRequest(
            event_type="recommendation_accepted",
            recommendation_type="budget",
            recommendation_id="rec_bgt_1"
        ),
        db=db_session
    )
    FeedbackService.record_feedback(
        user=user,
        req=FeedbackSubmitRequest(
            event_type="recommendation_rejected",
            recommendation_type="recurring",
            recommendation_id="rec_rec_1"
        ),
        db=db_session
    )

    test_insights = [
        {"id": "1", "category": "recurring", "priority": "high", "title": "Subscriptions"},
        {"id": "2", "category": "budget", "priority": "medium", "title": "Budget Optimization"},
    ]

    # Rank insights based on user history
    ranked = FeedbackService.rank_proactive_insights(test_insights, user, db_session)
    assert ranked[0]["category"] == "budget"  # Boosted because of acceptance


def test_api_endpoints_action_lifecycle(client):
    """Verifies end-to-end HTTP endpoints for the shared Web & Telegram Action Service."""
    reg = client.post("/api/v1/auth/register", json={
        "email": "agent_api_test@example.com",
        "password": "Password123!",
        "full_name": "Agent User",
        "role": "salaried"
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Send natural language write command
    chat_res = client.post("/api/v1/assistant/chat", json={
        "message": "Record ₹1,200 spent on dining"
    }, headers=headers)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["pending_action"] is not None
    action_id = chat_data["pending_action"]["id"]
    assert chat_data["pending_action"]["status"] == "awaiting_confirmation"

    # 2. Check pending actions list endpoint
    pending_list = client.get("/api/v1/assistant/actions/pending", headers=headers)
    assert pending_list.status_code == 200
    assert any(a["id"] == action_id for a in pending_list.json())

    # 3. Confirm and execute action endpoint
    confirm_res = client.post(f"/api/v1/assistant/actions/{action_id}/confirm", json={
        "idempotency_key": "test_idem_123"
    }, headers=headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "succeeded"

    # 4. Submit feedback endpoint
    fb_res = client.post("/api/v1/assistant/feedback", json={
        "event_type": "rating_feedback",
        "rating": 1,
        "correction_text": "Accurately recorded under dining."
    }, headers=headers)
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "success"
