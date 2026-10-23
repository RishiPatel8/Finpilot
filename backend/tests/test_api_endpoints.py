import pytest
from decimal import Decimal


def test_auth_register_and_login_flow(client):
    # Register
    reg_payload = {
        "email": "testuser@example.com",
        "full_name": "Rohan Sharma",
        "password": "Password123!",
        "role": "salaried"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == "testuser@example.com"

    # Login
    login_payload = {
        "email": "testuser@example.com",
        "password": "Password123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token

    # /auth/me with valid token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Rohan Sharma"

    # /auth/me without token should be 401
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401


def test_profile_and_dashboard_flow(client):
    # Register a new user
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "priya@example.com",
        "full_name": "Priya Nair",
        "password": "SecurePassword456!",
        "role": "freelancer"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update Profile
    update_res = client.put("/api/v1/profile", headers=headers, json={
        "age": 28,
        "dependents": 0,
        "monthly_income": 120000.0,
        "monthly_expenses": 50000.0,
        "risk_tolerance": "moderate"
    })
    assert update_res.status_code == 200
    assert float(update_res.json()["monthly_income"]) == 120000.0

    # Seed demo data
    seed_res = client.post("/api/v1/demo/seed", headers=headers)
    assert seed_res.status_code == 200

    # Check Dashboard Summary
    dash_res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert float(data["monthly_income"]) > 0
    assert float(data["total_assets"]) > 0
    assert float(data["total_liabilities"]) > 0
    assert len(data["recent_transactions"]) > 0
    assert len(data["goals"]) > 0


def test_transactions_crud_and_csv_flow(client):
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "amit@example.com",
        "full_name": "Amit Patel",
        "password": "Password789!",
        "role": "salaried"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create transaction
    txn_res = client.post("/api/v1/transactions", headers=headers, json={
        "date": "2024-05-15",
        "amount": 1500.0,
        "type": "expense",
        "category": "Food & Dining",
        "description": "Team lunch at Social",
        "source": "manual",
        "is_recurring": False
    })
    assert txn_res.status_code == 201
    txn_id = txn_res.json()["id"]

    # List transactions
    list_res = client.get("/api/v1/transactions", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Delete transaction
    del_res = client.delete(f"/api/v1/transactions/{txn_id}", headers=headers)
    assert del_res.status_code == 204


def test_tax_compare_api(client):
    payload = {
        "assessment_year": "2025-26",
        "taxpayer_type": "salaried",
        "gross_annual_salary": 1200000.0,
        "section_80c": 150000.0,
        "section_80d": 25000.0
    }
    res = client.post("/api/v1/tax/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["recommended_regime"] in ["new", "old"]
    assert "new_regime" in data
    assert "old_regime" in data


def test_investments_compare_api(client):
    payload = {
        "investment_amount": 250000.0,
        "time_horizon_months": 6,
        "can_lock_funds": False
    }
    res = client.post("/api/v1/investments/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["comparisons"]) == 3
    assert data["top_recommendation"] == "Liquid Mutual Fund"


def test_goals_api_flow(client):
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "ananya@example.com",
        "full_name": "Ananya Sen",
        "password": "Password999!",
        "role": "salaried"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create goal
    goal_res = client.post("/api/v1/goals", headers=headers, json={
        "name": "Japan Vacation",
        "category": "custom",
        "target_amount": 300000.0,
        "current_amount": 50000.0,
        "target_date": "2025-12-31",
        "priority": "high"
    })
    assert goal_res.status_code == 201
    g_data = goal_res.json()
    assert float(g_data["monthly_required"]) > 0

    # List goals
    list_res = client.get("/api/v1/goals", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_assistant_chat_api(client):
    chat_res = client.post("/api/v1/assistant/chat", json={
        "message": "Which is better: liquid fund or bond for 6 months?"
    })
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "content" in data
    assert len(data["citations"]) > 0
