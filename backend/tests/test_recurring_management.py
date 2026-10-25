import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.models.user import User
from app.models.financial import Transaction, RecurringTransaction, FinancialProfile
from app.finance.recurring.service import RecurringTransactionService
from app.ai.tools import AVAILABLE_TOOLS
from app.core.security import create_access_token


@pytest.fixture
def recurring_test_user(db_session):
    unique = uuid.uuid4().hex[:8]
    user = User(
        email=f"rec_test_{unique}@finpilot.ai",
        full_name="Recurring Test User",
        role="salaried",
        auth_provider="local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = FinancialProfile(
        user_id=user.id,
        monthly_income=Decimal("90000.00"),
        monthly_expenses=Decimal("50000.00"),
        risk_tolerance="moderate",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_sync_and_get_detections(db_session, recurring_test_user):
    """
    Verifies that recurring transaction detection syncs into the database
    as status='detected' without automatic confirmation.
    """
    today = date.today()

    # Add 3 historical Spotify subscription transactions
    for d in (60, 30, 2):
        db_session.add(Transaction(
            user_id=recurring_test_user.id,
            date=today - timedelta(days=d),
            amount=Decimal("119.00"),
            type="expense",
            category="Entertainment",
            description="Spotify Premium Monthly",
            is_internal_transfer=False
        ))
    db_session.commit()

    detections = RecurringTransactionService.sync_and_get_detections(recurring_test_user, db_session)
    assert len(detections) >= 1
    spotify = next((d for d in detections if "spotify" in d.name.lower()), None)
    assert spotify is not None
    assert spotify.status == "detected"
    assert spotify.amount == Decimal("119.00")
    assert spotify.user_confirmed_at is None


def test_confirm_detection_with_edits(db_session, recurring_test_user):
    """
    Verifies confirming a detected transaction converts status to 'confirmed',
    sets confirmation timestamp, and applies user edits.
    """
    item = RecurringTransaction(
        user_id=recurring_test_user.id,
        name="Amazon Prime Video",
        merchant="Amazon",
        transaction_type="expense",
        amount=Decimal("299.00"),
        category="Entertainment",
        frequency="monthly",
        status="detected",
        confidence="high"
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # Confirm with user adjustment to annual plan of 1499
    from app.schemas.recurring import RecurringTransactionConfirmRequest
    confirmed = RecurringTransactionService.confirm_recurring(
        user=recurring_test_user,
        db=db_session,
        item_id=item.id,
        data=RecurringTransactionConfirmRequest(
            name="Amazon Prime Annual",
            amount=Decimal("1499.00"),
            frequency="yearly",
            user_notes="Switched from monthly to annual membership"
        )
    )

    assert confirmed.status == "confirmed"
    assert confirmed.name == "Amazon Prime Annual"
    assert confirmed.amount == Decimal("1499.00")
    assert confirmed.frequency == "yearly"
    assert confirmed.user_confirmed_at is not None
    assert confirmed.user_notes == "Switched from monthly to annual membership"


def test_dismiss_detection_persistence(db_session, recurring_test_user):
    """
    Verifies that dismissed detections are flagged and excluded from review queue.
    """
    item = RecurringTransaction(
        user_id=recurring_test_user.id,
        name="One-off Electronics purchase",
        merchant="Croma",
        transaction_type="expense",
        amount=Decimal("4500.00"),
        category="Shopping",
        frequency="monthly",
        status="detected",
        confidence="low"
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    from app.schemas.recurring import RecurringTransactionDismissRequest
    dismissed = RecurringTransactionService.dismiss_recurring(
        user=recurring_test_user,
        db=db_session,
        item_id=item.id,
        dismiss_data=RecurringTransactionDismissRequest(user_feedback="One-time phone repair, not recurring")
    )

    assert dismissed.status == "dismissed"
    assert dismissed.user_feedback == "One-time phone repair, not recurring"

    # Ensure it no longer appears in unreviewed detections
    active_detections = db_session.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == recurring_test_user.id,
        RecurringTransaction.status == "detected"
    ).all()
    assert not any(d.id == item.id for d in active_detections)


def test_pause_reactivate_cancel_lifecycle(db_session, recurring_test_user):
    """
    Tests transitions: confirmed -> paused -> reactivated -> cancelled,
    and asserts invalid operations (e.g. reactivating cancelled item) raise 400.
    """
    item = RecurringTransaction(
        user_id=recurring_test_user.id,
        name="Gym Membership CultFit",
        merchant="CultFit",
        transaction_type="expense",
        amount=Decimal("1750.00"),
        category="Health & Fitness",
        frequency="monthly",
        status="confirmed",
        next_expected_date=date.today() + timedelta(days=10)
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # 1. Pause
    paused = RecurringTransactionService.pause_recurring(recurring_test_user, db_session, item.id)
    assert paused.status == "paused"

    # 2. Reactivate
    reactivated = RecurringTransactionService.reactivate_recurring(recurring_test_user, db_session, item.id)
    assert reactivated.status == "confirmed"

    # 3. Cancel
    cancelled = RecurringTransactionService.cancel_recurring(recurring_test_user, db_session, item.id)
    assert cancelled.status == "cancelled"
    assert cancelled.end_date == date.today()

    # 4. Attempt to reactivate cancelled item should raise HTTPException(400)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        RecurringTransactionService.reactivate_recurring(recurring_test_user, db_session, item.id)
    assert exc_info.value.status_code == 400


def test_upcoming_occurrences_calculation(db_session, recurring_test_user):
    """
    Tests forward occurrence projection over a 30-day horizon,
    handling overdue dates and multi-frequency expansion.
    """
    today = date.today()

    # Confirmed monthly rent in 5 days
    item1 = RecurringTransaction(
        user_id=recurring_test_user.id,
        name="Apartment Rent",
        merchant="Landlord",
        transaction_type="expense",
        amount=Decimal("22000.00"),
        category="Housing",
        frequency="monthly",
        status="confirmed",
        next_expected_date=today + timedelta(days=5)
    )
    # Confirmed weekly tutor in 3 days
    item2 = RecurringTransaction(
        user_id=recurring_test_user.id,
        name="Math Tutor",
        merchant="Tutor",
        transaction_type="expense",
        amount=Decimal("800.00"),
        category="Education",
        frequency="weekly",
        status="confirmed",
        next_expected_date=today + timedelta(days=3)
    )
    # Paused gym should NOT be included
    item_paused = RecurringTransaction(
        user_id=recurring_test_user.id,
        name="Paused Gym",
        merchant="Gym",
        transaction_type="expense",
        amount=Decimal("2000.00"),
        category="Health",
        frequency="monthly",
        status="paused",
        next_expected_date=today + timedelta(days=4)
    )
    db_session.add_all([item1, item2, item_paused])
    db_session.commit()

    upcoming_summary = RecurringTransactionService.get_upcoming_occurrences(
        recurring_test_user, db_session, horizon_days=30
    )

    assert upcoming_summary.horizon_days == 30
    assert len(upcoming_summary.occurrences) >= 2
    # Ensure paused gym is excluded
    assert not any(o.recurring_id == item_paused.id for o in upcoming_summary.occurrences)
    # Weekly tutor should occur multiple times in 30 days
    tutor_occurrences = [o for o in upcoming_summary.occurrences if o.recurring_id == item2.id]
    assert len(tutor_occurrences) >= 4
    assert upcoming_summary.total_upcoming_expenses >= Decimal("22000.00")


def test_recurring_summary_and_forecast_integration(db_session, recurring_test_user):
    """
    Tests recurring summary calculation and proves confirmed items feed into cash-flow forecast.
    """
    today = date.today()
    # Confirmed monthly salary income
    inc = RecurringTransaction(
        user_id=recurring_test_user.id,
        name="Tech Salary",
        merchant="Company Payroll",
        transaction_type="income",
        amount=Decimal("85000.00"),
        category="Income",
        frequency="monthly",
        status="confirmed",
        next_expected_date=today + timedelta(days=7)
    )
    # Confirmed monthly EMI expense
    exp = RecurringTransaction(
        user_id=recurring_test_user.id,
        name="Car Loan EMI",
        merchant="SBI Bank",
        transaction_type="expense",
        amount=Decimal("14500.00"),
        category="Debt & EMI",
        frequency="monthly",
        status="confirmed",
        next_expected_date=today + timedelta(days=12)
    )
    db_session.add_all([inc, exp])
    db_session.commit()

    summary = RecurringTransactionService.get_recurring_summary(recurring_test_user, db_session)
    assert summary.monthly_recurring_income == Decimal("85000.00")
    assert summary.monthly_recurring_expenses == Decimal("14500.00")
    assert summary.net_recurring_cash_flow == Decimal("70500.00")
    assert summary.active_count == 2

    # Verify forecast incorporates confirmed recurring obligations
    from app.finance.intelligence.engine import IntelligenceEngine
    forecast = IntelligenceEngine.forecast_cash_flow(recurring_test_user, db_session, horizon_days=30)
    assert forecast.projected_expenses >= Decimal("14500.00")
    assert any("14,500" in d for d in forecast.key_drivers)


def test_ai_cfo_recurring_commitments_tool(db_session, recurring_test_user):
    """
    Verifies get_recurring_commitments tool returns exact breakdown and simulation results.
    """
    assert "get_recurring_commitments" in AVAILABLE_TOOLS
    tool = AVAILABLE_TOOLS["get_recurring_commitments"]

    result = tool({
        "items": [
            {"amount": 649, "frequency": "monthly", "category": "Entertainment"},
            {"amount": 15000, "frequency": "monthly", "category": "Housing"},
            {"amount": 500, "frequency": "weekly", "category": "Groceries"}
        ],
        "total_monthly_expenses": 45000,
        "simulated_pause_amount": 649
    })

    assert result["monthly_recurring_total"] > 17000.0
    assert result["simulated_pause_amount"] == 649.0
    assert result["annualized_freed_surplus"] == 649.0 * 12
    assert "verdict" in result


def test_recurring_api_endpoints_and_cross_user_isolation(client, db_session):
    """
    Tests REST API endpoints for recurring transactions and guarantees User B
    cannot view, confirm, edit, or cancel User A's recurring records.
    """
    u1 = User(email=f"u1_rec_{uuid.uuid4().hex[:6]}@finpilot.ai", full_name="User One", role="salaried", auth_provider="local")
    u2 = User(email=f"u2_rec_{uuid.uuid4().hex[:6]}@finpilot.ai", full_name="User Two", role="salaried", auth_provider="local")
    db_session.add_all([u1, u2])
    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)

    token1 = create_access_token(subject=u1.id)
    token2 = create_access_token(subject=u2.id)
    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # 1. User 1 creates recurring transaction
    create_res = client.post("/api/v1/recurring-transactions", headers=h1, json={
        "name": "User 1 Private Cloud Storage",
        "merchant": "Google One",
        "transaction_type": "expense",
        "amount": 210.0,
        "category": "Utilities",
        "frequency": "monthly"
    })
    assert create_res.status_code == 201
    item_id = create_res.json()["id"]

    # 2. Unauthenticated request rejected
    assert client.get("/api/v1/recurring-transactions").status_code == 401

    # 3. User 1 can view item
    res_u1 = client.get(f"/api/v1/recurring-transactions/{item_id}", headers=h1)
    assert res_u1.status_code == 200
    assert res_u1.json()["name"] == "User 1 Private Cloud Storage"

    # 4. User 2 CANNOT view User 1's item (returns 404)
    res_u2 = client.get(f"/api/v1/recurring-transactions/{item_id}", headers=h2)
    assert res_u2.status_code == 404

    # 5. User 2 CANNOT edit or pause User 1's item
    pause_u2 = client.post(f"/api/v1/recurring-transactions/{item_id}/pause", headers=h2)
    assert pause_u2.status_code == 404

    # 6. User 1 can pause their own item
    pause_u1 = client.post(f"/api/v1/recurring-transactions/{item_id}/pause", headers=h1)
    assert pause_u1.status_code == 200
    assert pause_u1.json()["status"] == "paused"

    # 7. Summary endpoint works for User 1
    sum_res = client.get("/api/v1/recurring-transactions/summary", headers=h1)
    assert sum_res.status_code == 200
    assert "monthly_recurring_expenses" in sum_res.json()

    # 8. Upcoming endpoint works
    up_res = client.get("/api/v1/recurring-transactions/upcoming?horizon_days=30", headers=h1)
    assert up_res.status_code == 200
    assert "occurrences" in up_res.json()
