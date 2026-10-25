import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.models.user import User
from app.models.financial import FinancialProfile, Transaction, FinancialGoal, Liability
from app.models.bank import BankAccount
from app.finance.intelligence.engine import IntelligenceEngine
from app.ai.tools import AVAILABLE_TOOLS
from app.core.security import create_access_token


@pytest.fixture
def test_user(db_session):
    unique_suffix = uuid.uuid4().hex[:8]
    user = User(
        email=f"intel_{unique_suffix}@finpilot.ai",
        full_name="Intelligence Test User",
        role="salaried",
        auth_provider="local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = FinancialProfile(
        user_id=user.id,
        monthly_income=Decimal("80000.00"),
        monthly_expenses=Decimal("45000.00"),
        risk_tolerance="moderate",
        tax_regime_preference="auto",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_canonical_snapshot_calculation_and_transfer_exclusion(db_session, test_user):
    """
    Verifies canonical snapshot correctly calculates cash flow,
    and explicitly EXCLUDES internal transfers between user accounts.
    """
    today = date.today()

    # Add standard transactions
    tx1 = Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=5),
        amount=Decimal("80000.00"),
        type="income",
        category="Salary",
        description="Monthly Salary Credit",
        is_internal_transfer=False,
    )
    tx2 = Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=4),
        amount=Decimal("20000.00"),
        type="expense",
        category="Rent",
        description="Apartment Rent",
        is_internal_transfer=False,
    )
    # Add an internal transfer of 15000 - MUST NOT be counted as expense
    tx_transfer = Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=3),
        amount=Decimal("15000.00"),
        type="expense",
        category="Transfer",
        description="Transfer to Savings A/C",
        is_internal_transfer=True,
    )
    db_session.add_all([tx1, tx2, tx_transfer])
    db_session.commit()

    snapshot = IntelligenceEngine.get_canonical_snapshot(test_user, db_session, period="current_month")
    assert snapshot.user_id == test_user.id
    assert snapshot.income == Decimal("80000.00")
    assert snapshot.expenses == Decimal("20000.00")  # transfer excluded!
    assert snapshot.net_cash_flow == Decimal("60000.00")
    assert snapshot.savings_rate_pct == 75.0
    assert "Rent" in snapshot.category_spending
    assert "Transfer" not in snapshot.category_spending


def test_recurring_transaction_detection(db_session, test_user):
    """
    Tests deterministic detection of recurring transactions by merchant similarity and periodicity.
    """
    today = date.today()

    # Create 3 monthly Netflix subscriptions
    for i in (60, 30, 2):
        db_session.add(Transaction(
            user_id=test_user.id,
            date=today - timedelta(days=i),
            amount=Decimal("649.00"),
            type="expense",
            category="Entertainment",
            description="Netflix India Subscription",
            is_internal_transfer=False,
        ))
    db_session.commit()

    recurring = IntelligenceEngine.detect_recurring_transactions(test_user, db_session)
    assert len(recurring) >= 1
    netflix_match = next((r for r in recurring if "netflix" in r.merchant_or_desc.lower()), None)
    assert netflix_match is not None
    assert netflix_match.estimated_amount == Decimal("649.00")
    assert netflix_match.frequency in ("monthly", "irregular")
    assert netflix_match.confidence in ("high", "medium")


def test_spending_anomaly_detection_with_thresholds(db_session, test_user):
    """
    Tests deterministic spending anomaly detection when spending in a category
    exceeds baseline by >30% and > ₹2,000.
    """
    today = date.today()

    # Prior baseline spending in Dining: ₹5,000/mo over 60 days
    db_session.add(Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=45),
        amount=Decimal("5000.00"),
        type="expense",
        category="Food & Dining",
        description="Normal Dinner",
        is_internal_transfer=False,
    ))
    # Current month spending in Dining: ₹12,000 (surge of +140% and > ₹2000)
    db_session.add(Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=3),
        amount=Decimal("12000.00"),
        type="expense",
        category="Food & Dining",
        description="Luxury Restaurant Celebration",
        is_internal_transfer=False,
    ))
    db_session.commit()

    anomalies = IntelligenceEngine.detect_spending_anomalies(test_user, db_session)
    assert len(anomalies) >= 1
    dining_anomaly = next((a for a in anomalies if a.category == "Food & Dining"), None)
    assert dining_anomaly is not None
    assert dining_anomaly.current_period_spend == Decimal("12000.00")
    assert dining_anomaly.variance_pct > 30.0
    assert dining_anomaly.severity in ("moderate", "elevated", "critical")


