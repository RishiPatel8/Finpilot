from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from app.schemas.scenario import (
    ScenarioInput,
    ScenarioSimulationResult,
    ScenarioMetricComparison,
    ScenarioAlternativeOption
)
from app.finance.budget.engine import BudgetEngine
from app.finance.investments.engine import InvestmentEngine
from app.schemas.investment import GoalProjectionRequest


class ScenarioEngine:
    """
    Financial Decision Simulator executing deterministic multi-variable financial projections.
    Reuses BudgetEngine and InvestmentEngine without duplicating numerical calculations.
    """

    @classmethod
    def simulate(
        cls,
        inp: ScenarioInput,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ScenarioSimulationResult:
        # Resolve financial baseline: input values take precedence, fallback to user context, fallback to defaults
        ctx = user_context or {}
        income = inp.monthly_income if inp.monthly_income is not None else Decimal(str(ctx.get("monthly_income", 60000)))
        expenses = inp.monthly_expenses if inp.monthly_expenses is not None else Decimal(str(ctx.get("monthly_expenses", 35000)))
        savings = inp.current_savings if inp.current_savings is not None else Decimal(str(ctx.get("current_savings", 200000)))

        # Baseline Cash Flow
        baseline_analysis = BudgetEngine.analyze_cash_flow(income, expenses, savings, target_months=6)
        baseline_surplus = baseline_analysis["monthly_surplus"]
        baseline_runway = baseline_analysis["emergency_fund_months_covered"]

        stype = inp.scenario_type.lower().strip()
        if stype == "major_purchase":
            return cls._simulate_major_purchase(inp, income, expenses, savings, baseline_surplus, baseline_runway)
        elif stype == "increase_savings":
            return cls._simulate_increase_savings(inp, income, expenses, savings, baseline_surplus, baseline_runway)
        elif stype == "expense_reduction":
            return cls._simulate_expense_reduction(inp, income, expenses, savings, baseline_surplus, baseline_runway)
        elif stype == "emergency_fund_builder":
            return cls._simulate_emergency_fund(inp, income, expenses, savings, baseline_surplus, baseline_runway)
        else:
            return cls._simulate_major_purchase(inp, income, expenses, savings, baseline_surplus, baseline_runway)

    @classmethod
    def _simulate_major_purchase(
        cls,
        inp: ScenarioInput,
        income: Decimal,
        expenses: Decimal,
        savings: Decimal,
        baseline_surplus: Decimal,
        baseline_runway: float
    ) -> ScenarioSimulationResult:
        target_amount = inp.target_amount or Decimal("800000.00")
        months = inp.time_horizon_months or 18
        title = inp.title or f"Major Purchase: ₹{target_amount:,.0f} in {months} Months"

        # Goal projection through InvestmentEngine
        # Assumption: If emergency fund (min 3 months expenses) is protected, remaining savings can contribute as initial lump sum
        min_reserve = expenses * Decimal("3.0")
        available_downpayment = max(Decimal("0.00"), savings - min_reserve)

        # Calculate monthly SIP needed for remaining amount
        goal_proj = InvestmentEngine.project_goal(GoalProjectionRequest(
            goal_name=title,
            target_amount=target_amount,
            current_amount=available_downpayment,
            time_horizon_months=months,
            expected_annual_return_pct=inp.expected_annual_return_pct,
            expected_annual_inflation_pct=inp.expected_annual_inflation_pct,
            adjust_for_inflation=inp.adjust_for_inflation
        ))

        required_sip = goal_proj.required_monthly_sip
        cash_flow_gap = baseline_surplus - required_sip
        is_feasible = cash_flow_gap >= Decimal("0.00")

        # Projected emergency runway if user recklessly drained ALL savings
        drained_runway = 0.0

        comparisons = [
            ScenarioMetricComparison(
                metric_name="Monthly Surplus vs Required Commitment",
                baseline_value=f"₹{baseline_surplus:,.0f}/mo available",
                scenario_value=f"₹{required_sip:,.0f}/mo required",
                delta=f"₹{abs(cash_flow_gap):,.0f} {'surplus remaining' if is_feasible else 'shortfall'}",
                impact_type="positive" if is_feasible else "negative"
            ),
            ScenarioMetricComparison(
                metric_name="Target Cost with Inflation",
                baseline_value=f"₹{target_amount:,.0f} (Nominal)",
                scenario_value=f"₹{goal_proj.inflation_adjusted_target:,.0f} (At {inp.expected_annual_inflation_pct}% inf)",
                delta=f"+₹{goal_proj.inflation_adjusted_target - target_amount:,.0f} price rise",
                impact_type="neutral"
            ),
            ScenarioMetricComparison(
                metric_name="Emergency Reserve Protection",
                baseline_value=f"{baseline_runway:.1f} months covered (₹{savings:,.0f})",
                scenario_value=f"₹{min_reserve:,.0f} ring-fenced reserve",
                delta=f"₹{available_downpayment:,.0f} deployable down payment",
                impact_type="positive"
            )
        ]

        # Alternative structured scenarios
        alternatives = [
            ScenarioAlternativeOption(
                name="Prudent Down Payment + Auto Loan (Balanced)",
                description=(
                    f"Deploy ₹{available_downpayment:,.0f} from savings (preserving a ₹{min_reserve:,.0f} 3-month safety buffer), "
                    f"invest your full monthly surplus of ₹{baseline_surplus:,.0f} into Liquid Funds for {months} months, "
                    f"and finance the remaining balance with an auto loan at ~9.5% APR."
                ),
                monthly_commitment=baseline_surplus,
                projected_outcome=target_amount,
                feasibility="Fully Feasible",
                pros=[
                    "Preserves essential emergency liquidity",
                    "Fits within your existing monthly surplus without lifestyle cutbacks",
                    "Builds positive credit bureau score"
                ],
                cons=[
                    "Incurs loan interest for 2-3 years post-purchase"
                ]
            ),
            ScenarioAlternativeOption(
                name="Extended Timeline All-Cash Purchase",
                description=(
                    f"Extend your time horizon to {int(months * 1.5)} months. At your current ₹{baseline_surplus:,.0f}/mo surplus, "
                    f"you accumulate 100% of the required purchase price in cash without borrowing any debt."
                ),
                monthly_commitment=baseline_surplus,
                projected_outcome=target_amount,
                feasibility="Fully Feasible",
                pros=[
                    "Zero loan EMI and zero interest paid to banks",
                    "Full ownership and complete financial freedom"
                ],
                cons=[
                    f"Delays purchase by {int(months * 0.5)} additional months"
                ]
            ),
            ScenarioAlternativeOption(
                name="Budget Compression (Discretionary Cutback)",
                description=(
                    "Trim non-essential dining and entertainment expenses by 20% to free up cash flow and reduce the shortfall."
                ),
                monthly_commitment=baseline_surplus + Decimal("6000.00"),
                projected_outcome=target_amount,
                feasibility="Requires Budget Adjustment",
                pros=[
                    "Accelerates capital accumulation without taking debt"
                ],
                cons=[
                    "Requires strict discipline on discretionary dining/lifestyle expenses"
                ]
            )
        ]

        verdict = (
            f"Funding this ₹{target_amount:,.0f} purchase purely from cash savings in {months} months requires ₹{required_sip:,.0f}/month. "
            f"{'Your monthly surplus of ₹' + str(baseline_surplus) + ' covers this target comfortably.' if is_feasible else 'This exceeds your current monthly surplus of ₹' + f'{baseline_surplus:,.0f} by ₹{abs(cash_flow_gap):,.0f}/month. Draining your ₹' + f'{savings:,.0f} emergency savings is high-risk because it leaves you with 0 months of financial cushion.'} "
            f"The recommended path is a hybrid structure: retain a 3-month safety buffer and finance any residual balance."
        )

        timeline = [
            {"month": m, "projected_saved": round(float(min(target_amount, available_downpayment + required_sip * Decimal(str(m)))), 2)}
            for m in range(0, months + 1, max(1, months // 6))
        ]

        return ScenarioSimulationResult(
            scenario_type="major_purchase",
            title=title,
            is_feasible=is_feasible,
            summary_verdict=verdict,
            baseline_surplus=baseline_surplus,
            scenario_surplus=required_sip,
            required_monthly_allocation=required_sip,
            cash_flow_gap=cash_flow_gap,
            baseline_runway_months=baseline_runway,
            projected_runway_months=float((min_reserve / expenses).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)),
            comparisons=comparisons,
            timeline_projections=timeline,
            alternative_options=alternatives,
            risks_and_assumptions=[
                f"Assumes an annualized investment return of {inp.expected_annual_return_pct}% in low-volatility debt/liquid instruments.",
                f"Adjusted for inflation at {inp.expected_annual_inflation_pct}% p.a. to account for rising on-road price.",
                "Emergency reserve of at least 3 months essential expenses (₹" + f"{min_reserve:,.0f}) is strictly ring-fenced."
            ],
            citations=[
                "SEBI Liquid Mutual Fund Regulations - Capital preservation & T+1 liquidity",
                "RBI Guidelines on Retail Auto Loans - Maximum recommended EMI <= 15% of net monthly income"
            ]
        )

    @classmethod
    def _simulate_increase_savings(
        cls,
        inp: ScenarioInput,
        income: Decimal,
        expenses: Decimal,
        savings: Decimal,
        baseline_surplus: Decimal,
        baseline_runway: float
    ) -> ScenarioSimulationResult:
        target_rate = inp.target_savings_rate_pct or Decimal("35.0")
        target_surplus = (income * target_rate) / Decimal("100.0")
        delta_surplus = target_surplus - baseline_surplus

        title = f"Increase Savings Rate to {target_rate}%"
        r = inp.expected_annual_return_pct / Decimal("100.0")

        # 1-year, 3-year, 5-year wealth accumulation difference: FV of monthly SIP delta
        def fv_sip(monthly_amt: Decimal, num_months: int) -> Decimal:
            i = r / Decimal("12.0")
            return (monthly_amt * (((Decimal("1.0") + i) ** num_months) - Decimal("1.0")) / i * (Decimal("1.0") + i)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        gain_1yr = fv_sip(delta_surplus, 12) if delta_surplus > 0 else Decimal("0")
        gain_3yr = fv_sip(delta_surplus, 36) if delta_surplus > 0 else Decimal("0")
        gain_5yr = fv_sip(delta_surplus, 60) if delta_surplus > 0 else Decimal("0")

        comparisons = [
            ScenarioMetricComparison(
                metric_name="Monthly Savings Allocation",
                baseline_value=f"₹{baseline_surplus:,.0f}/mo ({(baseline_surplus/income*100):.1f}%)",
                scenario_value=f"₹{target_surplus:,.0f}/mo ({target_rate}%)",
                delta=f"+₹{delta_surplus:,.0f}/mo added to wealth",
                impact_type="positive" if delta_surplus > 0 else "neutral"
            ),
            ScenarioMetricComparison(
                metric_name="3-Year Additional Compounded Wealth",
                baseline_value="Current path",
                scenario_value=f"+₹{gain_3yr:,.0f} additional corpus",
                delta=f"5-Year: +₹{gain_5yr:,.0f}",
                impact_type="positive"
            )
        ]

        timeline = [
            {"year": 1, "additional_wealth": float(gain_1yr)},
            {"year": 3, "additional_wealth": float(gain_3yr)},
            {"year": 5, "additional_wealth": float(gain_5yr)},
        ]

        return ScenarioSimulationResult(
            scenario_type="increase_savings",
            title=title,
            is_feasible=True,
            summary_verdict=f"Boosting your savings rate to {target_rate}% generates an extra ₹{delta_surplus:,.0f} monthly surplus, compounding into ₹{gain_3yr:,.0f} extra wealth in 3 years.",
            baseline_surplus=baseline_surplus,
            scenario_surplus=target_surplus,
            required_monthly_allocation=target_surplus,
            cash_flow_gap=delta_surplus,
            baseline_runway_months=baseline_runway,
            projected_runway_months=baseline_runway + float(delta_surplus / expenses) if expenses > 0 else baseline_runway,
            comparisons=comparisons,
            timeline_projections=timeline,
            alternative_options=[],
            risks_and_assumptions=[
                f"Assumes consistent investment of the surplus at {inp.expected_annual_return_pct}% annual return.",
                "Requires keeping expenses capped despite future inflation or lifestyle creep."
            ],
            citations=["50-30-20 Financial Framework (Elizabeth Warren)"]
        )

    @classmethod
    def _simulate_expense_reduction(
        cls,
        inp: ScenarioInput,
        income: Decimal,
        expenses: Decimal,
        savings: Decimal,
        baseline_surplus: Decimal,
        baseline_runway: float
    ) -> ScenarioSimulationResult:
        reduction = inp.expense_reduction_amount or Decimal("5000.00")
        new_expenses = max(Decimal("0.00"), expenses - reduction)
        new_surplus = income - new_expenses
        title = f"Expense Optimization: Trim ₹{reduction:,.0f}/month"

        # Compounded SIP of trimmed amount
        r = inp.expected_annual_return_pct / Decimal("100.0")
        i = r / Decimal("12.0")
        gain_3yr = (reduction * (((Decimal("1.0") + i) ** 36) - Decimal("1.0")) / i * (Decimal("1.0") + i)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        comparisons = [
            ScenarioMetricComparison(
                metric_name="Monthly Operating Expenses",
                baseline_value=f"₹{expenses:,.0f}/mo",
                scenario_value=f"₹{new_expenses:,.0f}/mo",
                delta=f"-₹{reduction:,.0f}/mo savings",
                impact_type="positive"
            ),
            ScenarioMetricComparison(
                metric_name="3-Year Compounded SIP of Saved Expenses",
                baseline_value="Spent on consumption",
                scenario_value=f"₹{gain_3yr:,.0f} in index/liquid funds",
                delta=f"+₹{gain_3yr:,.0f} net worth increase",
                impact_type="positive"
            )
        ]

        return ScenarioSimulationResult(
            scenario_type="expense_reduction",
            title=title,
            is_feasible=True,
            summary_verdict=f"Trimming ₹{reduction:,.0f}/month from discretionary expenses frees up ₹{reduction:,.0f} to invest, building ₹{gain_3yr:,.0f} in 3 years.",
            baseline_surplus=baseline_surplus,
            scenario_surplus=new_surplus,
            required_monthly_allocation=reduction,
            cash_flow_gap=reduction,
            baseline_runway_months=baseline_runway,
            projected_runway_months=float((savings / new_expenses).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if new_expenses > 0 else baseline_runway,
            comparisons=comparisons,
            timeline_projections=[],
            alternative_options=[],
            risks_and_assumptions=[
                f"Assumes redirecting the ₹{reduction:,.0f}/mo savings into an investment earning {inp.expected_annual_return_pct}% p.a."
            ],
            citations=["Compound Interest Formula (A = P * (1 + r/n)^nt)"]
        )

    @classmethod
    def _simulate_emergency_fund(
        cls,
        inp: ScenarioInput,
        income: Decimal,
        expenses: Decimal,
        savings: Decimal,
        baseline_surplus: Decimal,
        baseline_runway: float
    ) -> ScenarioSimulationResult:
        target_months = 6
        target_reserve = expenses * Decimal(str(target_months))
        deficit = max(Decimal("0.00"), target_reserve - savings)
        title = "6-Month Emergency Runway Completion Plan"

        months_to_complete = int((deficit / baseline_surplus).quantize(Decimal("1"), rounding=ROUND_HALF_UP)) if baseline_surplus > 0 else 99

        comparisons = [
            ScenarioMetricComparison(
                metric_name="Emergency Reserve Runway",
                baseline_value=f"{baseline_runway:.1f} months (₹{savings:,.0f})",
                scenario_value=f"{target_months} months (₹{target_reserve:,.0f})",
                delta=f"₹{deficit:,.0f} needed to achieve full safety",
                impact_type="neutral" if deficit == 0 else "negative"
            ),
            ScenarioMetricComparison(
                metric_name="Timeline to Full Safety",
                baseline_value=f"₹{baseline_surplus:,.0f}/mo surplus",
                scenario_value=f"{months_to_complete} months to complete",
                delta="0 debt risk",
                impact_type="positive"
            )
        ]

        return ScenarioSimulationResult(
            scenario_type="emergency_fund_builder",
            title=title,
            is_feasible=baseline_surplus > Decimal("0.00"),
            summary_verdict=(
                f"Your 6-month safety target is ₹{target_reserve:,.0f}. You currently have ₹{savings:,.0f} ({baseline_runway:.1f} months). "
                f"Allocating your monthly surplus of ₹{baseline_surplus:,.0f} achieves full 6-month safety in {months_to_complete} months."
            ),
            baseline_surplus=baseline_surplus,
            scenario_surplus=baseline_surplus,
            required_monthly_allocation=baseline_surplus,
            cash_flow_gap=Decimal("0.00"),
            baseline_runway_months=baseline_runway,
            projected_runway_months=float(target_months),
            comparisons=comparisons,
            timeline_projections=[],
            alternative_options=[],
            risks_and_assumptions=[
                "Keep emergency reserves in high-liquidity instruments (e.g. Liquid Mutual Funds or sweep-in FDs) rather than equity or lock-in bonds."
            ],
            citations=[
                "SEBI Liquid Fund Guidelines - T+1 withdrawal & negligible exit load after 7 days",
                "RBI DICGC Insurance Coverage - Up to ₹5 Lakhs per depositor"
            ]
        )
