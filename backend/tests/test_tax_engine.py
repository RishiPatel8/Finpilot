from decimal import Decimal
import pytest
from app.finance.tax.engine import IndianTaxEngine
from app.schemas.tax import TaxCalculationInput


def test_ay_2025_26_new_regime_zero_tax_up_to_7_75_lakhs():
    """Under Budget 2024 AY 2025-26, salary of 7.75L with 75k std deduction leaves 7.00L taxable, paying ZERO tax due to 87A."""
    inp = TaxCalculationInput(
        assessment_year="2025-26",
        taxpayer_type="salaried",
        gross_annual_salary=Decimal("775000.00"),
    )
    res = IndianTaxEngine.calculate_new_regime(inp)
    assert res.standard_deduction == Decimal("75000.00")
    assert res.taxable_income == Decimal("700000.00")
    assert res.rebate_87a > Decimal("0")
    assert res.total_tax_liability == Decimal("0.00")


def test_ay_2025_26_new_regime_marginal_relief():
    """Test marginal relief under Section 87A when salary slightly exceeds 7.75L."""
    inp = TaxCalculationInput(
        assessment_year="2025-26",
        taxpayer_type="salaried",
        gross_annual_salary=Decimal("785000.00"),
    )
    res = IndianTaxEngine.calculate_new_regime(inp)
    assert res.taxable_income == Decimal("710000.00")
    # Excess over 7L is 10,000. Tax before cess cannot exceed 10,000.
    assert res.marginal_relief > Decimal("0")
    assert res.tax_after_rebate <= Decimal("10000.00")


def test_ay_2024_25_new_regime_std_deduction_50k():
    """Under AY 2024-25, std deduction was 50,000."""
    inp = TaxCalculationInput(
        assessment_year="2024-25",
        taxpayer_type="salaried",
        gross_annual_salary=Decimal("750000.00"),
    )
    res = IndianTaxEngine.calculate_new_regime(inp)
    assert res.standard_deduction == Decimal("50000.00")
    assert res.taxable_income == Decimal("700000.00")
    assert res.total_tax_liability == Decimal("0.00")


def test_old_regime_zero_tax_up_to_5_lakhs():
    """Old regime 87A rebate gives zero tax up to 5L taxable income."""
    inp = TaxCalculationInput(
        assessment_year="2025-26",
        taxpayer_type="salaried",
        gross_annual_salary=Decimal("550000.00"),  # 5.5L - 50k std deduction = 5L taxable
    )
    res = IndianTaxEngine.calculate_old_regime(inp)
    assert res.taxable_income == Decimal("500000.00")
    assert res.rebate_87a == Decimal("12500.00")
    assert res.total_tax_liability == Decimal("0.00")


def test_regime_comparison_high_deductions_favors_old():
    """When a user has high deductions (80C, 80D, 24b, HRA, NPS), Old Regime should win."""
    inp = TaxCalculationInput(
        assessment_year="2025-26",
        taxpayer_type="salaried",
        gross_annual_salary=Decimal("1500000.00"),
        section_80c=Decimal("150000.00"),
        section_80d=Decimal("50000.00"),
        section_80ccd_1b=Decimal("50000.00"),
        home_loan_interest_24b=Decimal("200000.00"),
        hra_exemption=Decimal("180000.00"),
    )
    comp = IndianTaxEngine.compare_regimes(inp)
    assert comp.recommended_regime == "old"
    assert comp.tax_savings > Decimal("0")


def test_regime_comparison_low_deductions_favors_new():
    """When a user has low or zero deductions, New Regime should win."""
    inp = TaxCalculationInput(
        assessment_year="2025-26",
        taxpayer_type="salaried",
        gross_annual_salary=Decimal("1200000.00"),
        section_80c=Decimal("20000.00"),
    )
    comp = IndianTaxEngine.compare_regimes(inp)
    assert comp.recommended_regime == "new"
    assert comp.tax_savings > Decimal("0")


def test_freelancer_presumptive_taxation_44ada():
    """Section 44ADA allows professionals to declare 50% profit."""
    inp = TaxCalculationInput(
        assessment_year="2025-26",
        taxpayer_type="freelancer",
        business_turnover=Decimal("1200000.00"),
        presumptive_profit_pct=Decimal("50.0"),
    )
    res = IndianTaxEngine.calculate_new_regime(inp)
    # 50% of 12L = 6L gross income, no salary std deduction, <= 7L taxable => zero tax
    assert res.taxable_income == Decimal("600000.00")
    assert res.total_tax_liability == Decimal("0.00")


def test_section_288b_rounding():
    """Verify Section 288B rounds to multiple of 10."""
    from app.finance.tax.engine import round_to_nearest_ten
    assert round_to_nearest_ten(Decimal("1054.4")) == Decimal("1050")
    assert round_to_nearest_ten(Decimal("1055.0")) == Decimal("1060")
    assert round_to_nearest_ten(Decimal("1058.9")) == Decimal("1060")


def test_surcharge_marginal_relief_high_income():
    """Verify statutory marginal relief on surcharge when income just exceeds ₹50 Lakhs."""
    inp = TaxCalculationInput(
        assessment_year="2025-26",
        taxpayer_type="freelancer",
        other_income=Decimal("5100000.00")
    )
    res = IndianTaxEngine.calculate_new_regime(inp)
    assert res.taxable_income == Decimal("5100000.00")
    assert res.tax_on_income == Decimal("1220000.00")
    # Surcharge capped by marginal relief at 70,000 instead of nominal 1,22,000
    assert res.surcharge == Decimal("70000.00")
    assert (res.tax_after_rebate + res.surcharge) == Decimal("1290000.00")

