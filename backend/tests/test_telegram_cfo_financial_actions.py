import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from app.models.user import User
from app.models.financial import Liability
from app.models.agent import PendingAction, PendingClarification
from app.models.telegram import TelegramAccountLink
from app.telegram.client import TelegramClient
from app.telegram.handler import TelegramUpdateHandler
from app.ai.action_service import ActionExecutor


class MockTelegramClient(TelegramClient):
    """
    Test spy client recording outgoing Telegram Bot API calls.
    """
    def __init__(self):
        super().__init__(token="mock_test_token_123")
        self.sent_messages = []
        self.edited_messages = []
        self.answered_callbacks = []

    async def send_message(self, chat_id, text, parse_mode="HTML", reply_markup=None, disable_web_page_preview=True):
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": reply_markup,
        }
        self.sent_messages.append(payload)
        return {"ok": True, "result": {"message_id": len(self.sent_messages), "text": text}}

    async def edit_message_text(self, chat_id, message_id, text, parse_mode="HTML", reply_markup=None):
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": reply_markup,
        }
        self.edited_messages.append(payload)
        return {"ok": True, "result": {"message_id": message_id, "text": text}}

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        self.answered_callbacks.append({"id": callback_query_id, "text": text, "alert": show_alert})
        return {"ok": True, "result": True}


@pytest.fixture
def user_a(db_session):
    import uuid
    uid = uuid.uuid4().hex[:6]
    tg_id = str(abs(hash(uid)) % 1000000 + 100000)
    u = User(
        email=f"tg_user_a_{uid}@example.com",
        full_name="User Alpha",
        role="salaried",
        is_active=True
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)

    # Link Telegram ID
    link = TelegramAccountLink(
        user_id=u.id,
        telegram_user_id=tg_id,
        telegram_chat_id=tg_id,
        telegram_username=f"user_alpha_{uid}",
        telegram_first_name="Alpha",
        notifications_enabled=True,
    )
    db_session.add(link)
    db_session.commit()
    u._tg_id = int(tg_id)
    return u


@pytest.fixture
def user_b(db_session):
    import uuid
    uid = uuid.uuid4().hex[:6]
    tg_id = str(abs(hash(uid)) % 1000000 + 200000)
    u = User(
        email=f"tg_user_b_{uid}@example.com",
        full_name="User Beta",
        role="salaried",
        is_active=True
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)

    # Link Telegram ID
    link = TelegramAccountLink(
        user_id=u.id,
        telegram_user_id=tg_id,
        telegram_chat_id=tg_id,
        telegram_username=f"user_beta_{uid}",
        telegram_first_name="Beta",
        notifications_enabled=True,
    )
    db_session.add(link)
    db_session.commit()
    u._tg_id = int(tg_id)
    return u


@pytest.mark.asyncio
async def test_1_valid_debt_request_reaches_real_action_handler(db_session, user_a):
    """
    1. A valid debt request reaches the real action handler and stages a PendingAction.
    """
    mock_client = MockTelegramClient()
    handler = TelegramUpdateHandler(client=mock_client)
    tg_id = user_a._tg_id

    msg_update = {
        "update_id": 100001,
        "message": {
            "message_id": 1,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Add a debt of ₹1,000 to my friend at 1% monthly interest.",
        }
    }

    res = await handler.handle_update(msg_update, db_session)
    assert res["status"] == "action_proposed"
    action_id = res["action_id"]

    # Verify pending action in DB
    action = db_session.query(PendingAction).filter_by(id=action_id).first()
    assert action is not None
    assert action.user_id == user_a.id
    assert action.action_type == "create_debt"
    assert action.target_entity == "liability"
    assert action.status == "awaiting_confirmation"
    assert action.parameters["principal"] == 1000.0
    assert action.parameters["counterparty"] == "Friend"
    assert action.parameters["debt_type"] == "payable"
    assert action.parameters["interest_period"] == "monthly"

    # Verify proposal message contains confirm and cancel inline buttons
    assert len(mock_client.sent_messages) == 1
    sent = mock_client.sent_messages[0]
    assert "Action Proposal:" in sent["text"]
    assert "₹1,000" in sent["text"]
    reply_markup = sent["reply_markup"]
    assert reply_markup is not None
    buttons = reply_markup["inline_keyboard"][0]
    assert buttons[0]["callback_data"] == f"confirm:{action_id}"
    assert buttons[1]["callback_data"] == f"cancel:{action_id}"


