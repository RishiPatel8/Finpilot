import pytest
from decimal import Decimal
from datetime import date
from app.models.user import User
from app.models.financial import FinancialProfile, Transaction, Liability, FinancialGoal, ScenarioRecord
from app.models.bank import BankAccount, BankConsent
from app.core.security import create_access_token


def test_cross_user_resource_isolation_and_authorization(client, db_session):
    """
    Verifies that User A's resources (goals, transactions, liabilities, scenarios, bank accounts)
    cannot be accessed, viewed, or deleted by User B.
    """
    # 1. Create User A
    user_a = User(
        email="usera_isolation@finpilot.ai",
        full_name="User Alpha",
        role="salaried",
        auth_provider="local"
    )
    db_session.add(user_a)
    db_session.flush()

    token_a = create_access_token(subject=user_a.id)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Create User B
    user_b = User(
        email="userb_isolation@finpilot.ai",
        full_name="User Beta",
        role="freelancer",
        auth_provider="local"
    )
    db_session.add(user_b)
    db_session.flush()

    token_b = create_access_token(subject=user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates resources
    # Goal
    goal_res = client.post("/api/v1/goals", headers=headers_a, json={
        "name": "Alpha Emergency Fund",
        "category": "emergency_fund",
        "target_amount": 500000.0,
        "current_amount": 150000.0,
        "target_date": "2026-12-31",
        "priority": "high"
    })
    assert goal_res.status_code == 201
    goal_a_id = goal_res.json()["id"]

    # Transaction
    txn_res = client.post("/api/v1/transactions", headers=headers_a, json={
        "date": "2026-10-24",
        "amount": 2500.0,
        "type": "expense",
        "category": "Shopping",
        "description": "Alpha Private Purchase",
        "source": "manual",
        "is_recurring": False
    })
    assert txn_res.status_code == 201
    txn_a_id = txn_res.json()["id"]

    # Liability
    liability_res = client.post("/api/v1/liabilities", headers=headers_a, json={
        "name": "Alpha Car Loan",
        "principal": 450000.0,
        "interest_rate": 9.2,
        "monthly_emi": 11500.0,
        "tenure_months": 48,
        "remaining_months": 36
    })
    assert liability_res.status_code == 201
    liability_a_id = liability_res.json()["id"]

    # Scenario
    scenario_res = client.post("/api/v1/scenarios/save", headers=headers_a, json={
        "title": "Alpha Downpayment Simulation",
        "scenario_type": "major_purchase",
        "input_data": {"monthlyIncome": 150000},
        "result_data": {"viable": True}
    })
    assert scenario_res.status_code == 201
    scenario_a_id = scenario_res.json()["id"]

    # Bank Account
    bank_acc_a = BankAccount(
        user_id=user_a.id,
        institution_name="HDFC Bank",
        account_number_masked="XXXX-XXXX-9999",
        account_type="savings",
        ifsc_code="HDFC0001234",
        current_balance=Decimal("250000.00"),
        balance_type="provider_reported",
        sync_status="synced"
    )
    db_session.add(bank_acc_a)
    db_session.commit()
    db_session.refresh(bank_acc_a)
    bank_a_id = bank_acc_a.id

    # 4. User B attempts to access User A's data (must return empty or filtered)
    b_goals = client.get("/api/v1/goals", headers=headers_b).json()
    assert not any(g["id"] == goal_a_id for g in b_goals)

    b_txns = client.get("/api/v1/transactions", headers=headers_b).json()
    assert not any(t["id"] == txn_a_id for t in b_txns)

    b_liabilities = client.get("/api/v1/liabilities", headers=headers_b).json()
    assert not any(l["id"] == liability_a_id for l in b_liabilities)

    b_scenarios = client.get("/api/v1/scenarios", headers=headers_b).json()
    assert not any(s["id"] == scenario_a_id for s in b_scenarios)

    b_bank_accs = client.get("/api/v1/bank/accounts", headers=headers_b).json()
    assert not any(ba["id"] == bank_a_id for ba in b_bank_accs)

    # 5. User B attempts to DELETE User A's resources (must be rejected with 404)
    del_goal_res = client.delete(f"/api/v1/goals/{goal_a_id}", headers=headers_b)
    assert del_goal_res.status_code == 404

    del_txn_res = client.delete(f"/api/v1/transactions/{txn_a_id}", headers=headers_b)
    assert del_txn_res.status_code == 404

    del_liability_res = client.delete(f"/api/v1/liabilities/{liability_a_id}", headers=headers_b)
    assert del_liability_res.status_code == 404

    del_scenario_res = client.delete(f"/api/v1/scenarios/{scenario_a_id}", headers=headers_b)
    assert del_scenario_res.status_code == 404

    del_bank_res = client.delete(f"/api/v1/bank/accounts/{bank_a_id}", headers=headers_b)
    assert del_bank_res.status_code == 404

    # 6. Verify User A's resources are still intact in User A's queries
    a_goals_after = client.get("/api/v1/goals", headers=headers_a).json()
    assert any(g["id"] == goal_a_id for g in a_goals_after)

    a_txns_after = client.get("/api/v1/transactions", headers=headers_a).json()
    assert any(t["id"] == txn_a_id for t in a_txns_after)


def test_schema_input_validation_boundaries(client, db_session):
    """
    Verifies that invalid input bounds (negative amounts, absurd ages) are strictly rejected with 422.
    """
    user = User(
        email="validator_user@finpilot.ai",
        full_name="Validation Tester",
        role="salaried",
        auth_provider="local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Negative transaction amount should fail validation (HTTP 422)
    bad_txn = client.post("/api/v1/transactions", headers=headers, json={
        "date": "2026-10-24",
        "amount": -500.0,
        "type": "expense",
        "category": "Food",
        "description": "Invalid negative transaction"
    })
    assert bad_txn.status_code == 422

    # 2. Negative liability principal should fail validation (HTTP 422)
    bad_liability = client.post("/api/v1/liabilities", headers=headers, json={
        "name": "Invalid Debt",
        "principal": -100000.0,
        "interest_rate": 10.0,
        "monthly_emi": 5000.0,
        "tenure_months": 24,
        "remaining_months": 24
    })
    assert bad_liability.status_code == 422

    # 3. Negative goal target should fail validation (HTTP 422)
    bad_goal = client.post("/api/v1/goals", headers=headers, json={
        "name": "Invalid Goal",
        "category": "custom",
        "target_amount": -50000.0,
        "current_amount": 0.0,
        "target_date": "2026-12-31"
    })
    assert bad_goal.status_code == 422

    # 4. Underage (< 18) profile should fail validation (HTTP 422)
    bad_profile = client.put("/api/v1/profile", headers=headers, json={
        "age": 14,
        "monthly_income": 50000.0,
        "monthly_expenses": 20000.0
    })
    assert bad_profile.status_code == 422
