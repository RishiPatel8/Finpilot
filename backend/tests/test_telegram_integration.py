import pytest
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.user import User
from app.models.telegram import (
    TelegramAccountLink,
    TelegramLinkCode,
    TelegramProcessedUpdate,
    TelegramNotificationLog,
)
from app.models.financial import FinancialProfile, RecurringTransaction, FinancialGoal, Transaction
from app.models.agent import PendingAction
from app.telegram.client import TelegramClient
from app.telegram.service import telegram_service
from app.telegram.handler import TelegramUpdateHandler
from app.telegram.notifications import NotificationDispatcher


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
def test_user(db_session):
    import uuid
    user = User(
        email=f"telegram_test_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Telegram Test User",
        role="salaried",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    from app.core.security import create_access_token
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_tg_client():
    return MockTelegramClient()


@pytest.fixture
def mock_tg_handler(mock_tg_client):
    return TelegramUpdateHandler(client=mock_tg_client)


@pytest.fixture
def mock_tg_dispatcher(mock_tg_client):
    return NotificationDispatcher(client=mock_tg_client)


def test_telegram_link_code_generation(client: TestClient, auth_headers: dict, test_user: User, db_session):
    """
    Test generating a single-use 15-minute cryptographic link code.
    """
    resp = client.post("/api/v1/telegram/link-code", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "code" in data
    assert data["code"].startswith("FP-")
    assert data["valid_for_seconds"] == 900

    # Verify code exists in DB
    code_record = db_session.query(TelegramLinkCode).filter(TelegramLinkCode.code == data["code"]).first()
    assert code_record is not None
    assert code_record.user_id == test_user.id
    assert code_record.is_used is False

    # Second generation should invalidate the first code
    resp2 = client.post("/api/v1/telegram/link-code", headers=auth_headers)
    assert resp2.status_code == 200
    db_session.refresh(code_record)
    assert code_record.is_used is True  # previous code invalidated


@pytest.mark.asyncio
async def test_telegram_account_linking_and_unlinking(db_session, test_user: User, mock_tg_client, mock_tg_handler):
    """
    Test end-to-end account linking via /start <code>, single-use enforcement, and /unlink.
    """
    # 1. Generate code
    code = telegram_service.generate_link_code(db_session, test_user.id)

    # 2. Link via private chat /start <code_str>
    update = {
        "update_id": 1001,
        "message": {
            "message_id": 1,
            "from": {"id": 987654321, "first_name": "Test", "username": "test_tg_user"},
            "chat": {"id": 987654321, "type": "private"},
            "date": 1700000000,
            "text": f"/start {code.code}",
        },
    }

    res = await mock_tg_handler.handle_update(update, db_session)
    assert res["status"] == "linked"
    assert res["user_id"] == test_user.id

    # Verify DB link
    link = db_session.query(TelegramAccountLink).filter(TelegramAccountLink.user_id == test_user.id).first()
    assert link is not None
    assert link.telegram_user_id == "987654321"
    assert link.is_active is True

    # Code should now be consumed
    db_session.refresh(code)
    assert code.is_used is True

    # 3. Trying to reuse consumed code should fail
    update_reuse = {
        "update_id": 1002,
        "message": {
            "message_id": 2,
            "from": {"id": 11223344, "first_name": "Attacker"},
            "chat": {"id": 11223344, "type": "private"},
            "date": 1700000001,
            "text": f"/start {code.code}",
        },
    }
    res_reuse = await mock_tg_handler.handle_update(update_reuse, db_session)
    assert res_reuse["status"] == "link_error"

    # 4. Status command
    status_update = {
        "update_id": 1003,
        "message": {
            "message_id": 3,
            "from": {"id": 987654321, "first_name": "Test"},
            "chat": {"id": 987654321, "type": "private"},
            "date": 1700000002,
            "text": "/status",
        },
    }
    res_status = await mock_tg_handler.handle_update(status_update, db_session)
    assert res_status["status"] == "connected"

    # 5. Unlink command
    unlink_update = {
        "update_id": 1004,
        "message": {
            "message_id": 4,
            "from": {"id": 987654321, "first_name": "Test"},
            "chat": {"id": 987654321, "type": "private"},
            "date": 1700000003,
            "text": "/unlink",
        },
    }
    res_unlink = await mock_tg_handler.handle_update(unlink_update, db_session)
    assert res_unlink["status"] == "unlinked"

    # Verify link removed in DB
    link_after = db_session.query(TelegramAccountLink).filter(TelegramAccountLink.user_id == test_user.id).first()
    assert link_after is None


@pytest.mark.asyncio
async def test_expired_code_rejected(db_session, test_user: User, mock_tg_handler):
    """
    Test that expired link codes (>15 minutes old) are rejected.
    """
    # Create manually expired code
    expired_code = TelegramLinkCode(
        user_id=test_user.id,
        code="FP-EXPD-CODE",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        is_used=False,
    )
    db_session.add(expired_code)
    db_session.commit()

    update = {
        "update_id": 1005,
        "message": {
            "message_id": 5,
            "from": {"id": 555666, "first_name": "LateUser"},
            "chat": {"id": 555666, "type": "private"},
            "date": 1700000010,
            "text": "/link FP-EXPD-CODE",
        },
    }
    res = await mock_tg_handler.handle_update(update, db_session)
    assert res["status"] == "link_failed"


@pytest.mark.asyncio
async def test_non_private_chat_rejected(db_session, mock_tg_handler):
    """
    Ensure group chats or channels are strictly rejected.
    """
    group_update = {
        "update_id": 1006,
        "message": {
            "message_id": 6,
            "from": {"id": 12345, "first_name": "GroupMember"},
            "chat": {"id": -1001234567, "type": "group"},
            "date": 1700000020,
            "text": "What is my bank balance?",
        },
    }
    res = await mock_tg_handler.handle_update(group_update, db_session)
    assert res["status"] == "rejected_non_private"


@pytest.mark.asyncio
async def test_update_deduplication(db_session, mock_tg_handler):
    """
    Verify that incoming Telegram updates with identical update_id are deduplicated.
    """
    dup_update = {
        "update_id": 8888,
        "message": {
            "message_id": 10,
            "from": {"id": 999, "first_name": "User"},
            "chat": {"id": 999, "type": "private"},
            "date": 1700000030,
            "text": "/help",
        },
    }

    res1 = await mock_tg_handler.handle_update(dup_update, db_session)
    assert res1["status"] == "help_sent"

    res2 = await mock_tg_handler.handle_update(dup_update, db_session)
    assert res2["status"] == "duplicate"


@pytest.mark.asyncio
async def test_cfo_action_confirmation_workflow(db_session, test_user: User, mock_tg_client, mock_tg_handler):
    """
    Verify full Global AI CFO action workflow:
    1. User proposes action: "Add goal Emergency Fund target 250000 by 2027"
    2. PendingAction created in DB awaiting confirmation, inline buttons sent.
    3. User clicks Confirm button (callback_query confirm:<action_id>).
    4. Action executed via ActionExecutor, database record persisted, buttons cleared.
    5. Re-clicking confirm is idempotent / rejected safely.
    """
    # Link test_user
    link = TelegramAccountLink(
        user_id=test_user.id,
        telegram_user_id="777888",
        telegram_chat_id="777888",
        telegram_username="cfo_user",
        is_active=True,
    )
    db_session.add(link)
    db_session.commit()

    # 1. Propose goal creation
    message_update = {
        "update_id": 2001,
        "message": {
            "message_id": 20,
            "from": {"id": 777888, "first_name": "CFOUser"},
            "chat": {"id": 777888, "type": "private"},
            "date": 1700000100,
            "text": "Add goal Emergency Fund target 250000 by 2027",
        },
    }

    res = await mock_tg_handler.handle_update(message_update, db_session)
    assert res["status"] == "action_proposed"
    action_id = res["action_id"]

    # Verify pending action in DB
    pending = db_session.query(PendingAction).filter(PendingAction.id == action_id).first()
    assert pending is not None
    assert pending.status == "awaiting_confirmation"

    # Verify inline keyboard was sent
    assert len(mock_tg_client.sent_messages) > 0
    last_msg = mock_tg_client.sent_messages[-1]
    assert "reply_markup" in last_msg
    assert "inline_keyboard" in last_msg["reply_markup"]

    # 2. Confirm action via callback query
    cb_update = {
        "update_id": 2002,
        "callback_query": {
            "id": "cb_query_1",
            "from": {"id": 777888, "first_name": "CFOUser"},
            "message": {
                "message_id": 21,
                "chat": {"id": 777888, "type": "private"},
            },
            "data": f"confirm:{action_id}",
        },
    }

    cb_res = await mock_tg_handler.handle_update(cb_update, db_session)
    assert cb_res["status"] == "action_executed"
    assert cb_res["result"] == "succeeded"

    # Verify action succeeded in DB
    db_session.refresh(pending)
    assert pending.status == "succeeded"

    # Verify FinancialGoal was actually persisted in DB
    created_goal = db_session.query(FinancialGoal).filter(
        FinancialGoal.user_id == test_user.id,
        FinancialGoal.name.ilike("%Emergency Fund%"),
    ).first()
    assert created_goal is not None
    assert float(created_goal.target_amount) == 250000.0

    # Verify message was edited to remove buttons
    assert len(mock_tg_client.edited_messages) > 0
    last_edit = mock_tg_client.edited_messages[-1]
    assert last_edit["reply_markup"] is None

    # 3. Duplicate confirmation attempt
    dup_cb = {
        "update_id": 2003,
        "callback_query": {
            "id": "cb_query_2",
            "from": {"id": 777888, "first_name": "CFOUser"},
            "message": {
                "message_id": 21,
                "chat": {"id": 777888, "type": "private"},
            },
            "data": f"confirm:{action_id}",
        },
    }
    dup_cb_res = await mock_tg_handler.handle_update(dup_cb, db_session)
    # ActionExecutor returns already executed message
    assert dup_cb_res["status"] == "action_executed"


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_confirm_other_user_action(db_session, test_user: User, mock_tg_handler):
    """
    Ensure User A cannot confirm User B's pending action (strict user isolation).
    """
    # Create User B
    user_b = User(
        email="attacker@test.com",
        full_name="Attacker",
        role="salaried",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.flush()

    link_b = TelegramAccountLink(
        user_id=user_b.id,
        telegram_user_id="999000",
        telegram_chat_id="999000",
        is_active=True,
    )
    db_session.add(link_b)

    # Pending action belongs to test_user (User A)
    pending_a = PendingAction(
        user_id=test_user.id,
        action_type="create_goal",
        target_entity="goal",
        parameters={"name": "Secret Goal", "target_amount": 100000},
        preview={"title": "Create Goal"},
        status="awaiting_confirmation",
        idempotency_key="idemp_test_user_a_123",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db_session.add(pending_a)
    db_session.commit()

    # User B attempts to confirm User A's action
    unauthorized_cb = {
        "update_id": 3001,
        "callback_query": {
            "id": "cb_unauth",
            "from": {"id": 999000, "first_name": "Attacker"},
            "message": {"message_id": 99, "chat": {"id": 999000, "type": "private"}},
            "data": f"confirm:{pending_a.id}",
        },
    }

    res = await mock_tg_handler.handle_update(unauthorized_cb, db_session)
    assert res["status"] == "forbidden"
    db_session.refresh(pending_a)
    assert pending_a.status == "awaiting_confirmation"  # untampered


@pytest.mark.asyncio
async def test_notifications_dispatch_and_deduplication(db_session, test_user: User, mock_tg_client, mock_tg_dispatcher):
    """
    Test outbound notifications for upcoming bills with strict deduplication.
    """
    # Link user
    link = TelegramAccountLink(
        user_id=test_user.id,
        telegram_user_id="888999",
        telegram_chat_id="888999",
        notifications_enabled=True,
        notify_bills=True,
        is_active=True,
    )
    db_session.add(link)

    # Add recurring transaction due tomorrow
    bill = RecurringTransaction(
        user_id=test_user.id,
        name="Broadband Fiber",
        amount=Decimal("1178.00"),
        category="Utilities",
        frequency="monthly",
        status="confirmed",
        next_expected_date=date.today() + timedelta(days=1),
    )
    db_session.add(bill)
    db_session.commit()

    # 1. Dispatch notifications
    sent_count = await mock_tg_dispatcher.dispatch_bill_reminders(db_session, user_id=test_user.id)
    assert sent_count == 1
    assert len(mock_tg_client.sent_messages) == 1
    assert "Broadband Fiber" in mock_tg_client.sent_messages[0]["text"]

    # 2. Re-dispatch: should be deduplicated and not sent again
    sent_count_again = await mock_tg_dispatcher.dispatch_bill_reminders(db_session, user_id=test_user.id)
    assert sent_count_again == 0
    assert len(mock_tg_client.sent_messages) == 1  # No new message


def test_telegram_api_endpoints_and_webhook_security(client: TestClient, auth_headers: dict, test_user: User, db_session):
    """
    Test Web REST endpoints and Webhook security token validation.
    """
    # 1. Status when not linked
    status_res = client.get("/api/v1/telegram/status", headers=auth_headers)
    assert status_res.status_code == 200
    assert status_res.json()["is_linked"] is False

    # 2. Update preferences before link should return 404
    pref_res = client.put("/api/v1/telegram/notifications", headers=auth_headers, json={"notify_bills": False})
    assert pref_res.status_code == 404

    # 3. Create active link
    link = TelegramAccountLink(
        user_id=test_user.id,
        telegram_user_id="333444",
        telegram_chat_id="333444",
        notifications_enabled=True,
        notify_bills=True,
        is_active=True,
    )
    db_session.add(link)
    db_session.commit()

    # 4. Status when linked
    status_res2 = client.get("/api/v1/telegram/status", headers=auth_headers)
    assert status_res2.status_code == 200
    assert status_res2.json()["is_linked"] is True

    # 5. Update preferences
    pref_res2 = client.put("/api/v1/telegram/notifications", headers=auth_headers, json={"notify_bills": False})
    assert pref_res2.status_code == 200
    assert pref_res2.json()["notify_bills"] is False

    # 6. Webhook security: rejected if secret token missing when configured
    settings.TELEGRAM_WEBHOOK_SECRET = "super_secret_webhook_token_xyz"
    try:
        # Request without header
        wh_fail = client.post("/api/v1/telegram/webhook", json={"update_id": 9999})
        assert wh_fail.status_code == 401

        # Request with wrong header
        wh_fail2 = client.post(
            "/api/v1/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_token"},
            json={"update_id": 9999},
        )
        assert wh_fail2.status_code == 401

        # Request with correct header
        wh_success = client.post(
            "/api/v1/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "super_secret_webhook_token_xyz"},
            json={"update_id": 9999},
        )
        assert wh_success.status_code == 200
        assert wh_success.json()["ok"] is True
    finally:
        settings.TELEGRAM_WEBHOOK_SECRET = ""

    # 7. Unlink from Web
    unlink_res = client.post("/api/v1/telegram/unlink", headers=auth_headers)
    assert unlink_res.status_code == 200
    assert unlink_res.json()["success"] is True

    # Status should now be False
    status_res3 = client.get("/api/v1/telegram/status", headers=auth_headers)
    assert status_res3.json()["is_linked"] is False