@pytest.mark.asyncio
async def test_2_missing_interest_period_triggers_clarification(db_session, user_a):
    """
    2. Missing interest-period information triggers a clarification without guessing.
    "Add a debt of 1000rs with interest of 1% to my friend."
    """
    mock_client = MockTelegramClient()
    handler = TelegramUpdateHandler(client=mock_client)
    tg_id = user_a._tg_id

    msg_update = {
        "update_id": 100002,
        "message": {
            "message_id": 2,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Add a debt of 1000rs with interest of 1% to my friend.",
        }
    }

    res = await handler.handle_update(msg_update, db_session)
    assert res["status"] == "clarification_sent"
    c_id = res["clarification_id"]

    # Verify clarification in DB
    clarification = db_session.query(PendingClarification).filter_by(id=c_id).first()
    assert clarification is not None
    assert clarification.user_id == user_a.id
    assert clarification.status == "unresolved"
    assert "monthly" in clarification.clarification_question.lower()
    assert len(clarification.options) == 2

    # Verify option 1 is monthly and option 2 is annual
    assert "monthly" in clarification.options[0]["label"].lower()
    assert "annual" in clarification.options[1]["label"].lower()

    # Selecting monthly option resolves clarification and stages create_debt
    cb_update = {
        "update_id": 100003,
        "callback_query": {
            "id": "cb_opt_1",
            "from": {"id": tg_id},
            "message": {"chat": {"id": tg_id}, "message_id": 2},
            "data": f"clarify:{c_id}:opt_monthly_interest"
        }
    }
    cb_res = await handler.handle_update(cb_update, db_session)
    assert cb_res["status"] == "action_proposed"

    # Verify a pending action was created for 1% monthly
    pending = db_session.query(PendingAction).filter(
        PendingAction.user_id == user_a.id,
        PendingAction.status == "awaiting_confirmation"
    ).order_by(PendingAction.created_at.desc()).first()
    assert pending is not None
    assert pending.action_type == "create_debt"
    assert pending.parameters["interest_period"] == "monthly"
    assert pending.parameters["interest_rate"] == 12.0  # 1% per month = 12% p.a.


@pytest.mark.asyncio
async def test_3_and_4_confirmed_request_creates_and_returns_persisted_record(db_session, user_a):
    """
    3. A confirmed request creates the correct database record.
    4. The bot returns the persisted record, not a fabricated success.
    """
    mock_client = MockTelegramClient()
    handler = TelegramUpdateHandler(client=mock_client)
    tg_id = user_a._tg_id

    # 1. Propose debt
    prop_update = {
        "update_id": 100004,
        "message": {
            "message_id": 3,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Add a debt of ₹1,000 to my friend at 1% monthly interest.",
        }
    }
    prop_res = await handler.handle_update(prop_update, db_session)
    action_id = prop_res["action_id"]

    # 2. Confirm via callback query
    cb_update = {
        "update_id": 100005,
        "callback_query": {
            "id": "cb_confirm_1",
            "from": {"id": tg_id},
            "message": {"chat": {"id": tg_id}, "message_id": 3},
            "data": f"confirm:{action_id}"
        }
    }
    exec_res = await handler.handle_update(cb_update, db_session)
    assert exec_res["status"] == "action_executed"
    assert exec_res["result"] == "succeeded"

    # 3. Verify actual row in liabilities table
    liab = db_session.query(Liability).filter(
        Liability.user_id == user_a.id,
        Liability.principal == Decimal("1000.00")
    ).first()
    assert liab is not None
    assert liab.counterparty == "Friend"
    assert liab.debt_type == "payable"
    assert liab.interest_period == "monthly"
    assert liab.status == "active"
    assert liab.created_at is not None

    # 4. Verify message edit contains persisted record details
    assert len(mock_client.edited_messages) == 1
    edited = mock_client.edited_messages[0]
    assert "Action Confirmed" in edited["text"]
    assert "Persisted Record Details:" in edited["text"]
    assert liab.id in edited["text"]
    assert "Friend" in edited["text"]
    assert "₹1,000.00" in edited["text"]


