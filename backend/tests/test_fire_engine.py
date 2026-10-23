import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.fire import FireCalculationInput
from app.finance.fire.engine import FireEngine
from app.finance.fire.health import FinancialHealthEngine

client = TestClient(app)


def test_fire_target_calculation():
    inp = FireCalculationInput(
        current_age=30,
        retirement_age=50,
        monthly_expenses=Decimal("50000.00"),
        withdrawal_rate_pct=Decimal("3.50"),
        expected_annual_inflation_pct=Decimal("6.00"),
        expected_nominal_return_pct=Decimal("11.00"),
        current_investable_assets=Decimal("1000000.00"),
        monthly_investment=Decimal("35000.00")
    )
    res = FireEngine.calculate_fire(inp)

    # Annual expenses = 50,000 * 12 = 6,00,000
    # Today's target = 6,00,000 / 0.035 = 1,71,42,857.14
    assert res.annual_expenses_today == Decimal("600000.00")
    expected_today = (Decimal("600000.00") / Decimal("0.035")).quantize(Decimal("0.01"))
    assert abs(res.fire_target_today - expected_today) <= Decimal("0.05")

    # Future target in 20 years at 6% inflation: Target_today * (1.06)^20
    inflation_factor = (Decimal("1.06") ** 20)
    expected_future = (expected_today * inflation_factor).quantize(Decimal("0.01"))
    assert abs(res.fire_target_future - expected_future) <= Decimal("1.00")
    assert res.years_to_retirement == 20
    assert res.safe_withdrawal_rate_pct == 3.5


def test_fisher_real_return_formula():
    inp = FireCalculationInput(
        current_age=25,
        retirement_age=45,
        monthly_expenses=Decimal("40000.00"),
        expected_annual_inflation_pct=Decimal("6.00"),
        expected_nominal_return_pct=Decimal("11.00")
    )
    res = FireEngine.calculate_fire(inp)
    # Exact: (1 + 0.11) / (1 + 0.06) - 1 = 1.11 / 1.06 - 1 = 0.047169... -> 4.72%
    assert abs(res.real_return_pct - 4.72) <= 0.05


def test_fire_strategies_comparison():
    inp = FireCalculationInput(
        current_age=28,
        retirement_age=48,
        monthly_expenses=Decimal("60000.00"),
        essential_expenses_pct=Decimal("70.00"),
        current_investable_assets=Decimal("2000000.00"),
        monthly_investment=Decimal("40000.00")
    )
    res = FireEngine.calculate_fire(inp)
    strategies = {s.strategy_type: s for s in res.strategies}

    assert "lean" in strategies
    assert "regular" in strategies
    assert "fat" in strategies
    assert "coast" in strategies

    # Lean spending is 70% of 60,000 = 42,000
    assert strategies["lean"].monthly_expense_in_retirement == Decimal("42000.00")
    # Fat spending is 135% of 60,000 = 81,000
    assert strategies["fat"].monthly_expense_in_retirement == Decimal("81000.00")
    # Lean target < Regular target < Fat target
    assert strategies["lean"].target_corpus_today < strategies["regular"].target_corpus_today
    assert strategies["regular"].target_corpus_today < strategies["fat"].target_corpus_today


def test_coast_fire_dynamics():
    # If a user already has massive assets, coast target today should be achieved
    inp = FireCalculationInput(
        current_age=30,
        retirement_age=50,
        monthly_expenses=Decimal("50000.00"),
        current_investable_assets=Decimal("50000000.00"),  # 5 Crore invested
        monthly_investment=Decimal("0.00")
    )
    res = FireEngine.calculate_fire(inp)
    coast_strat = next(s for s in res.strategies if s.strategy_type == "coast")
    assert coast_strat.is_achievable_by_target_age is True
    assert coast_strat.required_monthly_investment == Decimal("0.00")