def test_cash_flow_forecasting_30_and_90_days(db_session, test_user):
    """
    Tests cash-flow forecasting logic over 30-day and 90-day horizon with ending balances.
    """
    today = date.today()

    # Add bank account with ₹50,000
    account = BankAccount(
        user_id=test_user.id,
        account_number_masked="XXXX9999",
        institution_name="HDFC Bank",
        account_type="savings",
        ifsc_code="HDFC0001234",
        current_balance=Decimal("50000.00"),
    )
    db_session.add(account)

    # Add income and expense history
    db_session.add(Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=10),
        amount=Decimal("80000.00"),
        type="income",
        category="Salary",
        description="Salary",
        is_internal_transfer=False,
    ))
    db_session.add(Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=8),
        amount=Decimal("30000.00"),
        type="expense",
        category="Living",
        description="Living expenses",
        is_internal_transfer=False,
    ))
    db_session.commit()

    forecast_30 = IntelligenceEngine.forecast_cash_flow(test_user, db_session, horizon_days=30)
    assert forecast_30.horizon_days == 30
    assert forecast_30.projected_income > Decimal("0.00")
    assert forecast_30.projected_expenses > Decimal("0.00")
    assert forecast_30.projected_net > Decimal("0.00")
    assert forecast_30.projected_ending_cash is not None
    assert forecast_30.insufficient_data is False

    forecast_90 = IntelligenceEngine.forecast_cash_flow(test_user, db_session, horizon_days=90)
    assert forecast_90.horizon_days == 90
    assert forecast_90.projected_income >= forecast_30.projected_income


def test_adaptive_budget_recommendations(db_session, test_user):
    """
    Tests 50-30-20 adaptive budgeting recommendations and potential savings computations.
    """
    today = date.today()

    # Spend 40000 on Shopping (discretionary)
    db_session.add(Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=5),
        amount=Decimal("40000.00"),
        type="expense",
        category="Shopping",
        description="Heavy Shopping",
        is_internal_transfer=False,
    ))
    db_session.commit()

    recommendations = IntelligenceEngine.compute_adaptive_budget_recommendations(test_user, db_session)
    assert len(recommendations) >= 1
    shopping_rec = next((r for r in recommendations if r.category == "Shopping"), None)
    assert shopping_rec is not None
    assert shopping_rec.recommended_budget < shopping_rec.historical_average
    assert shopping_rec.potential_savings > Decimal("0.00")


def test_goals_feasibility_and_sensitivity_assessment(db_session, test_user):
    """
    Tests goal feasibility, required SIP calculation, and remediation sensitivity.
    """
    target_date = date.today() + timedelta(days=365)  # 12 months away
    goal = FinancialGoal(
        user_id=test_user.id,
        name="Emergency Corpus",
        category="emergency_fund",
        target_amount=Decimal("240000.00"),
        current_amount=Decimal("0.00"),
        target_date=target_date,
        priority="high"
    )
    db_session.add(goal)
    db_session.commit()

    feasibility_list = IntelligenceEngine.assess_goals_feasibility(test_user, db_session)
    assert len(feasibility_list) >= 1
    corpus_eval = feasibility_list[0]
    assert corpus_eval.target_amount == Decimal("240000.00")
    assert corpus_eval.required_monthly_sip > Decimal("0.00")
    assert isinstance(corpus_eval.is_on_track, bool)
    assert len(corpus_eval.remedial_actions) >= 1


def test_intelligence_feed_generation(db_session, test_user):
    """
    Tests prioritized synthesis of intelligence feed items.
    """
    today = date.today()
    # Add an anomaly
    db_session.add(Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=45),
        amount=Decimal("3000.00"),
        type="expense",
        category="Entertainment",
        description="Movie Ticket",
        is_internal_transfer=False,
    ))
    db_session.add(Transaction(
        user_id=test_user.id,
        date=today - timedelta(days=2),
        amount=Decimal("15000.00"),
        type="expense",
        category="Entertainment",
        description="Music Concert Pass",
        is_internal_transfer=False,
    ))
    db_session.commit()

    feed_response = IntelligenceEngine.generate_intelligence_feed(test_user, db_session)
    assert feed_response.total_insights >= 1
    assert len(feed_response.insights) >= 1


