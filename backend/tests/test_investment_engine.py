from decimal import Decimal
import pytest
from app.finance.investments.engine import InvestmentEngine
from app.schemas.investment import InvestmentCompareRequest, GoalProjectionRequest


def test_compare_instruments_short_horizon_recommends_liquid_fund():
    req = InvestmentCompareRequest(
        investment_amount=Decimal("200000.00"),
        time_horizon_months=3,
        can_lock_funds=False,
    )
    res = InvestmentEngine.compare_instruments(req)
    assert res.top_recommendation == "Liquid Mutual Fund"
    assert len(res.comparisons) == 3
    liquid = next(c for c in res.comparisons if c.category == "liquid_mf")
    assert liquid.projected_maturity_value > Decimal("200000.00")
    assert "Section 50AA" in liquid.tax_treatment_summary


def test_compare_instruments_long_horizon_recommends_bonds():
    req = InvestmentCompareRequest(
        investment_amount=Decimal("500000.00"),
        time_horizon_months=48,
        can_lock_funds=True,
    )
    res = InvestmentEngine.compare_instruments(req)
    assert res.top_recommendation == "Sovereign / AAA Bond"
    bond = next(c for c in res.comparisons if c.category == "bond")
    assert bond.projected_maturity_value > Decimal("500000.00")


def test_goal_projection_inflation_adjustment():
    req = GoalProjectionRequest(
        goal_name="Emergency Reserve",
        target_amount=Decimal("600000.00"),
        current_amount=Decimal("100000.00"),
        time_horizon_months=24,
        expected_annual_return_pct=Decimal("7.0"),
        expected_annual_inflation_pct=Decimal("6.0"),
        adjust_for_inflation=True
    )
    res = InvestmentEngine.project_goal(req)
    # Target should be adjusted upwards for 2 years of 6% inflation: 600,000 * 1.06^2 = 674,160
    assert res.inflation_adjusted_target > res.nominal_target_amount
    assert res.required_monthly_sip > Decimal("0.00")
    assert len(res.breakdown_by_year) == 2


def test_goal_projection_zero_return_edge_case():
    """Verify that expected return of 0% does not trigger division by zero."""
    req = GoalProjectionRequest(
        goal_name="Cash Goal",
        target_amount=Decimal("120000.00"),
        current_amount=Decimal("0.00"),
        time_horizon_months=12,
        expected_annual_return_pct=Decimal("0.0"),
        expected_annual_inflation_pct=Decimal("0.0"),
        adjust_for_inflation=False
    )
    res = InvestmentEngine.project_goal(req)
    assert res.required_monthly_sip == Decimal("10000.00")
    assert res.projected_wealth_gain == Decimal("0.00")