@pytest.mark.asyncio
async def test_5_database_failures_produce_honest_error(db_session, user_a):
    """
    5. Database failures produce an honest error response.
    """
    mock_client = MockTelegramClient()
    handler = TelegramUpdateHandler(client=mock_client)
    tg_id = user_a._tg_id

    # Stage action
    prop_update = {
        "update_id": 100006,
        "message": {
            "message_id": 4,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Add a debt of ₹1,000 to my friend at 1% monthly interest.",
        }
    }
    prop_res = await handler.handle_update(prop_update, db_session)
    action_id = prop_res["action_id"]

    # Mock database failure during ActionExecutor._dispatch_execution
    with patch.object(ActionExecutor, "_dispatch_execution", side_effect=RuntimeError("Database write error: Disk I/O failure")):
        cb_update = {
            "update_id": 100007,
            "callback_query": {
                "id": "cb_fail_1",
                "from": {"id": tg_id},
                "message": {"chat": {"id": tg_id}, "message_id": 4},
                "data": f"confirm:{action_id}"
            }
        }
        res = await handler.handle_update(cb_update, db_session)
        assert res["status"] == "action_executed"
        assert res["result"] == "failed"

        # Check pending action state in DB
        action = db_session.query(PendingAction).filter_by(id=action_id).first()
        assert action.status == "failed"
        assert "Database write error" in action.error_message

        # Verify edited message tells the honest truth
        edited = mock_client.edited_messages[-1]
        assert "⚠️" in edited["text"]
        assert "Execution failed" in edited["text"]


@pytest.mark.asyncio
async def test_6_duplicate_updates_do_not_create_duplicate_debts(db_session, user_a):
    """
    6. Duplicate updates do not create duplicate debts.
    """
    mock_client = MockTelegramClient()
    handler = TelegramUpdateHandler(client=mock_client)
    tg_id = user_a._tg_id

    dup_update = {
        "update_id": 777777,
        "message": {
            "message_id": 5,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Add a debt of ₹1,000 to my friend at 1% monthly interest.",
        }
    }

    # First delivery
    res1 = await handler.handle_update(dup_update, db_session)
    assert res1["status"] == "action_proposed"
    action_id = res1["action_id"]

    # Duplicate delivery with identical update_id
    res2 = await handler.handle_update(dup_update, db_session)
    assert res2["status"] == "duplicate"
    assert res2["update_id"] == 777777

    # Confirm action once
    cb_update_1 = {
        "update_id": 777778,
        "callback_query": {
            "id": "cb_dup_1",
            "from": {"id": tg_id},
            "message": {"chat": {"id": tg_id}, "message_id": 5},
            "data": f"confirm:{action_id}"
        }
    }
    await handler.handle_update(cb_update_1, db_session)

    # Replay confirmation with a new update_id
    cb_update_2 = {
        "update_id": 777779,
        "callback_query": {
            "id": "cb_dup_2",
            "from": {"id": tg_id},
            "message": {"chat": {"id": tg_id}, "message_id": 5},
            "data": f"confirm:{action_id}"
        }
    }
    replay_res = await handler.handle_update(cb_update_2, db_session)
    assert replay_res["status"] == "action_executed"
    assert replay_res["result"] == "succeeded"

    # Verify only ONE liability record was created in the database
    count = db_session.query(Liability).filter(
        Liability.user_id == user_a.id,
        Liability.principal == Decimal("1000.00")
    ).count()
    assert count == 1


@pytest.mark.asyncio
async def test_7_users_cannot_access_or_mutate_another_users_debts(db_session, user_a, user_b):
    """
    7. Users cannot access or mutate another user's debts.
    """
    mock_client = MockTelegramClient()
    handler = TelegramUpdateHandler(client=mock_client)
    tg_id_a = user_a._tg_id
    tg_id_b = user_b._tg_id

    # User A creates a pending debt proposal
    prop_update = {
        "update_id": 100010,
        "message": {
            "message_id": 6,
            "chat": {"id": tg_id_a, "type": "private"},
            "from": {"id": tg_id_a, "first_name": "Alpha"},
            "text": "Add a debt of ₹1,000 to my friend at 1% monthly interest.",
        }
    }
    prop_res = await handler.handle_update(prop_update, db_session)
    action_id = prop_res["action_id"]

    # User B attempts to confirm User A's action
    cb_user_b = {
        "update_id": 100011,
        "callback_query": {
            "id": "cb_unauth_b",
            "from": {"id": tg_id_b},  # User B's Telegram ID
            "message": {"chat": {"id": tg_id_b}, "message_id": 100},
            "data": f"confirm:{action_id}"
        }
    }
    forbidden_res = await handler.handle_update(cb_user_b, db_session)
    assert forbidden_res["status"] == "forbidden"

    # Action remains unexecuted
    pending = db_session.query(PendingAction).filter_by(id=action_id).first()
    assert pending.status == "awaiting_confirmation"

    # User B sees 0 liabilities
    b_liabs = db_session.query(Liability).filter(Liability.user_id == user_b.id).all()
    assert len(b_liabs) == 0


