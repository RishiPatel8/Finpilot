import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.user import User
from app.models.financial import Liability




@pytest.fixture
def test_user_a(db_session):
    user = User(
        email="debt_user_a@finpilot.ai",
        full_name="User A",
        role="salaried",
        auth_provider="local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_b(db_session):
    user = User(
        email="debt_user_b@finpilot.ai",
        full_name="User B",
        role="salaried",
        auth_provider="local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_liabilities_crud_and_avalanche_vs_snowball(client, test_user_a, test_user_b, db_session):
    token_a = create_access_token(subject=test_user_a.id)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    token_b = create_access_token(subject=test_user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Initial liabilities should be empty
    res = client.get("/api/v1/liabilities", headers=headers_a)
    assert res.status_code == 200
    assert res.json() == []

    # 2. Add Home Loan (Lower interest rate, higher principal)
    res_hl = client.post(
        "/api/v1/liabilities",
        headers=headers_a,
        json={
            "name": "HDFC Home Loan",
            "principal": 3500000.0,
            "interest_rate": 8.5,
            "monthly_emi": 32000.0,
            "tenure_months": 240,
            "remaining_months": 210
        }
    )
    assert res_hl.status_code == 201
    hl_id = res_hl.json()["id"]
    assert res_hl.json()["name"] == "HDFC Home Loan"

    # 3. Add Credit Card Debt (Higher interest rate, lower principal)
    res_cc = client.post(
        "/api/v1/liabilities",
        headers=headers_a,
        json={
            "name": "ICICI Credit Card",
            "principal": 85000.0,
            "interest_rate": 42.0,
            "monthly_emi": 8500.0,
            "tenure_months": 12,
            "remaining_months": 10
        }
    )
    assert res_cc.status_code == 201
    cc_id = res_cc.json()["id"]
    assert res_cc.json()["name"] == "ICICI Credit Card"

    # 4. Add Personal Loan (Intermediate interest rate and principal)
    res_pl = client.post(
        "/api/v1/liabilities",
        headers=headers_a,
        json={
            "name": "Axis Personal Loan",
            "principal": 250000.0,
            "interest_rate": 14.5,
            "monthly_emi": 11500.0,
            "tenure_months": 36,
            "remaining_months": 24
        }
    )
    assert res_pl.status_code == 201
    pl_id = res_pl.json()["id"]

    # 5. Verify user isolation: User B should see 0 liabilities
    res_b = client.get("/api/v1/liabilities", headers=headers_b)
    assert res_b.status_code == 200
    assert res_b.json() == []

    # User B cannot delete User A's liability
    del_forbidden = client.delete(f"/api/v1/liabilities/{hl_id}", headers=headers_b)
    assert del_forbidden.status_code == 404

    # 6. Test Repayment Plan (Avalanche vs Snowball)
    plan_res = client.post(
        "/api/v1/liabilities/repayment-plan",
        headers=headers_a,
        json={"extra_monthly_payment": 5000.0}
    )
    assert plan_res.status_code == 200
    data = plan_res.json()
    assert float(data["total_debt_principal"]) == 3500000.0 + 85000.0 + 250000.0
    assert float(data["total_monthly_emi"]) == 32000.0 + 8500.0 + 11500.0
    assert float(data["extra_payment_applied"]) == 5000.0

    # Avalanche priority (highest interest first: 42% CC -> 14.5% PL -> 8.5% HL)
    assert data["avalanche_priority"] == ["ICICI Credit Card", "Axis Personal Loan", "HDFC Home Loan"]

    # Snowball priority (lowest principal first: 85k CC -> 250k PL -> 35L HL)
    assert data["snowball_priority"] == ["ICICI Credit Card", "Axis Personal Loan", "HDFC Home Loan"]

    # 7. Delete liability
    del_res = client.delete(f"/api/v1/liabilities/{cc_id}", headers=headers_a)
    assert del_res.status_code == 204

    # Verify only 2 remaining
    res_after = client.get("/api/v1/liabilities", headers=headers_a)
    assert len(res_after.json()) == 2
