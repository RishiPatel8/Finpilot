import pytest
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.models.user import User
from app.models.agent import PendingAction, PendingClarification
from app.models.financial import Liability, Transaction
from app.ai.intent_parser import AgentIntentParser
from app.ai.clarification_service import ClarificationService
from app.ai.action_service import ActionPlanner, ActionExecutor
from app.ai.agent import FinancialAgent
from app.core.security import create_access_token


@pytest.fixture
def test_user(db_session):
    user = User(
        email=f"cfo_repair_{uuid.uuid4().hex[:6]}@example.com",
        full_name="AI CFO Repair User",
        role="salaried"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_1_ambiguous_credit_card_loan_generates_clarification(db_session, test_user):
    """
    Requirement 1 & 3:
    'add 10000rs has credit card loan' generates a clarification with 4 distinct options
    and extracts the amount ₹10,000 without jumping to a generic questionnaire.
    """
    conv_id = "test_conv_cc_1"
    res = FinancialAgent.process_message(
        message="add 10000rs has credit card loan",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )

    assert res["status"] == "needs_clarification"
    assert res["pending_action"] is None
    assert res["clarification"] is not None

    clar = res["clarification"]
    assert clar["id"] is not None
    assert len(clar["options"]) == 4

    labels = [opt["label"] for opt in clar["options"]]
    assert "Credit-card outstanding balance" in labels
    assert "Credit-card EMI/loan liability" in labels
    assert "Loan received as income" in labels
    assert "Record a repayment already made" in labels

    # Check persistence in database
    db_clar = db_session.query(PendingClarification).filter_by(id=clar["id"]).first()
    assert db_clar is not None
    assert db_clar.user_id == test_user.id
    assert db_clar.conversation_id == conv_id
    assert db_clar.status == "unresolved"
    assert float(db_clar.extracted_amount) == 10000.0


def test_2_selecting_option_1_resolves_clarification_and_creates_action(db_session, test_user):
    """
    Requirement 2 & 4:
    User replies '1. update it' -> resolves clarification option 1
    and stages a pending action for ₹10,000 Credit Card Outstanding Balance.
    """
    conv_id = "test_conv_cc_2"
    # Turn 1: Ambiguous credit card loan
    res1 = FinancialAgent.process_message(
        message="add 10000rs has credit card loan",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )
    clar_id = res1["clarification"]["id"]

    # Turn 2: User says '1. update it'
    res2 = FinancialAgent.process_message(
        message="1. update it",
        user=test_user,
        db=db_session,
        conversation_id=conv_id,
        clarification_id=clar_id
    )

    assert res2["status"] == "awaiting_confirmation"
    assert res2["pending_action"] is not None
    assert "Action Proposal: Create Debt Record" in res2["content"] or "Action Proposal" in res2["content"]
    assert "questionnaire" not in res2["content"].lower()

    action_data = res2["pending_action"]
    assert action_data["action_type"] == "create_debt"
    assert action_data["target_entity"] == "liability"
    assert action_data["parameters"]["principal"] == 10000.0
    assert action_data["parameters"]["name"] == "Credit Card Outstanding Balance"

    # Verify clarification marked resolved in DB
    db_clar = db_session.query(PendingClarification).filter_by(id=clar_id).first()
    assert db_clar.status == "resolved"
    assert db_clar.selected_option_id == "opt_cc_balance"

    # Verify pending action in DB
    db_action = db_session.query(PendingAction).filter_by(id=action_data["id"]).first()
    assert db_action is not None
    assert db_action.user_id == test_user.id
    assert db_action.status == "awaiting_confirmation"


def test_3_typed_variations_resolve_clarification(db_session, test_user):
    """
    Tests various user text inputs: '1', 'Option 1', 'Yes, update it.'
    All resolve the active clarification correctly.
    """
    variations = ["1", "Option 1", "Yes, update it."]
    for idx, phrase in enumerate(variations):
        conv_id = f"test_conv_var_{idx}"
        FinancialAgent.process_message(
            message="add 10000rs has credit card loan",
            user=test_user,
            db=db_session,
            conversation_id=conv_id
        )

        res = FinancialAgent.process_message(
            message=phrase,
            user=test_user,
            db=db_session,
            conversation_id=conv_id
        )
        assert res["status"] == "awaiting_confirmation"
        assert res["pending_action"]["parameters"]["principal"] == 10000.0
        assert res["pending_action"]["parameters"]["name"] == "Credit Card Outstanding Balance"


def test_4_confirmation_persists_record_and_verifies_db(db_session, test_user):
    """
    Requirement 4 & 6:
    When user confirms with 'Confirm.', the record is persisted to the Liability table,
    verified via database query, and returns success.
    """
    conv_id = "test_conv_confirm"
    # Stage action
    FinancialAgent.process_message(
        message="add 10000rs has credit card loan",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )
    res_stage = FinancialAgent.process_message(
        message="1. update it",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )
    action_id = res_stage["pending_action"]["id"]

    # Confirm action
    res_confirm = FinancialAgent.process_message(
        message="Confirm.",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )

    assert res_confirm["status"] == "succeeded"
    assert "Action Confirmed" in res_confirm["content"]

    # Verify directly in Liability table
    liab = db_session.query(Liability).filter_by(user_id=test_user.id).first()
    assert liab is not None
    assert liab.name == "Credit Card Outstanding Balance"
    assert float(liab.principal) == 10000.0
    assert float(liab.interest_rate) == 36.0
    assert liab.tenure_months == 1

    # Verify action marked succeeded
    db_act = db_session.query(PendingAction).filter_by(id=action_id).first()
    assert db_act.status == "succeeded"
    assert db_act.executed_at is not None


def test_5_cancellation_creates_no_financial_record(db_session, test_user):
    """
    Requirement 7:
    Cancelling creates no financial record in the database.
    """
    conv_id = "test_conv_cancel"
    # Stage action
    FinancialAgent.process_message(
        message="add 10000rs has credit card loan",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )
    res_stage = FinancialAgent.process_message(
        message="1. update it",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )
    action_id = res_stage["pending_action"]["id"]

    # Cancel action
    res_cancel = FinancialAgent.process_message(
        message="Cancel.",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )

    assert res_cancel["status"] == "cancelled"
    assert "safely cancelled" in res_cancel["content"].lower()

    # Verify no Liability record exists
    count = db_session.query(Liability).filter_by(user_id=test_user.id).count()
    assert count == 0

    # Verify action marked cancelled
    db_act = db_session.query(PendingAction).filter_by(id=action_id).first()
    assert db_act.status == "cancelled"


def test_6_repeated_confirmation_does_not_duplicate(db_session, test_user):
    """
    Requirement 8:
    Repeated confirmation does not create duplicate database records.
    """
    params = {
        "name": "Credit Card Outstanding Balance",
        "principal": 10000.0,
        "interest_rate": 36.0,
        "monthly_emi": 10000.0,
        "tenure_months": 1
    }
    pending = ActionPlanner.create_pending_action(
        user=test_user,
        action_type="create_debt",
        target_entity="liability",
        parameters=params,
        db=db_session
    )

    # First execution
    res1 = ActionExecutor.confirm_and_execute(pending.id, test_user, db_session)
    assert res1.status == "succeeded"
    assert db_session.query(Liability).filter_by(user_id=test_user.id).count() == 1

    # Second execution (idempotent replay)
    res2 = ActionExecutor.confirm_and_execute(pending.id, test_user, db_session)
    assert res2.status == "succeeded"
    assert "already executed" in res2.message.lower()
    assert db_session.query(Liability).filter_by(user_id=test_user.id).count() == 1


def test_7_cross_conversation_isolation(db_session, test_user):
    """
    Requirement 9:
    An answer from another conversation cannot resolve a clarification in the first conversation.
    """
    # Create clarification in conv_1
    res1 = FinancialAgent.process_message(
        message="add 10000rs has credit card loan",
        user=test_user,
        db=db_session,
        conversation_id="conv_user_1"
    )
    assert res1["status"] == "needs_clarification"

    # User sends '1. update it' in conv_user_2
    res2 = FinancialAgent.process_message(
        message="1. update it",
        user=test_user,
        db=db_session,
        conversation_id="conv_user_2"
    )
    # conv_2 has no active clarification, so it does not resolve conv_1's clarification
    assert res2.get("pending_action") is None

    # conv_1 clarification remains unresolved
    db_clar = db_session.query(PendingClarification).filter_by(
        user_id=test_user.id,
        conversation_id="conv_user_1"
    ).first()
    assert db_clar.status == "unresolved"


def test_8_expired_clarification_cannot_be_resolved(db_session, test_user):
    """
    Requirement 10:
    Expired clarifications cannot be used.
    """
    conv_id = "test_conv_expired"
    past_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    clar = PendingClarification(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        conversation_id=conv_id,
        original_request="add 10000rs has credit card loan",
        clarification_question="What should I add?",
        options=[{"id": "opt_cc_balance", "label": "Credit-card outstanding balance", "action_type": "create_debt"}],
        extracted_amount=Decimal("10000.00"),
        status="unresolved",
        created_at=past_time - timedelta(minutes=15),
        expires_at=past_time
    )
    db_session.add(clar)
    db_session.commit()

    # User attempts to resolve expired clarification
    res = FinancialAgent.process_message(
        message="1. update it",
        user=test_user,
        db=db_session,
        conversation_id=conv_id,
        clarification_id=clar.id
    )

    assert res["status"] == "clarification_expired"
    assert "expired" in res["content"].lower()
    assert res["pending_action"] is None

    # Check status transitioned to expired
    db_session.refresh(clar)
    assert clar.status == "expired"


def test_9_general_loan_to_debt_workflow(db_session, test_user):
    """
    Tests 'Add ₹1,000 loan to debt.' followed by '1' and 'Confirm.'
    """
    conv_id = "test_conv_gen_debt"
    res1 = FinancialAgent.process_message(
        message="Add ₹1,000 loan to debt.",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )
    assert res1["status"] == "needs_clarification"
    assert float(res1["clarification"]["options"][0]["parameters"]["principal"]) == 1000.0

    res2 = FinancialAgent.process_message(
        message="1",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )
    assert res2["status"] == "awaiting_confirmation"
    assert res2["pending_action"]["parameters"]["principal"] == 1000.0

    res3 = FinancialAgent.process_message(
        message="Confirm.",
        user=test_user,
        db=db_session,
        conversation_id=conv_id
    )
    assert res3["status"] == "succeeded"

    # Verify liability record
    liab = db_session.query(Liability).filter_by(user_id=test_user.id, principal=1000.0).first()
    assert liab is not None
    assert liab.name == "Personal Loan"


def test_10_http_endpoint_end_to_end_clarification_flow(client, db_session, test_user):
    """
    End-to-end integration test through FastAPI /api/v1/assistant/chat and /actions/{id}/confirm endpoints.
    """
    token = create_access_token(subject=test_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = "http_conv_1"

    # 1. Post ambiguous credit card loan
    r1 = client.post(
        "/api/v1/assistant/chat",
        headers=headers,
        json={
            "message": "add 10000rs has credit card loan",
            "conversation_id": conv_id
        }
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] == "needs_clarification"
    assert d1["clarification"] is not None
    clar_id = d1["clarification"]["id"]
    opt_id = d1["clarification"]["options"][0]["id"]

    # 2. Select option 1 via structured chip parameters
    r2 = client.post(
        "/api/v1/assistant/chat",
        headers=headers,
        json={
            "message": "Credit-card outstanding balance",
            "conversation_id": conv_id,
            "clarification_id": clar_id,
            "option_id": opt_id
        }
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["status"] == "awaiting_confirmation"
    assert d2["pending_action"] is not None
    action_id = d2["pending_action"]["id"]
    assert d2["pending_action"]["parameters"]["principal"] == 10000.0

    # 3. Confirm via API
    r3 = client.post(
        f"/api/v1/assistant/actions/{action_id}/confirm",
        headers=headers,
        json={"idempotency_key": "http_test_key_1"}
    )
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["status"] == "succeeded"

    # 4. Verify persisted record
    liab = db_session.query(Liability).filter_by(user_id=test_user.id).first()
    assert liab is not None
    assert float(liab.principal) == 10000.0
    assert liab.name == "Credit Card Outstanding Balance"