def test_deterministic_ai_tools_execution(db_session, test_user):
    """
    Ensures newly added AI CFO deterministic tools execute with exact parameter handling.
    """
    # 1. Verify tools exist in catalog
    assert "get_cash_flow_forecast" in AVAILABLE_TOOLS
    assert "explain_spending_anomalies" in AVAILABLE_TOOLS
    assert "assess_goal_feasibility" in AVAILABLE_TOOLS

    # 2. Execute forecast tool
    tool_forecast = AVAILABLE_TOOLS["get_cash_flow_forecast"]
    res_fc = tool_forecast({"horizon_days": 30, "monthly_income": 80000, "monthly_expenses": 35000, "liquid_savings": 50000})
    assert res_fc["horizon_days"] == 30
    assert res_fc["projected_income"] == 80000.0
    assert res_fc["projected_expenses"] == 35000.0
    assert res_fc["projected_net_cash_flow"] == 45000.0
    assert "summary" in res_fc

    # 3. Execute anomalies tool
    tool_anomalies = AVAILABLE_TOOLS["explain_spending_anomalies"]
    res_an = tool_anomalies({"category": "Food & Dining", "current_spend": 12000, "baseline_spend": 5000})
    assert res_an["category"] == "Food & Dining"
    assert res_an["variance_amount"] == 7000.0
    assert res_an["is_elevated"] is True

    # 4. Execute goal feasibility tool
    tool_goal = AVAILABLE_TOOLS["assess_goal_feasibility"]
    res_gf = tool_goal({"target_amount": 240000, "current_amount": 0, "months_remaining": 12, "monthly_surplus": 25000})
    assert res_gf["required_monthly_sip"] == 20000.0
    assert res_gf["is_on_track"] is True


def test_intelligence_api_endpoints_and_cross_user_isolation(client, db_session):
    """
    Verifies that all new /api/v1/intelligence/* endpoints require authentication,
    return validated schemas, and enforce strict cross-user isolation.
    """
    # 1. Create User 1 & User 2
    u1_suffix = uuid.uuid4().hex[:8]
    u2_suffix = uuid.uuid4().hex[:8]
    u1 = User(email=f"u1_{u1_suffix}@finpilot.ai", full_name="User One", role="salaried", auth_provider="local")
    u2 = User(email=f"u2_{u2_suffix}@finpilot.ai", full_name="User Two", role="salaried", auth_provider="local")
    db_session.add_all([u1, u2])
    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)

    token1 = create_access_token(subject=u1.id)
    token2 = create_access_token(subject=u2.id)
    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # Add transaction for User 1 only
    tx1 = Transaction(
        user_id=u1.id,
        date=date.today(),
        amount=Decimal("95000.00"),
        type="income",
        category="Consulting",
        description="Private Consulting Invoice",
        is_internal_transfer=False,
    )
    db_session.add(tx1)
    db_session.commit()

    # 2. Test unauthenticated request fails
    unauth = client.get("/api/v1/intelligence/snapshot")
    assert unauth.status_code == 401

    # 3. Test User 1 snapshot sees User 1's income
    res1 = client.get("/api/v1/intelligence/snapshot", headers=h1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["user_id"] == u1.id
    assert float(data1["income"]) == 95000.0

    # 4. Test User 2 snapshot CANNOT see User 1's income (strict user isolation)
    res2 = client.get("/api/v1/intelligence/snapshot", headers=h2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["user_id"] == u2.id
    assert float(data2["income"]) == 0.0  # isolated!

    # 5. Test Feed endpoint
    feed_res = client.get("/api/v1/intelligence/feed", headers=h1)
    assert feed_res.status_code == 200
    assert "insights" in feed_res.json()

    # 6. Test Forecast endpoint
    fc_res = client.get("/api/v1/intelligence/forecast?horizon_days=30", headers=h1)
    assert fc_res.status_code == 200
    assert fc_res.json()["horizon_days"] == 30

    # 7. Test Categorization endpoint
    cat_res = client.post("/api/v1/intelligence/categorize", headers=h1, json={
        "description": "SWIGGY BANGALORE UPI",
        "amount": 450.0
    })
    assert cat_res.status_code == 200
    assert cat_res.json()["suggested_category"] == "Food & Dining"
