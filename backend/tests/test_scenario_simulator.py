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
