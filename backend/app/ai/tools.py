from typing import Dict, Any
from decimal import Decimal
from app.finance.tax.engine import IndianTaxEngine
from app.schemas.tax import TaxCalculationInput
from app.finance.investments.engine import InvestmentEngine
from app.schemas.investment import InvestmentCompareRequest, GoalProjectionRequest
from app.finance.budget.engine import BudgetEngine
from app.finance.scenarios.engine import ScenarioEngine
from app.schemas.scenario import ScenarioInput
from app.finance.fire.engine import FireEngine
from app.finance.fire.health import FinancialHealthEngine
from app.schemas.fire import FireCalculationInput


class FinancialToolsRegistry:
    """
    Exposes validated financial calculation tools to the AI assistant.
    Guarantees deterministic execution; calculations are never hallucinated.
    """

    @classmethod
    def calculate_tax(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates and compares Old vs New Regime tax liabilities."""
        gross = Decimal(str(params.get("gross_annual_salary", 0)))
        ay = str(params.get("assessment_year", "2025-26"))
        taxpayer_type = str(params.get("taxpayer_type", "salaried"))
        
        inp = TaxCalculationInput(
            assessment_year=ay,
            taxpayer_type=taxpayer_type,
            gross_annual_salary=gross,
            section_80c=Decimal(str(params.get("section_80c", 0))),
            section_80d=Decimal(str(params.get("section_80d", 0))),
            section_80ccd_1b=Decimal(str(params.get("section_80ccd_1b", 0))),
            home_loan_interest_24b=Decimal(str(params.get("home_loan_interest_24b", 0))),
            hra_exemption=Decimal(str(params.get("hra_exemption", 0))),
        )
        res = IndianTaxEngine.compare_regimes(inp)
        return {
            "recommended_regime": res.recommended_regime,
            "tax_savings": float(res.tax_savings),
            "new_regime_tax": float(res.new_regime.total_tax_liability),
            "old_regime_tax": float(res.old_regime.total_tax_liability),
            "new_regime_std_deduction": float(res.new_regime.standard_deduction),
            "taxable_income_new": float(res.new_regime.taxable_income),
            "taxable_income_old": float(res.old_regime.taxable_income),
            "explanation": res.explanation,
            "citations": res.new_regime.official_citations
        }

    @classmethod
    def compare_investments(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compares Liquid Mutual Funds, Fixed Deposits, and Bonds."""
        amount = Decimal(str(params.get("amount", 100000)))
        months = int(params.get("time_horizon_months", 12))
        can_lock = bool(params.get("can_lock_funds", False))

        req = InvestmentCompareRequest(
            investment_amount=amount,
            time_horizon_months=months,
            can_lock_funds=can_lock
        )
        res = InvestmentEngine.compare_instruments(req)
        return {
            "top_recommendation": res.top_recommendation,
            "rationale": res.rationale,
            "principal_amount": float(res.principal_amount),
            "time_horizon_months": res.time_horizon_months,
            "comparisons": [
                {
                    "name": c.display_name,
                    "yield_pct": float(c.indicative_annual_yield_pct),
                    "maturity_value": float(c.projected_maturity_value),
                    "liquidity": c.liquidity_mechanism,
                    "credit_risk": c.credit_risk_level,
                    "interest_rate_risk": c.interest_rate_risk,
                    "tax_treatment": c.tax_treatment_summary,
                    "exit_penalty": c.exit_load_or_penalty
                } for c in res.comparisons
            ],
            "disclaimer": res.disclaimer
        }

    @classmethod
    def calculate_goal_plan(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates monthly contribution and inflation-adjusted targets for financial goals."""
        target = Decimal(str(params.get("target_amount", 1000000)))
        current = Decimal(str(params.get("current_amount", 0)))
        months = int(params.get("time_horizon_months", 36))
        goal_name = str(params.get("goal_name", "Financial Goal"))
        return_rate = Decimal(str(params.get("expected_return_pct", 8.0)))
        inflation_rate = Decimal(str(params.get("expected_inflation_pct", 6.0)))

        req = GoalProjectionRequest(
            goal_name=goal_name,
            target_amount=target,
            current_amount=current,
            time_horizon_months=months,
            expected_annual_return_pct=return_rate,
            expected_annual_inflation_pct=inflation_rate,
            adjust_for_inflation=True
        )
        res = InvestmentEngine.project_goal(req)
        return {
            "goal_name": res.goal_name,
            "nominal_target": float(res.nominal_target_amount),
            "inflation_adjusted_target": float(res.inflation_adjusted_target),
            "required_monthly_sip": float(res.required_monthly_sip),
            "total_contributed": float(res.total_investment_contributed),
            "projected_wealth_gain": float(res.projected_wealth_gain),
            "time_horizon_months": res.time_horizon_months
        }

    @classmethod
    def analyze_budget(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes cash flow, savings rate, and emergency runway."""
        income = Decimal(str(params.get("monthly_income", 100000)))
        expenses = Decimal(str(params.get("monthly_expenses", 60000)))
        fund = Decimal(str(params.get("emergency_fund_current", 120000)))

        res = BudgetEngine.analyze_cash_flow(income, expenses, fund, target_months=6)
        return {
            "monthly_income": float(res["monthly_income"]),
            "monthly_expenses": float(res["monthly_expenses"]),
            "monthly_surplus": float(res["monthly_surplus"]),
            "savings_rate_pct": res["savings_rate_pct"],
            "emergency_fund_target": float(res["emergency_fund_target"]),
            "emergency_fund_months_covered": res["emergency_fund_months_covered"],
            "is_emergency_fund_sufficient": res["is_emergency_fund_sufficient"]
        }

    @classmethod
    def simulate_scenario(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates multi-variable financial decision scenarios."""
        inp = ScenarioInput(
            scenario_type=params.get("scenario_type", "major_purchase"),
            monthly_income=Decimal(str(params["monthly_income"])) if "monthly_income" in params else None,
            monthly_expenses=Decimal(str(params["monthly_expenses"])) if "monthly_expenses" in params else None,
            current_savings=Decimal(str(params["current_savings"])) if "current_savings" in params else None,
            target_amount=Decimal(str(params["target_amount"])) if "target_amount" in params else None,
            time_horizon_months=int(params["time_horizon_months"]) if "time_horizon_months" in params else None,
            expense_reduction_amount=Decimal(str(params["expense_reduction_amount"])) if "expense_reduction_amount" in params else None,
            target_savings_rate_pct=Decimal(str(params["target_savings_rate_pct"])) if "target_savings_rate_pct" in params else None,
        )
        res = ScenarioEngine.simulate(inp)
        return {
            "scenario_type": res.scenario_type,
            "title": res.title,
            "is_feasible": res.is_feasible,
            "summary_verdict": res.summary_verdict,
            "baseline_surplus": float(res.baseline_surplus),
            "scenario_surplus": float(res.scenario_surplus),
            "required_monthly_allocation": float(res.required_monthly_allocation),
            "cash_flow_gap": float(res.cash_flow_gap),
            "baseline_runway_months": res.baseline_runway_months,
            "projected_runway_months": res.projected_runway_months,
            "alternative_options": [
                {
                    "name": opt.name,
                    "description": opt.description,
                    "monthly_commitment": float(opt.monthly_commitment),
                    "feasibility": opt.feasibility,
                    "pros": opt.pros,
                    "cons": opt.cons
                } for opt in res.alternative_options
            ],
            "risks_and_assumptions": res.risks_and_assumptions,
            "citations": res.citations
        }


    @classmethod
    def compare_debt_payoff(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates and compares Debt Avalanche vs Debt Snowball repayment strategies."""
        debts = params.get("debts", [])
        extra = Decimal(str(params.get("extra_monthly_prepayment", 0)))
        res = BudgetEngine.calculate_debt_payoff(debts, extra_monthly_payment=extra)
        return {
            "total_debt_principal": float(res["total_debt_principal"]),
            "total_monthly_emi": float(res["total_monthly_emi"]),
            "extra_payment_applied": float(res["extra_payment_applied"]),
            "avalanche_order": res["avalanche_priority"],
            "snowball_order": res["snowball_priority"],
            "recommendation": res["strategy_recommendation"]
        }

    @classmethod
    def calculate_fire_plan(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates FIRE target, projected retirement age, required SIP, and shortfall."""
        inp = FireCalculationInput(
            current_age=int(params.get("current_age", 28)),
            retirement_age=int(params.get("retirement_age", 50)),
            monthly_expenses=Decimal(str(params.get("monthly_expenses", 50000))),
            monthly_income=Decimal(str(params.get("monthly_income", 100000))) if "monthly_income" in params else None,
            current_investable_assets=Decimal(str(params.get("current_investable_assets", 1000000))) if "current_investable_assets" in params else None,
            monthly_investment=Decimal(str(params.get("monthly_investment", 30000))) if "monthly_investment" in params else None,
            expected_annual_inflation_pct=Decimal(str(params.get("expected_annual_inflation_pct", 6.0))),
            expected_nominal_return_pct=Decimal(str(params.get("expected_nominal_return_pct", 11.0))),
            withdrawal_rate_pct=Decimal(str(params.get("withdrawal_rate_pct", 3.5)))
        )
        res = FireEngine.calculate_fire(inp)
        return {
            "current_age": res.current_age,
            "planned_retirement_age": res.planned_retirement_age,
            "years_to_retirement": res.years_to_retirement,
            "fire_target_today": float(res.fire_target_today),
            "fire_target_future": float(res.fire_target_future),
            "fire_progress_pct": res.fire_progress_pct,
            "projected_fire_age": res.projected_fire_age,
            "projected_portfolio_at_retirement": float(res.projected_portfolio_at_retirement),
            "portfolio_surplus_or_shortfall": float(res.portfolio_surplus_or_shortfall),
            "required_monthly_investment": float(res.required_monthly_investment),
            "current_monthly_investment": float(res.current_monthly_investment),
            "monthly_investment_gap": float(res.monthly_investment_gap),
            "disclaimers": res.disclaimers
        }

    @classmethod
    def compare_fire_strategies(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compares Lean FIRE, Regular FIRE, Fat FIRE, and Coast FIRE targets and feasibility."""
        inp = FireCalculationInput(
            current_age=int(params.get("current_age", 28)),
            retirement_age=int(params.get("retirement_age", 50)),
            monthly_expenses=Decimal(str(params.get("monthly_expenses", 50000))),
            current_investable_assets=Decimal(str(params.get("current_investable_assets", 1000000))),
            monthly_investment=Decimal(str(params.get("monthly_investment", 30000)))
        )
        res = FireEngine.calculate_fire(inp)
        return {
            "strategies": [
                {
                    "type": s.strategy_type,
                    "name": s.name,
                    "monthly_expense": float(s.monthly_expense_in_retirement),
                    "target_today": float(s.target_corpus_today),
                    "target_future": float(s.target_corpus_at_retirement),
                    "projected_age": s.projected_fire_age,
                    "is_achievable": s.is_achievable_by_target_age,
                    "required_sip": float(s.required_monthly_investment),
                    "shortfall_or_surplus": float(s.shortfall_or_surplus_at_retirement),
                    "notes": s.assumptions_and_limitations
                } for s in res.strategies
            ]
        }

    @classmethod
    def assess_financial_health(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates 8-pillar financial health and returns prioritized 12-month action checklist."""
        res = FinancialHealthEngine.assess_health(
            age=int(params.get("age", 30)),
            monthly_income=Decimal(str(params.get("monthly_income", 100000))),
            monthly_expenses=Decimal(str(params.get("monthly_expenses", 50000))),
            liquid_assets=Decimal(str(params.get("liquid_assets", 300000))),
            investable_assets=Decimal(str(params.get("investable_assets", 1500000))),
            total_debt_principal=Decimal(str(params.get("total_debt_principal", 0))),
            total_monthly_emi=Decimal(str(params.get("total_monthly_emi", 0))),
            goals_on_track_pct=float(params.get("goals_on_track_pct", 80.0)),
            fire_progress_pct=float(params.get("fire_progress_pct", 35.0)),
            fire_shortfall=Decimal(str(params.get("fire_shortfall", 0)))
        )
        return {
            "overall_score": res.overall_score,
            "status": res.status,
            "summary": res.summary,
            "pillars": [
                {
                    "pillar": p.name,
                    "score": p.score,
                    "status": p.status,
                    "metric": p.metric_value,
                    "benchmark": p.target_benchmark,
                    "priority": p.action_priority,
                    "recommendation": p.recommendation
                } for p in res.pillars
            ],
            "action_checklist": res.actionable_checklist_12_months
        }


AVAILABLE_TOOLS = {
    "calculate_tax": FinancialToolsRegistry.calculate_tax,
    "compare_investments": FinancialToolsRegistry.compare_investments,
    "calculate_goal_plan": FinancialToolsRegistry.calculate_goal_plan,
    "analyze_budget": FinancialToolsRegistry.analyze_budget,
    "simulate_scenario": FinancialToolsRegistry.simulate_scenario,
    "compare_debt_payoff": FinancialToolsRegistry.compare_debt_payoff,
    "calculate_fire_plan": FinancialToolsRegistry.calculate_fire_plan,
    "compare_fire_strategies": FinancialToolsRegistry.compare_fire_strategies,
    "assess_financial_health": FinancialToolsRegistry.assess_financial_health,
}

