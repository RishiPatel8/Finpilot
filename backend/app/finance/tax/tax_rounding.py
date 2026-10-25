from decimal import Decimal, ROUND_HALF_UP


def round_to_nearest_ten(val: Decimal) -> Decimal:
    """
    Income Tax Act 1961 Section 288A (Taxable Income) & Section 288B (Tax Liability).
    Rounds any rupee figure to the nearest multiple of ten.
    If the last digit is 5 or more, round up; otherwise round down.
    """
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    return (val / Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("10")
