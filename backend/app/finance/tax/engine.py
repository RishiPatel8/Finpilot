from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List
from app.schemas.tax import (
    TaxCalculationInput,
    RegimeTaxBreakdown,
    TaxComparisonResponse,
    SlabCalculation
)


def round_to_nearest_ten(val: Decimal) -> Decimal:
    """Income Tax Act Section 288A & 288B rounding to nearest multiple of 10."""
    return (val / Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("10")


class IndianTaxEngine:
    """
    Deterministic Indian Income Tax Engine for Assessment Years 2025-26 and 2024-25.
    Implements:
    - Section 115BAC (New Tax Regime as amended by Finance Act 2024)
    - Old Tax Regime with Sections 16, 24(b), 80C, 80D, 80CCD, 87A
    - Section 288B rounding
    - Surcharge & 4% Health and Education Cess
    """

    @classmethod
    def calculate_new_regime(cls, inp: TaxCalculationInput) -> RegimeTaxBreakdown:
        ay = inp.assessment_year.strip()
        is_salaried = inp.taxpayer_type.lower() == "salaried"
        
        # Gross Total Income computation
        gross_income = inp.gross_annual_salary + inp.other_income
        if inp.business_turnover > Decimal("0"):
            # Presumptive taxation 44AD / 44ADA
            profit_rate = inp.presumptive_profit_pct or (Decimal("50.0") if inp.taxpayer_type == "freelancer" else Decimal("8.0"))
            presumptive_income = (inp.business_turnover * profit_rate) / Decimal("100.0")
            gross_income += presumptive_income

        # Standard deduction under 115BAC
        # Finance Act 2024 increased standard deduction to 75,000 for AY 2025-26; was 50,000 for AY 2024-25
        std_deduction = Decimal("0.00")
        if is_salaried:
            if "2025-26" in ay:
                std_deduction = Decimal("75000.00")
            else:
                std_deduction = Decimal("50000.00")
            std_deduction = min(std_deduction, inp.gross_annual_salary)

        # Section 80CCD(2) employer NPS is allowed under New Regime
        employer_nps = min(inp.section_80ccd_2, inp.gross_annual_salary * Decimal("0.14"))
        
        allowed_deductions = {
            "Standard Deduction (Section 16(ia))": std_deduction,
        }
        if employer_nps > Decimal("0"):
            allowed_deductions["Employer NPS (Section 80CCD(2))"] = employer_nps

        total_deductions = sum(allowed_deductions.values())
        taxable_income = max(Decimal("0.00"), gross_income - total_deductions)
        taxable_income = round_to_nearest_ten(taxable_income)

        # Slabs calculation
        slab_details: List[SlabCalculation] = []
        tax_on_income = Decimal("0.00")

        if "2025-26" in ay:
            # Slabs for AY 2025-26 (Budget 2024)
            # 0 - 3L: 0%
            # 3L - 7L: 5%
            # 7L - 10L: 10%
            # 10L - 12L: 15%
            # 12L - 15L: 20%
            # > 15L: 30%
            slabs = [
                ("Up to ₹3,00,000", Decimal("0"), Decimal("300000"), Decimal("0.0")),
                ("₹3,00,001 to ₹7,00,000", Decimal("300000"), Decimal("700000"), Decimal("5.0")),
                ("₹7,00,001 to ₹10,00,000", Decimal("700000"), Decimal("1000000"), Decimal("10.0")),
                ("₹10,00,001 to ₹12,00,000", Decimal("1000000"), Decimal("1200000"), Decimal("15.0")),
                ("₹12,00,001 to ₹15,00,000", Decimal("1200000"), Decimal("1500000"), Decimal("20.0")),
                ("Above ₹15,00,000", Decimal("1500000"), Decimal("9999999999"), Decimal("30.0")),
            ]
        else:
            # Slabs for AY 2024-25
            # 0 - 3L: 0%, 3L - 6L: 5%, 6L - 9L: 10%, 9L - 12L: 15%, 12L - 15L: 20%, > 15L: 30%
            slabs = [
                ("Up to ₹3,00,000", Decimal("0"), Decimal("300000"), Decimal("0.0")),
                ("₹3,00,001 to ₹6,00,000", Decimal("300000"), Decimal("600000"), Decimal("5.0")),
                ("₹6,00,001 to ₹9,00,000", Decimal("600000"), Decimal("900000"), Decimal("10.0")),
                ("₹9,00,001 to ₹12,00,000", Decimal("900000"), Decimal("1200000"), Decimal("15.0")),
                ("₹12,00,001 to ₹15,00,000", Decimal("1200000"), Decimal("1500000"), Decimal("20.0")),
                ("Above ₹15,00,000", Decimal("1500000"), Decimal("9999999999"), Decimal("30.0")),
            ]

        for desc, lower, upper, rate in slabs:
            if taxable_income > lower:
                taxable_in_slab = min(taxable_income, upper) - lower
                slab_tax = (taxable_in_slab * rate) / Decimal("100.0")
                tax_on_income += slab_tax
                slab_details.append(SlabCalculation(
                    slab_range=desc,
                    taxable_in_slab=taxable_in_slab,
                    rate_pct=rate,
                    tax_amount=slab_tax
                ))

        # Section 87A Rebate & Marginal Relief
        rebate_87a = Decimal("0.00")
        marginal_relief = Decimal("0.00")

        if taxable_income <= Decimal("700000.00"):
            rebate_87a = tax_on_income
        else:
            # Marginal relief under Section 87A:
            # Tax payable cannot exceed (Taxable Income - 7,00,000)
            excess_income = taxable_income - Decimal("700000.00")
            if tax_on_income > excess_income:
                marginal_relief = tax_on_income - excess_income

        tax_after_rebate = max(Decimal("0.00"), tax_on_income - rebate_87a - marginal_relief)

        # Surcharge (capped at 25% under New Regime)
        surcharge = cls._calculate_surcharge(taxable_income, tax_after_rebate, max_rate=Decimal("25.0"))
        
        # 4% Health and Education Cess
        cess = Decimal("0.00")
        if (tax_after_rebate + surcharge) > Decimal("0"):
            cess = (tax_after_rebate + surcharge) * Decimal("0.04")

        total_tax = round_to_nearest_ten(tax_after_rebate + surcharge + cess)
        effective_rate = float((total_tax / gross_income * 100)) if gross_income > 0 else 0.0

        citations = [
            "Income Tax Act 1961 Section 115BAC(1A) - Concessional New Tax Regime",
            "Section 87A - Rebate up to ₹25,000 for income up to ₹7,00,000 with marginal relief",
            "Finance Act 2024 - Enhanced standard deduction of ₹75,000 for salaried employees",
            "Section 288B - Rounding off of tax liability to the nearest ₹10"
        ]

        return RegimeTaxBreakdown(
            regime="new",
            assessment_year=ay,
            gross_total_income=gross_income,
            standard_deduction=std_deduction,
            allowed_deductions=allowed_deductions,
            total_deductions=total_deductions,
            taxable_income=taxable_income,
            slab_details=slab_details,
            tax_on_income=tax_on_income,
            rebate_87a=rebate_87a,
            marginal_relief=marginal_relief,
            tax_after_rebate=tax_after_rebate,
            surcharge=surcharge,
            health_and_education_cess=cess,
            total_tax_liability=total_tax,
            effective_tax_rate_pct=round(effective_rate, 2),
            official_citations=citations
        )

    @classmethod
    def calculate_old_regime(cls, inp: TaxCalculationInput) -> RegimeTaxBreakdown:
        ay = inp.assessment_year.strip()
        is_salaried = inp.taxpayer_type.lower() == "salaried"
        is_senior = inp.taxpayer_type.lower() == "senior_citizen"

        gross_income = inp.gross_annual_salary + inp.other_income
        if inp.business_turnover > Decimal("0"):
            profit_rate = inp.presumptive_profit_pct or (Decimal("50.0") if inp.taxpayer_type == "freelancer" else Decimal("8.0"))
            gross_income += (inp.business_turnover * profit_rate) / Decimal("100.0")

        # Deductions allowed under Old Regime
        allowed_deductions: Dict[str, Decimal] = {}

        # Standard deduction (50,000)
        std_deduction = Decimal("0.00")
        if is_salaried:
            std_deduction = min(Decimal("50000.00"), inp.gross_annual_salary)
            allowed_deductions["Standard Deduction (Section 16(ia))"] = std_deduction

        # HRA Exemption (Section 10(13A))
        if inp.hra_exemption > Decimal("0") and is_salaried:
            allowed_deductions["HRA Exemption (Section 10(13A))"] = inp.hra_exemption

        # Section 80C (Capped at 1,50,000)
        if inp.section_80c > Decimal("0"):
            allowed_deductions["Section 80C (EPF/PPF/ELSS/Principal)"] = min(inp.section_80c, Decimal("150000.00"))

        # Section 80D (Health Insurance: Self 25k, Parents 50k - cap at 75k)
        if inp.section_80d > Decimal("0"):
            allowed_deductions["Section 80D (Health Insurance)"] = min(inp.section_80d, Decimal("75000.00"))

        # Section 80CCD(1B) (Additional NPS up to 50,000)
        if inp.section_80ccd_1b > Decimal("0"):
            allowed_deductions["Section 80CCD(1B) (NPS Self)"] = min(inp.section_80ccd_1b, Decimal("50000.00"))

        # Section 80CCD(2) (Employer NPS)
        if inp.section_80ccd_2 > Decimal("0"):
            employer_nps = min(inp.section_80ccd_2, inp.gross_annual_salary * Decimal("0.14"))
            allowed_deductions["Section 80CCD(2) (Employer NPS)"] = employer_nps

        # Section 24(b) (Home loan interest self-occupied capped at 2,00,000)
        if inp.home_loan_interest_24b > Decimal("0"):
            allowed_deductions["Section 24(b) (Home Loan Interest)"] = min(inp.home_loan_interest_24b, Decimal("200000.00"))

        # Other 80TTA / 80G
        if inp.other_deductions_80tta_80g > Decimal("0"):
            allowed_deductions["Other Chapter VI-A Deductions"] = inp.other_deductions_80tta_80g

        total_deductions = sum(allowed_deductions.values())
        taxable_income = max(Decimal("0.00"), gross_income - total_deductions)
        taxable_income = round_to_nearest_ten(taxable_income)

        # Old Regime Slabs
        slab_details: List[SlabCalculation] = []
        tax_on_income = Decimal("0.00")

        if is_senior:
            slabs = [
                ("Up to ₹3,00,000", Decimal("0"), Decimal("300000"), Decimal("0.0")),
                ("₹3,00,001 to ₹5,00,000", Decimal("300000"), Decimal("500000"), Decimal("5.0")),
                ("₹5,00,001 to ₹10,00,000", Decimal("500000"), Decimal("1000000"), Decimal("20.0")),
                ("Above ₹10,00,000", Decimal("1000000"), Decimal("9999999999"), Decimal("30.0")),
            ]
        else:
            slabs = [
                ("Up to ₹2,50,000", Decimal("0"), Decimal("250000"), Decimal("0.0")),
                ("₹2,50,001 to ₹5,00,000", Decimal("250000"), Decimal("500000"), Decimal("5.0")),
                ("₹5,00,001 to ₹10,00,000", Decimal("500000"), Decimal("1000000"), Decimal("20.0")),
                ("Above ₹10,00,000", Decimal("1000000"), Decimal("9999999999"), Decimal("30.0")),
            ]

        for desc, lower, upper, rate in slabs:
            if taxable_income > lower:
                taxable_in_slab = min(taxable_income, upper) - lower
                slab_tax = (taxable_in_slab * rate) / Decimal("100.0")
                tax_on_income += slab_tax
                slab_details.append(SlabCalculation(
                    slab_range=desc,
                    taxable_in_slab=taxable_in_slab,
                    rate_pct=rate,
                    tax_amount=slab_tax
                ))

        # Section 87A Rebate for Old Regime (Up to ₹5,00,000 taxable income, max ₹12,500)
        rebate_87a = Decimal("0.00")
        if taxable_income <= Decimal("500000.00"):
            rebate_87a = min(tax_on_income, Decimal("12500.00"))

        tax_after_rebate = max(Decimal("0.00"), tax_on_income - rebate_87a)

        # Surcharge (Up to 37% for >5Cr in Old Regime)
        surcharge = cls._calculate_surcharge(taxable_income, tax_after_rebate, max_rate=Decimal("37.0"))

        # 4% Health and Education Cess
        cess = Decimal("0.00")
        if (tax_after_rebate + surcharge) > Decimal("0"):
            cess = (tax_after_rebate + surcharge) * Decimal("0.04")

        total_tax = round_to_nearest_ten(tax_after_rebate + surcharge + cess)
        effective_rate = float((total_tax / gross_income * 100)) if gross_income > 0 else 0.0

        citations = [
            "Income Tax Act 1961 Section 115BAC(6) - Option to exercise Old Tax Regime",
            "Section 87A - Rebate up to ₹12,500 for taxable income up to ₹5,00,000",
            "Chapter VI-A Deductions: Sections 80C (₹1.5L), 80D (Health), 80CCD(1B) (₹50k NPS)",
            "Section 24(b) - Deduction for interest on borrowed capital for house property up to ₹2,00,000"
        ]

        return RegimeTaxBreakdown(
            regime="old",
            assessment_year=ay,
            gross_total_income=gross_income,
            standard_deduction=std_deduction,
            allowed_deductions=allowed_deductions,
            total_deductions=total_deductions,
            taxable_income=taxable_income,
            slab_details=slab_details,
            tax_on_income=tax_on_income,
            rebate_87a=rebate_87a,
            marginal_relief=Decimal("0.00"),
            tax_after_rebate=tax_after_rebate,
            surcharge=surcharge,
            health_and_education_cess=cess,
            total_tax_liability=total_tax,
            effective_tax_rate_pct=round(effective_rate, 2),
            official_citations=citations
        )

    @classmethod
    def compare_regimes(cls, inp: TaxCalculationInput) -> TaxComparisonResponse:
        new_res = cls.calculate_new_regime(inp)
        old_res = cls.calculate_old_regime(inp)

        if new_res.total_tax_liability <= old_res.total_tax_liability:
            recommended = "new"
            savings = old_res.total_tax_liability - new_res.total_tax_liability
            explanation = (
                f"The New Tax Regime is more beneficial, saving you ₹{savings:,.0f} in tax liability. "
                f"Under the New Regime (FY 24-25 / AY 25-26), lower slab rates and a higher standard deduction "
                f"of ₹{new_res.standard_deduction:,.0f} provide greater net savings than your available Old Regime deductions."
            )
        else:
            recommended = "old"
            savings = new_res.total_tax_liability - old_res.total_tax_liability
            explanation = (
                f"The Old Tax Regime is more beneficial, saving you ₹{savings:,.0f} in tax liability. "
                f"Your total claimed deductions of ₹{old_res.total_deductions:,.0f} (including Section 80C, 80D, HRA, and Home Loan interest) "
                f"significantly reduce your taxable bracket under the Old Regime."
            )

        missing_notes = None
        if inp.taxpayer_type == "salaried" and inp.gross_annual_salary > Decimal("1000000") and old_res.total_deductions < Decimal("100000"):
            missing_notes = "You have claimed minimal deductions under Old Regime. If you pay rent (HRA) or have EPF/NPS contributions, claiming them may further reduce Old Regime tax."

        return TaxComparisonResponse(
            assessment_year=inp.assessment_year,
            taxpayer_type=inp.taxpayer_type,
            recommended_regime=recommended,
            tax_savings=savings,
            explanation=explanation,
            new_regime=new_res,
            old_regime=old_res,
            missing_inputs_note=missing_notes
        )

    @classmethod
    def _calculate_surcharge(cls, taxable_income: Decimal, tax_amount: Decimal, max_rate: Decimal) -> Decimal:
        if taxable_income <= Decimal("5000000"):
            return Decimal("0.00")

        if taxable_income <= Decimal("10000000"):
            rate = Decimal("10.0")
            threshold = Decimal("5000000")
            prev_surcharge_rate = Decimal("0.0")
        elif taxable_income <= Decimal("20000000"):
            rate = Decimal("15.0")
            threshold = Decimal("10000000")
            prev_surcharge_rate = Decimal("10.0")
        elif taxable_income <= Decimal("50000000"):
            rate = min(Decimal("25.0"), max_rate)
            threshold = Decimal("20000000")
            prev_surcharge_rate = Decimal("15.0")
        else:
            rate = min(Decimal("37.0"), max_rate)
            threshold = Decimal("50000000")
            prev_surcharge_rate = min(Decimal("25.0"), max_rate)

        nominal_surcharge = (tax_amount * rate) / Decimal("100.0")
        
        # Statutory Marginal Relief on Surcharge:
        # Total amount payable as tax + surcharge cannot exceed:
        # (Tax at threshold + Surcharge at threshold) + (Taxable income - threshold)
        excess_income = taxable_income - threshold
        tax_at_threshold = tax_amount - (excess_income * Decimal("0.30"))
        surcharge_at_threshold = (tax_at_threshold * prev_surcharge_rate) / Decimal("100.0")
        max_payable = tax_at_threshold + surcharge_at_threshold + excess_income

        if (tax_amount + nominal_surcharge) > max_payable:
            nominal_surcharge = max(Decimal("0.00"), max_payable - tax_amount)

        return nominal_surcharge
