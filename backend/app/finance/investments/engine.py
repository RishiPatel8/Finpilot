from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.schemas.investment import (
    InvestmentCompareRequest,
    InvestmentCompareResponse,
    InvestmentOptionComparison,
    GoalProjectionRequest,
    GoalProjectionResponse,
    MultiProductCompareRequest,
    MultiProductCompareResponse,
    MultiProductCompareItem,
    LumpSumVsSipRequest,
    LumpSumVsSipResponse,
    LumpSumVsSipSchedulePoint,
    GoalInvestmentPlanRequest,
    GoalInvestmentPlanResponse,
    GoalAllocationSlice,
    InvestmentStressTestRequest,
    InvestmentStressTestResponse,
    PortfolioAnalysisResponse,
    AssetCategorySlice,
)
from app.finance.investments.data import (
    INDIAN_INVESTMENT_PRODUCTS,
    get_all_products,
    get_product_by_id,
    filter_products
)
from app.models.financial import AssetHolding, FinancialGoal


class InvestmentEngine:
    """
    Deterministic Indian Investment Comparison, Portfolio Planner, and Stress-Testing Engine.
    Strictly follows statutory RBI, SEBI, AMFI, and Finance Act 2024 taxation and compounding rules.
    """

    # -------------------------------------------------------------------------
    # 1. Multi-Product Comparison Engine
    # -------------------------------------------------------------------------
    @classmethod
    def compare_multi_products(cls, req: MultiProductCompareRequest) -> MultiProductCompareResponse:
        amount = req.investment_amount
        months = req.time_horizon_months
        years = Decimal(str(months)) / Decimal("12.0")
        inf = req.expected_inflation_pct / Decimal("100.0")
        user_slab_rate = req.user_tax_slab_pct / Decimal("100.0")

        items: List[MultiProductCompareItem] = []

        for pid in req.selected_product_ids:
            product = get_product_by_id(pid)
            if not product:
                continue

            # 1. Determine Rate Used
            if req.custom_return_overrides and pid in req.custom_return_overrides:
                annual_rate_pct = req.custom_return_overrides[pid]
                rate_type_label = f"User Assumption ({annual_rate_pct}%)"
            else:
                annual_rate_pct = Decimal(str(product["indicative_annual_yield_pct"]))
                rate_type_label = product["rate_type"]

            r = annual_rate_pct / Decimal("100.0")
            freq = product["compounding_frequency"]
            ter = Decimal(str(product.get("ter_pct", 0.0))) / Decimal("100.0")

            # 2. Compute Compounded Gross Maturity Value & Invested Principal
            if req.investment_mode == "lump_sum":
                invested_principal = amount
                if freq == "quarterly":
                    q_rate = r / Decimal("4.0")
                    quarters = years * Decimal("4.0")
                    gross_fv = invested_principal * ((Decimal("1.0") + q_rate) ** quarters)
                elif freq == "semi_annual":
                    s_rate = r / Decimal("2.0")
                    half_years = years * Decimal("2.0")
                    gross_fv = invested_principal * ((Decimal("1.0") + s_rate) ** half_years)
                elif freq == "annual":
                    gross_fv = invested_principal * ((Decimal("1.0") + r) ** years)
                elif freq == "daily" or freq == "monthly":
                    # Daily/monthly NAV compounding (Mutual Funds, ETFs)
                    m_rate = r / Decimal("12.0")
                    gross_fv = invested_principal * ((Decimal("1.0") + m_rate) ** Decimal(str(months)))
                elif freq == "on_maturity":
                    # T-Bills or zero-coupon instruments
                    gross_fv = invested_principal * (Decimal("1.0") + (r * years))
                else:
                    gross_fv = invested_principal * ((Decimal("1.0") + r) ** years)

            else:
                # Monthly SIP Mode
                monthly_sip = amount
                invested_principal = monthly_sip * Decimal(str(months))
                m_rate = r / Decimal("12.0")

                if months <= 0:
                    gross_fv = Decimal("0.00")
                elif m_rate == Decimal("0.00"):
                    gross_fv = invested_principal
                else:
                    # Annuity Due formula (invested at start of each month)
                    # FV = P * [((1 + i)^n - 1) / i] * (1 + i)
                    factor = ((Decimal("1.0") + m_rate) ** Decimal(str(months))) - Decimal("1.0")
                    gross_fv = monthly_sip * (factor / m_rate) * (Decimal("1.0") + m_rate)

            gross_fv = gross_fv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            gain = max(Decimal("0.00"), gross_fv - invested_principal)

            # 3. Transparent Fee / Expense Drag Calculation
            # For direct MFs, TER is already reflected in NAV, but we display the cumulative cost drag
            estimated_fees = (invested_principal * ter * years).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # 4. Deterministic Statutory Tax Calculation (Finance Act 2024 Rules)
            tax_cat = product.get("tax_category", "fd_slab")
            estimated_tax = Decimal("0.00")
            tax_rule_applied = ""

            if tax_cat == "savings_80tta":
                # Up to ₹10,000 exempt in Old Regime under Section 80TTA
                taxable_interest = max(Decimal("0.00"), gain - Decimal("10000.00"))
                estimated_tax = (taxable_interest * user_slab_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax_rule_applied = f"Section 80TTA: ₹10,000 annual exemption applied; balance taxed at {req.user_tax_slab_pct}% slab rate."

            elif tax_cat == "fd_slab":
                # 100% of interest taxed at marginal slab rate
                estimated_tax = (gain * user_slab_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax_rule_applied = f"Interest added to income; taxed at marginal slab rate of {req.user_tax_slab_pct}%. 10% TDS threshold ₹40k."

            elif tax_cat == "debt_slab_50aa":
                # Finance Act 2023 / Section 50AA: All debt mutual fund gains treated as STCG, taxed at slab rate
                estimated_tax = (gain * user_slab_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax_rule_applied = f"Section 50AA: Capital gains deemed short-term; taxed at investor's {req.user_tax_slab_pct}% slab rate."

            elif tax_cat == "equity_2024":
                # Finance Act 2024 Equity Rules:
                # Holding period <= 12 months: STCG at 20%
                # Holding period > 12 months: LTCG at 12.5% beyond ₹1,25,000 exemption
                if months <= 12:
                    estimated_tax = (gain * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    tax_rule_applied = "Finance Act 2024 STCG (holding <= 12 months): Taxed at 20.0% flat."
                else:
                    taxable_ltcg = max(Decimal("0.00"), gain - Decimal("125000.00"))
                    estimated_tax = (taxable_ltcg * Decimal("0.125")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    tax_rule_applied = "Finance Act 2024 LTCG (holding > 12 months): ₹1,25,000 exemption; balance taxed at 12.5% flat."

            elif tax_cat == "eee":
                # PPF / EPF: 100% tax exempt
                estimated_tax = Decimal("0.00")
                tax_rule_applied = "Section 10(11)/10(12) EEE Status: 100% tax-exempt principal, annual interest, and maturity corpus."

            elif tax_cat == "sgb_special":
                # Sovereign Gold Bond: 2.5% coupon taxed at slab rate; capital gains on redemption at 8 years 100% tax-free
                coupon_share = min(gain, invested_principal * Decimal("0.025") * years)
                estimated_tax = (coupon_share * user_slab_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax_rule_applied = "Section 47(viic): Capital gains on RBI maturity redemption are 100% TAX-FREE. 2.5% annual coupon taxed at slab."

            elif tax_cat == "gold_2024":
                # Gold ETF Finance Act 2024: LTCG (>12m) at 12.5%, STCG (<=12m) at slab
                if months <= 12:
                    estimated_tax = (gain * user_slab_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    tax_rule_applied = f"Finance Act 2024: Gold STCG (<= 12 months) taxed at slab rate ({req.user_tax_slab_pct}%)."
                else:
                    estimated_tax = (gain * Decimal("0.125")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    tax_rule_applied = "Finance Act 2024: Gold LTCG (> 12 months) taxed at 12.5% without indexation."

            elif tax_cat == "nps":
                # NPS: 60% lump sum at 60 is tax-free; remaining 40% mandatory annuity taxed as pension
                estimated_tax = (gain * Decimal("0.40") * user_slab_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax_rule_applied = "PFRDA / Income Tax: 60% lump sum at maturity is 100% tax-free. 40% mandatory annuity taxed as pension income."

            else:
                estimated_tax = (gain * user_slab_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax_rule_applied = f"Standard slab rate taxation ({req.user_tax_slab_pct}%)."

            # 5. Net Proceeds, Post-Tax CAGR & Inflation Adjustment
            net_proceeds = max(invested_principal, gross_fv - estimated_tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if req.investment_mode == "lump_sum" and years > Decimal("0.0"):
                try:
                    cagr = (((net_proceeds / invested_principal) ** (Decimal("1.0") / years)) - Decimal("1.0")) * Decimal("100.0")
                    net_cagr = cagr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                except Exception:
                    net_cagr = annual_rate_pct
            else:
                # Approximation of net annualized return for SIP
                net_gain = net_proceeds - invested_principal
                net_cagr = ((net_gain / (invested_principal * (years / Decimal("2.0")))) * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if years > 0 and invested_principal > 0 else Decimal("0.00")

            inf_factor = (Decimal("1.0") + inf) ** years
            inf_adjusted_value = (net_proceeds / inf_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # 6. Premature Exit Penalty & Lock-in Analysis
            lock_months = product.get("lock_in_months", 0)
            is_locked = lock_months > 0 and months < lock_months
            penalty_desc = product.get("exit_penalty_rules", "No exit penalty.")
            haircut_est = Decimal("0.00")

            if not req.can_lock_funds:
                if product["id"] == "bank_fd" or product["id"] == "recurring_deposit":
                    # ~1% interest reduction on broken deposits
                    haircut_est = (invested_principal * Decimal("0.01") * years).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                elif "mf" in product["id"] and product["asset_class"] == "equity" and months < 12:
                    # 1% exit load on equity funds exited under 1 year
                    haircut_est = (gross_fv * Decimal("0.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                elif product["id"] == "elss_tax_saving" and months < 36:
                    penalty_desc = "CANNOT BE WITHDRAWN: Statutory 36-month lock-in under SEBI / IT Act."
                    haircut_est = Decimal("0.00")

            # 7. DICGC Coverage
            dicgc_cov = Decimal("0.00")
            if product.get("dicgc_insured", False):
                dicgc_cov = min(invested_principal, Decimal(str(product.get("dicgc_limit", 500000.0))))

            # 8. Pros & Cons Synthesis
            pros = []
            cons = []
            if product["rate_type"] == "guaranteed":
                pros.append("100% Capital Guaranteed / Fixed statutory interest rate")
            else:
                pros.append(f"Market-linked compounding potential (~{annual_rate_pct}% benchmark)")

            if product.get("dicgc_insured", False):
                pros.append(f"DICGC Sovereign Insurance Protection up to ₹{dicgc_cov:,.0f}")
            if tax_cat == "eee":
                pros.append("Triple Tax-Exempt (EEE) status — zero tax on gains")
            elif tax_cat == "equity_2024" and months > 12:
                pros.append("₹1,25,000 annual LTCG tax exemption")

            if product.get("lock_in_months", 0) > 0:
                cons.append(f"Mandatory lock-in period of {product['lock_in_months']} months")
            if tax_cat in ("fd_slab", "debt_slab_50aa"):
                cons.append(f"Gains taxed at high personal slab rate ({req.user_tax_slab_pct}%) without indexation")
            if product["market_risk_level"] in ("High", "Very High"):
                cons.append(f"High market volatility and interim drawdown risk ({product['market_risk_level']})")

            items.append(
                MultiProductCompareItem(
                    product_id=product["id"],
                    name=product["name"],
                    category=product["category"],
                    asset_class=product["asset_class"],
                    rate_used_pct=annual_rate_pct,
                    rate_type=rate_type_label,
                    compounding_frequency=freq,
                    invested_principal=invested_principal,
                    gross_maturity_value=gross_fv,
                    estimated_gain=gain,
                    estimated_fees_ter=estimated_fees,
                    estimated_tax=estimated_tax,
                    tax_rules_applied=tax_rule_applied,
                    net_post_tax_proceeds=net_proceeds,
                    net_annualized_cagr_pct=net_cagr,
                    inflation_adjusted_value=inf_adjusted_value,
                    is_locked=is_locked,
                    lock_in_months=lock_months,
                    liquidity_rating=product.get("liquidity_rating", "t_plus_2"),
                    liquidity_mechanism=product.get("liquidity_mechanism", ""),
                    credit_risk_level=product.get("credit_risk_level", "Low"),
                    market_risk_level=product.get("market_risk_level", "Low"),
                    dicgc_insured=product.get("dicgc_insured", False),
                    dicgc_coverage_amount=dicgc_cov,
                    premature_exit_penalty=penalty_desc,
                    premature_exit_haircut_estimate=haircut_est,
                    data_provenance=product.get("data_provenance", "Official Statutory Source"),
                    as_of_date=product.get("as_of_date", "October 2024"),
                    pros=pros,
                    cons=cons,
                    suitability_verdict=product.get("suitability", "")
                )
            )

        # Multi-factor recommendation logic
        # Evaluates time horizon, liquidity need, and post-tax yield
        if not items:
            top_rec = "No valid product selected"
            rationale = "Please select at least one verified Indian investment instrument."
        else:
            # Sort eligible options: filter out locked if user cannot lock funds
            eligible = [it for it in items if not (it.is_locked and not req.can_lock_funds)]
            if not eligible:
                eligible = items

            if months <= 6 or not req.can_lock_funds:
                # Prefer high liquidity and low credit risk
                liquid_candidates = [it for it in eligible if it.category == "liquid"]
                best_item = max(liquid_candidates or eligible, key=lambda x: x.net_post_tax_proceeds)
                top_rec = best_item.name
                rationale = (
                    f"For a short horizon of {months} months with high liquidity priority, {best_item.name} is the optimal choice. "
                    f"It provides instant or T+1 liquidity without lock-in penalties while preserving capital."
                )
            elif months <= 36:
                # Fixed income / moderate horizon
                best_item = max(eligible, key=lambda x: x.net_post_tax_proceeds)
                top_rec = best_item.name
                rationale = (
                    f"For a medium horizon of {months} months, {best_item.name} delivers the most balanced post-tax yield "
                    f"({best_item.net_annualized_cagr_pct}% net CAGR) matching your tax slab and locking capabilities."
                )
            else:
                # Long term: consider post-tax real purchasing power
                best_item = max(eligible, key=lambda x: x.inflation_adjusted_value)
                top_rec = best_item.name
                rationale = (
                    f"Over {months} months ({years:.1f} years), inflation-adjusted wealth generation is paramount. "
                    f"{best_item.name} generates the highest real purchasing power (₹{best_item.inflation_adjusted_value:,.2f}) "
                    f"after accounting for statutory Finance Act 2024 taxation and {req.expected_inflation_pct}% inflation."
                )

        disclaimer = (
            "Educational comparison only. Not SEBI-registered personalized investment advice. "
            "All rates and yields reflect verified RBI notifications, AMFI benchmark disclosures, and Finance Act 2024 statutory tax provisions. "
            "Mutual fund investments and equities are subject to market risks; read all scheme-related documents carefully."
        )

        return MultiProductCompareResponse(
            investment_mode=req.investment_mode,
            investment_amount=amount,
            time_horizon_months=months,
            user_tax_slab_pct=req.user_tax_slab_pct,
            inflation_rate_pct=req.expected_inflation_pct,
            items=items,
            top_recommendation=top_rec,
            rationale=rationale,
            regulatory_disclaimer=disclaimer
        )

    # -------------------------------------------------------------------------
    # 2. Lump Sum vs. SIP Engine
    # -------------------------------------------------------------------------
    @classmethod
    def compare_lumpsum_vs_sip(cls, req: LumpSumVsSipRequest) -> LumpSumVsSipResponse:
        product = get_product_by_id(req.product_id)
        prod_name = product["name"] if product else "Diversified Index Fund"
        months = req.time_horizon_months
        years = Decimal(str(months)) / Decimal("12.0")
        r_annual = req.expected_annual_return_pct / Decimal("100.0")
        m_rate = r_annual / Decimal("12.0")
        inf = req.expected_annual_inflation_pct / Decimal("100.0")
        tax_slab = req.user_tax_slab_pct / Decimal("100.0")

        # 1. Lump Sum Projection
        lump_invested = req.lump_sum_amount
        lump_fv = (lump_invested * ((Decimal("1.0") + m_rate) ** Decimal(str(months)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        lump_gain = max(Decimal("0.00"), lump_fv - lump_invested)

        # Lump sum tax (Finance Act 2024 equity rule if index fund/equity, else slab)
        if product and product.get("tax_category") == "equity_2024":
            if months <= 12:
                lump_tax = (lump_gain * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                taxable = max(Decimal("0.00"), lump_gain - Decimal("125000.00"))
                lump_tax = (taxable * Decimal("0.125")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            lump_tax = (lump_gain * tax_slab).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        lump_net = max(lump_invested, lump_fv - lump_tax)
        lump_real = (lump_net / ((Decimal("1.0") + inf) ** years)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 2. Monthly SIP Projection
        sip_m = req.monthly_sip_amount
        sip_total_invested = sip_m * Decimal(str(months))

        if months == 0 or m_rate == Decimal("0.00"):
            sip_fv = sip_total_invested
        else:
            factor = ((Decimal("1.0") + m_rate) ** Decimal(str(months))) - Decimal("1.0")
            sip_fv = (sip_m * (factor / m_rate) * (Decimal("1.0") + m_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        sip_gain = max(Decimal("0.00"), sip_fv - sip_total_invested)
        if product and product.get("tax_category") == "equity_2024":
            if months <= 12:
                sip_tax = (sip_gain * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                # With SIP, each instalment has its own holding period; standard approximation with ₹1.25L exemption
                taxable = max(Decimal("0.00"), sip_gain - Decimal("125000.00"))
                sip_tax = (taxable * Decimal("0.125")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            sip_tax = (sip_gain * tax_slab).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        sip_net = max(sip_total_invested, sip_fv - sip_tax)
        sip_real = (sip_net / ((Decimal("1.0") + inf) ** years)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Step-by-Step Schedule Points
        # Sample points up to 60 or every step if <= 36
        step_interval = 1 if months <= 36 else (2 if months <= 72 else 6)
        schedule: List[LumpSumVsSipSchedulePoint] = []

        for m in range(1, months + 1):
            if m % step_interval == 0 or m == months or m == 1:
                cur_lump_val = (lump_invested * ((Decimal("1.0") + m_rate) ** Decimal(str(m)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                cur_sip_invested = sip_m * Decimal(str(m))
                if m_rate > 0:
                    c_factor = ((Decimal("1.0") + m_rate) ** Decimal(str(m))) - Decimal("1.0")
                    cur_sip_val = (sip_m * (c_factor / m_rate) * (Decimal("1.0") + m_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    cur_sip_val = cur_sip_invested

                schedule.append(
                    LumpSumVsSipSchedulePoint(
                        month=m,
                        lump_sum_value=cur_lump_val,
                        lump_sum_invested=lump_invested,
                        sip_value=cur_sip_val,
                        sip_invested=cur_sip_invested
                    )
                )

        # Rupee Cost Averaging Assessment
        rca_verdict = (
            "Systematic Investment Plan (SIP) eliminates market-timing anxiety by averaging purchase costs across "
            "market peaks and troughs. Over the long run, lump sum achieves higher terminal wealth if markets trend upwards, "
            "but SIP provides superior risk-adjusted comfort and shields against immediate post-investment market corrections."
        )

        rec = (
            f"If you currently possess ₹{lump_invested:,.0f} as idle surplus, deploying it via a Systematic Transfer Plan (STP) "
            f"from a Liquid Fund into {prod_name} over 6 to 12 months provides the ideal balance between full capital deployment "
            "and Rupee-Cost Averaging."
        )

        return LumpSumVsSipResponse(
            product_name=prod_name,
            time_horizon_months=months,
            expected_return_pct=req.expected_annual_return_pct,
            lump_sum_total_invested=lump_invested,
            lump_sum_gross_value=lump_fv,
            lump_sum_net_post_tax=lump_net,
            lump_sum_real_purchasing_power=lump_real,
            sip_total_invested=sip_total_invested,
            sip_gross_value=sip_fv,
            sip_net_post_tax=sip_net,
            sip_real_purchasing_power=sip_real,
            rupee_cost_averaging_verdict=rca_verdict,
            schedule=schedule,
            recommendation=rec
        )

    # -------------------------------------------------------------------------
    # 3. Goal-Based Investment Planner Engine
    # -------------------------------------------------------------------------
    @classmethod
    def plan_goal_investment(
        cls,
        req: GoalInvestmentPlanRequest,
        verified_liquid_cash: Optional[Decimal] = None
    ) -> GoalInvestmentPlanResponse:
        n = req.time_horizon_months
        years = Decimal(str(n)) / Decimal("12.0")
        inf = req.expected_annual_inflation_pct / Decimal("100.0")

        # 1. Inflation-adjusted target
        nominal_target = req.target_amount
        if req.adjust_for_inflation and years > Decimal("0.0"):
            inflation_factor = (Decimal("1.0") + inf) ** years
            target = (nominal_target * inflation_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            target = nominal_target

        # 2. Risk-Profile & Horizon Based Blended Asset Allocation
        # Determines target % equity, debt, gold
        if n <= 36:
            # Short-Term (< 3 yrs): Conservative
            equity_pct = Decimal("15.0")
            debt_pct = Decimal("75.0")
            gold_pct = Decimal("10.0")
        elif n <= 84:
            # Medium-Term (3 - 7 yrs): Moderate
            if req.risk_profile == "conservative":
                equity_pct = Decimal("30.0")
                debt_pct = Decimal("60.0")
                gold_pct = Decimal("10.0")
            elif req.risk_profile == "aggressive":
                equity_pct = Decimal("70.0")
                debt_pct = Decimal("20.0")
                gold_pct = Decimal("10.0")
            else:
                equity_pct = Decimal("50.0")
                debt_pct = Decimal("40.0")
                gold_pct = Decimal("10.0")
        else:
            # Long-Term (7+ yrs)
            if req.risk_profile == "conservative":
                equity_pct = Decimal("50.0")
                debt_pct = Decimal("40.0")
                gold_pct = Decimal("10.0")
            elif req.risk_profile == "aggressive":
                equity_pct = Decimal("80.0")
                debt_pct = Decimal("10.0")
                gold_pct = Decimal("10.0")
            else:
                equity_pct = Decimal("65.0")
                debt_pct = Decimal("25.0")
                gold_pct = Decimal("10.0")

        # Statutory Blended CAGR
        # Equity ~12.0%, Debt ~7.2%, Gold ~8.5%
        blended_cagr = (
            (equity_pct * Decimal("0.12")) +
            (debt_pct * Decimal("0.072")) +
            (gold_pct * Decimal("0.085"))
        ) / Decimal("100.0")
        blended_cagr_pct = (blended_cagr * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        m_rate = blended_cagr / Decimal("12.0")

        # 3. Current Amount Compounded
        current_grown = (req.current_amount_allocated * ((Decimal("1.0") + m_rate) ** Decimal(str(n)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        remaining_target = max(Decimal("0.00"), target - current_grown)

        # 4. Required Monthly SIP & Lump Sum Alternative
        if remaining_target <= Decimal("0.00") or n == 0:
            required_sip = Decimal("0.00")
            required_lump_sum = Decimal("0.00")
            is_fully_funded = True
        elif m_rate == Decimal("0.00"):
            required_sip = (remaining_target / Decimal(str(n))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            required_lump_sum = remaining_target
            is_fully_funded = False
        else:
            compound_factor = ((Decimal("1.0") + m_rate) ** Decimal(str(n))) - Decimal("1.0")
            required_sip = (remaining_target * m_rate / (compound_factor * (Decimal("1.0") + m_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            required_lump_sum = (remaining_target / ((Decimal("1.0") + m_rate) ** Decimal(str(n)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            is_fully_funded = False

        # 5. Asset Allocation Slices
        slices: List[GoalAllocationSlice] = [
            GoalAllocationSlice(
                asset_class="Equity (Bluechip & Flexi-Cap)",
                target_percentage=equity_pct,
                allocated_sip=(required_sip * (equity_pct / Decimal("100.0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                allocated_lump_sum=(required_lump_sum * (equity_pct / Decimal("100.0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                suggested_product="Nifty 50 Index Fund & Flexi-Cap Fund",
                indicative_rate_pct=Decimal("12.00")
            ),
            GoalAllocationSlice(
                asset_class="Debt & Fixed Income",
                target_percentage=debt_pct,
                allocated_sip=(required_sip * (debt_pct / Decimal("100.0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                allocated_lump_sum=(required_lump_sum * (debt_pct / Decimal("100.0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                suggested_product="Corporate Bond Fund / Bank FD / PPF",
                indicative_rate_pct=Decimal("7.20")
            ),
            GoalAllocationSlice(
                asset_class="Gold / Sovereign Gold Bonds",
                target_percentage=gold_pct,
                allocated_sip=(required_sip * (gold_pct / Decimal("100.0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                allocated_lump_sum=(required_lump_sum * (gold_pct / Decimal("100.0"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                suggested_product="Gold ETF or Sovereign Gold Bond (SGB)",
                indicative_rate_pct=Decimal("8.50")
            )
        ]

        # 6. Cash Sufficiency Notice (Zero Double-Counting)
        if verified_liquid_cash is not None:
            if is_fully_funded:
                cash_notice = (
                    f"Goal is already fully funded by your currently allocated capital (₹{req.current_amount_allocated:,.0f}). "
                    f"Your verified liquid cash reserve (₹{verified_liquid_cash:,.0f}) remains intact."
                )
            elif verified_liquid_cash >= required_lump_sum:
                cash_notice = (
                    f"Cash Check PASSED: Your verified bank liquidity (₹{verified_liquid_cash:,.0f}) can comfortably cover "
                    f"the upfront lump sum requirement (₹{required_lump_sum:,.0f}) or the monthly SIP of ₹{required_sip:,.0f}."
                )
            else:
                cash_notice = (
                    f"Caution: Your verified bank liquidity is ₹{verified_liquid_cash:,.0f}. Committing an upfront lump sum of "
                    f"₹{required_lump_sum:,.0f} would exceed available liquid reserves. "
                    f"Recommendation: Fund this goal via the monthly SIP route (₹{required_sip:,.0f}/month) to protect your emergency buffer."
                )
        else:
            cash_notice = (
                f"Required monthly SIP is ₹{required_sip:,.0f} (or upfront lump sum ₹{required_lump_sum:,.0f}). "
                "Ensure this allocation does not deplete your 3-6 month core emergency runway."
            )

        disclaimer = (
            "Goal projection engine utilizes deterministic compound interest math and historical asset-class benchmarks. "
            "Actual future returns will vary with market conditions. Review and rebalance annually."
        )

        return GoalInvestmentPlanResponse(
            goal_name=req.goal_name,
            nominal_target=nominal_target,
            inflation_adjusted_target=target,
            time_horizon_months=n,
            current_amount_allocated=req.current_amount_allocated,
            required_monthly_sip=required_sip,
            required_lump_sum_alternative=required_lump_sum,
            expected_blended_cagr_pct=blended_cagr_pct,
            allocation_breakdown=slices,
            cash_sufficiency_notice=cash_notice,
            verified_liquid_cash_available=verified_liquid_cash,
            is_fully_funded=is_fully_funded,
            disclaimer=disclaimer
        )

    # -------------------------------------------------------------------------
    # 4. Investment Stress-Testing & Shock Engine
    # -------------------------------------------------------------------------
    @classmethod
    def stress_test_portfolio(cls, req: InvestmentStressTestRequest) -> InvestmentStressTestResponse:
        total_invested = sum((item.amount_invested for item in req.portfolio_items), Decimal("0.00"))
        months = req.time_horizon_months
        years = Decimal(str(months)) / Decimal("12.0")

        # Calculate Baseline Value without Shock
        # Weight by product rates
        baseline_val = Decimal("0.00")
        for item in req.portfolio_items:
            prod = get_product_by_id(item.product_id)
            r = Decimal(str(prod["indicative_annual_yield_pct"])) / Decimal("100.0") if prod else Decimal("0.07")
            val = item.amount_invested * ((Decimal("1.0") + r) ** years)
            baseline_val += val

        baseline_val = baseline_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        scenario = req.stress_scenario
        stressed_val = Decimal("0.00")
        vulnerable = []
        cushioning = []
        recommendations = []

        if scenario == "market_crash_20":
            title = "Immediate 20% Equity Market Correction"
            desc = "Simulates a sudden 20% drop in domestic and global equity markets, with debt and cash yields holding steady."
            recovery_months = 14
            for item in req.portfolio_items:
                prod = get_product_by_id(item.product_id)
                ac = prod["asset_class"] if prod else "debt"
                r = Decimal(str(prod["indicative_annual_yield_pct"])) / Decimal("100.0") if prod else Decimal("0.07")
                if ac == "equity":
                    # Instant 20% haircut, followed by normal growth
                    post_shock = item.amount_invested * Decimal("0.80")
                    val = post_shock * ((Decimal("1.0") + r) ** years)
                    vulnerable.append(f"{prod['name']} (-20% market shock)")
                elif ac == "gold":
                    # Gold typically holds or gains +3%
                    post_shock = item.amount_invested * Decimal("1.03")
                    val = post_shock * ((Decimal("1.0") + r) ** years)
                    cushioning.append(f"{prod['name']} (Safe-haven gold buffer)")
                else:
                    # Debt and liquid unaffected
                    val = item.amount_invested * ((Decimal("1.0") + r) ** years)
                    cushioning.append(f"{prod['name']} (Zero equity exposure)")
                stressed_val += val

            recommendations = [
                "Avoid panic selling: Historical Indian equity market drawdowns of 20% have recovered within 12-18 months.",
                "Continue ongoing monthly SIPs to accumulate additional mutual fund units at discounted NAVs (Rupee-Cost Averaging).",
                "Maintain a 6-month liquid emergency fund in Liquid Funds or FDs to avoid touching depressed equity holdings."
            ]

        elif scenario == "severe_recession_35":
            title = "Severe Bear Market & Credit Spread Widening (-35%)"
            desc = "Severe recession shock: 35% equity crash, 5% mark-to-market drop in corporate bonds, +15% surge in gold prices."
            recovery_months = 30
            for item in req.portfolio_items:
                prod = get_product_by_id(item.product_id)
                ac = prod["asset_class"] if prod else "debt"
                r = Decimal(str(prod["indicative_annual_yield_pct"])) / Decimal("100.0") if prod else Decimal("0.07")
                if ac == "equity":
                    post_shock = item.amount_invested * Decimal("0.65")
                    val = post_shock * ((Decimal("1.0") + r) ** years)
                    vulnerable.append(f"{prod['name']} (-35% deep drawdown)")
                elif prod["id"] == "corporate_bond_fund":
                    post_shock = item.amount_invested * Decimal("0.95")
                    val = post_shock * ((Decimal("1.0") + r) ** years)
                    vulnerable.append(f"{prod['name']} (-5% credit spread risk)")
                elif ac == "gold":
                    post_shock = item.amount_invested * Decimal("1.15")
                    val = post_shock * ((Decimal("1.0") + r) ** years)
                    cushioning.append(f"{prod['name']} (+15% flight-to-safety surge)")
                else:
                    val = item.amount_invested * ((Decimal("1.0") + r) ** years)
                    cushioning.append(f"{prod['name']} (Guaranteed deposit safety)")
                stressed_val += val

            recommendations = [
                "Rebalance: Harvest gains from surging gold allocations and rebalance into undervalued equities.",
                "Verify debt quality: Ensure bond holdings are concentrated in Sovereign Gilts and AAA corporate credits.",
                "Extend investment horizon for equity goals by at least 1-2 years to allow full market cycle recovery."
            ]

        elif scenario == "prolonged_stagnation":
            title = "Prolonged Low Return / Stagnation Period"
            desc = "Simulates 3 consecutive years of muted 4.0% equity growth and high inflation eating into real returns."
            recovery_months = 36
            for item in req.portfolio_items:
                prod = get_product_by_id(item.product_id)
                ac = prod["asset_class"] if prod else "debt"
                if ac == "equity":
                    # Returns crushed to 4%
                    val = item.amount_invested * ((Decimal("1.04")) ** years)
                    vulnerable.append(f"{prod['name']} (Stagnant 4% return vs 12% benchmark)")
                else:
                    r = Decimal(str(prod["indicative_annual_yield_pct"])) / Decimal("100.0") if prod else Decimal("0.07")
                    val = item.amount_invested * ((Decimal("1.0") + r) ** years)
                    cushioning.append(f"{prod['name']} (Contractual {prod['indicative_annual_yield_pct']}% yield)")
                stressed_val += val

            recommendations = [
                "Shift focus to hybrid / balanced advantage funds that dynamically capture market valuation opportunities.",
                "Ensure fixed income allocations are locked in high-yielding deposits before rate cycles soften."
            ]

        elif scenario == "high_inflation_shock":
            title = "Macro Inflation Shock (Inflation Spikes to 9.5%)"
            desc = "Inflation spikes to 9.5%, RBI hikes repo rate +150 bps, bond prices fall, cash yields rise."
            recovery_months = 18
            for item in req.portfolio_items:
                prod = get_product_by_id(item.product_id)
                pid = prod["id"] if prod else ""
                r = Decimal(str(prod["indicative_annual_yield_pct"])) / Decimal("100.0") if prod else Decimal("0.07")
                if pid in ("gilt_fund", "corporate_bond_fund"):
                    # Long duration bonds suffer capital loss
                    post_shock = item.amount_invested * Decimal("0.92")
                    val = post_shock * ((Decimal("1.0") + r) ** years)
                    vulnerable.append(f"{prod['name']} (-8% duration loss from rate hikes)")
                elif prod["category"] == "liquid":
                    # Liquid funds benefit from rising repo rates (+1.25%)
                    val = item.amount_invested * ((Decimal("1.0") + r + Decimal("0.0125")) ** years)
                    cushioning.append(f"{prod['name']} (Captures rising interest rate yields)")
                else:
                    val = item.amount_invested * ((Decimal("1.0") + r) ** years)
                    cushioning.append(f"{prod['name']}")
                stressed_val += val

            recommendations = [
                "Reduce duration in debt funds: Prefer money market or short-duration funds over long-term gilts.",
                "Deploy surplus cash into floating-rate instruments or short-tenure bank FDs rolling over at higher rates."
            ]

        elif scenario == "premature_emergency_exit":
            title = "Forced Premature Exit at Month 6"
            desc = "Simulates sudden liquidation of all investments at Month 6 due to an unexpected emergency requirement."
            recovery_months = 0
            for item in req.portfolio_items:
                prod = get_product_by_id(item.product_id)
                pid = prod["id"] if prod else ""
                half_year = Decimal("0.5")
                r = Decimal(str(prod["indicative_annual_yield_pct"])) / Decimal("100.0") if prod else Decimal("0.07")
                growth_6m = item.amount_invested * ((Decimal("1.0") + r) ** half_year)

                if pid == "elss_tax_saving" or pid == "ppf":
                    # Inaccessible! Locked!
                    val = Decimal("0.00")
                    vulnerable.append(f"{prod['name']} (₹0 accessible — locked under statutory rules!)")
                elif pid in ("bank_fd", "recurring_deposit"):
                    # 1% penalty on premature break
                    val = item.amount_invested * ((Decimal("1.0") + max(Decimal("0.01"), r - Decimal("0.01"))) ** half_year)
                    vulnerable.append(f"{prod['name']} (1.0% premature withdrawal penalty)")
                elif prod["asset_class"] == "equity":
                    # 1% exit load under 1 year
                    val = growth_6m * Decimal("0.99")
                    vulnerable.append(f"{prod['name']} (1.0% exit load)")
                else:
                    val = growth_6m
                    cushioning.append(f"{prod['name']} (Instant/T+1 liquidity with zero exit load)")
                stressed_val += val

            recommendations = [
                "CRITICAL: Never put money needed within 1-3 years into locked tax-savers (ELSS, PPF, NPS).",
                "Build a dedicated 6-month emergency reserve strictly in Liquid Funds and sweep-in deposits."
            ]

        else:  # paused_sip_6mo
            title = "Income Disruption / 6-Month SIP Pause"
            desc = "Simulates an emergency income halt where monthly SIP investments are paused for 6 months."
            recovery_months = 6
            sip_loss = req.monthly_sip_amount * Decimal("6.0")
            stressed_val = max(Decimal("0.00"), baseline_val - (sip_loss * Decimal("1.20")))
            vulnerable.append("Monthly Wealth Accumulation Pace (6 instalments missed)")
            cushioning.append("Existing Capital Compounding Safely")
            recommendations = [
                "Use the 'Pause SIP' facility offered by AMCs rather than permanently canceling the mandate.",
                "Catch up via step-up SIPs once income normalizes to stay on track for your financial target."
            ]

        stressed_val = stressed_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        drawdown_amt = max(Decimal("0.00"), baseline_val - stressed_val)
        drawdown_pct = ((drawdown_amt / baseline_val) * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if baseline_val > 0 else Decimal("0.00")

        if drawdown_pct < Decimal("5.0"):
            resilience = "High"
        elif drawdown_pct < Decimal("18.0"):
            resilience = "Moderate"
        else:
            resilience = "Vulnerable"

        disclaimer = (
            "Stress test models are deterministic scenario simulations. They do not constitute forward-looking return guarantees "
            "or price predictions. Real-world market shocks may vary in depth, speed, and recovery duration."
        )

        return InvestmentStressTestResponse(
            stress_scenario=scenario,
            scenario_title=title,
            scenario_description=desc,
            total_capital_deployed=total_invested,
            baseline_projected_value=baseline_val,
            stressed_projected_value=stressed_val,
            drawdown_amount=drawdown_amt,
            drawdown_pct=drawdown_pct,
            estimated_recovery_months=recovery_months,
            resilience_rating=resilience,
            vulnerable_assets=vulnerable,
            cushioning_assets=cushioning,
            safeguard_recommendations=recommendations,
            disclaimer=disclaimer
        )

    # -------------------------------------------------------------------------
    # 5. Portfolio Holdings Analysis Engine
    # -------------------------------------------------------------------------
    @classmethod
    def analyze_existing_portfolio(cls, db: Session, user_id: str) -> PortfolioAnalysisResponse:
        holdings = db.query(AssetHolding).filter(AssetHolding.user_id == user_id).all()

        if not holdings:
            # Clean, transparent response with zero fabricated assets
            return PortfolioAnalysisResponse(
                total_portfolio_value=Decimal("0.00"),
                categories_breakdown=[],
                equity_exposure_pct=Decimal("0.00"),
                debt_fixed_income_pct=Decimal("0.00"),
                liquid_cash_pct=Decimal("0.00"),
                gold_alternatives_pct=Decimal("0.00"),
                risk_profile="Unallocated",
                risk_alignment_verdict="No existing portfolio assets recorded in your FinPilot profile.",
                concentration_risks=["No assets detected. Record your bank deposits, mutual funds, or gold to receive automated allocation insights."],
                rebalancing_recommendations=[
                    "Step 1: Set aside 3 to 6 months of mandatory living expenses in a Liquid Fund or Bank Auto-Sweep FD.",
                    "Step 2: Start an equity index fund SIP for goals at least 5 years away.",
                    "Step 3: Allocate 5-10% to Sovereign Gold Bonds or Gold ETFs for portfolio diversification."
                ],
                data_source="Verified FinPilot Database Records (AssetHolding Table)"
            )

        total_val = sum((Decimal(str(h.current_value)) for h in holdings), Decimal("0.00"))

        equity_val = Decimal("0.00")
        debt_val = Decimal("0.00")
        liquid_val = Decimal("0.00")
        gold_val = Decimal("0.00")

        for h in holdings:
            cat = (h.category or "").lower()
            val = Decimal(str(h.current_value))
            if cat in ("equity_mf", "equity", "stock", "shares"):
                equity_val += val
            elif cat in ("liquid_mf", "cash", "savings"):
                liquid_val += val
            elif cat in ("gold", "sgb", "real_estate"):
                gold_val += val
            else:
                # bond, fd, epf_ppf, debt
                debt_val += val

        def calc_pct(v: Decimal) -> Decimal:
            if total_val == Decimal("0.00"):
                return Decimal("0.00")
            return ((v / total_val) * Decimal("100.0")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        eq_pct = calc_pct(equity_val)
        debt_pct = calc_pct(debt_val)
        liq_pct = calc_pct(liquid_val)
        gold_pct = calc_pct(gold_val)

        # Target benchmarks (Moderate profile: 50% Equity, 30% Debt, 10% Liquid, 10% Gold)
        slices = [
            AssetCategorySlice(
                category="equity",
                label="Equities & Mutual Funds",
                total_value=equity_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                percentage=eq_pct,
                target_percentage=Decimal("50.0"),
                difference_pct=(eq_pct - Decimal("50.0")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            ),
            AssetCategorySlice(
                category="debt",
                label="Fixed Income & Bonds",
                total_value=debt_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                percentage=debt_pct,
                target_percentage=Decimal("30.0"),
                difference_pct=(debt_pct - Decimal("30.0")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            ),
            AssetCategorySlice(
                category="liquid",
                label="Liquid Cash & Emergency Reserves",
                total_value=liquid_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                percentage=liq_pct,
                target_percentage=Decimal("10.0"),
                difference_pct=(liq_pct - Decimal("10.0")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            ),
            AssetCategorySlice(
                category="gold",
                label="Gold & Alternatives",
                total_value=gold_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                percentage=gold_pct,
                target_percentage=Decimal("10.0"),
                difference_pct=(gold_pct - Decimal("10.0")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            )
        ]

        # Risk profile deduction
        if eq_pct > Decimal("65.0"):
            profile = "Aggressive Growth"
            verdict = "Heavy equity exposure makes portfolio susceptible to steep drawdowns during market corrections."
        elif eq_pct < Decimal("25.0"):
            profile = "Conservative Capital Preservation"
            verdict = "Portfolio is heavily tilted towards fixed income; real purchasing power may lag inflation over long horizons."
        else:
            profile = "Balanced Moderate"
            verdict = "Healthy diversification between wealth compounding and fixed-income downside stability."

        conc_risks = []
        if eq_pct > Decimal("75.0"):
            conc_risks.append(f"Extreme equity concentration ({eq_pct}%). Portfolio lacks fixed-income cushion during bear markets.")
        if liq_pct < Decimal("5.0"):
            conc_risks.append("Critically low liquid reserves (<5%). Any cash emergency may force premature liquidation of investments.")
        if gold_pct == Decimal("0.0"):
            conc_risks.append("Zero gold/alternative allocation. Missing a proven inflation hedge and currency shock buffer.")

        rebalancing = []
        if liq_pct < Decimal("10.0"):
            rebalancing.append("Top up your liquid emergency fund to cover at least 3 to 6 months of mandatory household expenditure.")
        if eq_pct > Decimal("60.0"):
            rebalancing.append("Direct next monthly contributions into debt mutual funds or PPF to restore the 50/30/10/10 target balance.")
        elif eq_pct < Decimal("40.0"):
            rebalancing.append("Increase equity index fund SIPs to ensure wealth does not lose purchasing power against inflation.")

        return PortfolioAnalysisResponse(
            total_portfolio_value=total_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            categories_breakdown=slices,
            equity_exposure_pct=eq_pct,
            debt_fixed_income_pct=debt_pct,
            liquid_cash_pct=liq_pct,
            gold_alternatives_pct=gold_pct,
            risk_profile=profile,
            risk_alignment_verdict=verdict,
            concentration_risks=conc_risks or ["Portfolio is well-diversified across primary asset classes."],
            rebalancing_recommendations=rebalancing or ["Asset allocation is aligned with optimal risk parameters."],
            data_source="Verified FinPilot Database Records (AssetHolding Table)"
        )

    # -------------------------------------------------------------------------
    # 6. Backward-Compatible Legacy Methods (AI CFO & Chat Tools Support)
    # -------------------------------------------------------------------------
    @classmethod
    def compare_instruments(cls, req: InvestmentCompareRequest) -> InvestmentCompareResponse:
        amount = req.investment_amount
        months = req.time_horizon_months
        years = Decimal(str(months)) / Decimal("12.0")
        inf = req.expected_inflation_pct / Decimal("100.0")

        # Typical indicative pre-tax annual yields
        liquid_rate = Decimal("0.0675")  # ~6.75%
        bond_rate = Decimal("0.0760")    # ~7.60%
        fd_rate = Decimal("0.0710")      # ~7.10%

        # 1. Liquid Mutual Fund Projection
        liquid_fv = (amount * ((Decimal("1.0") + liquid_rate / Decimal("12.0")) ** (Decimal("12.0") * years))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        liquid_real = (liquid_fv / ((Decimal("1.0") + inf) ** years)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        liquid_comp = InvestmentOptionComparison(
            category="liquid_mf",
            display_name="Liquid Mutual Fund",
            indicative_annual_yield_pct=liquid_rate * Decimal("100.0"),
            recommended_time_horizon="1 day to 6 months",
            liquidity_mechanism="Instant redemption up to ₹50,000/day per fund; T+1 business day for full balance.",
            credit_risk_level="Low (AAA/A1+ commercial papers and Treasury bills with maturity <= 91 days).",
            interest_rate_risk="Negligible (Average portfolio maturity is under 91 days).",
            tax_treatment_summary="Section 50AA: Capital gains taxed at your applicable income tax slab rate.",
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
            tax_treatment_summary="Annual interest accrued is taxed at your income slab rate. 10% TDS deducted if annual interest exceeds ₹40,000.",
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

        # 3. High-Quality Bonds Projection
        bond_fv = (amount * ((Decimal("1.0") + bond_rate / Decimal("2.0")) ** (Decimal("2.0") * years))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        bond_real = (bond_fv / ((Decimal("1.0") + inf) ** years)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        bond_comp = InvestmentOptionComparison(
            category="bond",
            display_name="Sovereign / AAA Corporate Bond",
            indicative_annual_yield_pct=bond_rate * Decimal("100.0"),
            recommended_time_horizon="3 years to 7+ years",
            liquidity_mechanism="Secondary market sale via exchange (NSE/BSE/RBI Retail Direct).",
            credit_risk_level="Zero for Sovereign/G-Sec; Low for AAA Corporate Bonds.",
            interest_rate_risk="Moderate to High (Longer duration bonds lose market value if interest rates rise).",
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

        if months <= 6 or not req.can_lock_funds:
            top_rec = "Liquid Mutual Fund"
            rationale = (
                f"For your {months}-month time horizon and need for liquidity, Liquid Mutual Funds are superior. "
                "They offer instant T+1 redemption without premature lock-in penalties, while capturing "
                "competitive yields."
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
                f"For a longer horizon of {months} months ({years:.1f} years), Sovereign or AAA Bonds deliver steady coupon income, "
                "allowing you to ride through short-term rate cycles."
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

        nominal_target = req.target_amount
        if req.adjust_for_inflation:
            inflation_factor = (Decimal("1.0") + inf) ** years
            target = (nominal_target * inflation_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            target = nominal_target

        current_grown = (req.current_amount * ((Decimal("1.0") + monthly_rate) ** n)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        remaining_target = max(Decimal("0.00"), target - current_grown)

        if remaining_target == Decimal("0.00") or n == 0:
            monthly_sip = Decimal("0.00")
        elif monthly_rate == Decimal("0.00"):
            monthly_sip = (remaining_target / Decimal(str(n))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            compound_factor = ((Decimal("1.0") + monthly_rate) ** n) - Decimal("1.0")
            monthly_sip = (remaining_target * monthly_rate / (compound_factor * (Decimal("1.0") + monthly_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_contributed = req.current_amount + (monthly_sip * Decimal(str(n)))
        wealth_gain = max(Decimal("0.00"), target - total_contributed)

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
