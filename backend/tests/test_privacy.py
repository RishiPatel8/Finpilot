import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.user import User
from app.models.financial import FinancialProfile, Transaction

def test_export_data_and_account_deletion(client, db_session):

    user = User(
        email="privacy_user@finpilot.ai",
        full_name="Privacy Tester",
        role="salaried",
        auth_provider="local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = FinancialProfile(
        user_id=user.id,
        monthly_income=120000.0,
        monthly_expenses=55000.0,
        risk_tolerance="moderate"
    )
    txn = Transaction(
        user_id=user.id,
        amount=5000.0,
        type="expense",
        category="Food & Dining",
        description="Grocery Store"
    )
    db_session.add(profile)
    db_session.add(txn)
    db_session.commit()

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test Data Export
    res = client.get("/api/v1/auth/export-data", headers=headers)
    assert res.status_code == 200
    export_payload = res.json()
    assert export_payload["user"]["email"] == "privacy_user@finpilot.ai"
    assert export_payload["financial_profile"]["monthly_income"] == 120000.0
    assert len(export_payload["transactions"]) == 1
    assert export_payload["transactions"][0]["description"] == "Grocery Store"

    # 2. Test Account Deletion
    del_res = client.delete("/api/v1/auth/me", headers=headers)
    assert del_res.status_code == 204

    # Verify user record is gone
    deleted_user = db_session.query(User).filter(User.id == user.id).first()
    assert deleted_user is None

    # Subsequent request with token fails (User not found)
    unauth_res = client.get("/api/v1/auth/me", headers=headers)
    assert unauth_res.status_code == 404