def test_multi_scenario_projections():
    inp = FireCalculationInput(
        current_age=30,
        retirement_age=50,
        life_expectancy_age=80,
        monthly_expenses=Decimal("50000.00"),
        current_investable_assets=Decimal("1000000.00"),
        monthly_investment=Decimal("30000.00")
    )
    res = FireEngine.calculate_fire(inp)
    assert len(res.yearly_projections) == 51  # Age 30 to 80 inclusive

    # Check projection before retirement (Age 40)
    p_pre = next(p for p in res.yearly_projections if p.age == 40)
    assert p_pre.is_retired is False
    assert p_pre.annual_contribution > Decimal("0.00")
    assert p_pre.annual_withdrawal == Decimal("0.00")
    assert p_pre.portfolio_optimistic > p_pre.portfolio_base > p_pre.portfolio_conservative

    # Check projection after retirement (Age 60)
    p_post = next(p for p in res.yearly_projections if p.age == 60)
    assert p_post.is_retired is True
    assert p_post.annual_contribution == Decimal("0.00")
    assert p_post.annual_withdrawal > Decimal("0.00")


def test_fire_edge_cases():
    # 1. Zero nominal returns
    inp_zero = FireCalculationInput(
        current_age=30,
        retirement_age=40,
        monthly_expenses=Decimal("50000.00"),
        expected_nominal_return_pct=Decimal("0.00"),
        current_investable_assets=Decimal("500000.00"),
        monthly_investment=Decimal("20000.00")
    )
    res_zero = FireEngine.calculate_fire(inp_zero)
    assert res_zero.projected_portfolio_at_retirement >= Decimal("500000.00")

    # 2. Negative nominal returns
    inp_neg = FireCalculationInput(
        current_age=30,
        retirement_age=40,
        monthly_expenses=Decimal("50000.00"),
        expected_nominal_return_pct=Decimal("-5.00"),
        current_investable_assets=Decimal("500000.00"),
        monthly_investment=Decimal("0.00")
    )
    res_neg = FireEngine.calculate_fire(inp_neg)
    assert res_neg.projected_portfolio_at_retirement < Decimal("500000.00")

    # 3. Current age equals retirement age
    inp_same_age = FireCalculationInput(
        current_age=55,
        retirement_age=55,
        monthly_expenses=Decimal("50000.00"),
        current_investable_assets=Decimal("20000000.00")
    )
    res_same = FireEngine.calculate_fire(inp_same_age)
    assert res_same.years_to_retirement == 0


def test_financial_health_assessment():
    res = FinancialHealthEngine.assess_health(
        age=32,
        monthly_income=Decimal("150000.00"),
        monthly_expenses=Decimal("60000.00"),
        liquid_assets=Decimal("400000.00"),       # ~6.6 months runway
        investable_assets=Decimal("2500000.00"),   # ~1.38x annual income
        total_debt_principal=Decimal("500000.00"),
        total_monthly_emi=Decimal("18000.00"),    # 12% EMI ratio
        goals_on_track_pct=85.0,
        fire_progress_pct=45.0,
        fire_shortfall=Decimal("0.00")
    )

    assert 0 <= res.overall_score <= 100
    assert len(res.pillars) == 8
    assert res.is_provisional is False
    assert len(res.actionable_checklist_12_months) == 3

    # Emergency cushion should be excellent (>6 months)
    p_ef = next(p for p in res.pillars if p.pillar_id == "emergency_fund")
    assert p_ef.status == "excellent"
    assert p_ef.score == 100


def test_fire_api_endpoints():
    payload = {
        "current_age": 29,
        "retirement_age": 49,
        "monthly_expenses": 55000,
        "monthly_income": 120000,
        "current_investable_assets": 1200000,
        "monthly_investment": 40000,
        "withdrawal_rate_pct": 3.5
    }
    resp = client.post("/api/v1/fire/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "fire_target_today" in data
    assert "strategies" in data
    assert len(data["strategies"]) >= 4
    assert len(data["yearly_projections"]) > 0
