import pytest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from app.models.user import User
from app.models.bank import BankAccount
from app.models.financial import (
    FinancialProfile,
    AssetHolding,
    Liability,
    FinancialGoal,
    Transaction,
    RecurringTransaction,
    ChatMessage
)
from app.ai.financial_context import FinancialContextService
from app.ai.tools import AVAILABLE_TOOLS, FinancialToolsRegistry


def test_financial_context_service_guest_and_empty_user(db_session):
    """Verifies graceful handling of guest demo and users with minimal or empty records."""
    # 1. Guest zero-mock-data context
    guest_ctx = FinancialContextService.get_complete_financial_context(None, db_session)
    assert guest_ctx["user_id"] == "guest"
    assert guest_ctx["is_guest_demo"] is False
    assert guest_ctx["monthly_income"] == 0.0
    assert guest_ctx["active_page"] == "overview"

    # 2. Freshly created user with no linked data
    user = User(
        email="empty_cfo_user@example.com",
        full_name="Empty User",
        role="salaried"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    user_ctx = FinancialContextService.get_complete_financial_context(
        user,
        db_session,
        page_context={"page": "budget", "selected_category": "Dining"}
    )
    assert user_ctx["user_id"] == user.id
    assert user_ctx["monthly_income"] == 0.0
    assert user_ctx["verified_bank_balance"] == 0.0
    assert user_ctx["active_page"] == "budget"
    assert user_ctx["page_metadata"]["selected_category"] == "Dining"


def test_financial_context_service_comprehensive_assembly(db_session):
    """Verifies full canonical aggregation across accounts, debts, recurring, and transactions."""
    user = User(
        email="rich_cfo_user@example.com",
        full_name="Rich User",
        role="salaried"
    )
    db_session.add(user)
    db_session.flush()

    # Profile
    profile = FinancialProfile(
        user_id=user.id,
        monthly_income=120000.0,
        monthly_expenses=55000.0,
        age=32,
        dependents=1
    )
    db_session.add(profile)

    # Bank account
    acc = BankAccount(
        user_id=user.id,
        institution_name="HDFC Bank",
        account_number_masked="XXXX-1234",
        account_type="savings",
        ifsc_code="HDFC0000001",
        current_balance=250000.0,
        sync_status="synced",
        balance_timestamp=datetime.now(timezone.utc)
    )
    db_session.add(acc)

    # Liabilities / EMI
    liab = Liability(
        user_id=user.id,
        name="Auto Loan",
        principal=400000.0,
        interest_rate=8.5,
        monthly_emi=14500.0,
        tenure_months=36,
        remaining_months=24
    )
    db_session.add(liab)

    # Recurring commitment
    rec = RecurringTransaction(
        user_id=user.id,
        name="Gym Membership",
        amount=2500.0,
        frequency="monthly",
        status="confirmed",
        category="Fitness",
        transaction_type="expense",
        next_expected_date=date.today() + timedelta(days=5)
    )
    db_session.add(rec)

    # Transaction
    txn = Transaction(
        user_id=user.id,
        date=date.today() - timedelta(days=2),
        amount=2500.0,
        type="expense",
        category="Fitness",
        description="Gym Membership Monthly Fee"
    )
    db_session.add(txn)

    db_session.commit()

    ctx = FinancialContextService.get_complete_financial_context(user, db_session)

    assert ctx["monthly_income"] == 120000.0
    assert ctx["monthly_expenses"] == 55000.0
    assert ctx["verified_bank_balance"] == 250000.0
    assert ctx["total_debt"] == 400000.0
    assert ctx["monthly_emi"] == 14500.0
    assert ctx["confirmed_recurring_count"] == 1
    assert ctx["recurring_monthly_expenses"] == 2500.0
    assert ctx["recent_transactions_count"] >= 1


def test_deterministic_evaluate_affordability_tool():
    """Tests the cross-feature affordability tool for various financial conditions."""
    # Case 1: Healthy & Comfortable
    params_healthy = {
        "proposed_amount": 15000.0,
        "item_type": "emi",
        "monthly_income": 120000.0,
        "monthly_expenses": 50000.0,
        "monthly_emi": 10000.0,
        "recurring_monthly_expenses": 5000.0,
        "current_savings": 300000.0
    }
    res_healthy = FinancialToolsRegistry.evaluate_affordability(params_healthy)
    assert res_healthy["status"] == "Comfortably Affordable"
    assert res_healthy["revised_net_surplus"] == 45000.0
    assert res_healthy["new_debt_to_income_pct"] == round((25000.0 / 120000.0) * 100, 1)

    # Case 2: Deficit / Not Affordable
    params_deficit = {
        "proposed_amount": 35000.0,
        "item_type": "emi",
        "monthly_income": 60000.0,
        "monthly_expenses": 45000.0,
        "monthly_emi": 5000.0,
        "current_savings": 50000.0
    }
    res_deficit = FinancialToolsRegistry.evaluate_affordability(params_deficit)
    assert res_deficit["status"] == "Not Affordable / Deficit"
    assert res_deficit["revised_net_surplus"] < 0

    # Case 3: High Risk DTI
    params_high_dti = {
        "proposed_amount": 30000.0,
        "item_type": "emi",
        "monthly_income": 80000.0,
        "monthly_expenses": 30000.0,
        "monthly_emi": 15000.0,  # Total EMI becomes 45k on 80k income = 56.25% DTI
        "current_savings": 200000.0
    }
    res_high_dti = FinancialToolsRegistry.evaluate_affordability(params_high_dti)
    assert res_high_dti["status"] == "High Risk / Tight"
    assert res_high_dti["new_debt_to_income_pct"] > 45.0


def test_deterministic_portfolio_and_budget_tools():
    """Tests overview, account balances, net worth, and overspending tools."""
    # 1. Overview
    ov = FinancialToolsRegistry.get_financial_overview({
        "monthly_income": 100000.0,
        "monthly_expenses": 40000.0,
        "current_savings": 240000.0,
        "total_debt": 0.0,
        "monthly_emi": 0.0
    })
    assert ov["net_monthly_surplus"] == 60000.0
    assert ov["savings_rate_pct"] == 60.0
    assert ov["emergency_runway_months"] == 6.0

    # 2. Upcoming Obligations
    rec = FinancialToolsRegistry.get_upcoming_obligations({
        "recurring_commitments": [
            {"name": "Broadband", "monthly_normalized": 1200.0, "type": "expense", "frequency": "monthly"},
            {"name": "Streaming", "monthly_normalized": 800.0, "type": "expense", "frequency": "monthly"}
        ],
        "liabilities_list": [
            {"name": "Home Loan", "monthly_emi": 22000.0}
        ]
    })
    assert rec["total_upcoming_30d"] == 24000.0
    assert rec["obligations_count"] == 3

    # 3. Overspending
    over = FinancialToolsRegistry.find_overspending({
        "budget_categories": [{"category": "Dining", "monthly_allocation": 5000.0}],
        "category_spending": {"Dining": 7500.0},
        "spending_anomalies": [{"category": "Dining", "explanation": "Spike in restaurants", "deviation_pct": 50.0}]
    })
    assert len(over["overspent_budgets"]) == 1
    assert over["action_required"] is True


def test_ai_cfo_chat_endpoint_affordability_flow(client, monkeypatch):
    """Verifies that the /assistant/chat endpoint performs cross-feature reasoning."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")

    # Register test user
    reg = client.post("/api/v1/auth/register", json={
        "email": "affordability_test@example.com",
        "password": "Password123!",
        "full_name": "Affordability User",
        "role": "salaried"
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query with affordability intent
    res = client.post("/api/v1/assistant/chat", json={
        "message": "Can I afford a ₹25,000 monthly EMI?",
        "page_context": {"page": "debts"}
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert "Affordability Assessment" in data["content"]
    assert "Debt-to-Income" in data["content"]
    assert any(t["tool"] == "evaluate_affordability" for t in data["tool_invocations"])
    assert data["active_page"] == "debts"


def test_ai_cfo_chat_endpoint_recurring_and_overspending(client, monkeypatch):
    """Verifies recurring obligations and overspending queries return rich tool data."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")

    reg = client.post("/api/v1/auth/register", json={
        "email": "query_flows@example.com",
        "password": "Password123!",
        "full_name": "Query Flow User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upcoming recurring payments
    res_rec = client.post("/api/v1/assistant/chat", json={
        "message": "What recurring payments do I have next month?",
        "page_context": {"page": "recurring"}
    }, headers=headers)
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert "Upcoming Obligations" in rec_data["content"]
    assert any(t["tool"] == "get_upcoming_obligations" for t in rec_data["tool_invocations"])

    # 2. Overspending query
    res_bgt = client.post("/api/v1/assistant/chat", json={
        "message": "Why am I overspending this month?",
        "page_context": {"page": "budget"}
    }, headers=headers)
    assert res_bgt.status_code == 200
    bgt_data = res_bgt.json()
    assert "Spending Variance" in bgt_data["content"] or "Overspending" in bgt_data["content"]


def test_proactive_insights_endpoint(client):
    """Verifies proactive insights generation when opening the assistant."""
    reg = client.post("/api/v1/auth/register", json={
        "email": "proactive_insights@example.com",
        "password": "Password123!",
        "full_name": "Insight User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/assistant/proactive-insights", headers=headers)
    assert res.status_code == 200
    insights = res.json()
    assert isinstance(insights, list)
    assert len(insights) > 0
    first = insights[0]
    assert "id" in first
    assert "title" in first
    assert "priority" in first
    assert "suggested_prompt" in first


def test_conversation_history_persistence_and_clearing(client):
    """Verifies message storage, user-isolation, and clearing of chat history."""
    # User 1
    reg1 = client.post("/api/v1/auth/register", json={
        "email": "chat_user1@example.com",
        "password": "Password123!",
        "full_name": "Chat User 1",
        "role": "salaried"
    })
    token1 = reg1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # User 2
    reg2 = client.post("/api/v1/auth/register", json={
        "email": "chat_user2@example.com",
        "password": "Password123!",
        "full_name": "Chat User 2",
        "role": "salaried"
    })
    token2 = reg2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 chats
    client.post("/api/v1/assistant/chat", json={"message": "What is my net worth?"}, headers=headers1)

    # Verify User 1 has 2 messages (1 user, 1 assistant)
    hist1 = client.get("/api/v1/assistant/history", headers=headers1).json()
    assert len(hist1) >= 2
    assert any("net worth" in m["content"].lower() for m in hist1)

    # Verify User 2 sees 0 messages (strict cross-user isolation)
    hist2 = client.get("/api/v1/assistant/history", headers=headers2).json()
    assert len(hist2) == 0

    # User 1 clears history
    del_res = client.delete("/api/v1/assistant/history", headers=headers1)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # User 1 history is now empty
    hist1_after = client.get("/api/v1/assistant/history", headers=headers1).json()
    assert len(hist1_after) == 0
