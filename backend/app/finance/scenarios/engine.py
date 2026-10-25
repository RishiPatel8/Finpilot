from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from app.schemas.scenario import (
    ScenarioInput,
    ScenarioSimulationResult,
    ScenarioMetricComparison,
    ScenarioAlternativeOption,
    LoanAnalysis,
    SavingsImpact,
    CashFlowImpact,
    GoalTimeline,
    StressTestResult
)
from app.finance.budget.engine import BudgetEngine
from app.finance.investments.engine import InvestmentEngine
from app.schemas.investment import GoalProjectionRequest


class ScenarioEngine:
    """
    Financial Decision Simulator executing deterministic multi-variable financial projections.
    Uses real user baseline records without mock data, supporting 10 distinct decision types,
    exact amortization mathematics, cash-flow impact, savings impact, 3-way option comparisons,
    stress testing, and transparent rule-based recommendations.
    """

    DECISION_TYPES = {
        "vehicle", "house", "personal_loan", "expensive_product", "major_trip",
        "business", "investment_increase", "financial_goal", "cash_vs_loan", "custom"
    }

    @classmethod
    def calculate_emi(cls, principal: Decimal, annual_rate_pct: Decimal, tenure_months: int) -> Decimal:
        """Standard amortization EMI calculation with zero-interest fallback."""
        if principal <= Decimal("0") or tenure_months <= 0:
            return Decimal("0.00")
        if annual_rate_pct <= Decimal("0"):
            return (principal / Decimal(str(tenure_months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        r_monthly = (annual_rate_pct / Decimal("100.0")) / Decimal("12.0")
        one_plus_r_n = (Decimal("1.0") + r_monthly) ** tenure_months
        emi = principal * (r_monthly * one_plus_r_n) / (one_plus_r_n - Decimal("1.0"))
        return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def simulate(
        cls,
        inp: ScenarioInput,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ScenarioSimulationResult:
        ctx = user_context or {}
        # Resolve baseline: explicit input overrides -> user context records -> fallback 0
        income = inp.monthly_income if inp.monthly_income is not None else Decimal(str(ctx.get("monthly_income", 0)))
        expenses = inp.monthly_expenses if inp.monthly_expenses is not None else Decimal(str(ctx.get("monthly_expenses", 0)))
        savings = inp.current_savings if inp.current_savings is not None else Decimal(str(ctx.get("current_savings", 0)))
        existing_emi = inp.existing_monthly_emi if inp.existing_monthly_emi is not None else Decimal(str(ctx.get("monthly_emi", 0)))
        existing_rec = inp.existing_recurring_commitments if inp.existing_recurring_commitments is not None else Decimal(str(ctx.get("recurring_monthly_expenses", 0)))
        target_months = Decimal(str(inp.emergency_fund_target_months or 6.0))

        stype = inp.scenario_type.lower().strip()

        # Handle legacy / specific budget scenarios
        if stype == "increase_savings":
            return cls._simulate_increase_savings(inp, income, expenses, savings)
        elif stype == "expense_reduction":
            return cls._simulate_expense_reduction(inp, income, expenses, savings)
        elif stype == "emergency_fund_builder":
            return cls._simulate_emergency_fund(inp, income, expenses, savings)
        elif stype == "major_purchase":
            return cls._simulate_major_purchase_legacy(inp, income, expenses, savings)
        else:
            return cls._simulate_decision(inp, income, expenses, savings, existing_emi, existing_rec, target_months)

    @classmethod
    def _simulate_decision(
        cls,
        inp: ScenarioInput,
        income: Decimal,
        expenses: Decimal,
        savings: Decimal,
        existing_emi: Decimal,
        existing_rec: Decimal,
        target_months: Decimal
    ) -> ScenarioSimulationResult:
        stype = inp.scenario_type.lower().strip()

        # Baseline Cash Flow Calculation
        existing_obligations = existing_emi + existing_rec
        baseline_surplus = income - expenses - existing_obligations
        emergency_target = expenses * target_months
        baseline_runway = float((savings / expenses).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if expenses > Decimal("0") else 0.0

        # Title & Scenario Defaults
        titles_map = {
            "vehicle": "Vehicle Purchase (Car / Bike)",
            "house": "Home Purchase & Down Payment",
            "personal_loan": "Personal Loan Commitment",
            "expensive_product": "High-Value Product Purchase",
            "major_trip": "Major Vacation / Travel Plan",
            "business": "New Business / Expansion",
            "investment_increase": "Increase Monthly Investment",
            "financial_goal": "Financial Savings Milestone",
            "cash_vs_loan": "Cash vs. Loan Comparison",
            "custom": "Custom Financial Decision"
        }
        title = inp.title or titles_map.get(stype, "Financial Decision Simulation")

        # Determine Purchase / Target amount
        purchase_price = inp.purchase_price or inp.target_amount or Decimal("0")
        is_investment = stype in ["investment_increase", "financial_goal"]
        is_business = stype == "business"

        # Defaults by Decision Type
        if stype == "vehicle":
            rate = inp.loan_interest_rate_pct if inp.loan_interest_rate_pct is not None else Decimal("9.5")
            tenure = inp.loan_tenure_months or 60
            down_payment = inp.down_payment if inp.down_payment is not None else (purchase_price * Decimal("0.20"))
            monthly_ongoing = inp.monthly_ongoing_costs or Decimal("4000")  # fuel, insurance, maintenance
            upfront_costs = inp.upfront_one_time_costs or Decimal("25000")   # registration, accessories
        elif stype == "house":
            rate = inp.loan_interest_rate_pct if inp.loan_interest_rate_pct is not None else Decimal("8.5")
            tenure = inp.loan_tenure_months or 240
            down_payment = inp.down_payment if inp.down_payment is not None else (purchase_price * Decimal("0.20"))
            monthly_ongoing = inp.monthly_ongoing_costs or Decimal("3500")  # society maintenance, property tax
            upfront_costs = inp.upfront_one_time_costs or (purchase_price * Decimal("0.07"))  # stamp duty & registration
        elif stype == "personal_loan":
            rate = inp.loan_interest_rate_pct if inp.loan_interest_rate_pct is not None else Decimal("12.5")
            tenure = inp.loan_tenure_months or 36
            down_payment = Decimal("0")
            monthly_ongoing = Decimal("0")
            upfront_costs = Decimal("0")
        elif stype == "expensive_product":
            rate = inp.loan_interest_rate_pct if inp.loan_interest_rate_pct is not None else Decimal("0.0")  # default No-Cost EMI
            tenure = inp.loan_tenure_months or 12
            down_payment = inp.down_payment or Decimal("0")
            monthly_ongoing = inp.monthly_ongoing_costs or Decimal("0")
            upfront_costs = inp.upfront_one_time_costs or Decimal("0")
        elif stype == "major_trip":
            rate = inp.loan_interest_rate_pct or Decimal("0.0")
            tenure = inp.loan_tenure_months or inp.time_horizon_months or 6
            down_payment = inp.down_payment or purchase_price
            monthly_ongoing = Decimal("0")
            upfront_costs = Decimal("0")
        elif stype == "business":
            rate = inp.loan_interest_rate_pct or Decimal("11.0")
            tenure = inp.loan_tenure_months or 36
            down_payment = inp.down_payment or purchase_price
            monthly_ongoing = inp.monthly_ongoing_costs or Decimal("15000")  # operating burn
            upfront_costs = inp.upfront_one_time_costs or Decimal("0")
        elif stype == "cash_vs_loan":
            rate = inp.loan_interest_rate_pct if inp.loan_interest_rate_pct is not None else Decimal("10.0")
            tenure = inp.loan_tenure_months or 36
            down_payment = inp.down_payment or (purchase_price * Decimal("0.20"))
            monthly_ongoing = inp.monthly_ongoing_costs or Decimal("0")
            upfront_costs = inp.upfront_one_time_costs or Decimal("0")
        else:
            rate = inp.loan_interest_rate_pct or Decimal("9.0")
            tenure = inp.loan_tenure_months or inp.time_horizon_months or 24
            down_payment = inp.down_payment or Decimal("0")
            monthly_ongoing = inp.monthly_ongoing_costs or Decimal("0")
            upfront_costs = inp.upfront_one_time_costs or Decimal("0")

        revenue_gain = inp.monthly_revenue_gain or Decimal("0")

        # Loan Amortization Calculation
        principal_borrowed = max(Decimal("0"), purchase_price - down_payment) if not is_investment else Decimal("0")
        fee_pct = inp.loan_processing_fee_pct or Decimal("1.0")
        processing_fee = (principal_borrowed * fee_pct / Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if principal_borrowed > Decimal("0") and tenure > 0:
            emi = cls.calculate_emi(principal_borrowed, rate, tenure)
            total_repaid = (emi * Decimal(str(tenure))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_interest = max(Decimal("0.00"), total_repaid - principal_borrowed)
        else:
            emi = Decimal("0.00")
            total_repaid = Decimal("0.00")
            total_interest = Decimal("0.00")

        # For pure savings / investment / goal scenarios: monthly payment is the required investment SIP
        if is_investment or (stype == "major_trip" and principal_borrowed == Decimal("0")):
            horizon = inp.time_horizon_months or tenure or 12
            needed_capital = max(Decimal("0"), purchase_price - down_payment)
            if horizon > 0:
                # Target SIP
                r_inv = (inp.expected_annual_return_pct / Decimal("100.0")) / Decimal("12.0")
                if r_inv > Decimal("0"):
                    growth_factor = ((Decimal("1.0") + r_inv) ** horizon - Decimal("1.0")) / r_inv
                    new_monthly_payment = (needed_capital / growth_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    new_monthly_payment = (needed_capital / Decimal(str(horizon))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                new_monthly_payment = Decimal("0.00")
        else:
            new_monthly_payment = emi

        # Avoid double-counting if user checked "existing_loan_in_budget"
        effective_new_payment = Decimal("0.00") if inp.existing_loan_in_budget else new_monthly_payment
        total_incremental_monthly = effective_new_payment + monthly_ongoing - revenue_gain

        # Cash Flow After Decision
        projected_surplus_after = baseline_surplus - total_incremental_monthly
        dti_before = float(((existing_obligations / income) * 100).quantize(Decimal("0.1"))) if income > Decimal("0") else 0.0
        dti_after = float((((existing_obligations + effective_new_payment) / income) * 100).quantize(Decimal("0.1"))) if income > Decimal("0") else 0.0

        cash_flow_impact = CashFlowImpact(
            monthly_income=float(income),
            monthly_living_expenses=float(expenses),
            existing_obligations=float(existing_obligations),
            available_surplus_before=float(baseline_surplus),
            proposed_new_monthly_payment=float(new_monthly_payment),
            additional_ongoing_costs=float(monthly_ongoing),
            monthly_revenue_gain=float(revenue_gain),
            projected_surplus_after=float(projected_surplus_after),
            surplus_delta=float(projected_surplus_after - baseline_surplus),
            debt_to_income_before_pct=dti_before,
            debt_to_income_after_pct=dti_after
        )

        # Savings & Emergency Fund Impact
        initial_cash_required = down_payment + upfront_costs + processing_fee
        remaining_savings = max(Decimal("0.00"), savings - initial_cash_required)
        emergency_fund_preserved = remaining_savings >= emergency_target
        total_monthly_spend_after = expenses + existing_obligations + effective_new_payment + monthly_ongoing
        projected_runway = float((remaining_savings / total_monthly_spend_after).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if total_monthly_spend_after > Decimal("0") else 0.0

        savings_impact = SavingsImpact(
            starting_liquid_savings=float(savings),
            initial_cash_required=float(initial_cash_required),
            remaining_liquid_savings=float(remaining_savings),
            emergency_fund_target=float(emergency_target),
            emergency_fund_preserved=emergency_fund_preserved,
            baseline_runway_months=baseline_runway,
            projected_runway_months=projected_runway,
            runway_delta_months=float(projected_runway - baseline_runway),
            is_partial_data=income == Decimal("0") or savings == Decimal("0")
        )

        # Loan Analysis (if borrowing)
        loan_analysis = None
        if principal_borrowed > Decimal("0"):
            total_ownership = down_payment + total_repaid + processing_fee + upfront_costs + (monthly_ongoing * Decimal(str(tenure)))
            loan_analysis = LoanAnalysis(
                purchase_price=float(purchase_price),
                down_payment=float(down_payment),
                principal_borrowed=float(principal_borrowed),
                annual_interest_rate_pct=float(rate),
                tenure_months=tenure,
                monthly_emi=float(emi),
                total_amount_repaid=float(total_repaid),
                total_interest_paid=float(total_interest),
                processing_fee_amount=float(processing_fee),
                total_cost_of_ownership=float(total_ownership)
            )

        # Goal Timeline
        horizon_months = inp.time_horizon_months or tenure or 12
        months_needed = float((purchase_price / baseline_surplus).quantize(Decimal("0.1"))) if baseline_surplus > Decimal("0") else None
        goal_timeline = GoalTimeline(
            target_amount=float(purchase_price),
            already_saved=float(min(purchase_price, savings)),
            remaining_to_save=float(max(Decimal("0"), purchase_price - min(purchase_price, savings))),
            target_horizon_months=horizon_months,
            required_monthly_savings=float(new_monthly_payment),
            months_needed_at_current_surplus=months_needed,
            is_achievable_by_target_date=baseline_surplus >= new_monthly_payment
        )

        # Rule-based Verdict & Category
        missing_info = []
        if income <= Decimal("0"):
            missing_info.append("Monthly net income not provided.")
        if expenses <= Decimal("0"):
            missing_info.append("Living expenses not provided.")
        if savings <= Decimal("0"):
            missing_info.append("Current savings not provided.")
        if principal_borrowed > Decimal("0") and (inp.loan_interest_rate_pct is None or inp.loan_interest_rate_pct <= Decimal("0")):
            missing_info.append(f"Loan interest rate was assumed at {rate}%. Enter your actual bank rate for precise EMI.")

        recommendations = []
        if len(missing_info) >= 2 and income <= Decimal("0"):
            verdict_cat = "DATA_INCOMPLETE"
            summary_verdict = "We cannot determine affordability accurately until you enter your monthly income and savings."
            recommendations.append("Connect your bank account or manually enter baseline income and living expenses.")
            is_feasible = False
        elif projected_surplus_after < Decimal("0"):
            verdict_cat = "HIGH_RISK_DEFICIT"
            summary_verdict = f"High Risk: This decision creates a monthly cash flow deficit of ₹{abs(projected_surplus_after):,.0f}/month. Your expenses and payments would exceed your monthly income."
            recommendations.append(f"Reduce the purchase budget or increase your down payment to lower the monthly commitment below ₹{baseline_surplus:,.0f}/month.")
            recommendations.append("Consider postponing this decision until you can build additional savings or reduce non-essential expenses.")
            is_feasible = False
        elif initial_cash_required > savings:
            verdict_cat = "EMERGENCY_FUND_AT_RISK"
            summary_verdict = f"Cash Shortfall: Upfront cash required (₹{initial_cash_required:,.0f}) exceeds your available liquid savings (₹{savings:,.0f}) by ₹{initial_cash_required - savings:,.0f}."
            recommendations.append("Do not borrow additional unsecured personal loans for the down payment.")
            recommendations.append("Extend your savings horizon by 6-12 months to accumulate the upfront payment.")
            is_feasible = False
        elif not emergency_fund_preserved:
            verdict_cat = "EMERGENCY_FUND_AT_RISK"
            summary_verdict = f"Caution: Upfront cash leaves you with ₹{remaining_savings:,.0f} in savings, which is below your safety target of ₹{emergency_target:,.0f} ({target_months} months)."
            recommendations.append(f"Maintain at least ₹{emergency_target:,.0f} ring-fenced for unexpected emergencies before committing cash.")
            recommendations.append("Consider a slightly lower down payment if the loan interest rate is moderate.")
            is_feasible = True
        elif dti_after > 45.0 or projected_surplus_after < (income * Decimal("0.10")):
            verdict_cat = "TIGHT_CASH_FLOW"
            summary_verdict = f"Tight Cash Flow: You would have ₹{projected_surplus_after:,.0f}/month left over. Your debt commitments would take {dti_after:.1f}% of your monthly income."
            recommendations.append("Aim to keep total debt payments below 40% of take-home pay.")
            recommendations.append("Set aside an interest rate buffer if taking a floating-rate loan.")
            is_feasible = True
        else:
            verdict_cat = "AFFORDABLE"
            summary_verdict = f"Comfortably Affordable: You would have approximately ₹{projected_surplus_after:,.0f} left each month after all payments, while keeping {projected_runway:.1f} months of emergency savings intact."
            recommendations.append("Set up automated monthly transfers for the payment to maintain budget discipline.")
            recommendations.append("Continue investing your remaining surplus into your long-term goals.")
            is_feasible = True

        # Generate 3 Clearly Explained Alternatives (Section 4)
        alternatives = cls._generate_alternatives(
            stype, purchase_price, down_payment, principal_borrowed, rate, tenure,
            baseline_surplus, savings, emergency_target, monthly_ongoing, upfront_costs
        )

        # Generate 5 Understandable Stress Tests (Section 5)
        stress_tests = cls._generate_stress_tests(
            income, expenses, existing_obligations, effective_new_payment, monthly_ongoing,
            savings, initial_cash_required, principal_borrowed, rate, tenure
        )

        # Standard comparisons table
        comparisons = [
            ScenarioMetricComparison(
                metric_name="Monthly Cash Flow Surplus",
                baseline_value=f"₹{baseline_surplus:,.0f} / mo",
                scenario_value=f"₹{projected_surplus_after:,.0f} / mo",
                delta=f"-₹{total_incremental_monthly:,.0f}/mo",
                impact_type="positive" if projected_surplus_after >= (income * Decimal("0.20")) else ("neutral" if projected_surplus_after >= 0 else "negative")
            ),
            ScenarioMetricComparison(
                metric_name="Liquid Savings & Emergency Cushion",
                baseline_value=f"₹{savings:,.0f} ({baseline_runway:.1f} mos)",
                scenario_value=f"₹{remaining_savings:,.0f} ({projected_runway:.1f} mos)",
                delta=f"-₹{initial_cash_required:,.0f} upfront",
                impact_type="positive" if emergency_fund_preserved else "negative"
            ),
            ScenarioMetricComparison(
                metric_name="Debt-to-Income (DTI) Share",
                baseline_value=f"{dti_before:.1f}%",
                scenario_value=f"{dti_after:.1f}%",
                delta=f"+{dti_after - dti_before:.1f}%" if dti_after > dti_before else "0.0%",
                impact_type="positive" if dti_after <= 35.0 else ("neutral" if dti_after <= 45.0 else "negative")
            )
        ]

        # Timeline Projections (for charts)
        timeline_projections = []
        sample_step = max(1, tenure // 6) if tenure > 0 else 2
        for m in range(0, tenure + 1, sample_step):
            rem_loan = max(Decimal("0.00"), principal_borrowed - (principal_borrowed * Decimal(str(m)) / Decimal(str(tenure)))) if tenure > 0 else Decimal("0.00")
            cum_surplus = max(Decimal("0.00"), remaining_savings + (projected_surplus_after * Decimal(str(m))))
            timeline_projections.append({
                "month": m,
                "projected_savings": float(cum_surplus.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "remaining_debt": float(rem_loan.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            })

        return ScenarioSimulationResult(
            scenario_type=stype,
            title=title,
            is_feasible=is_feasible,
            verdict_category=verdict_cat,
            summary_verdict=summary_verdict,
            detailed_recommendations=recommendations,
            baseline_surplus=baseline_surplus,
            scenario_surplus=new_monthly_payment,
            required_monthly_allocation=new_monthly_payment,
            cash_flow_gap=projected_surplus_after,
            baseline_runway_months=baseline_runway,
            projected_runway_months=projected_runway,
            cash_flow_impact=cash_flow_impact,
            savings_impact=savings_impact,
            loan_analysis=loan_analysis,
            goal_timeline=goal_timeline,
            comparisons=comparisons,
            timeline_projections=timeline_projections,
            alternative_options=alternatives,
            stress_tests=stress_tests,
            risks_and_assumptions=[
                f"Amortization calculated at {rate}% annual interest rate over {tenure} months.",
                f"Assumes living expenses remain steady at ₹{expenses:,.0f}/month.",
                f"Emergency reserve target is set to {target_months} months of essential living costs (₹{emergency_target:,.0f}).",
                "Does not count illiquid assets, home equity, or credit card limits as available cash."
            ],
            missing_information=missing_info,
            citations=[
                "RBI Guidelines on Retail Credit & Debt-to-Income Norms (Target DTI <= 40%)",
                "Indian Banking Code of Practice - Standard Reducing Balance Amortization Formula"
            ]
        )

    @classmethod
    def _generate_alternatives(
        cls,
        stype: str,
        price: Decimal,
        down_payment: Decimal,
        principal: Decimal,
        rate: Decimal,
        tenure: int,
        baseline_surplus: Decimal,
        savings: Decimal,
        emergency_target: Decimal,
        monthly_ongoing: Decimal,
        upfront_costs: Decimal
    ) -> List[ScenarioAlternativeOption]:
        """Generates up to 3 clearly explained alternatives with explicit trade-offs."""
        alts = []

        # Option A: Proposed Plan
        proposed_emi = cls.calculate_emi(principal, rate, tenure) if principal > Decimal("0") else Decimal("0")
        proposed_initial = down_payment + upfront_costs
        proposed_surplus = baseline_surplus - proposed_emi - monthly_ongoing
        proposed_rem_sav = max(Decimal("0"), savings - proposed_initial)
        total_proposed_cost = proposed_initial + (proposed_emi * Decimal(str(tenure))) + (monthly_ongoing * Decimal(str(tenure)))

        alts.append(ScenarioAlternativeOption(
            name="Option A: Proceed with Proposed Plan",
            description=f"Purchase at ₹{price:,.0f} with ₹{down_payment:,.0f} down payment and {tenure}-month financing.",
            monthly_commitment=proposed_emi + monthly_ongoing,
            projected_outcome=price,
            feasibility="Affordable" if proposed_surplus >= Decimal("0") else "High Risk / Tight Cash Flow",
            initial_cash_required=proposed_initial,
            projected_surplus=proposed_surplus,
            remaining_savings=proposed_rem_sav,
            total_estimated_cost=total_proposed_cost,
            pros=["Get what you want immediately", "Predictable monthly payment"],
            cons=["Incurs loan interest charges", "Locks monthly cash flow for the full tenure"],
            trade_offs="Immediate enjoyment balanced against ongoing interest and reduced monthly flexibility."
        ))

        # Option B: Prudent Lower-Cost / Higher Down Payment Alternative
        # Suggest 15-20% lower purchase price OR +25% down payment
        prudent_price = (price * Decimal("0.85")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        prudent_down = min(savings * Decimal("0.5"), (down_payment * Decimal("1.25"))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        prudent_principal = max(Decimal("0"), prudent_price - prudent_down)
        prudent_emi = cls.calculate_emi(prudent_principal, rate, tenure) if prudent_principal > Decimal("0") else Decimal("0")
        prudent_initial = prudent_down + (upfront_costs * Decimal("0.85"))
        prudent_surplus = baseline_surplus - prudent_emi - (monthly_ongoing * Decimal("0.9"))
        prudent_rem_sav = max(Decimal("0"), savings - prudent_initial)
        prudent_total_cost = prudent_initial + (prudent_emi * Decimal(str(tenure))) + (monthly_ongoing * Decimal("0.9") * Decimal(str(tenure)))

        alts.append(ScenarioAlternativeOption(
            name="Option B: Prudent / Value Alternative (Recommended)",
            description=f"Choose a 15% more economical variant (₹{prudent_price:,.0f}) or increase down payment to ₹{prudent_down:,.0f}.",
            monthly_commitment=prudent_emi + (monthly_ongoing * Decimal("0.9")),
            projected_outcome=prudent_price,
            feasibility="Affordable",
            initial_cash_required=prudent_initial,
            projected_surplus=prudent_surplus,
            remaining_savings=prudent_rem_sav,
            total_estimated_cost=prudent_total_cost,
            pros=[
                f"Saves approximately ₹{total_proposed_cost - prudent_total_cost:,.0f} in total cost",
                f"Leaves ₹{prudent_surplus - proposed_surplus:,.0f}/mo more in your pocket each month",
                "Lower monthly stress during unexpected events"
            ],
            cons=["Slightly lower trim or smaller model"],
            trade_offs="Sacrifices minor non-essential features to gain significant cash flow security and lower interest."
        ))

        # Option C: Delay & Save First / All Cash
        delay_months = 12
        added_savings = max(Decimal("0"), baseline_surplus * Decimal(str(delay_months)))
        cash_down = min(price, max(down_payment, down_payment + added_savings))
        cash_loan = max(Decimal("0"), price - cash_down)
        cash_emi = cls.calculate_emi(cash_loan, rate, max(12, tenure - 12)) if cash_loan > Decimal("0") else Decimal("0")
        cash_initial = cash_down + upfront_costs
        cash_total_cost = cash_initial + (cash_emi * Decimal(str(max(12, tenure - 12)))) + (monthly_ongoing * Decimal(str(tenure)))

        alts.append(ScenarioAlternativeOption(
            name=f"Option C: Delay by {delay_months} Months & Save First",
            description=f"Postpone purchase by {delay_months} months. Save your monthly surplus to increase cash down payment to ₹{cash_down:,.0f}.",
            monthly_commitment=cash_emi + monthly_ongoing,
            projected_outcome=price,
            feasibility="Affordable",
            initial_cash_required=cash_initial,
            projected_surplus=baseline_surplus - cash_emi - monthly_ongoing,
            remaining_savings=max(Decimal("0"), savings + added_savings - cash_initial),
            total_estimated_cost=cash_total_cost,
            pros=[
                f"Drastically reduces or eliminates borrowing (saves ~₹{total_proposed_cost - cash_total_cost:,.0f} in interest)",
                "Full peace of mind with virtually zero monthly debt drag",
                "Preserves emergency reserves completely"
            ],
            cons=[f"Requires waiting {delay_months} months before making the purchase"],
            trade_offs="Exchanges patience for substantial interest savings and lower financial vulnerability."
        ))

        return alts

    @classmethod
    def _generate_stress_tests(
        cls,
        income: Decimal,
        expenses: Decimal,
        obligations: Decimal,
        new_payment: Decimal,
        ongoing_costs: Decimal,
        savings: Decimal,
        initial_cash: Decimal,
        principal: Decimal,
        rate: Decimal,
        tenure: int
    ) -> List[StressTestResult]:
        """Generates 5 deterministic stress test scenarios."""
        tests = []
        rem_savings = max(Decimal("0"), savings - initial_cash)

        # 1. Income Drops by 15%
        stressed_income = income * Decimal("0.85")
        surplus_1 = stressed_income - expenses - obligations - new_payment - ongoing_costs
        runway_1 = float((rem_savings / (expenses + obligations + new_payment + ongoing_costs)).quantize(Decimal("0.1"))) if (expenses + obligations + new_payment + ongoing_costs) > 0 else 0.0
        v_1 = "Manageable" if surplus_1 >= 0 else "Deficit"
        tests.append(StressTestResult(
            name="15% Income Drop",
            description="If job changes, bonuses reduce, or business slows by 15%",
            projected_surplus=float(surplus_1),
            projected_runway_months=runway_1,
            verdict=v_1,
            impact_summary=f"Surplus drops to ₹{surplus_1:,.0f}/mo. {'Cash flow remains positive.' if surplus_1 >= 0 else 'Results in monthly deficit — emergency savings will be drained.'}"
        ))

        # 2. Living Expenses Surge by 15%
        stressed_expenses = expenses * Decimal("1.15")
        surplus_2 = income - stressed_expenses - obligations - new_payment - ongoing_costs
        runway_2 = float((rem_savings / (stressed_expenses + obligations + new_payment + ongoing_costs)).quantize(Decimal("0.1"))) if (stressed_expenses + obligations + new_payment + ongoing_costs) > 0 else 0.0
        v_2 = "Manageable" if surplus_2 >= 0 else "Strained"
        tests.append(StressTestResult(
            name="15% Expense Increase",
            description="If medical, grocery, rent, or inflation costs rise by 15%",
            projected_surplus=float(surplus_2),
            projected_runway_months=runway_2,
            verdict=v_2,
            impact_summary=f"Monthly surplus narrows to ₹{surplus_2:,.0f}/mo. Leaves {runway_2:.1f} months runway."
        ))

        # 3. Unexpected One-Time Emergency (₹50,000)
        rem_after_med = max(Decimal("0"), rem_savings - Decimal("50000"))
        tot_spend = expenses + obligations + new_payment + ongoing_costs
        runway_3 = float((rem_after_med / tot_spend).quantize(Decimal("0.1"))) if tot_spend > 0 else 0.0
        v_3 = "Manageable" if runway_3 >= 3.0 else "Strained"
        tests.append(StressTestResult(
            name="₹50,000 Medical/Emergency Expense",
            description="An immediate unexpected hospital bill or major appliance repair",
            projected_surplus=float(income - tot_spend),
            projected_runway_months=runway_3,
            verdict=v_3,
            impact_summary=f"Savings drop to ₹{rem_after_med:,.0f}. Emergency runway becomes {runway_3:.1f} months."
        ))

        # 4. Interest Rate Hike (+1.5% APR)
        if principal > Decimal("0") and tenure > 0:
            stressed_emi = cls.calculate_emi(principal, rate + Decimal("1.5"), tenure)
            emi_hike = stressed_emi - new_payment
            surplus_4 = income - expenses - obligations - stressed_emi - ongoing_costs
            tests.append(StressTestResult(
                name="Loan Interest Rate Rises +1.5%",
                description=f"If RBI raises repo rates and your floating rate increases from {rate}% to {rate + Decimal('1.5')}%",
                projected_surplus=float(surplus_4),
                projected_runway_months=float((rem_savings / (expenses + obligations + stressed_emi + ongoing_costs)).quantize(Decimal("0.1"))) if (expenses + obligations + stressed_emi + ongoing_costs) > 0 else 0.0,
                verdict="Manageable" if surplus_4 >= 0 else "Strained",
                impact_summary=f"Monthly EMI increases by +₹{emi_hike:,.0f}/mo. Monthly surplus becomes ₹{surplus_4:,.0f}."
            ))
        else:
            tests.append(StressTestResult(
                name="Zero Debt Exposure",
                description="Because no loan is taken, interest rate fluctuations have zero impact on your budget.",
                projected_surplus=float(income - tot_spend),
                projected_runway_months=float(runway_1),
                verdict="Manageable",
                impact_summary="100% immune to interest rate hikes."
            ))

        # 5. Delay Purchase by 6 Months
        saved_6m = max(Decimal("0"), (income - expenses - obligations) * Decimal("6"))
        tests.append(StressTestResult(
            name="Delay Purchase by 6 Months",
            description="Accumulate cash for 6 additional months before committing",
            projected_surplus=float(income - expenses - obligations),
            projected_runway_months=float(((savings + saved_6m) / expenses).quantize(Decimal("0.1"))) if expenses > 0 else 0.0,
            verdict="Manageable",
            impact_summary=f"Builds +₹{saved_6m:,.0f} extra savings. Can be used to reduce debt or avoid loans completely."
        ))

        return tests

    @classmethod
    def _simulate_major_purchase_legacy(
        cls,
        inp: ScenarioInput,
        income: Decimal,
        expenses: Decimal,
        savings: Decimal
    ) -> ScenarioSimulationResult:
        """Legacy helper maintained for backward compatibility with existing tests."""
        target_amount = inp.target_amount or Decimal("800000.00")
        months = inp.time_horizon_months or 18
        title = inp.title or f"Major Purchase: ₹{target_amount:,.0f} in {months} Months"

        min_reserve = expenses * Decimal("3.0")
        available_downpayment = max(Decimal("0.00"), savings - min_reserve)

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
        baseline_surplus = income - expenses
        cash_flow_gap = baseline_surplus - required_sip
        is_feasible = cash_flow_gap >= Decimal("0.00")
        baseline_runway = float((savings / expenses).quantize(Decimal("0.1"))) if expenses > 0 else 0.0

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
                name="Optimized Budget / Lower-Cost Variant",
                description=(
                    f"Choose a variant or pre-owned model priced at ₹{target_amount * Decimal('0.8'):,.0f} (20% lower). "
                    f"This reduces your required monthly allocation and enables completion in {months} months with zero financial strain."
                ),
                monthly_commitment=required_sip * Decimal('0.8'),
                projected_outcome=target_amount * Decimal('0.8'),
                feasibility="Fully Feasible",
                pros=[
                    "Faster achievement without depleting emergency liquidity",
                    "Lower ongoing insurance and maintenance expenses"
                ],
                cons=[
                    "Slight compromise on top-tier vehicle features or brand tier"
                ]
            )
        ]

        timeline = [
            {"month": m, "projected_saved": round(float(min(target_amount, available_downpayment + required_sip * Decimal(str(m)))), 2)}
            for m in range(0, months + 1, max(1, months // 6))
        ]

        cash_flow_impact = CashFlowImpact(
            monthly_income=float(income),
            monthly_living_expenses=float(expenses),
            existing_obligations=0.0,
            available_surplus_before=float(baseline_surplus),
            proposed_new_monthly_payment=float(required_sip),
            additional_ongoing_costs=0.0,
            monthly_revenue_gain=0.0,
            projected_surplus_after=float(cash_flow_gap),
            surplus_delta=float(cash_flow_gap - baseline_surplus),
            debt_to_income_before_pct=0.0,
            debt_to_income_after_pct=0.0
        )

        savings_impact = SavingsImpact(
            starting_liquid_savings=float(savings),
            initial_cash_required=float(available_downpayment),
            remaining_liquid_savings=float(min_reserve),
            emergency_fund_target=float(min_reserve),
            emergency_fund_preserved=True,
            baseline_runway_months=baseline_runway,
            projected_runway_months=3.0,
            runway_delta_months=float(3.0 - baseline_runway)
        )

        return ScenarioSimulationResult(
            scenario_type="major_purchase",
            title=title,
            is_feasible=is_feasible,
            verdict_category="AFFORDABLE" if is_feasible else "HIGH_RISK_DEFICIT",
            summary_verdict=f"Funding this ₹{target_amount:,.0f} purchase purely from cash savings in {months} months requires ₹{required_sip:,.0f}/month.",
            detailed_recommendations=["Deploy a prudent down payment and finance the residual balance."],
            baseline_surplus=baseline_surplus,
            scenario_surplus=required_sip,
            required_monthly_allocation=required_sip,
            cash_flow_gap=cash_flow_gap,
            baseline_runway_months=baseline_runway,
            projected_runway_months=3.0,
            cash_flow_impact=cash_flow_impact,
            savings_impact=savings_impact,
            comparisons=comparisons,
            timeline_projections=timeline,
            alternative_options=alternatives,
            stress_tests=[],
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
        savings: Decimal
    ) -> ScenarioSimulationResult:
        baseline_surplus = income - expenses
        target_rate = inp.target_savings_rate_pct or Decimal("35.0")
        target_surplus = (income * target_rate) / Decimal("100.0") if income > 0 else Decimal("0")
        delta_surplus = target_surplus - baseline_surplus

        title = f"Increase Savings Rate to {target_rate}%"
        r = inp.expected_annual_return_pct / Decimal("100.0")

        def fv_sip(monthly_amt: Decimal, num_months: int) -> Decimal:
            i = r / Decimal("12.0")
            if i <= 0:
                return monthly_amt * num_months
            return (monthly_amt * (((Decimal("1.0") + i) ** num_months) - Decimal("1.0")) / i * (Decimal("1.0") + i)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        gain_1yr = fv_sip(delta_surplus, 12) if delta_surplus > 0 else Decimal("0")
        gain_3yr = fv_sip(delta_surplus, 36) if delta_surplus > 0 else Decimal("0")
        gain_5yr = fv_sip(delta_surplus, 60) if delta_surplus > 0 else Decimal("0")

        baseline_runway = float((savings / expenses).quantize(Decimal("0.1"))) if expenses > 0 else 0.0

        comparisons = [
            ScenarioMetricComparison(
                metric_name="Monthly Savings Allocation",
                baseline_value=f"₹{baseline_surplus:,.0f}/mo ({(baseline_surplus/income*100 if income > 0 else 0):.1f}%)",
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

        cash_flow_impact = CashFlowImpact(
            monthly_income=float(income),
            monthly_living_expenses=float(expenses),
            existing_obligations=0.0,
            available_surplus_before=float(baseline_surplus),
            proposed_new_monthly_payment=float(target_surplus),
            additional_ongoing_costs=0.0,
            monthly_revenue_gain=0.0,
            projected_surplus_after=float(target_surplus),
            surplus_delta=float(delta_surplus),
            debt_to_income_before_pct=0.0,
            debt_to_income_after_pct=0.0
        )

        savings_impact = SavingsImpact(
            starting_liquid_savings=float(savings),
            initial_cash_required=0.0,
            remaining_liquid_savings=float(savings),
            emergency_fund_target=float(expenses * Decimal("6")),
            emergency_fund_preserved=savings >= (expenses * Decimal("6")),
            baseline_runway_months=baseline_runway,
            projected_runway_months=baseline_runway,
            runway_delta_months=0.0
        )

        return ScenarioSimulationResult(
            scenario_type="increase_savings",
            title=title,
            is_feasible=True,
            verdict_category="AFFORDABLE",
            summary_verdict=f"Increasing your savings rate to {target_rate}% generates ₹{delta_surplus:,.0f}/month additional investment capacity, accumulating ₹{gain_3yr:,.0f} in 3 years.",
            detailed_recommendations=["Automate systematic investment plans on salary day."],
            baseline_surplus=baseline_surplus,
            scenario_surplus=target_surplus,
            required_monthly_allocation=delta_surplus,
            cash_flow_gap=delta_surplus,
            baseline_runway_months=baseline_runway,
            projected_runway_months=baseline_runway,
            cash_flow_impact=cash_flow_impact,
            savings_impact=savings_impact,
            comparisons=comparisons,
            timeline_projections=timeline,
            alternative_options=[],
            stress_tests=[],
            risks_and_assumptions=[
                f"Assumes an annualized return of {inp.expected_annual_return_pct}% in a diversified portfolio."
            ],
            citations=["Compound Interest Formula"]
        )

    @classmethod
    def _simulate_expense_reduction(
        cls,
        inp: ScenarioInput,
        income: Decimal,
        expenses: Decimal,
        savings: Decimal
    ) -> ScenarioSimulationResult:
        baseline_surplus = income - expenses
        reduction = inp.expense_reduction_amount or Decimal("5000.00")
        new_expenses = max(Decimal("0.00"), expenses - reduction)
        new_surplus = baseline_surplus + reduction

        title = f"Reduce Monthly Spending by ₹{reduction:,.0f}"
        r = inp.expected_annual_return_pct / Decimal("100.0")

        def fv_sip(monthly_amt: Decimal, num_months: int) -> Decimal:
            i = r / Decimal("12.0")
            if i <= 0:
                return monthly_amt * num_months
            return (monthly_amt * (((Decimal("1.0") + i) ** num_months) - Decimal("1.0")) / i * (Decimal("1.0") + i)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        gain_3yr = fv_sip(reduction, 36)
        baseline_runway = float((savings / expenses).quantize(Decimal("0.1"))) if expenses > 0 else 0.0
        proj_runway = float((savings / new_expenses).quantize(Decimal("0.1"))) if new_expenses > 0 else baseline_runway

        comparisons = [
            ScenarioMetricComparison(
                metric_name="Monthly Living Burn",
                baseline_value=f"₹{expenses:,.0f}/mo",
                scenario_value=f"₹{new_expenses:,.0f}/mo",
                delta=f"-₹{reduction:,.0f}/mo cutback",
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

        cash_flow_impact = CashFlowImpact(
            monthly_income=float(income),
            monthly_living_expenses=float(new_expenses),
            existing_obligations=0.0,
            available_surplus_before=float(baseline_surplus),
            proposed_new_monthly_payment=0.0,
            additional_ongoing_costs=0.0,
            monthly_revenue_gain=0.0,
            projected_surplus_after=float(new_surplus),
            surplus_delta=float(reduction),
            debt_to_income_before_pct=0.0,
            debt_to_income_after_pct=0.0
        )

        savings_impact = SavingsImpact(
            starting_liquid_savings=float(savings),
            initial_cash_required=0.0,
            remaining_liquid_savings=float(savings),
            emergency_fund_target=float(new_expenses * Decimal("6")),
            emergency_fund_preserved=True,
            baseline_runway_months=baseline_runway,
            projected_runway_months=proj_runway,
            runway_delta_months=float(proj_runway - baseline_runway)
        )

        return ScenarioSimulationResult(
            scenario_type="expense_reduction",
            title=title,
            is_feasible=True,
            verdict_category="AFFORDABLE",
            summary_verdict=f"Trimming ₹{reduction:,.0f}/month from discretionary expenses frees up ₹{reduction:,.0f} to invest, building ₹{gain_3yr:,.0f} in 3 years.",
            detailed_recommendations=["Target non-essential dining and subscription categories first."],
            baseline_surplus=baseline_surplus,
            scenario_surplus=new_surplus,
            required_monthly_allocation=reduction,
            cash_flow_gap=reduction,
            baseline_runway_months=baseline_runway,
            projected_runway_months=proj_runway,
            cash_flow_impact=cash_flow_impact,
            savings_impact=savings_impact,
            comparisons=comparisons,
            timeline_projections=[],
            alternative_options=[],
            stress_tests=[],
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
        savings: Decimal
    ) -> ScenarioSimulationResult:
        baseline_surplus = income - expenses
        target_months = 6
        target_reserve = expenses * Decimal(str(target_months))
        deficit = max(Decimal("0.00"), target_reserve - savings)
        title = "6-Month Emergency Runway Completion Plan"

        months_to_complete = int((deficit / baseline_surplus).quantize(Decimal("1"), rounding=ROUND_HALF_UP)) if baseline_surplus > 0 else 99
        baseline_runway = float((savings / expenses).quantize(Decimal("0.1"))) if expenses > 0 else 0.0

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

        cash_flow_impact = CashFlowImpact(
            monthly_income=float(income),
            monthly_living_expenses=float(expenses),
            existing_obligations=0.0,
            available_surplus_before=float(baseline_surplus),
            proposed_new_monthly_payment=float(baseline_surplus),
            additional_ongoing_costs=0.0,
            monthly_revenue_gain=0.0,
            projected_surplus_after=0.0,
            surplus_delta=float(-baseline_surplus),
            debt_to_income_before_pct=0.0,
            debt_to_income_after_pct=0.0
        )

        savings_impact = SavingsImpact(
            starting_liquid_savings=float(savings),
            initial_cash_required=0.0,
            remaining_liquid_savings=float(savings),
            emergency_fund_target=float(target_reserve),
            emergency_fund_preserved=deficit == 0,
            baseline_runway_months=baseline_runway,
            projected_runway_months=float(target_months),
            runway_delta_months=float(target_months - baseline_runway)
        )

        return ScenarioSimulationResult(
            scenario_type="emergency_fund_builder",
            title=title,
            is_feasible=baseline_surplus > Decimal("0.00"),
            verdict_category="AFFORDABLE" if baseline_surplus > 0 else "HIGH_RISK_DEFICIT",
            summary_verdict=(
                f"Your 6-month safety target is ₹{target_reserve:,.0f}. You currently have ₹{savings:,.0f} ({baseline_runway:.1f} months). "
                f"Allocating your monthly surplus of ₹{baseline_surplus:,.0f} achieves full 6-month safety in {months_to_complete} months."
            ),
            detailed_recommendations=["Park liquid safety reserves in liquid mutual funds or sweep-in fixed deposits."],
            baseline_surplus=baseline_surplus,
            scenario_surplus=baseline_surplus,
            required_monthly_allocation=baseline_surplus,
            cash_flow_gap=Decimal("0.00"),
            baseline_runway_months=baseline_runway,
            projected_runway_months=float(target_months),
            cash_flow_impact=cash_flow_impact,
            savings_impact=savings_impact,
            comparisons=comparisons,
            timeline_projections=[],
            alternative_options=[],
            stress_tests=[],
            risks_and_assumptions=[
                "Keep emergency reserves in high-liquidity instruments rather than volatile equity or locked-in bonds."
            ],
            citations=[
                "SEBI Liquid Fund Guidelines - T+1 withdrawal & negligible exit load after 7 days",
                "RBI DICGC Insurance Coverage - Up to ₹5 Lakhs per depositor"
            ]
        )
