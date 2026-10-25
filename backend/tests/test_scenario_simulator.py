from decimal import Decimal
import pytest
from app.schemas.scenario import ScenarioInput
from app.finance.scenarios.engine import ScenarioEngine


def test_major_purchase_simulation_car_purchase():
    # User earns 60k, spends 35k, has 2L savings, wants to buy 8L car in 18 months
    inp = ScenarioInput(
        scenario_type="major_purchase",
        monthly_income=Decimal("60000.00"),
        monthly_expenses=Decimal("35000.00"),
        current_savings=Decimal("200000.00"),
        target_amount=Decimal("800000.00"),
        time_horizon_months=18
    )
    result = ScenarioEngine.simulate(inp)

    assert result.scenario_type == "major_purchase"
    assert result.baseline_surplus == Decimal("25000.00")
    # Required SIP > surplus, so gap is negative (shortfall)
    assert result.cash_flow_gap < Decimal("0.00")
    assert result.is_feasible is False
    # Safety reserve is maintained (projected runway is 3 months)
    assert result.projected_runway_months == 3.0
    # Alternative options provided
    assert len(result.alternative_options) >= 2
    assert any("Auto Loan" in opt.name for opt in result.alternative_options)


def test_increase_savings_simulation():
    inp = ScenarioInput(
        scenario_type="increase_savings",
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("60000.00"),
        current_savings=Decimal("300000.00"),
        target_savings_rate_pct=Decimal("50.0")
    )
    result = ScenarioEngine.simulate(inp)

    assert result.scenario_type == "increase_savings"
    assert result.baseline_surplus == Decimal("40000.00")
    assert result.scenario_surplus == Decimal("50000.00")
    assert result.cash_flow_gap == Decimal("10000.00")
    assert len(result.timeline_projections) == 3


def test_expense_reduction_simulation():
    inp = ScenarioInput(
        scenario_type="expense_reduction",
        monthly_income=Decimal("80000.00"),
        monthly_expenses=Decimal("50000.00"),
        current_savings=Decimal("150000.00"),
        expense_reduction_amount=Decimal("5000.00")
    )
    result = ScenarioEngine.simulate(inp)

    assert result.scenario_type == "expense_reduction"
    assert result.scenario_surplus == Decimal("35000.00")
    assert len(result.comparisons) == 2


def test_scenarios_api_endpoint(client):
    res = client.post("/api/v1/scenarios/simulate", json={
        "scenario_type": "major_purchase",
        "monthly_income": 60000.0,
        "monthly_expenses": 35000.0,
        "current_savings": 200000.0,
        "target_amount": 800000.0,
        "time_horizon_months": 18
    })
    assert res.status_code == 200
    data = res.json()
    assert "summary_verdict" in data
    assert len(data["alternative_options"]) > 0


