from decimal import Decimal
from typing import Dict, Any, Optional


class HousePropertyTaxCalculator:
    """
    Computes Income / Loss from House Property under Section 22 to Section 27 of the Income Tax Act 1961.
    Handles:
    - Self-occupied property (Section 24(b) interest deduction capped at ₹2,00,000 under Old Regime; Nil under New Regime).
    - Let-out property (Municipal tax deduction, Section 24(a) 30% standard deduction, and Section 24(b) actual interest).
    - Section 71(3A) restriction: Loss from house property set-off against other heads capped at ₹2,00,000.
    """

    @classmethod
    def compute_house_property_income(
        cls,
        regime: str,
        property_type: str = "none",  # "none", "self_occupied", "let_out"
        gross_rent_received: Decimal = Decimal("0.00"),
        municipal_taxes_paid: Decimal = Decimal("0.00"),
        home_loan_interest: Decimal = Decimal("0.00"),
    ) -> Dict[str, Any]:
        ptype = property_type.lower()
        is_new = regime.lower() == "new"

        if ptype == "none" and home_loan_interest <= Decimal("0") and gross_rent_received <= Decimal("0"):
            return {
                "property_type": "none",
                "gross_annual_value": Decimal("0.00"),
                "municipal_taxes": Decimal("0.00"),
                "net_annual_value": Decimal("0.00"),
                "standard_deduction_24a": Decimal("0.00"),
                "interest_deduction_24b": Decimal("0.00"),
                "net_house_property_income": Decimal("0.00"),
                "loss_eligible_for_setoff": Decimal("0.00"),
                "notes": "No house property reported."
            }

        if ptype in ["self_occupied", "none"] and gross_rent_received <= Decimal("0"):
            # Self-occupied property
            # Under Section 115BAC (New Regime), self-occupied house loan interest is DISALLOWED
            if is_new:
                return {
                    "property_type": "self_occupied",
                    "gross_annual_value": Decimal("0.00"),
                    "municipal_taxes": Decimal("0.00"),
                    "net_annual_value": Decimal("0.00"),
                    "standard_deduction_24a": Decimal("0.00"),
                    "interest_deduction_24b": Decimal("0.00"),
                    "net_house_property_income": Decimal("0.00"),
                    "loss_eligible_for_setoff": Decimal("0.00"),
                    "notes": "Section 24(b) interest on self-occupied property is disallowed under New Regime (Section 115BAC)."
                }
            else:
                # Old Regime: Deduction up to ₹2,00,000
                interest_deduction = min(home_loan_interest, Decimal("200000.00"))
                net_income = -interest_deduction
                return {
                    "property_type": "self_occupied",
                    "gross_annual_value": Decimal("0.00"),
                    "municipal_taxes": Decimal("0.00"),
                    "net_annual_value": Decimal("0.00"),
                    "standard_deduction_24a": Decimal("0.00"),
                    "interest_deduction_24b": interest_deduction,
                    "net_house_property_income": net_income,
                    "loss_eligible_for_setoff": interest_deduction,
                    "notes": f"Section 24(b) home loan interest capped at ₹2,00,000 for self-occupied property. Creates eligible loss of ₹{interest_deduction:,.0f}."
                }

        # Let-out Property
        gav = max(Decimal("0.00"), gross_rent_received)
        # Municipal taxes only deductible if actually paid
        muni_tax = min(municipal_taxes_paid, gav)
        nav = max(Decimal("0.00"), gav - muni_tax)

        # Section 24(a) Standard 30% Deduction on NAV
        std_24a = nav * Decimal("0.30")

        # Section 24(b) Interest on borrowed capital (no ₹2L cap for let-out property)
        int_24b = home_loan_interest

        net_income = nav - std_24a - int_24b

        # Loss set-off rules (Section 71(3A)):
        # Under Old Regime, house property loss can be set off against other heads up to ₹2,00,000.
        # Under New Regime, house property loss CANNOT be set off against other heads.
        eligible_setoff = Decimal("0.00")
        if net_income < Decimal("0.00"):
            abs_loss = abs(net_income)
            if is_new:
                eligible_setoff = Decimal("0.00")
            else:
                eligible_setoff = min(abs_loss, Decimal("200000.00"))

        return {
            "property_type": "let_out",
            "gross_annual_value": gav,
            "municipal_taxes": muni_tax,
            "net_annual_value": nav,
            "standard_deduction_24a": std_24a,
            "interest_deduction_24b": int_24b,
            "net_house_property_income": net_income,
            "loss_eligible_for_setoff": eligible_setoff,
            "notes": (
                "Let-out property: 30% standard deduction under Sec 24(a) and full interest under Sec 24(b) applied. "
                + ("Loss set-off against other heads capped at ₹2,00,000 (Section 71(3A))." if not is_new else "Loss from house property cannot be set off against other heads under New Regime.")
            )
        }
