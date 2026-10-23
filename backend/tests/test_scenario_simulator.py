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