def test_scenario_persistence_and_user_isolation(client):
    """Verify saved scenarios persist and cannot be accessed or deleted by another user."""
    # 1. Register User A
    user_a = client.post("/api/v1/auth/register", json={
        "email": "user_alpha_test@example.com",
        "full_name": "User Alpha",
        "password": "Password123!",
        "role": "salaried"
    }).json()
    token_a = user_a["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. User A saves a scenario
    save_res = client.post("/api/v1/scenarios/save", json={
        "title": "Alpha Car Goal",
        "scenario_type": "major_purchase",
        "input_data": {"target": 800000},
        "result_data": {"feasible": True}
    }, headers=headers_a)
    assert save_res.status_code == 201
    scenario_id = save_res.json()["id"]

    # Verify User A can list it
    list_a = client.get("/api/v1/scenarios", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1
    assert list_a.json()[0]["id"] == scenario_id

    # 3. Register User B
    user_b = client.post("/api/v1/auth/register", json={
        "email": "user_beta_test@example.com",
        "full_name": "User Beta",
        "password": "Password123!",
        "role": "salaried"
    }).json()
    token_b = user_b["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 4. User B checks saved scenarios -> MUST BE EMPTY (isolation verified!)
    list_b = client.get("/api/v1/scenarios", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0

    # 5. User B tries to delete User A's scenario -> MUST BE 404 NOT FOUND
    del_res = client.delete(f"/api/v1/scenarios/{scenario_id}", headers=headers_b)
    assert del_res.status_code == 404

    # 6. User A gets single scenario
    get_res = client.get(f"/api/v1/scenarios/{scenario_id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Alpha Car Goal"

    # 7. User A updates/renames scenario
    put_res = client.put(f"/api/v1/scenarios/{scenario_id}", json={
        "title": "Alpha Car Goal - Renamed",
        "input_data": {"target": 900000}
    }, headers=headers_a)
    assert put_res.status_code == 200
    assert put_res.json()["title"] == "Alpha Car Goal - Renamed"


def test_vehicle_decision_simulation():
    """Verify car purchase decision analysis with loan, ongoing fuel/insurance, options and stress tests."""
    inp = ScenarioInput(
        scenario_type="vehicle",
        monthly_income=Decimal("80000.00"),
        monthly_expenses=Decimal("40000.00"),
        current_savings=Decimal("300000.00"),
        existing_monthly_emi=Decimal("5000.00"),
        purchase_price=Decimal("1000000.00"),
        down_payment=Decimal("200000.00"),
        loan_interest_rate_pct=Decimal("9.5"),
        loan_tenure_months=60,
        monthly_ongoing_costs=Decimal("4000.00"),
        upfront_one_time_costs=Decimal("30000.00")
    )
    result = ScenarioEngine.simulate(inp)

    assert result.scenario_type == "vehicle"
    assert result.loan_analysis is not None
    assert result.loan_analysis.principal_borrowed == 800000.0
    assert result.loan_analysis.monthly_emi > 0.0
    assert result.cash_flow_impact.available_surplus_before == 35000.0  # 80k - 40k - 5k
    assert result.cash_flow_impact.projected_surplus_after < 35000.0
    assert len(result.alternative_options) == 3
    assert len(result.stress_tests) == 5
    assert result.savings_impact.initial_cash_required == 238000.0  # 200k down + 30k upfront + 8k proc fee (1%)
    assert result.savings_impact.remaining_liquid_savings == 62000.0  # 300k - 238k


def test_house_decision_simulation():
    """Verify home purchase with 20-year amortization, stamp duty, and DTI tracking."""
    inp = ScenarioInput(
        scenario_type="house",
        monthly_income=Decimal("150000.00"),
        monthly_expenses=Decimal("60000.00"),
        current_savings=Decimal("2500000.00"),
        purchase_price=Decimal("6000000.00"),
        down_payment=Decimal("1200000.00"),
        loan_interest_rate_pct=Decimal("8.5"),
        loan_tenure_months=240,
        monthly_ongoing_costs=Decimal("3000.00")
    )
    result = ScenarioEngine.simulate(inp)

    assert result.scenario_type == "house"
    assert result.loan_analysis is not None
    assert result.loan_analysis.principal_borrowed == 4800000.0
    assert result.loan_analysis.tenure_months == 240
    assert result.cash_flow_impact.debt_to_income_after_pct > 0.0
    assert result.is_feasible is True
    assert len(result.stress_tests) == 5


def test_cash_vs_loan_decision_simulation():
    """Verify cash vs loan decision evaluation with opportunity cost."""
    inp = ScenarioInput(
        scenario_type="cash_vs_loan",
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("40000.00"),
        current_savings=Decimal("1000000.00"),
        purchase_price=Decimal("500000.00"),
        down_payment=Decimal("100000.00"),
        loan_interest_rate_pct=Decimal("10.0"),
        loan_tenure_months=36
    )
    result = ScenarioEngine.simulate(inp)

    assert result.scenario_type == "cash_vs_loan"
    assert result.loan_analysis is not None
    assert result.loan_analysis.principal_borrowed == 400000.0
    assert len(result.alternative_options) == 3


def test_baseline_endpoint_unauthenticated(client):
    """Verify unauthenticated baseline returns honest empty state with zero mock data."""
    res = client.get("/api/v1/scenarios/baseline")
    assert res.status_code == 200
    data = res.json()
    assert data["is_verified_data"] is False
    assert data["monthly_income"] == 0.0
    assert data["total_monthly_expenses"] == 0.0
    assert data["liquid_savings"] == 0.0
    assert len(data["missing_fields"]) > 0


def test_baseline_endpoint_authenticated(client):
    """Verify authenticated user baseline loads verified profile, bank balance, and debt obligations."""
    # 1. Register a test user
    user = client.post("/api/v1/auth/register", json={
        "email": "baseline_test_user@example.com",
        "full_name": "Baseline Tester",
        "password": "Password123!",
        "role": "salaried"
    }).json()
    token = user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Update profile baseline
    profile_res = client.put("/api/v1/profile", json={
        "monthly_income": 75000.0,
        "monthly_expenses": 38000.0,
        "emergency_fund_target_months": 6
    }, headers=headers)
    assert profile_res.status_code == 200

    # 3. Add liability
    liab_res = client.post("/api/v1/liabilities", json={
        "name": "Personal Loan",
        "principal": 100000.0,
        "interest_rate": 12.0,
        "tenure_months": 24,
        "remaining_months": 20,
        "monthly_emi": 4700.0
    }, headers=headers)
    assert liab_res.status_code == 201

    # 4. Fetch scenario baseline
    res = client.get("/api/v1/scenarios/baseline", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["monthly_income"] == 75000.0
    assert data["total_monthly_expenses"] == 38000.0
    assert data["existing_monthly_emi"] == 4700.0
    assert data["available_monthly_surplus"] == 32300.0  # 75k - 38k - 4.7k
    assert data["total_debt"] == 100000.0
    assert data["is_verified_data"] is True



