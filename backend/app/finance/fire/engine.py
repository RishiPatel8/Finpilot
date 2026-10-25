from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
import math
from app.schemas.fire import (
    FireCalculationInput,
    FireCalculationResponse,
    FireStrategySummary,
    FireProjectionPoint
)


class FireEngine:
    """
    Deterministic Financial Independence, Retire Early (FIRE) Engine.
    Executes mathematically exact compound interest, inflation adjustments,
    and portfolio decumulation formulas. Never hallucinates numbers.
    """

    @classmethod
    def calculate_fire(cls, inp: FireCalculationInput) -> FireCalculationResponse:
        current_age = inp.current_age
        retirement_age = inp.retirement_age
        life_exp = inp.life_expectancy_age
        years_to_retire = max(0, retirement_age - current_age)

        curr_assets = inp.current_investable_assets or Decimal("0.00")
        monthly_exp = inp.monthly_expenses
        annual_exp_today = (monthly_exp * Decimal("12.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        monthly_inc = inp.monthly_income or Decimal("0.00")
        monthly_inv = inp.monthly_investment or Decimal("0.00")

        inf_rate = inp.expected_annual_inflation_pct / Decimal("100.0")
        nom_return = inp.expected_nominal_return_pct / Decimal("100.0")
        post_return = inp.post_retirement_return_pct / Decimal("100.0")
        swr = inp.withdrawal_rate_pct / Decimal("100.0")
        other_retire_inc = (inp.other_retirement_monthly_income or Decimal("0.00")) * Decimal("12.0")

        # Savings Rate Calculation
        savings_rate = 0.0
        if monthly_inc > Decimal("0.00"):
            # Savings = Income - Expenses or monthly_inv
            surplus = monthly_inc - monthly_exp
            savings_rate = float(round((surplus / monthly_inc) * Decimal("100.0"), 2))

        # Real Return Calculation (Fisher Equation: (1 + r)/(1 + i) - 1)
        if (Decimal("1.0") + inf_rate) > Decimal("0.0001"):
            real_return = ((Decimal("1.0") + nom_return) / (Decimal("1.0") + inf_rate)) - Decimal("1.0")
        else:
            real_return = nom_return - inf_rate
        real_return_pct = float(round(real_return * Decimal("100.0"), 2))

        # Regular FIRE Target in Today's Rupees
        net_annual_exp_today = max(Decimal("0.00"), annual_exp_today - other_retire_inc)
        if swr > Decimal("0.00"):
            fire_target_today = (net_annual_exp_today / swr).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            fire_target_today = (net_annual_exp_today * Decimal("25.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Future Target at Retirement Age (inflation-adjusted)
        inflation_factor = (Decimal("1.0") + inf_rate) ** Decimal(str(years_to_retire))
        fire_target_future = (fire_target_today * inflation_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Current Progress %
        fire_progress_pct = 0.0
        if fire_target_today > Decimal("0.00"):
            prog = (curr_assets / fire_target_today) * Decimal("100.0")
            fire_progress_pct = float(round(min(Decimal("1000.0"), prog), 2))

        # Project Current Portfolio to Retirement (Assets + Monthly Contributions)
        projected_at_retire = cls._project_portfolio_future(
            initial=curr_assets,
            monthly_contrib=monthly_inv,
            years=years_to_retire,
            annual_return=nom_return
        )

        surplus_or_shortfall = (projected_at_retire - fire_target_future).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Required Monthly SIP to bridge any gap
        required_monthly = cls._calculate_required_monthly_sip(
            target=fire_target_future,
            initial=curr_assets,
            years=years_to_retire,
            annual_return=nom_return
        )
        monthly_gap = (required_monthly - monthly_inv).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Projected FIRE Age at current contribution rate
        projected_fire_age = cls._estimate_fire_age(
            current_age=current_age,
            max_age=life_exp,
            initial_assets=curr_assets,
            monthly_contrib=monthly_inv,
            annual_exp_today=annual_exp_today,
            other_retire_income=other_retire_inc,
            swr=swr,
            inf_rate=inf_rate,
            annual_return=nom_return
        )

        # Strategy Summaries (Lean, Regular, Fat, Coast, Custom)
        strategies = cls._compute_strategies(
            inp=inp,
            years_to_retire=years_to_retire,
            curr_assets=curr_assets,
            monthly_inv=monthly_inv,
            annual_exp_today=annual_exp_today,
            other_retire_inc=other_retire_inc,
            swr=swr,
            inf_rate=inf_rate,
            nom_return=nom_return,
            inflation_factor=inflation_factor
        )

        # Multi-Scenario Year-by-Year Projections (Conservative, Base, Optimistic)
        projections = cls._generate_yearly_projections(
            inp=inp,
            years_to_retire=years_to_retire,
            curr_assets=curr_assets,
            monthly_inv=monthly_inv,
            net_annual_exp_today=net_annual_exp_today,
            fire_target_today=fire_target_today,
            inf_rate=inf_rate,
            nom_return=nom_return,
            post_return=post_return
        )

        disclaimers = [
            "Deterministic mathematical projection based on constant annualized assumptions. Real-world market returns are volatile and non-linear.",
            f"Safe Withdrawal Rate is set at {inp.withdrawal_rate_pct}%. Indian inflation dynamics (historical CPI ~5%-7%) recommend 3.0%-3.5% for 30+ year horizons compared to US Trinity Study (4%).",
            "Excludes primary residence real estate value to prevent double-counting illiquid shelter as income-generating assets.",
            "Post-retirement withdrawals assume annual inflation escalation and asset rebalancing between debt and equity.",
            "Taxes on capital gains (Section 112A LTCG / Section 50AA debt) and health inflation must be planned with appropriate buffers."
        ]

        return FireCalculationResponse(
            current_age=current_age,
            planned_retirement_age=retirement_age,
            years_to_retirement=years_to_retire,
            current_investable_assets=curr_assets,
            current_monthly_expenses=monthly_exp,
            current_monthly_income=monthly_inc,
            annual_expenses_today=annual_exp_today,
            savings_rate_pct=savings_rate,
            safe_withdrawal_rate_pct=float(inp.withdrawal_rate_pct),
            real_return_pct=real_return_pct,
            fire_target_today=fire_target_today,
            fire_target_future=fire_target_future,
            fire_progress_pct=fire_progress_pct,
            projected_fire_age=projected_fire_age,
            projected_portfolio_at_retirement=projected_at_retire,
            portfolio_surplus_or_shortfall=surplus_or_shortfall,
            required_monthly_investment=required_monthly,
            current_monthly_investment=monthly_inv,
            monthly_investment_gap=monthly_gap,
            strategies=strategies,
            yearly_projections=projections,
            disclaimers=disclaimers
        )

    @classmethod
    def _project_portfolio_future(
        cls,
        initial: Decimal,
        monthly_contrib: Decimal,
        years: int,
        annual_return: Decimal
    ) -> Decimal:
        """Projects portfolio value with compound returns and monthly contributions."""
        if years <= 0:
            return initial.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        months = years * 12
        monthly_rate = annual_return / Decimal("12.0")

        # Initial lump sum growth
        if monthly_rate == Decimal("0.00"):
            fv_initial = initial
            fv_contrib = monthly_contrib * Decimal(str(months))
        else:
            compound_factor = (Decimal("1.0") + monthly_rate) ** months
            fv_initial = initial * compound_factor
            # Annuity due formula (contributions made at start of each month)
            fv_contrib = monthly_contrib * ((compound_factor - Decimal("1.0")) / monthly_rate) * (Decimal("1.0") + monthly_rate)

        return (fv_initial + fv_contrib).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def _calculate_required_monthly_sip(
        cls,
        target: Decimal,
        initial: Decimal,
        years: int,
        annual_return: Decimal
    ) -> Decimal:
        """Calculates monthly contribution needed to reach target."""
        if years <= 0:
            return Decimal("0.00")

        months = years * 12
        monthly_rate = annual_return / Decimal("12.0")

        if monthly_rate == Decimal("0.00"):
            growth_initial = initial
            gap = max(Decimal("0.00"), target - growth_initial)
            return (gap / Decimal(str(months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        compound_factor = (Decimal("1.0") + monthly_rate) ** months
        grown_initial = initial * compound_factor
        gap = max(Decimal("0.00"), target - grown_initial)

        if gap == Decimal("0.00"):
            return Decimal("0.00")

        # PMT = Gap * r_m / [((1 + r_m)^n - 1) * (1 + r_m)]
        annuity_factor = (compound_factor - Decimal("1.0")) * (Decimal("1.0") + monthly_rate)
        required_pmt = (gap * monthly_rate) / annuity_factor
        return required_pmt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def _estimate_fire_age(
        cls,
        current_age: int,
        max_age: int,
        initial_assets: Decimal,
        monthly_contrib: Decimal,
        annual_exp_today: Decimal,
        other_retire_income: Decimal,
        swr: Decimal,
        inf_rate: Decimal,
        annual_return: Decimal
    ) -> Optional[int]:
        """Iterates year-by-year to estimate age at which portfolio >= target."""
        net_exp_today = max(Decimal("0.00"), annual_exp_today - other_retire_income)
        if swr <= Decimal("0.00"):
            swr = Decimal("0.035")
        target_today = net_exp_today / swr

        running_portfolio = initial_assets
        for t in range(1, (max_age - current_age) + 1):
            running_portfolio = cls._project_portfolio_future(
                initial=running_portfolio,
                monthly_contrib=monthly_contrib,
                years=1,
                annual_return=annual_return
            )
            # Inflation-adjusted target at year t
            target_t = target_today * ((Decimal("1.0") + inf_rate) ** Decimal(str(t)))
            if running_portfolio >= target_t:
                return current_age + t
        return None

    @classmethod
    def _compute_strategies(
        cls,
        inp: FireCalculationInput,
        years_to_retire: int,
        curr_assets: Decimal,
        monthly_inv: Decimal,
        annual_exp_today: Decimal,
        other_retire_inc: Decimal,
        swr: Decimal,
        inf_rate: Decimal,
        nom_return: Decimal,
        inflation_factor: Decimal
    ) -> List[FireStrategySummary]:
        strategies: List[FireStrategySummary] = []

        # 1. Lean FIRE (Essential expenses only, e.g. 70%)
        lean_ratio = inp.essential_expenses_pct / Decimal("100.0")
        lean_monthly_exp = inp.monthly_expenses * lean_ratio
        lean_annual_exp = lean_monthly_exp * Decimal("12.0")
        lean_net_annual = max(Decimal("0.00"), lean_annual_exp - other_retire_inc)
        lean_target_today = (lean_net_annual / swr).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        lean_target_future = (lean_target_today * inflation_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        lean_req_sip = cls._calculate_required_monthly_sip(lean_target_future, curr_assets, years_to_retire, nom_return)
        lean_proj = cls._project_portfolio_future(curr_assets, monthly_inv, years_to_retire, nom_return)
        lean_age = cls._estimate_fire_age(
            inp.current_age, inp.life_expectancy_age, curr_assets, monthly_inv,
            lean_annual_exp, other_retire_inc, swr, inf_rate, nom_return
        )

        strategies.append(FireStrategySummary(
            strategy_type="lean",
            name="Lean FIRE",
            description="Minimalist retirement covering only essential needs (groceries, housing, healthcare, basic utilities).",
            monthly_expense_in_retirement=lean_monthly_exp.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            target_corpus_today=lean_target_today,
            target_corpus_at_retirement=lean_target_future,
            projected_fire_age=lean_age,
            years_to_fire=(lean_age - inp.current_age) if lean_age else None,
            required_monthly_investment=lean_req_sip,
            is_achievable_by_target_age=lean_proj >= lean_target_future,
            shortfall_or_surplus_at_retirement=(lean_proj - lean_target_future).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            assumptions_and_limitations=f"Based on {inp.essential_expenses_pct}% of current spending. Leaves zero cushion for luxury travel, high discretionary costs, or family emergencies."
        ))

        # 2. Regular FIRE (100% current spending)
        reg_monthly_exp = inp.monthly_expenses
        reg_net_annual = max(Decimal("0.00"), annual_exp_today - other_retire_inc)
        reg_target_today = (reg_net_annual / swr).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        reg_target_future = (reg_target_today * inflation_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        reg_req_sip = cls._calculate_required_monthly_sip(reg_target_future, curr_assets, years_to_retire, nom_return)
        reg_proj = cls._project_portfolio_future(curr_assets, monthly_inv, years_to_retire, nom_return)
        reg_age = cls._estimate_fire_age(
            inp.current_age, inp.life_expectancy_age, curr_assets, monthly_inv,
            annual_exp_today, other_retire_inc, swr, inf_rate, nom_return
        )

        strategies.append(FireStrategySummary(
            strategy_type="regular",
            name="Regular FIRE",
            description="Maintains your current middle-class lifestyle and spending power completely into retirement.",
            monthly_expense_in_retirement=reg_monthly_exp.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            target_corpus_today=reg_target_today,
            target_corpus_at_retirement=reg_target_future,
            projected_fire_age=reg_age,
            years_to_fire=(reg_age - inp.current_age) if reg_age else None,
            required_monthly_investment=reg_req_sip,
            is_achievable_by_target_age=reg_proj >= reg_target_future,
            shortfall_or_surplus_at_retirement=(reg_proj - reg_target_future).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            assumptions_and_limitations="Assumes living expenses remain consistent in real terms. Does not account for sudden changes in family size or healthcare shocks without insurance."
        ))

        # 3. Fat FIRE (135% of current spending)
        fat_monthly_exp = (inp.monthly_expenses * Decimal("1.35")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fat_annual_exp = fat_monthly_exp * Decimal("12.0")
        fat_net_annual = max(Decimal("0.00"), fat_annual_exp - other_retire_inc)
        fat_target_today = (fat_net_annual / swr).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fat_target_future = (fat_target_today * inflation_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fat_req_sip = cls._calculate_required_monthly_sip(fat_target_future, curr_assets, years_to_retire, nom_return)
        fat_proj = cls._project_portfolio_future(curr_assets, monthly_inv, years_to_retire, nom_return)
        fat_age = cls._estimate_fire_age(
            inp.current_age, inp.life_expectancy_age, curr_assets, monthly_inv,
            fat_annual_exp, other_retire_inc, swr, inf_rate, nom_return
        )

        strategies.append(FireStrategySummary(
            strategy_type="fat",
            name="Fat FIRE",
            description="Upgraded luxury retirement with higher discretionary allocation for frequent travel, hobbies, and premium healthcare.",
            monthly_expense_in_retirement=fat_monthly_exp,
            target_corpus_today=fat_target_today,
            target_corpus_at_retirement=fat_target_future,
            projected_fire_age=fat_age,
            years_to_fire=(fat_age - inp.current_age) if fat_age else None,
            required_monthly_investment=fat_req_sip,
            is_achievable_by_target_age=fat_proj >= fat_target_future,
            shortfall_or_surplus_at_retirement=(fat_proj - fat_target_future).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            assumptions_and_limitations="Assumes 35% higher real lifestyle expenditure. Requires aggressive savings rate or longer accumulation phase."
        ))

        # 4. Coast FIRE
        # Portfolio today that, with zero future contributions, will compound to Regular FIRE target at retirement age.
        # Coast Target Today = Target Future / (1 + r)^N
        growth_discount = (Decimal("1.0") + nom_return) ** Decimal(str(years_to_retire))
        if growth_discount > Decimal("0.00"):
            coast_target_today = (reg_target_future / growth_discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            coast_target_today = reg_target_future

        is_coast_achieved = curr_assets >= coast_target_today
        coast_surplus = (curr_assets - coast_target_today).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        strategies.append(FireStrategySummary(
            strategy_type="coast",
            name="Coast FIRE",
            description="You already have enough invested today such that compound interest alone will hit your Regular FIRE target by your planned retirement age with ZERO further savings.",
            monthly_expense_in_retirement=reg_monthly_exp,
            target_corpus_today=coast_target_today,
            target_corpus_at_retirement=reg_target_future,
            projected_fire_age=inp.retirement_age if is_coast_achieved else None,
            years_to_fire=float(years_to_retire) if is_coast_achieved else None,
            required_monthly_investment=Decimal("0.00") if is_coast_achieved else reg_req_sip,
            is_achievable_by_target_age=is_coast_achieved,
            shortfall_or_surplus_at_retirement=coast_surplus,
            assumptions_and_limitations=(
                f"Requires {inp.expected_nominal_return_pct}% constant compounding on existing assets. "
                "Once reached, you only need to earn enough to cover current day-to-day living expenses."
            )
        ))

        return strategies

    @classmethod
    def _generate_yearly_projections(
        cls,
        inp: FireCalculationInput,
        years_to_retire: int,
        curr_assets: Decimal,
        monthly_inv: Decimal,
        net_annual_exp_today: Decimal,
        fire_target_today: Decimal,
        inf_rate: Decimal,
        nom_return: Decimal,
        post_return: Decimal
    ) -> List[FireProjectionPoint]:
        projections: List[FireProjectionPoint] = []

        # Scenario return tracks
        # Base: nom_return / post_return
        # Conservative: nom_return - 2.5%, post_return - 1.5%, inf + 1.0%
        # Optimistic: nom_return + 2.0%, post_return + 1.5%, inf - 0.5%
        r_base_pre = nom_return
        r_base_post = post_return
        i_base = inf_rate

        r_cons_pre = max(Decimal("0.03"), nom_return - Decimal("0.025"))
        r_cons_post = max(Decimal("0.03"), post_return - Decimal("0.015"))
        i_cons = inf_rate + Decimal("0.010")

        r_opt_pre = nom_return + Decimal("0.020")
        r_opt_post = post_return + Decimal("0.015")
        i_opt = max(Decimal("0.02"), inf_rate - Decimal("0.005"))

        bal_base = curr_assets
        bal_cons = curr_assets
        bal_opt = curr_assets

        total_years = max(1, inp.life_expectancy_age - inp.current_age)
        annual_inv = monthly_inv * Decimal("12.0")

        for t in range(total_years + 1):
            age = inp.current_age + t
            year = 2026 + t
            is_retired = age >= inp.retirement_age

            target_curve = (fire_target_today * ((Decimal("1.0") + i_base) ** Decimal(str(t)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            annual_contrib = Decimal("0.00") if is_retired else annual_inv
            annual_withdraw = Decimal("0.00")
            if is_retired:
                retire_year_idx = age - inp.retirement_age
                # Escalating withdrawal for inflation
                annual_withdraw = (net_annual_exp_today * ((Decimal("1.0") + i_base) ** Decimal(str(t)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            projections.append(FireProjectionPoint(
                age=age,
                year=year,
                portfolio_conservative=bal_cons.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                portfolio_base=bal_base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                portfolio_optimistic=bal_opt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                annual_contribution=annual_contrib,
                annual_withdrawal=annual_withdraw,
                fire_target_curve=target_curve,
                is_retired=is_retired
            ))

            # Advance 1 year for next step
            if not is_retired:
                bal_base = (bal_base * (Decimal("1.0") + r_base_pre)) + annual_contrib
                bal_cons = (bal_cons * (Decimal("1.0") + r_cons_pre)) + annual_contrib
                bal_opt = (bal_opt * (Decimal("1.0") + r_opt_pre)) + annual_contrib
            else:
                withdraw_base = net_annual_exp_today * ((Decimal("1.0") + i_base) ** Decimal(str(t)))
                withdraw_cons = net_annual_exp_today * ((Decimal("1.0") + i_cons) ** Decimal(str(t)))
                withdraw_opt = net_annual_exp_today * ((Decimal("1.0") + i_opt) ** Decimal(str(t)))

                bal_base = max(Decimal("0.00"), (bal_base * (Decimal("1.0") + r_base_post)) - withdraw_base)
                bal_cons = max(Decimal("0.00"), (bal_cons * (Decimal("1.0") + r_cons_post)) - withdraw_cons)
                bal_opt = max(Decimal("0.00"), (bal_opt * (Decimal("1.0") + r_opt_post)) - withdraw_opt)

        return projections