@pytest.mark.asyncio
async def test_8_repayment_and_listing_receivables_and_debts(db_session, user_a):
    """
    8. Repayment and listing work on the database model.
    """
    mock_client = MockTelegramClient()
    handler = TelegramUpdateHandler(client=mock_client)
    tg_id = user_a._tg_id

    # 1. User records money lent to friend: "My friend owes me ₹5,000"
    lent_update = {
        "update_id": 100020,
        "message": {
            "message_id": 7,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "My friend owes me ₹5,000.",
        }
    }
    lent_res = await handler.handle_update(lent_update, db_session)
    assert lent_res["status"] == "action_proposed"
    action_id = lent_res["action_id"]

    # Confirm the lent money record
    confirm_lent = {
        "update_id": 100021,
        "callback_query": {
            "id": "cb_lent",
            "from": {"id": tg_id},
            "message": {"chat": {"id": tg_id}, "message_id": 7},
            "data": f"confirm:{action_id}"
        }
    }
    await handler.handle_update(confirm_lent, db_session)

    # 2. Query receivables: "Show all money I have lent to others."
    list_update = {
        "update_id": 100022,
        "message": {
            "message_id": 8,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Show all money I have lent to others.",
        }
    }
    await handler.handle_update(list_update, db_session)
    sent_list = mock_client.sent_messages[-1]
    assert "Money Lent to Others (Receivables)" in sent_list["text"]
    assert "Friend" in sent_list["text"]
    assert "₹5,000.00" in sent_list["text"]

    # 3. Create a loan of ₹1,000 to test repayment: "I borrowed ₹1,000 from my brother."
    borrow_update = {
        "update_id": 100023,
        "message": {
            "message_id": 9,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "I borrowed ₹1,000 from my brother.",
        }
    }
    borrow_res = await handler.handle_update(borrow_update, db_session)
    b_action_id = borrow_res["action_id"]
    await handler.handle_update({
        "update_id": 100024,
        "callback_query": {
            "id": "cb_borrow",
            "from": {"id": tg_id},
            "message": {"chat": {"id": tg_id}, "message_id": 9},
            "data": f"confirm:{b_action_id}"
        }
    }, db_session)

    # 4. Mark as repaid: "Mark the ₹1,000 loan as repaid."
    repay_update = {
        "update_id": 100025,
        "message": {
            "message_id": 10,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Mark the ₹1,000 loan as repaid.",
        }
    }
    repay_res = await handler.handle_update(repay_update, db_session)
    assert repay_res["status"] == "action_proposed"
    repay_action_id = repay_res["action_id"]

    # Confirm repayment
    await handler.handle_update({
        "update_id": 100026,
        "callback_query": {
            "id": "cb_repay",
            "from": {"id": tg_id},
            "message": {"chat": {"id": tg_id}, "message_id": 10},
            "data": f"confirm:{repay_action_id}"
        }
    }, db_session)

    # Verify liability in DB has status == 'repaid' and remaining_months == 0
    repaid_liab = db_session.query(Liability).filter(
        Liability.user_id == user_a.id,
        Liability.principal == Decimal("1000.00")
    ).first()
    assert repaid_liab.status == "repaid"
    assert repaid_liab.remaining_months == 0


@pytest.mark.asyncio
async def test_9_unsupported_actions_clearly_identified(db_session, user_a):
    """
    9. Unsupported actions are clearly identified rather than falsely claimed as completed.
    """
    mock_client = MockTelegramClient()
    handler = TelegramUpdateHandler(client=mock_client)
    tg_id = user_a._tg_id

    # 1. Direct bank transfer
    wire_update = {
        "update_id": 100030,
        "message": {
            "message_id": 11,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Transfer money to John via UPI 5000",
        }
    }
    await handler.handle_update(wire_update, db_session)
    sent_wire = mock_client.sent_messages[-1]
    assert "personal finance intelligence" in sent_wire["text"]
    assert "do not execute direct bank fund transfers" in sent_wire["text"]

    # 2. Stock trading
    trade_update = {
        "update_id": 100031,
        "message": {
            "message_id": 12,
            "chat": {"id": tg_id, "type": "private"},
            "from": {"id": tg_id, "first_name": "Alpha"},
            "text": "Buy stock of Apple for 50000",
        }
    }
    await handler.handle_update(trade_update, db_session)
    sent_trade = mock_client.sent_messages[-1]
    assert "I do not execute live broker stock orders" in sent_trade["text"]
