from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any
from app.schemas.investment import (
    InvestmentCompareRequest,
    InvestmentCompareResponse,
    InvestmentOptionComparison,
    GoalProjectionRequest,
    GoalProjectionResponse
)


class InvestmentEngine:
    """
    Deterministic Investment Comparison (Liquid MF vs Bonds vs FD) and Goal Projection Engine.
    """

    @classmethod
    def compare_instruments(cls, req: InvestmentCompareRequest) -> InvestmentCompareResponse:
        amount = req.investment_amount
        months = req.time_horizon_months
        years = Decimal(str(months)) / Decimal("12.0")
        inf = req.expected_inflation_pct / Decimal("100.0")

        # Typical indicative pre-tax annual yields
        liquid_rate = Decimal("0.0675")  # ~6.75%
        bond_rate = Decimal("0.0760")    # ~7.60% (e.g. RBI Floating Rate / AAA Corporate)
        fd_rate = Decimal("0.0710")      # ~7.10% (Major bank 1-3 yr FD)

        # 1. Liquid Mutual Fund Projection
        # Compounded daily/monthly, negligible exit load past 7 days, taxed at slab rate under Section 50AA
        liquid_fv = (amount * ((Decimal("1.0") + liquid_rate / Decimal("12.0")) ** (Decimal("12.0") * years))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        liquid_real = (liquid_fv / ((Decimal("1.0") + inf) ** years)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        liquid_comp = InvestmentOptionComparison(
            category="liquid_mf",
            display_name="Liquid Mutual Fund",
            indicative_annual_yield_pct=liquid_rate * Decimal("100.0"),
            recommended_time_horizon="1 day to 6 months",
            liquidity_mechanism="Instant redemption up to ₹50,000/day per fund; T+1 business day for full balance.",
            credit_risk_level="Low (Invests only in AAA/A1+ commercial papers and Treasury bills with maturity <= 91 days).",
            interest_rate_risk="Negligible (Average portfolio maturity is under 91 days, minimizing duration risk).",
            tax_treatment_summary="Section 50AA: Capital gains taxed at your applicable income tax slab rate (short-term deemed).",
            exit_load_or_penalty="Tiered exit load only for first 7 days (0.0070% down to 0%); 0% thereafter.",
            pros=[
                "High liquidity without breaking an entire deposit",
                "No penalty after 7 days",
                "Market-linked returns adjusting quickly to rising RBI repo rates"
            ],
            cons=[
                "Returns are market-linked and not capital-guaranteed",
                "Subject to capital gains tax at your highest slab rate"
            ],
            suitability_verdict="Best for emergency reserves, parking surplus cash, or funds needed within 1 to 6 months.",
            projected_maturity_value=liquid_fv,
            inflation_adjusted_value=liquid_real
        )

        # 2. Fixed Deposit Projection
        # Compounded quarterly, breakable with ~0.5% - 1% interest rate penalty
        fd_fv = (amount * ((Decimal("1.0") + fd_rate / Decimal("4.0")) ** (Decimal("4.0") * years))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fd_real = (fd_fv / ((Decimal("1.0") + inf) ** years)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        fd_comp = InvestmentOptionComparison(
            category="fd",
            display_name="Bank Fixed Deposit",
            indicative_annual_yield_pct=fd_rate * Decimal("100.0"),
            recommended_time_horizon="6 months to 5 years",
            liquidity_mechanism="Breakable via net banking; funds credited instantly to savings account.",
            credit_risk_level="Very Low (Covered by DICGC deposit insurance up to ₹5,00,000 per bank).",
            interest_rate_risk="Zero if held to maturity; locked-in rate immune to rate cuts.",
            tax_treatment_summary="Annual interest accrued is taxed at your income slab rate. 10% TDS deducted if annual interest exceeds ₹40,000 (₹50k for seniors).",
            exit_load_or_penalty="Premature withdrawal penalty of 0.50% to 1.00% lower interest rate.",
            pros=[
                "Guaranteed returns locked for chosen tenure",
                "DICGC insurance safety up to ₹5 Lakhs",
                "Zero market volatility"
            ],
            cons=[
                "TDS deducted yearly even before maturity",
                "Penalty on premature exit reduces actual return",
                "Locked at fixed rate during rate-hiking cycles"
            ],
            suitability_verdict="Best if you require complete capital certainty and know you won't need the money before maturity.",
            projected_maturity_value=fd_fv,
            inflation_adjusted_value=fd_real
        )

        # 3. High-Quality Bonds Projection (e.g. RBI Floating Rate / Sovereign G-Sec / AAA Corp)
        # Semi-annual coupon or maturity payout
        bond_fv = (amount * ((Decimal("1.0") + bond_rate / Decimal("2.0")) ** (Decimal("2.0") * years))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        bond_real = (bond_fv / ((Decimal("1.0") + inf) ** years)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        bond_comp = InvestmentOptionComparison(
            category="bond",
            display_name="Sovereign / AAA Corporate Bond",
            indicative_annual_yield_pct=bond_rate * Decimal("100.0"),
            recommended_time_horizon="3 years to 7+ years",
            liquidity_mechanism="Secondary market sale via exchange (NSE/BSE/RBI Retail Direct), subject to market trading volume.",
            credit_risk_level="Zero for Sovereign/G-Sec; Low for AAA Corporate Bonds; High for unsecured NBFCs.",
            interest_rate_risk="Moderate to High (Longer duration bonds lose market value if prevailing interest rates rise).",
            tax_treatment_summary="Coupons taxed at slab rate. Listed bonds held >12 months taxed at revised capital gains rate.",
            exit_load_or_penalty="No early exit fee, but early sale on secondary market is exposed to market price fluctuations.",
            pros=[
                "Higher yields than liquid funds and regular FDs",
                "Regular predictable semi-annual coupon cash flow",
                "Sovereign backing available on RBI G-Secs"
            ],
            cons=[
                "Secondary market liquidity can be low for retail lots",
                "Price drops if interest rates rise before maturity",
                "Lock-in required to avoid market price risk"
            ],
            suitability_verdict="Best for intermediate to long horizons (3+ years) where funds will not be needed on short notice.",
            projected_maturity_value=bond_fv,
            inflation_adjusted_value=bond_real
        )

        comparisons = [liquid_comp, fd_comp, bond_comp]

        # Recommendation logic based on tenure and lock capability
        if months <= 6 or not req.can_lock_funds:
            top_rec = "Liquid Mutual Fund"
            rationale = (
                f"For your {months}-month time horizon and need for liquidity, Liquid Mutual Funds are superior. "
                "They offer instant T+1 redemption without premature lock-in penalties, while capturing "
                "competitive ~6.75% annualized yields."
            )
        elif months <= 24:
            top_rec = "Bank Fixed Deposit"
            rationale = (
                f"For a {months}-month horizon with lockable funds, a Bank Fixed Deposit guarantees your "
                "fixed interest without exposure to market fluctuations, protected by DICGC insurance up to ₹5 Lakhs."
            )
        else:
            top_rec = "Sovereign / AAA Bond"
            rationale = (
                f"For a longer horizon of {months} months ({years:.1f} years), Sovereign or AAA Bonds deliver the "
                "highest yield (~7.60%) and steady coupon income, allowing you to ride through short-term rate cycles."
            )

        disclaimer = (
            "Educational comparison only. Not SEBI-registered personalized investment advice. "
            "Mutual fund investments are subject to market risks; read scheme-related documents carefully."
        )

        return InvestmentCompareResponse(
            principal_amount=amount,
            time_horizon_months=months,
            inflation_rate_pct=req.expected_inflation_pct,
            comparisons=comparisons,
            top_recommendation=top_rec,
            rationale=rationale,
            disclaimer=disclaimer
        )

    @classmethod
    def project_goal(cls, req: GoalProjectionRequest) -> GoalProjectionResponse:
        n = req.time_horizon_months
        years = Decimal(str(n)) / Decimal("12.0")
        inf = req.expected_annual_inflation_pct / Decimal("100.0")
        r = req.expected_annual_return_pct / Decimal("100.0")
        monthly_rate = r / Decimal("12.0")

        # Adjust target for inflation if requested: Target_infl = Target * (1 + inf)^years
        nominal_target = req.target_amount
        if req.adjust_for_inflation:
            inflation_factor = (Decimal("1.0") + inf) ** years
            target = (nominal_target * inflation_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            target = nominal_target

        # Grow current amount: Current_FV = Current * (1 + monthly_rate)^n
        current_grown = (req.current_amount * ((Decimal("1.0") + monthly_rate) ** n)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        remaining_target = max(Decimal("0.00"), target - current_grown)

        # Monthly SIP required for remaining target:
        # Formula: SIP = Target * i / [((1 + i)^n - 1) * (1 + i)]
        if remaining_target == Decimal("0.00") or n == 0:
            monthly_sip = Decimal("0.00")
        else:
            compound_factor = ((Decimal("1.0") + monthly_rate) ** n) - Decimal("1.0")
            monthly_sip = (remaining_target * monthly_rate / (compound_factor * (Decimal("1.0") + monthly_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_contributed = req.current_amount + (monthly_sip * Decimal(str(n)))
        wealth_gain = max(Decimal("0.00"), target - total_contributed)

        # Yearly breakdown
        breakdown = []
        running_bal = req.current_amount
        for y in range(1, int(years) + 1):
            for _ in range(12):
                running_bal = (running_bal + monthly_sip) * (Decimal("1.0") + monthly_rate)
            breakdown.append({
                "year": y,
                "projected_balance": round(float(running_bal), 2),
                "total_invested": round(float(req.current_amount + monthly_sip * Decimal(str(y * 12))), 2)
            })

        return GoalProjectionResponse(
            goal_name=req.goal_name,
            nominal_target_amount=nominal_target,
            inflation_adjusted_target=target,
            current_amount=req.current_amount,
            time_horizon_months=n,
            required_monthly_sip=monthly_sip,
            total_investment_contributed=total_contributed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            projected_wealth_gain=wealth_gain.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            breakdown_by_year=breakdown
        )
