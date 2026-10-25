from decimal import Decimal
from typing import Dict, Any, Optional
from app.finance.tax.tax_rules import TaxRules


class CapitalGainsTaxCalculator:
    """
    Computes Capital Gains taxation under Section 111A, 112A, and 112.
    Implements Finance (No. 2) Act 2024 revisions:
    - Section 111A STCG: 20% (AY 2025-26 & 2026-27) vs 15% (AY 2024-25)
    - Section 112A LTCG: 12.5% exceeding ₹1,25,000 (AY 2025-26 & 2026-27) vs 10% exceeding ₹1,00,000 (AY 2024-25)
    - Section 112 Other LTCG: 12.5% (AY 2025-26) / 20% (AY 2024-25)
    - Handles basic exemption limit shortfall adjustment for resident individuals/HUFs.
    """

    @classmethod
    def compute_capital_gains(
        cls,
        assessment_year: str,
        stcg_111a: Decimal = Decimal("0.00"),
        ltcg_112a: Decimal = Decimal("0.00"),
        ltcg_112: Decimal = Decimal("0.00"),
        stcg_slab_rate: Decimal = Decimal("0.00"),
        basic_exemption_shortfall: Decimal = Decimal("0.00"),
        is_resident: bool = True
    ) -> Dict[str, Any]:
        rates = TaxRules.get_capital_gains_rates(assessment_year)
        
        # 1. Section 112A LTCG Exemption (1.25L for AY 2025-26; 1L for AY 2024-25)
        ltcg_112a_exemption = rates["ltcg_112a_exemption"]
        ltcg_112a_exempt = min(ltcg_112a, ltcg_112a_exemption)
        taxable_ltcg_112a = max(Decimal("0.00"), ltcg_112a - ltcg_112a_exempt)

        # 2. Basic exemption limit shortfall adjustment:
        # Resident individuals/HUFs can adjust basic exemption limit deficit against special-rate capital gains
        # Priority of adjustment: 1. Other LTCG 112 -> 2. LTCG 112A -> 3. STCG 111A
        remaining_shortfall = basic_exemption_shortfall if is_resident else Decimal("0.00")

        # Adjust against LTCG 112
        ltcg_112_adj = min(ltcg_112, remaining_shortfall)
        net_taxable_ltcg_112 = ltcg_112 - ltcg_112_adj
        remaining_shortfall -= ltcg_112_adj

        # Adjust against LTCG 112A
        ltcg_112a_adj = min(taxable_ltcg_112a, remaining_shortfall)
        net_taxable_ltcg_112a = taxable_ltcg_112a - ltcg_112a_adj
        remaining_shortfall -= ltcg_112a_adj

        # Adjust against STCG 111A
        stcg_111a_adj = min(stcg_111a, remaining_shortfall)
        net_taxable_stcg_111a = stcg_111a - stcg_111a_adj
        remaining_shortfall -= stcg_111a_adj

        # Tax calculations
        tax_stcg_111a = (net_taxable_stcg_111a * rates["stcg_111a_rate"]) / Decimal("100.0")
        tax_ltcg_112a = (net_taxable_ltcg_112a * rates["ltcg_112a_rate"]) / Decimal("100.0")
        tax_ltcg_112 = (net_taxable_ltcg_112 * rates["ltcg_112_rate"]) / Decimal("100.0")

        total_special_tax = tax_stcg_111a + tax_ltcg_112a + tax_ltcg_112
        total_special_income = net_taxable_stcg_111a + net_taxable_ltcg_112a + net_taxable_ltcg_112

        return {
            "stcg_111a_gross": stcg_111a,
            "stcg_111a_rate_pct": rates["stcg_111a_rate"],
            "stcg_111a_taxable": net_taxable_stcg_111a,
            "tax_stcg_111a": tax_stcg_111a,

            "ltcg_112a_gross": ltcg_112a,
            "ltcg_112a_exempt": ltcg_112a_exempt,
            "ltcg_112a_rate_pct": rates["ltcg_112a_rate"],
            "ltcg_112a_taxable": net_taxable_ltcg_112a,
            "tax_ltcg_112a": tax_ltcg_112a,

            "ltcg_112_gross": ltcg_112,
            "ltcg_112_rate_pct": rates["ltcg_112_rate"],
            "ltcg_112_taxable": net_taxable_ltcg_112,
            "tax_ltcg_112": tax_ltcg_112,

            "stcg_slab_rate": stcg_slab_rate,
            "total_special_income": total_special_income,
            "total_special_tax": total_special_tax,
            "basic_exemption_shortfall_used": basic_exemption_shortfall - remaining_shortfall,
            "citations": [
                f"Section 111A - STCG on equity taxed at {rates['stcg_111a_rate']}%",
                f"Section 112A - LTCG on equity taxed at {rates['ltcg_112a_rate']}% on gains exceeding ₹{ltcg_112a_exemption:,.0f}",
                f"Section 112 - Other LTCG taxed at {rates['ltcg_112_rate']}%"
            ]
        }
