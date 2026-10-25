from decimal import Decimal
from typing import Dict, Any, Optional
from app.finance.tax.tax_rules import TaxRules


class SalaryTaxCalculator:
    """
    Computes Net Taxable Salary under the Income Tax Act 1961.
    Handles:
    - Basic, Dearness Allowance (DA), HRA, Special Allowances, Bonus/Arrears
    - Section 10(13A) HRA Exemption (Rule 2A)
    - Section 16(ia) Standard Deduction
    - Section 16(iii) Professional Tax
    """

    @classmethod
    def calculate_hra_exemption(
        cls,
        basic_salary: Decimal,
        dearness_allowance: Decimal,
        hra_received: Decimal,
        rent_paid: Decimal,
        is_metro: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates House Rent Allowance (HRA) exemption under Section 10(13A) read with Rule 2A.
        Salary for HRA = Basic + DA (forming part of retirement benefits).
        Exemption is least of:
        1. Actual HRA received
        2. Rent paid - 10% of Salary
        3. 50% of Salary (Metro: Mumbai, Delhi, Kolkata, Chennai) or 40% (Non-Metro)
        """
        salary_for_hra = basic_salary + dearness_allowance
        if rent_paid <= Decimal("0") or hra_received <= Decimal("0") or salary_for_hra <= Decimal("0"):
            return {
                "exempt_hra": Decimal("0.00"),
                "taxable_hra": hra_received,
                "rule_details": {
                    "actual_hra": hra_received,
                    "rent_minus_10pct": Decimal("0.00"),
                    "pct_of_salary": Decimal("0.00"),
                }
            }

        ten_pct_salary = salary_for_hra * Decimal("0.10")
        rent_minus_10pct = max(Decimal("0.00"), rent_paid - ten_pct_salary)

        factor = Decimal("0.50") if is_metro else Decimal("0.40")
        pct_of_salary = salary_for_hra * factor

        exempt_hra = min(hra_received, rent_minus_10pct, pct_of_salary)
        taxable_hra = max(Decimal("0.00"), hra_received - exempt_hra)

        return {
            "exempt_hra": exempt_hra,
            "taxable_hra": taxable_hra,
            "rule_details": {
                "actual_hra": hra_received,
                "rent_minus_10pct": rent_minus_10pct,
                "pct_of_salary": pct_of_salary,
                "metro_applied": is_metro
            }
        }

    @classmethod
    def compute_salary_income(
        cls,
        regime: str,
        assessment_year: str,
        gross_salary: Decimal,
        basic_salary: Optional[Decimal] = None,
        dearness_allowance: Optional[Decimal] = None,
        hra_received: Optional[Decimal] = None,
        rent_paid: Optional[Decimal] = None,
        is_metro: bool = False,
        hra_exemption_override: Optional[Decimal] = None,
        professional_tax: Decimal = Decimal("0.00"),
    ) -> Dict[str, Any]:
        """
        Computes Gross Salary, Exemptions, Standard Deduction, and Net Taxable Salary.
        """
        # Determine HRA exemption:
        # In New Regime (Section 115BAC), HRA exemption is legally disallowed.
        exempt_hra = Decimal("0.00")
        hra_info = {}

        if regime.lower() == "old":
            if hra_exemption_override and hra_exemption_override > Decimal("0"):
                exempt_hra = hra_exemption_override
                hra_info = {"actual_hra": exempt_hra, "rent_minus_10pct": exempt_hra, "pct_of_salary": exempt_hra}
            elif (
                basic_salary is not None and basic_salary > Decimal("0")
                and hra_received is not None and hra_received > Decimal("0")
                and rent_paid is not None and rent_paid > Decimal("0")
            ):
                da = dearness_allowance or Decimal("0.00")
                calc = cls.calculate_hra_exemption(basic_salary, da, hra_received, rent_paid, is_metro)
                exempt_hra = calc["exempt_hra"]
                hra_info = calc["rule_details"]

        # Ensure exempt salary does not exceed gross salary
        exempt_hra = min(exempt_hra, gross_salary)

        # Standard Deduction (Section 16(ia))
        std_deduction = TaxRules.get_standard_deduction(assessment_year, regime, is_salaried=True)
        # Standard deduction cannot exceed (gross_salary - exemptions)
        std_deduction = min(std_deduction, max(Decimal("0.00"), gross_salary - exempt_hra))

        # Professional Tax (Section 16(iii)) - allowed in Old Regime only
        pt_allowed = Decimal("0.00")
        if regime.lower() == "old" and professional_tax > Decimal("0"):
            pt_allowed = min(professional_tax, Decimal("2500.00"))  # Constitution Article 276 cap

        total_salary_deductions = std_deduction + pt_allowed
        net_salary = max(Decimal("0.00"), gross_salary - exempt_hra - total_salary_deductions)

        return {
            "gross_salary": gross_salary,
            "exempt_hra": exempt_hra,
            "hra_details": hra_info,
            "standard_deduction": std_deduction,
            "professional_tax": pt_allowed,
            "total_salary_deductions": total_salary_deductions,
            "net_taxable_salary": net_salary
        }
