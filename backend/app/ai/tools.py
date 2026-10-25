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

    @classmethod
    def get_cash_flow_forecast(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Projects upcoming 30/90-day cash flow, net surplus, and daily burn rate."""
        horizon = int(params.get("horizon_days", 30))
        income = Decimal(str(params.get("monthly_income", 100000)))
        expenses = Decimal(str(params.get("monthly_expenses", 50000)))
        liquid = Decimal(str(params.get("liquid_savings", 200000)))

        horizon_fraction = Decimal(str(horizon / 30.0))
        proj_income = income * horizon_fraction
        proj_expenses = expenses * horizon_fraction
        proj_net = proj_income - proj_expenses
        daily_burn = proj_expenses / Decimal(str(horizon)) if horizon > 0 else Decimal("0.00")

        return {
            "horizon_days": horizon,
            "projected_income": float(proj_income),
            "projected_expenses": float(proj_expenses),
            "projected_net_cash_flow": float(proj_net),
            "projected_ending_cash": float(liquid + proj_net),
            "daily_burn_rate": float(daily_burn),
            "summary": f"Over the next {horizon} days, projected net cash surplus is ₹{proj_net:,.0f} at a daily burn rate of ₹{daily_burn:,.0f}."
        }

    @classmethod
    def explain_spending_anomalies(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explains category spending variance compared to prior monthly baselines."""
        category = str(params.get("category", "General Spending"))
        current_spend = Decimal(str(params.get("current_spend", 0)))
        baseline = Decimal(str(params.get("baseline_spend", 1)))

        diff = current_spend - baseline
        pct = float((diff / baseline) * 100) if baseline > Decimal("0") else 0.0

        return {
            "category": category,
            "current_spend": float(current_spend),
            "baseline_spend": float(baseline),
            "variance_amount": float(diff),
            "variance_pct": round(pct, 1),
            "is_elevated": pct >= 25.0 and diff >= Decimal("2000.00"),
            "explanation": f"{category} spending is ₹{current_spend:,.0f}, which is ₹{diff:,.0f} ({pct:+.1f}%) relative to the monthly baseline of ₹{baseline:,.0f}."
        }

    @classmethod
    def assess_goal_feasibility(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates exact required monthly contribution, feasibility status, and timeline delay."""
        target = Decimal(str(params.get("target_amount", 100000)))
        current = Decimal(str(params.get("current_amount", 0)))
        months_left = max(1, int(params.get("months_remaining", 12)))
        monthly_surplus = Decimal(str(params.get("monthly_surplus", 20000)))

        remaining = max(Decimal("0.00"), target - current)
        required_sip = (remaining / Decimal(str(months_left))).quantize(Decimal("1.00"))
        is_on_track = monthly_surplus >= required_sip

        delay_months = 0
        if not is_on_track and monthly_surplus > Decimal("0"):
            needed_months = int(remaining / monthly_surplus)
            delay_months = max(0, needed_months - months_left)

        return {
            "target_amount": float(target),
            "current_amount": float(current),
            "months_remaining": months_left,
            "required_monthly_sip": float(required_sip),
            "current_monthly_surplus": float(monthly_surplus),
            "is_on_track": is_on_track,
            "delay_months": delay_months,
            "verdict": "On track" if is_on_track else f"Behind schedule by ~{delay_months} months (shortfall of ₹{float(required_sip - monthly_surplus):,.0f}/mo)"
        }


    @classmethod
    def get_recurring_commitments(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates total monthly recurring commitments, budget percentage, and pause impact."""
        items = params.get("items", [])
        total_monthly_exp = Decimal(str(params.get("total_monthly_expenses", 50000)))
        simulated_pause_amount = Decimal(str(params.get("simulated_pause_amount", 0)))

        monthly_commitments = Decimal("0.00")
        categories: Dict[str, float] = {}

        for item in items:
            amt = Decimal(str(item.get("amount", 0)))
            freq = str(item.get("frequency", "monthly"))
            if freq == "weekly":
                m_amt = amt * Decimal("52") / Decimal("12")
            elif freq == "fortnightly":
                m_amt = amt * Decimal("26") / Decimal("12")
            elif freq == "quarterly":
                m_amt = amt / Decimal("3")
            elif freq == "yearly":
                m_amt = amt / Decimal("12")
            else:
                m_amt = amt

            monthly_commitments += m_amt
            cat = item.get("category", "General")
            categories[cat] = categories.get(cat, 0.0) + float(m_amt)

        pct_of_expenses = float((monthly_commitments / total_monthly_exp) * 100) if total_monthly_exp > Decimal("0") else 0.0
        new_commitments = max(Decimal("0.00"), monthly_commitments - simulated_pause_amount)
        freed_surplus_annual = simulated_pause_amount * Decimal("12")

        return {
            "monthly_recurring_total": float(monthly_commitments),
            "percentage_of_living_expenses": round(pct_of_expenses, 1),
            "category_breakdown": categories,
            "simulated_pause_amount": float(simulated_pause_amount),
            "revised_monthly_commitments": float(new_commitments),
            "annualized_freed_surplus": float(freed_surplus_annual),
            "verdict": (
                f"Recurring commitments total ₹{monthly_commitments:,.0f}/month ({pct_of_expenses:.1f}% of expenses). "
                + (f"Pausing selected item frees ₹{simulated_pause_amount:,.0f}/mo (₹{freed_surplus_annual:,.0f}/year) for goal investments." if simulated_pause_amount > 0 else "")
            )
        }


    @classmethod
    def get_financial_overview(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Provides high-level deterministic financial health, surplus, and reserve metrics."""
        income = Decimal(str(params.get("monthly_income", 0)))
        expenses = Decimal(str(params.get("monthly_expenses", 0)))
        savings = Decimal(str(params.get("current_savings", 0)))
        debt = Decimal(str(params.get("total_debt", 0)))
        emis = Decimal(str(params.get("monthly_emi", 0)))
        net_worth = Decimal(str(params.get("net_worth", max(Decimal("0"), savings - debt))))

        surplus = max(Decimal("0.00"), income - expenses - emis)
        savings_rate = float((surplus / income) * 100) if income > Decimal("0") else 0.0
        dti = float((emis / income) * 100) if income > Decimal("0") else 0.0
        runway = float((savings / expenses).quantize(Decimal("0.1"))) if expenses > Decimal("0") else 0.0

        return {
            "monthly_income": float(income),
            "monthly_expenses": float(expenses),
            "monthly_emi": float(emis),
            "net_monthly_surplus": float(surplus),
            "savings_rate_pct": round(savings_rate, 1),
            "debt_to_income_pct": round(dti, 1),
            "liquid_savings": float(savings),
            "total_debt": float(debt),
            "net_worth": float(net_worth),
            "emergency_runway_months": runway,
            "status": "Healthy" if savings_rate >= 20.0 and runway >= 3.0 and dti <= 40.0 else "Needs Attention",
            "summary": f"Net surplus is ₹{surplus:,.0f}/mo (savings rate {savings_rate:.1f}%). Emergency runway covers {runway:.1f} months of expenses. DTI is {dti:.1f}%."
        }

    @classmethod
    def get_account_balances(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarizes verified bank account balances and asset distributions."""
        accounts = params.get("bank_accounts", [])
        verified_total = sum(float(a.get("balance", 0.0)) for a in accounts if a.get("status") == "synced")
        asset_breakdown = params.get("asset_breakdown", {})
        manual_total = float(params.get("manual_assets_total", sum(asset_breakdown.values())))

        return {
            "linked_accounts_count": len(accounts),
            "verified_bank_balance": round(verified_total, 2),
            "manual_assets_total": round(manual_total, 2),
            "total_liquid_reserves": round(verified_total + float(asset_breakdown.get("liquid_mf", 0)) + float(asset_breakdown.get("cash", 0)), 2),
            "accounts_detail": [
                {
                    "institution": a.get("institution", "Unknown Bank"),
                    "account_masked": a.get("account_masked", "XXXX"),
                    "balance": float(a.get("balance", 0.0)),
                    "status": a.get("status", "synced")
                }
                for a in accounts
            ],
            "asset_breakdown": asset_breakdown
        }

    @classmethod
    def get_net_worth(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates total assets, total debt liabilities, and net worth."""
        liquid = Decimal(str(params.get("current_savings", 0)))
        investments = Decimal(str(params.get("manual_assets_total", 0)))
        total_assets = max(liquid, liquid + investments)
        total_liabilities = Decimal(str(params.get("total_debt", 0)))
        net_worth = total_assets - total_liabilities

        return {
            "total_assets": float(total_assets),
            "total_liabilities": float(total_liabilities),
            "net_worth": float(net_worth),
            "debt_to_asset_pct": round(float((total_liabilities / total_assets) * 100) if total_assets > 0 else 0.0, 1),
            "summary": f"Total assets: ₹{total_assets:,.0f}, Total liabilities: ₹{total_liabilities:,.0f}, Net Worth: ₹{net_worth:,.0f}."
        }

    @classmethod
    def query_transactions(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filters transaction history by category, type, min/max amount, and search term."""
        txns = params.get("transactions", [])
        cat_filter = str(params.get("category", "")).lower()
        type_filter = str(params.get("transaction_type", "")).lower()
        keyword = str(params.get("keyword", "")).lower()
        min_amt = float(params.get("min_amount", 0))
        max_amt = float(params.get("max_amount", 10000000))
        limit = int(params.get("limit", 20))

        filtered = []
        total_matched_amt = 0.0

        for t in txns:
            amt = float(t.get("amount", 0.0))
            cat = str(t.get("category", "")).lower()
            t_type = str(t.get("transaction_type", "expense")).lower()
            desc = str(t.get("description", "")).lower()

            if cat_filter and cat_filter != cat:
                continue
            if type_filter and type_filter != t_type:
                continue
            if keyword and keyword not in desc and keyword not in cat:
                continue
            if amt < min_amt or amt > max_amt:
                continue

            filtered.append(t)
            total_matched_amt += amt
            if len(filtered) >= limit:
                break

        return {
            "total_matches": len(filtered),
            "total_amount": round(total_matched_amt, 2),
            "transactions": filtered
        }

    @classmethod
    def summarize_income_and_expenses(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates total income, total expenditure, and net cash surplus for a specified window."""
        income = float(params.get("last_30d_income", params.get("monthly_income", 0.0)))
        expenses = float(params.get("last_30d_expenses", params.get("monthly_expenses", 0.0)))
        net = income - expenses

        return {
            "total_income": round(income, 2),
            "total_expenses": round(expenses, 2),
            "net_savings": round(net, 2),
            "daily_burn_rate": round(expenses / 30.0, 2) if expenses > 0 else 0.0,
            "savings_rate_pct": round((net / income * 100) if income > 0 else 0.0, 1)
        }

    @classmethod
    def analyze_spending_by_category(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Breaks down category expenditures and highlights disproportionate cash burns."""
        cat_spending = params.get("category_spending", params.get("category_spending_30d", {}))
        total_exp = sum(float(v) for v in cat_spending.values())

        breakdown = []
        high_spend_categories = []

        for cat, amt_f in sorted(cat_spending.items(), key=lambda x: x[1], reverse=True):
            amt = float(amt_f)
            pct = round((amt / total_exp * 100) if total_exp > 0 else 0.0, 1)
            breakdown.append({
                "category": cat,
                "amount": round(amt, 2),
                "percentage_of_total": pct
            })
            if pct >= 30.0 and cat.lower() not in ["investments", "savings", "rent"]:
                high_spend_categories.append(f"{cat} ({pct}% of total)")

        return {
            "total_spending": round(total_exp, 2),
            "categories_count": len(breakdown),
            "category_breakdown": breakdown,
            "top_category": breakdown[0] if breakdown else None,
            "high_concentration_categories": high_spend_categories
        }

    @classmethod
    def get_budget_performance(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compares budget targets against actual spend per category."""
        budgets = params.get("budget_categories", [])
        actuals = params.get("category_spending", params.get("category_spending_30d", {}))

        performance = []
        total_allocated = 0.0
        total_spent = 0.0
        overspent = []

        for b in budgets:
            cat = b.get("category", "")
            alloc = float(b.get("monthly_allocation", 0.0))
            spent = float(actuals.get(cat, 0.0))
            rem = alloc - spent
            variance_pct = round(((spent - alloc) / alloc * 100) if alloc > 0 else 0.0, 1)
            is_over = spent > alloc

            total_allocated += alloc
            total_spent += spent

            perf_item = {
                "category": cat,
                "allocated": alloc,
                "spent": spent,
                "remaining": round(rem, 2),
                "variance_pct": variance_pct,
                "is_overspent": is_over
            }
            performance.append(perf_item)
            if is_over:
                overspent.append(f"{cat}: Spent ₹{spent:,.0f} vs Budget ₹{alloc:,.0f} (+₹{spent-alloc:,.0f})")

        return {
            "total_budget_allocated": round(total_allocated, 2),
            "total_budget_spent": round(total_spent, 2),
            "total_remaining": round(total_allocated - total_spent, 2),
            "categories_performance": performance,
            "overspent_categories": overspent,
            "adherence_rate_pct": round(((total_allocated - max(0, total_spent - total_allocated)) / total_allocated * 100) if total_allocated > 0 else 100.0, 1)
        }

    @classmethod
    def find_overspending(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Identifies specific budget lines or anomalous categories exceeding thresholds."""
        res = cls.get_budget_performance(params)
        anomalies = params.get("spending_anomalies", [])

        return {
            "overspent_budgets": res["overspent_categories"],
            "anomalous_spikes": anomalies,
            "action_required": len(res["overspent_categories"]) > 0 or len(anomalies) > 0,
            "summary": f"Detected {len(res['overspent_categories'])} overspent budgets and {len(anomalies)} statistical spending spikes."
        }

    @classmethod
    def get_upcoming_obligations(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Returns chronological 30-day forecast of recurring payments and EMIs."""
        commitments = params.get("recurring_commitments", [])
        emis = params.get("liabilities_list", [])

        items = []
        total_30d = 0.0

        for r in commitments:
            if r.get("type", "expense") == "expense":
                amt = float(r.get("monthly_normalized", r.get("amount", 0)))
                total_30d += amt
                items.append({
                    "name": r.get("name", "Recurring Bill"),
                    "amount": amt,
                    "type": "recurring_subscription",
                    "frequency": r.get("frequency", "monthly"),
                    "next_date": r.get("next_date")
                })

        for emi in emis:
            amt = float(emi.get("monthly_emi", 0))
            total_30d += amt
            items.append({
                "name": f"EMI: {emi.get('name', 'Loan')}",
                "amount": amt,
                "type": "loan_emi",
                "frequency": "monthly",
                "next_date": None
            })

        return {
            "total_upcoming_30d": round(total_30d, 2),
            "obligations_count": len(items),
            "obligations": items,
            "summary": f"Total confirmed obligations over next 30 days: ₹{total_30d:,.0f} across {len(items)} commitments."
        }

    @classmethod
    def analyze_emergency_runway(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates emergency reserve adequacy based on user role and monthly burn."""
        savings = Decimal(str(params.get("current_savings", 0)))
        expenses = Decimal(str(params.get("monthly_expenses", 35000)))
        emis = Decimal(str(params.get("monthly_emi", 0)))
        role = str(params.get("user_role", "salaried")).lower()

        essential_burn = expenses + emis
        months_covered = float((savings / essential_burn).quantize(Decimal("0.1"))) if essential_burn > Decimal("0") else 0.0
        target_months = 6.0 if role in ["freelancer", "business_owner"] else 3.0
        target_savings = essential_burn * Decimal(str(target_months))
        shortfall = max(Decimal("0.00"), target_savings - savings)

        return {
            "current_liquid_reserves": float(savings),
            "monthly_essential_burn": float(essential_burn),
            "months_covered": months_covered,
            "recommended_target_months": target_months,
            "recommended_target_amount": float(target_savings),
            "reserve_shortfall": float(shortfall),
            "status": "Adequate" if months_covered >= target_months else "Shortfall",
            "verdict": f"Liquid reserves cover {months_covered:.1f} months of essential expenses (recommended: {target_months:.0f} months for {role} profiles)."
        }

    @classmethod
    def evaluate_affordability(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-feature financial reasoning: Determines if user can afford a proposed EMI or recurring commitment.
        Synthesizes income, living expenses, existing recurring commitments, loan EMIs, and liquid runway.
        """
        proposed_amt = Decimal(str(params.get("proposed_amount", 0)))
        item_type = str(params.get("item_type", "emi"))  # emi, subscription, purchase
        income = Decimal(str(params.get("monthly_income", 60000)))
        expenses = Decimal(str(params.get("monthly_expenses", 35000)))
        existing_emis = Decimal(str(params.get("monthly_emi", 0)))
        existing_rec = Decimal(str(params.get("recurring_monthly_expenses", 0)))
        liquid_savings = Decimal(str(params.get("current_savings", 100000)))

        # 1. Net monthly surplus before proposed commitment
        base_essential_burn = expenses + existing_emis
        current_surplus = max(Decimal("0.00"), income - base_essential_burn)

        # 2. Revised surplus after proposed commitment
        revised_surplus = current_surplus - proposed_amt
        is_positive_surplus = revised_surplus >= Decimal("0.00")

        # 3. Debt to income calculation
        new_total_emi = existing_emis + (proposed_amt if item_type == "emi" else Decimal("0"))
        new_dti = float((new_total_emi / income) * 100) if income > Decimal("0") else 0.0

        # 4. Emergency reserve impact
        new_burn = base_essential_burn + proposed_amt
        revised_runway = float((liquid_savings / new_burn).quantize(Decimal("0.1"))) if new_burn > Decimal("0") else 0.0

        # 5. Affordability Decision Matrix
        if not is_positive_surplus:
            status = "Not Affordable / Deficit"
            recommendation = (
                f"Taking on ₹{proposed_amt:,.0f}/mo causes a monthly cash deficit of ₹{abs(revised_surplus):,.0f}. "
                f"You would need to cut living expenses or increase income before committing."
            )
        elif new_dti > 45.0:
            status = "High Risk / Tight"
            recommendation = (
                f"Monthly surplus remains positive (₹{revised_surplus:,.0f}/mo), but your Debt-to-Income (DTI) ratio "
                f"rises to {new_dti:.1f}% (RBI recommended cap is 40-50%). Lenders may reject or charge higher interest."
            )
        elif revised_surplus < Decimal("5000.00"):
            status = "Borderline Tight"
            recommendation = (
                f"Affordable, but leaves only ₹{revised_surplus:,.0f}/month breathing room for unexpected expenses and discretionary lifestyle."
            )
        else:
            status = "Comfortably Affordable"
            recommendation = (
                f"Comfortably fits within your cash flow. Leaves ₹{revised_surplus:,.0f}/month net surplus while maintaining "
                f"a {new_dti:.1f}% DTI and {revised_runway:.1f} months of emergency runway."
            )

        return {
            "proposed_amount": float(proposed_amt),
            "item_type": item_type,
            "monthly_income": float(income),
            "current_monthly_expenses": float(expenses),
            "existing_monthly_emi": float(existing_emis),
            "existing_recurring_commitments": float(existing_rec),
            "current_net_surplus": float(current_surplus),
            "revised_net_surplus": float(revised_surplus),
            "new_debt_to_income_pct": round(new_dti, 1),
            "revised_emergency_runway_months": revised_runway,
            "status": status,
            "recommendation": recommendation
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
    "get_cash_flow_forecast": FinancialToolsRegistry.get_cash_flow_forecast,
    "explain_spending_anomalies": FinancialToolsRegistry.explain_spending_anomalies,
    "assess_goal_feasibility": FinancialToolsRegistry.assess_goal_feasibility,
    "get_recurring_commitments": FinancialToolsRegistry.get_recurring_commitments,
    # Global AI CFO 2.0 Tools
    "get_financial_overview": FinancialToolsRegistry.get_financial_overview,
    "get_account_balances": FinancialToolsRegistry.get_account_balances,
    "get_net_worth": FinancialToolsRegistry.get_net_worth,
    "query_transactions": FinancialToolsRegistry.query_transactions,
    "summarize_income_and_expenses": FinancialToolsRegistry.summarize_income_and_expenses,
    "analyze_spending_by_category": FinancialToolsRegistry.analyze_spending_by_category,
    "get_budget_performance": FinancialToolsRegistry.get_budget_performance,
    "find_overspending": FinancialToolsRegistry.find_overspending,
    "get_upcoming_obligations": FinancialToolsRegistry.get_upcoming_obligations,
    "analyze_emergency_runway": FinancialToolsRegistry.analyze_emergency_runway,
    "evaluate_affordability": FinancialToolsRegistry.evaluate_affordability,
}

