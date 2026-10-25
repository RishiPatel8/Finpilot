from decimal import Decimal
from typing import List, Tuple, Dict, Any, Optional


SUPPORTED_ASSESSMENT_YEARS = ["2024-25", "2025-26", "2026-27"]

AY_TO_FY_MAP = {
    "2024-25": "2023-24",
    "2025-26": "2024-25",
    "2026-27": "2025-26",
}


def normalize_assessment_year(year_str: str) -> str:
    """Validates and normalizes Assessment Year string (e.g. '2025-26' or 'AY 2025-26' or 'FY 2024-25')."""
    cleaned = year_str.replace("AY", "").replace("ay", "").strip()
    if cleaned in SUPPORTED_ASSESSMENT_YEARS:
        return cleaned
    
    # Check if user entered Financial Year e.g. "2024-25" -> AY "2025-26"
    for ay, fy in AY_TO_FY_MAP.items():
        if cleaned == fy or cleaned == f"FY {fy}" or cleaned == f"fy {fy}":
            return ay

    raise ValueError(
        f"Assessment Year '{year_str}' is unsupported. "
        f"FinPilot Income Tax Engine strictly supports verified statutory rules for AY 2024-25 (FY 2023-24), "
        f"AY 2025-26 (FY 2024-25), and AY 2026-27 (FY 2025-26)."
    )


class TaxRules:
    """Versioned statutory constants and rules for Indian Income Tax."""

    @staticmethod
    def get_standard_deduction(assessment_year: str, regime: str, is_salaried: bool) -> Decimal:
        """Section 16(ia) Standard Deduction."""
        if not is_salaried:
            return Decimal("0.00")
        
        ay = normalize_assessment_year(assessment_year)
        if regime.lower() == "new":
            if ay in ["2025-26", "2026-27"]:
                # Finance (No. 2) Act 2024 increased standard deduction to ₹75,000
                return Decimal("75000.00")
            else:
                return Decimal("50000.00")
        else:
            # Old Regime remains ₹50,000
            return Decimal("50000.00")

    @staticmethod
    def get_new_regime_slabs(assessment_year: str) -> List[Tuple[str, Decimal, Decimal, Decimal]]:
        """
        Returns list of (Description, LowerBound, UpperBound, RatePct) for Section 115BAC.
        """
        ay = normalize_assessment_year(assessment_year)
        if ay in ["2025-26", "2026-27"]:
            # Finance (No. 2) Act 2024 (Budget July 2024)
            return [
                ("Up to ₹3,00,000", Decimal("0"), Decimal("300000"), Decimal("0.0")),
                ("₹3,00,001 to ₹7,00,000", Decimal("300000"), Decimal("700000"), Decimal("5.0")),
                ("₹7,00,001 to ₹10,00,000", Decimal("700000"), Decimal("1000000"), Decimal("10.0")),
                ("₹10,00,001 to ₹12,00,000", Decimal("1000000"), Decimal("1200000"), Decimal("15.0")),
                ("₹12,00,001 to ₹15,00,000", Decimal("1200000"), Decimal("1500000"), Decimal("20.0")),
                ("Above ₹15,00,000", Decimal("1500000"), Decimal("9999999999"), Decimal("30.0")),
            ]
        else:
            # AY 2024-25 (Finance Act 2023)
            return [
                ("Up to ₹3,00,000", Decimal("0"), Decimal("300000"), Decimal("0.0")),
                ("₹3,00,001 to ₹6,00,000", Decimal("300000"), Decimal("600000"), Decimal("5.0")),
                ("₹6,00,001 to ₹9,00,000", Decimal("600000"), Decimal("900000"), Decimal("10.0")),
                ("₹9,00,001 to ₹12,00,000", Decimal("900000"), Decimal("1200000"), Decimal("15.0")),
                ("₹12,00,001 to ₹15,00,000", Decimal("1200000"), Decimal("1500000"), Decimal("20.0")),
                ("Above ₹15,00,000", Decimal("1500000"), Decimal("9999999999"), Decimal("30.0")),
            ]

    @staticmethod
    def get_old_regime_slabs(
        assessment_year: str,
        taxpayer_category: str,
        residence_status: str
    ) -> List[Tuple[str, Decimal, Decimal, Decimal]]:
        """
        Returns Old Regime slabs based on age and residency.
        Non-residents are taxed as general individuals regardless of age.
        """
        normalize_assessment_year(assessment_year)
        cat = taxpayer_category.lower()
        is_resident = residence_status.lower() != "non_resident"

        if is_resident and (cat in ["super_senior", "super_senior_citizen"]):
            # Resident 80 years or older: basic exemption limit is ₹5,00,000
            return [
                ("Up to ₹5,00,000", Decimal("0"), Decimal("500000"), Decimal("0.0")),
                ("₹5,00,001 to ₹10,00,000", Decimal("500000"), Decimal("1000000"), Decimal("20.0")),
                ("Above ₹10,00,000", Decimal("1000000"), Decimal("9999999999"), Decimal("30.0")),
            ]
        elif is_resident and (cat in ["senior_citizen", "senior"]):
            # Resident 60 to 79 years: basic exemption limit is ₹3,00,000
            return [
                ("Up to ₹3,00,000", Decimal("0"), Decimal("300000"), Decimal("0.0")),
                ("₹3,00,001 to ₹5,00,000", Decimal("300000"), Decimal("500000"), Decimal("5.0")),
                ("₹5,00,001 to ₹10,00,000", Decimal("500000"), Decimal("1000000"), Decimal("20.0")),
                ("Above ₹10,00,000", Decimal("1000000"), Decimal("9999999999"), Decimal("30.0")),
            ]
        else:
            # Individual below 60, NRI, or HUF: basic exemption limit is ₹2,50,000
            return [
                ("Up to ₹2,50,000", Decimal("0"), Decimal("250000"), Decimal("0.0")),
                ("₹2,50,001 to ₹5,00,000", Decimal("250000"), Decimal("500000"), Decimal("5.0")),
                ("₹5,00,001 to ₹10,00,000", Decimal("500000"), Decimal("1000000"), Decimal("20.0")),
                ("Above ₹10,00,000", Decimal("1000000"), Decimal("9999999999"), Decimal("30.0")),
            ]

    @staticmethod
    def get_capital_gains_rates(assessment_year: str) -> Dict[str, Any]:
        """
        Special rates for capital gains.
        Finance (No. 2) Act 2024:
        - STCG Sec 111A: 20% (was 15%)
        - LTCG Sec 112A: 12.5% exceeding ₹1,25,000 (was 10% exceeding ₹1,00,000)
        - LTCG Sec 112: 12.5% without indexation
        """
        ay = normalize_assessment_year(assessment_year)
        if ay in ["2025-26", "2026-27"]:
            return {
                "stcg_111a_rate": Decimal("20.0"),
                "ltcg_112a_rate": Decimal("12.5"),
                "ltcg_112a_exemption": Decimal("125000.00"),
                "ltcg_112_rate": Decimal("12.5"),
            }
        else:
            return {
                "stcg_111a_rate": Decimal("15.0"),
                "ltcg_112a_rate": Decimal("10.0"),
                "ltcg_112a_exemption": Decimal("100000.00"),
                "ltcg_112_rate": Decimal("20.0"),
            }
