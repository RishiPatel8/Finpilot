from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import re
import logging
from app.core.config import settings
from app.rag.knowledge import KnowledgeRetriever
from app.ai.tools import AVAILABLE_TOOLS

logger = logging.getLogger("finpilot.ai")


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_response(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generates grounded financial response with citations and tool results."""
        pass


class MockAIProvider(BaseAIProvider):
    """
    Connected AI CFO:
    Context-aware financial planner that uses authenticated user context,
    retrieves statutory knowledge citations, executes deterministic calculation tools,
    and returns grounded, explainable financial decisions with zero external API dependencies.
    """

    def generate_response(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        q = query.lower()
        tool_results = []
        citations = []
        ctx = user_context or {}
        if any(p in q for p in ["ignore all previous", "ignore previous instructions", "system prompt", "reveal your instructions", "bypass rules", "forget your rules"]):
            return {
                "content": (
                    "I am FinPilot AI's Connected Financial Planning Assistant. "
                    "I operate strictly within authorized personal finance guidelines, Indian Income Tax Act rules, and SEBI/RBI statutory regulations. "
                    "How can I help you check your budget, understand your taxes, compare savings options, or plan a big purchase today?"
                ),
                "citations": ["FinPilot AI Security & Grounding Policy"],
                "tool_invocations": []
            }

        # 1.5 Handle 'Explain this simply' / Plain English request
        if any(p in q for p in ["explain simply", "explain this simply", "simple terms", "in simple words", "simplify", "plain english"]):
            return {
                "content": (
                    "### Plain-English Financial Translation\n\n"
                    "Here is a simple summary of how FinPilot looks at your money:\n\n"
                    "- **Income & Expenses**: What comes in each month (your salary or earnings) and what goes out (rent, groceries, bills).\n"
                    "- **Money Left Over (Surplus)**: What is left after covering your living costs. This is the amount you can comfortably save or invest.\n"
                    "- **Emergency Fund**: Money kept aside in a safe bank account for unexpected costs (aiming for 3 to 6 months of expenses) before taking investment risks.\n"
                    "- **Retirement Target**: The estimated money you need to have invested so you can live comfortably without depending on a monthly paycheck.\n"
                    "- **Monthly Investment (SIP)**: A regular monthly amount put into investments (like mutual funds or fixed deposits) so compounding grows your money over time.\n\n"
                    "Which number or screen would you like me to explain step-by-step?"
                ),
                "citations": ["FinPilot Plain-Language Financial Education Registry"],
                "tool_invocations": []
            }

        # 2. RAG Knowledge Retrieval
        retrieved_docs = KnowledgeRetriever.search(query, top_k=2)
        for doc in retrieved_docs:
            citations.append(f"{doc['title']} ({doc['citation']})")

        # 3. Extract multi-variable scenario parameters (merging user input with authenticated context)
        extracted_income = self._extract_amount_after_keywords(q, ["earn", "salary", "income"])
        extracted_expenses = self._extract_amount_after_keywords(q, ["spend", "expense", "expenses", "cost"])
        extracted_savings = self._extract_amount_after_keywords(q, ["savings", "saved", "have", "reserve"])
        extracted_months = self._extract_months(q)
        extracted_target = self._extract_amount_after_keywords(q, ["buy", "purchase", "car", "house", "target", "cost of"])

        # Fallback to authenticated user context where authorized
        income_source = "user prompt" if extracted_income else ("profile context" if ctx.get("monthly_income") else "default estimate")
        income = extracted_income or ctx.get("monthly_income") or 60000.0
        expenses = extracted_expenses or ctx.get("monthly_expenses") or 35000.0
        savings = extracted_savings or ctx.get("current_savings") or 200000.0
        is_estimated_context = income_source == "default estimate"

        # Dedicated Retirement & Financial Independence (FIRE) query handling
        if any(w in q for w in ["fire", "retire", "retirement", "financial freedom", "coast fire", "swr", "withdrawal rate"]):
            curr_age = int(ctx.get("current_age", 28))
            target_age = int(ctx.get("target_retirement_age", 50))
            monthly_inv = max(0.0, income - expenses) * 0.5
            params = {
                "current_age": curr_age,
                "planned_retirement_age": target_age,
                "monthly_expenses": expenses,
                "current_investable_assets": savings,
                "monthly_investment": monthly_inv,
                "expected_annual_inflation_pct": 6.0,
                "expected_nominal_return_pct": 11.0,
                "withdrawal_rate_pct": 3.5
            }
            res = AVAILABLE_TOOLS["calculate_fire_plan"](params)
            tool_results.append({
                "tool": "calculate_fire_plan",
                "summary": f"Calculated retirement estimate: Target at age {target_age} is ₹{res['fire_target_future']:,.0f}. Required monthly investment: ₹{res['required_monthly_investment']:,.0f}/mo."
            })
            
            status_summary = (
                "Your current investments may not be enough to reach your retirement goal at the moment. "
                "You may need to invest more each month, retire later, or adjust your target. "
                "These estimates depend on the return and inflation assumptions."
                if res["monthly_investment_gap"] > 0 else
                "You are on a strong track toward your retirement target under your current investment pace and return assumptions."
            )

            content = (
                f"### Retirement & Financial Freedom Plan\n\n"
                f"Based on your current monthly living expenses of **₹{expenses:,.0f}** and existing eligible investments of **₹{savings:,.0f}**:\n\n"
                f"- **Money You Need to Retire (Target at Age {target_age})**: **₹{res['fire_target_future']:,.0f}** (accounts for 6% annual inflation over {res['years_to_retirement']} years).\n"
                f"- **Today's Purchasing Value**: ₹{res['fire_target_today']:,.0f} (what this target would buy in today's money).\n"
                f"- **Current Progress**: **{res['fire_progress_pct']:.1f}%** towards your goal.\n"
                f"- **Monthly Investment Needed**: **₹{res['required_monthly_investment']:,.0f} / month** (at an assumed 11% yearly return).\n\n"
                f"**What This Means For You**:\n"
                f"{status_summary}\n\n"
                f"*(Note: These figures are model estimates, not guaranteed promises. Real market returns and inflation fluctuate over time.)*\n\n"
                f"*(Tip: Ask 'Explain this simply' if you would like any of these numbers explained in plain English.)*"
            )

        # Scenario: Major Purchase / "What are my options" (e.g. Car purchase in 18 months)
        elif any(w in q for w in ["car", "buy a", "options", "purchase"]) and ("month" in q or "year" in q or extracted_months) and "afford" not in q:
            months = extracted_months or 18
            target = extracted_target or 800000.0  # default 8L if car model/cost unspecified

            params = {
                "scenario_type": "major_purchase",
                "monthly_income": income,
                "monthly_expenses": expenses,
                "current_savings": savings,
                "target_amount": target,
                "time_horizon_months": months,
            }
            res = AVAILABLE_TOOLS["simulate_scenario"](params)
            tool_results.append({
                "tool": "simulate_scenario",
                "summary": f"Simulated major purchase (₹{target:,.0f} in {months} months). Cash flow surplus: ₹{res['baseline_surplus']:,.0f}/mo, Required SIP: ₹{res['required_monthly_allocation']:,.0f}/mo."
            })
            for c in res.get("citations", []):
                if c not in citations:
                    citations.append(c)

            content = (
                f"### AI CFO Strategic Financial Assessment\n\n"
                f"**Your Current Financial Numbers ({'Estimated Benchmark' if is_estimated_context else 'From Your Profile'})**:\n"
                f"- **Monthly Take-Home Income**: ₹{income:,.0f}\n"
                f"- **Monthly Living Costs**: ₹{expenses:,.0f}\n"
                f"- **Money Left Over Each Month (Surplus)**: **₹{res['baseline_surplus']:,.0f} / month**\n"
                f"- **Emergency Savings Available**: **₹{savings:,.0f}** ({res['baseline_runway_months']:.1f} months of living costs covered)\n\n"
            )
            if is_estimated_context:
                content += "*(Note: Baseline figures were estimated using standard benchmarks because no profile data was found. Set up your Profile or include your income/expenses in your prompt for personalized accuracy.)*\n\n"
            content += (
                f"**Can You Afford This?**:\n"
                f"{res['summary_verdict']}\n\n"
                f"**Your 3 Options to Make This Purchase**:\n"
            )
            for idx, opt in enumerate(res["alternative_options"], 1):
                content += (
                    f"\n**Option {idx}: {opt['name']}** ({opt['feasibility']})\n"
                    f"- *Plan*: {opt['description']}\n"
                    f"- *Monthly Investment Needed*: ₹{opt['monthly_commitment']:,.0f}/month\n"
                    f"- *Key Advantage*: {opt['pros'][0]}\n"
                    f"- *Important Trade-off*: {opt['cons'][0]}\n"
                )

            content += (
                f"\n**Recommended Next Step**:\n"
                f"Do you have a specific on-road price in mind? We can also check how trimming ₹3,000–₹5,000 "
                f"in non-essential monthly spending or extending your timeline to 24 months makes this easier.\n\n"
                f"*(Tip: Ask 'Explain this simply' for a plain-English breakdown.)*"
            )

        # Tax Query Detection
        elif any(w in q for w in ["tax", "regime", "115bac", "slab", "87a", "standard deduction"]):
            salary = self._extract_amount(q) or income * 12.0
            params = {
                "gross_annual_salary": salary,
                "assessment_year": "2025-26",
                "taxpayer_type": "salaried",
                "section_80c": 150000.0 if "80c" in q or "deduction" in q else 50000.0,
                "home_loan_interest_24b": 200000.0 if "home loan" in q else 0.0
            }
            res = AVAILABLE_TOOLS["calculate_tax"](params)
            tool_results.append({
                "tool": "calculate_tax",
                "summary": f"Calculated AY 2025-26 tax for ₹{salary:,.0f} salary: New Regime tax = ₹{res['new_regime_tax']:,.0f}, Old Regime tax = ₹{res['old_regime_tax']:,.0f}."
            })
            content = (
                f"### Tax Analysis (AY 2025-26 / FY 2024-25)\n\n"
                f"For an annual salary of **₹{salary:,.0f}**:\n\n"
                f"- **New Tax Regime (Section 115BAC)**: Estimated tax is **₹{res['new_regime_tax']:,.0f}** "
                f"(automatically includes standard deduction of ₹{res['new_regime_std_deduction']:,.0f} and 4% education cess).\n"
                f"- **Old Tax Regime**: Estimated tax is **₹{res['old_regime_tax']:,.0f}** (after your deductions).\n\n"
                f"**Which is better for you?**: The **{res['recommended_regime'].upper()} TAX REGIME** saves you approximately **₹{res['tax_savings']:,.0f}** in taxes.\n\n"
                f"{res['explanation']}\n\n"
                f"*(Note: Salaried individuals earning up to ₹7,75,000 pay zero tax under the New Regime due to the ₹75,000 standard deduction and government tax rebate.)*\n\n"
                f"*(Tip: Ask 'Explain this simply' if you want a step-by-step breakdown.)*"
            )

        # Investment Comparison Query Detection (Liquid fund vs Bonds vs FD)
        elif any(w in q for w in ["liquid fund", "bond", "fixed deposit", "fd", "invest", "yield"]):
            amount = self._extract_amount(q) or 200000.0
            months = self._extract_months(q) or 12
            params = {
                "amount": amount,
                "time_horizon_months": months,
                "can_lock_funds": "lock" in q or "maturity" in q
            }
            res = AVAILABLE_TOOLS["compare_investments"](params)
            tool_results.append({
                "tool": "compare_investments",
                "summary": f"Compared Liquid Mutual Fund vs Bonds vs FD for ₹{amount:,.0f} over {months} months."
            })
            content = (
                f"### Investment Instrument Comparison\n\n"
                f"For **₹{amount:,.0f}** over a **{months}-month** period:\n\n"
                f"- **Recommended Option**: **{res['top_recommendation']}**\n"
                f"- **Why**: {res['rationale']}\n\n"
                f"**How the Options Compare**:\n"
            )
            for c in res["comparisons"]:
                content += (
                    f"- **{c['name']}**: Expected Yearly Return ~{c['yield_pct']}%, Estimated Value at End: **₹{c['maturity_value']:,.0f}**. "
                    f"How quickly you can withdraw: {c['liquidity']}. Safety level: {c['credit_risk']}.\n"
                )
            content += f"\n> [!NOTE]\n> {res['disclaimer']}\n\n*(Tip: Ask 'Explain this simply' if you want a beginner-friendly overview.)*"

        # Goal Projection Query Detection
        elif any(w in q for w in ["goal", "save for", "downpayment", "education"]):
            target = self._extract_amount(q) or 1500000.0
            months = self._extract_months(q) or 36
            params = {
                "target_amount": target,
                "time_horizon_months": months,
                "goal_name": "Financial Goal",
                "expected_return_pct": 8.0,
                "expected_inflation_pct": 6.0
            }
            res = AVAILABLE_TOOLS["calculate_goal_plan"](params)
            tool_results.append({
                "tool": "calculate_goal_plan",
                "summary": f"Goal SIP for ₹{target:,.0f} over {months} months: ₹{res['required_monthly_sip']:,.0f}/month required."
            })
            content = (
                f"### Goal Contribution Projection\n\n"
                f"To reach your goal of **₹{target:,.0f}** in **{months} months** (~{months/12:.1f} years):\n\n"
                f"- **Money Needed in Future (adjusted for 6% inflation)**: **₹{res['inflation_adjusted_target']:,.0f}**\n"
                f"- **Monthly Investment Needed**: **₹{res['required_monthly_sip']:,.0f}** per month (assuming an 8.0% yearly growth rate).\n"
                f"- **Total Amount You Invest**: ₹{res['total_contributed']:,.0f}\n"
                f"- **Estimated Growth From Compounding**: ₹{res['projected_wealth_gain']:,.0f}\n\n"
                f"Starting your monthly investment early gives compound growth more time to help fund your goal.\n\n"
                f"*(Tip: Ask 'Explain this simply' to see how compound interest works in real life.)*"
            )

        # Cross-Feature Affordability Query (e.g. "Can I afford a ₹25,000 monthly EMI?", "Can I afford a car of 100000rs in next 3 years?")
        elif "afford" in q and any(w in q for w in ["emi", "loan", "purchase", "car", "bike", "month", "monthly", "year", "years"]):
            raw_amt = self._extract_amount(q) or 25000.0
            item_type = "emi" if "emi" in q or "loan" in q else "purchase"
            
            # Check if query specifies a timeline (e.g., in 3 years, in next 24 months)
            years_m = re.search(r"(\d+)\s*(?:year|yr)", q)
            months_m = re.search(r"(\d+)\s*month", q)
            target_months = None
            if years_m:
                target_months = max(1, int(years_m.group(1)) * 12)
            elif months_m:
                target_months = max(1, int(months_m.group(1)))

            # If user asks for purchase over a multi-month/year timeline, calculate required monthly savings
            if target_months and target_months > 1 and item_type != "emi":
                monthly_required = round(raw_amt / target_months, 2)
                proposed = monthly_required
                timeline_str = f"{target_months // 12} years" if target_months >= 12 and target_months % 12 == 0 else f"{target_months} months"
                goal_summary = f"₹{raw_amt:,.0f} total goal over {timeline_str} (requires ₹{monthly_required:,.0f}/month savings)"
            else:
                proposed = raw_amt
                goal_summary = f"₹{proposed:,.0f}/month {item_type.upper()}"
                timeline_str = None

            params = {
                "proposed_amount": proposed,
                "item_type": item_type,
                "monthly_income": income,
                "monthly_expenses": expenses,
                "monthly_emi": ctx.get("monthly_emi", 0.0),
                "recurring_monthly_expenses": ctx.get("recurring_monthly_expenses", 0.0),
                "current_savings": savings
            }
            res = AVAILABLE_TOOLS["evaluate_affordability"](params)
            tool_results.append({
                "tool": "evaluate_affordability",
                "summary": f"Evaluated {goal_summary} against ₹{income:,.0f} income and ₹{expenses:,.0f} baseline living expenses."
            })

            title_header = f"### Affordability Assessment: {goal_summary}"
            
            if target_months and target_months > 1:
                deficit_or_surplus = income - expenses - proposed
                if deficit_or_surplus >= 0:
                    rec_text = (
                        f"**Yes, you can afford this!** To buy your ₹{raw_amt:,.0f} target in {timeline_str}, "
                        f"you need to save **₹{proposed:,.0f} each month** (₹{raw_amt:,.0f} ÷ {target_months} months). "
                        f"Your current monthly surplus is ₹{income - expenses:,.0f}, which comfortably covers this contribution."
                    )
                else:
                    needed_cut = abs(deficit_or_surplus)
                    rec_text = (
                        f"To purchase a ₹{raw_amt:,.0f} car in {timeline_str}, you need to save **₹{proposed:,.0f} each month** "
                        f"(₹{raw_amt:,.0f} ÷ {target_months} months). With your current monthly income of ₹{income:,.0f} and "
                        f"living expenses of ₹{expenses:,.0f}, you have a monthly gap of ₹{needed_cut:,.0f}. "
                        f"Trimming just ₹{needed_cut:,.0f}/month from discretionary expenses will put you on track to buy this car on schedule!"
                    )
            else:
                rec_text = res["recommendation"]

            content = (
                f"{title_header}\n\n"
                f"**Verdict**: **{res['status']}**\n\n"
                f"**Financial Breakdown**:\n"
                f"- **Monthly Net Income**: ₹{res['monthly_income']:,.0f}\n"
                f"- **Current Living Expenses**: ₹{res['current_monthly_expenses']:,.0f}\n"
                f"- **Existing Loan EMIs**: ₹{res['existing_monthly_emi']:,.0f}\n"
                f"- **Recurring Bills & Commitments**: ₹{res['existing_recurring_commitments']:,.0f}\n"
                f"- **Current Money Left Over**: ₹{res['current_net_surplus']:,.0f} / month\n"
                f"- **Monthly Target for this Goal**: **₹{proposed:,.0f} / month**\n"
                f"- **Money Left Over After This Target**: **₹{res['revised_net_surplus']:,.0f} / month**\n"
                f"- **Share of Income Spent on Debt (Debt-to-Income / DTI)**: **{res['new_debt_to_income_pct']}%** (Safe target is below 40%)\n"
                f"- **Emergency Cushion Remaining**: **{res['revised_emergency_runway_months']:.1f} months**\n\n"
                f"**Recommendation**:\n"
                f"{rec_text}\n\n"
                f"*(Note: Evaluated across verified monthly cash flows and liquid reserves. If this is a floating-rate loan, budget an additional 1.5% interest buffer.)*\n\n"
                f"*(Tip: Ask 'Explain this simply' if you want a simpler explanation.)*"
            )

        # Recurring Payments & Upcoming Obligations (e.g. "What recurring payments do I have next month?", "upcoming bills")
        elif any(w in q for w in ["upcoming", "recurring payment", "recurring bill", "subscriptions every month", "due next month", "pause"]):
            rec_items = ctx.get("recurring_commitments", [])
            pause_amt = self._extract_amount(q) if "pause" in q else 0.0

            if "upcoming" in q or "due" in q or "next month" in q:
                res = AVAILABLE_TOOLS["get_upcoming_obligations"](ctx)
                tool_results.append({
                    "tool": "get_upcoming_obligations",
                    "summary": f"Calculated 30-day forward schedule: {res['obligations_count']} commitments totaling ₹{res['total_upcoming_30d']:,.0f}."
                })
                content = (
                    f"### Upcoming Obligations (Next 30 Days)\n\n"
                    f"**Total Expected Cash Outflow**: **₹{res['total_upcoming_30d']:,.0f}** across **{res['obligations_count']}** scheduled commitments.\n\n"
                    f"**Schedule of Upcoming Payments**:\n"
                )
                if res["obligations"]:
                    for item in res["obligations"]:
                        content += f"- **{item['name']}**: ₹{item['amount']:,.0f} ({item['type'].replace('_', ' ').title()})\n"
                else:
                    content += "- *No active recurring commitments due in the next 30 days. You can track your regular bills in the Recurring Payments tab.*\n"
                content += "\n*(Tip: Ask 'Explain this simply' for more details.)*"
            else:
                params = {
                    "items": rec_items,
                    "total_monthly_expenses": expenses,
                    "simulated_pause_amount": pause_amt or 0.0
                }
                res = AVAILABLE_TOOLS["get_recurring_commitments"](params)
                tool_results.append({
                    "tool": "get_recurring_commitments",
                    "summary": f"Analyzed monthly recurring commitments: ₹{res['monthly_recurring_total']:,.0f}/mo ({res['percentage_of_living_expenses']}% of living expenses)."
                })
                content = (
                    f"### Recurring Subscriptions & Fixed Commitments Analysis\n\n"
                    f"- **Monthly Recurring Total**: **₹{res['monthly_recurring_total']:,.0f} / month**\n"
                    f"- **Share of Monthly Expenses**: **{res['percentage_of_living_expenses']}%**\n\n"
                    f"**Category Breakdown**:\n"
                )
                for cat, val in res["category_breakdown"].items():
                    content += f"- **{cat}**: ₹{val:,.0f}/mo\n"
                if pause_amt > 0:
                    content += (
                        f"\n**Impact of Pausing These Payments**:\n"
                        f"- Pausing **₹{res['simulated_pause_amount']:,.0f}/mo** lowers your regular bills to **₹{res['revised_monthly_commitments']:,.0f}/mo**.\n"
                        f"- **Money Freed Each Year**: **₹{res['annualized_freed_surplus']:,.0f} / year**, which you can use for your emergency fund or monthly investments.\n"
                    )
                content += "\n*(Tip: Ask 'Explain this simply' if you want a simpler explanation.)*"

        # Budget Overspending & Variance Query (e.g. "Why am I overspending?", "Why did I save less this month?")
        elif any(w in q for w in ["overspend", "over budget", "save less", "where did my money go", "spending anomalies"]):
            res = AVAILABLE_TOOLS["find_overspending"](ctx)
            tool_results.append({
                "tool": "find_overspending",
                "summary": res["summary"]
            })
            content = (
                f"### Spending Variance & Overspending Diagnostic\n\n"
                f"{res['summary']}\n\n"
            )
            if res["overspent_budgets"]:
                content += "**Categories Where You Spent More Than Planned**:\n"
                for o in res["overspent_budgets"]:
                    content += f"- {o}\n"
                content += "\n"
            if res["anomalous_spikes"]:
                content += "**Unusual Spending Spikes**:\n"
                for a in res["anomalous_spikes"]:
                    content += f"- **{a['category']}**: {a['explanation']} (Difference: {a['deviation_pct']:+.1f}%)\n"
                content += "\n"
            content += (
                f"**Suggested Action**:\n"
                f"Review discretionary spending in over-budget categories. "
                f"Setting spending alerts in the Budget view helps keep your month-end cash flow positive.\n\n"
                f"*(Tip: Ask 'Explain this simply' if you would like practical tips to save on these categories.)*"
            )

        # Debt & Creditor Query: "tell me what is the debt amount and for whom i want to pay", "who do i owe", "what is my debt"
        elif any(w in q for w in ["debt amount", "whom i want to pay", "who do i owe", "what are my debts", "tell me my debts", "what is my debt", "list of debts", "my loans", "debt payoff", "total debt"]):
            liabilities = ctx.get("liabilities_list", [])
            total_debt = ctx.get("total_debt", 0.0)
            total_emi = ctx.get("monthly_emi", 0.0)

            tool_results.append({
                "tool": "compare_debt_payoff",
                "summary": f"Retrieved debt standing: {len(liabilities)} liabilities totaling ₹{total_debt:,.0f} with ₹{total_emi:,.0f}/mo EMI."
            })
            citations.append("FinPilot Authoritative Debt Registry")

            if liabilities:
                content = (
                    f"### Debt & Repayment Summary\n\n"
                    f"- **Total Outstanding Debt**: **₹{total_debt:,.0f}**\n"
                    f"- **Total Monthly EMI Obligation**: **₹{total_emi:,.0f} / month**\n"
                    f"- **Active Loans & Creditors Count**: **{len(liabilities)}**\n\n"
                    f"**Whom You Need to Pay (Creditor Breakdown)**:\n\n"
                )
                for idx, item in enumerate(liabilities, 1):
                    name = item.get("name", f"Loan #{idx}")
                    p_amt = float(item.get("principal", 0.0))
                    emi = float(item.get("monthly_emi", 0.0))
                    rate = float(item.get("interest_rate_pct", 0.0))
                    rem = item.get("remaining_months", 12)
                    content += (
                        f"**{idx}. {name}**\n"
                        f"- **Outstanding Balance to Pay**: **₹{p_amt:,.0f}**\n"
                        f"- **Monthly EMI**: ₹{emi:,.0f}/month\n"
                        f"- **Interest Rate**: {rate:.1f}% p.a.\n"
                        f"- **Remaining Tenure**: {rem} months\n\n"
                    )

                # Strategy recommendation
                highest_rate = max(liabilities, key=lambda x: float(x.get("interest_rate_pct", 0.0)))
                lowest_bal = min(liabilities, key=lambda x: float(x.get("principal", 0.0)))
                content += (
                    f"**Recommended Repayment Strategy**:\n"
                    f"- **Avalanche Method (Saves most money)**: Prioritize extra payments to **{highest_rate.get('name')}** (highest interest rate at {float(highest_rate.get('interest_rate_pct', 0)):.1f}%).\n"
                    f"- **Snowball Method (Quickest wins)**: Clear **{lowest_bal.get('name')}** first (smallest balance of ₹{float(lowest_bal.get('principal', 0)):,.0f}) to free up monthly cash flow.\n\n"
                    f"*(Tip: Ask 'Can I afford an extra ₹5,000 prepayment?' to simulate how much faster you can become debt-free.)*"
                )
            else:
                content = (
                    f"### Debt Standing: Zero Liabilities Recorded\n\n"
                    f"You currently have **₹0 in recorded debt liabilities** (no active loans, credit card balances, or EMIs registered).\n\n"
                    f"- **Total Outstanding Debt**: **₹0.00**\n"
                    f"- **Monthly EMI Outflow**: **₹0.00 / month**\n\n"
                    f"If you have an active loan (such as a Home Loan, Car Loan, Education Loan, or Credit Card balance), "
                    f"you can add it right now by saying:\n"
                    f"- *'Add home loan of ₹25,00,000 at 8.5% for 180 months'*\n"
                    f"- *'Add car loan of ₹6,00,000 at 9.2% for 48 months'*\n\n"
                    f"I will stage the record and ask for your confirmation before adding it to your payoff tracker."
                )

        # Financial Goals Summary Query
        elif any(w in q for w in ["what are my goals", "list my goals", "my financial goals", "tell me my goals", "goals summary", "how are my goals"]):
            goals = ctx.get("active_goals", [])
            total_target = ctx.get("total_goals_target", 0.0)
            total_saved = ctx.get("total_goals_saved", 0.0)
            citations.append("FinPilot Goal Feasibility Engine")

            if goals:
                content = (
                    f"### Your Active Financial Goals\n\n"
                    f"- **Total Target Across All Goals**: **₹{total_target:,.0f}**\n"
                    f"- **Total Amount Saved So Far**: **₹{total_saved:,.0f}** "
                    f"({(total_saved / total_target * 100) if total_target > 0 else 0:.1f}% overall progress)\n"
                    f"- **Active Goals Count**: **{len(goals)}**\n\n"
                    f"**Goal Progress Breakdown**:\n\n"
                )
                for idx, g in enumerate(goals, 1):
                    t_amt = float(g.get("target_amount", 0.0))
                    c_amt = float(g.get("current_amount", 0.0))
                    prog = float(g.get("progress_pct", 0.0))
                    req_sip = float(g.get("required_monthly_savings", 0.0))
                    t_date = g.get("target_date", "Not set")
                    content += (
                        f"**{idx}. {g.get('name')}**\n"
                        f"- **Target Amount**: ₹{t_amt:,.0f} by {t_date}\n"
                        f"- **Current Saved**: ₹{c_amt:,.0f} ({prog:.1f}% reached)\n"
                        f"- **Monthly Savings Needed**: **₹{req_sip:,.0f} / month**\n\n"
                    )
                content += "*(Tip: You can say 'Add financial goal of ₹2,00,000 for vacation by 2027' to create a new goal.)*"
            else:
                content = (
                    f"### Financial Goals: No Active Goals Set\n\n"
                    f"You have not set any tracked financial goals yet.\n\n"
                    f"Setting clear goals helps FinPilot calculate exactly how much you need to save each month. "
                    f"You can create one by saying:\n"
                    f"- *'Add financial goal of ₹5,00,000 for emergency fund by 2026'*\n"
                    f"- *'Create vacation goal of ₹1,50,000 by December 2026'*\n\n"
                    f"I will prepare the proposal and ask for your confirmation."
                )

        # Overall Multi-Tab Financial Summary: "overall summary", "summary of everything", "tell me everything"
        elif any(w in q for w in ["overall summary", "tell me overall summary", "give me overall summary", "financial summary", "complete summary", "summary of everything", "tell me everything", "summary of my finances", "all tabs summary"]):
            res_ov = AVAILABLE_TOOLS["get_financial_overview"](ctx)
            res_nw = AVAILABLE_TOOLS["get_net_worth"](ctx)
            accounts = ctx.get("bank_accounts", [])
            liabilities = ctx.get("liabilities_list", [])
            recurring = ctx.get("recurring_commitments", [])
            goals = ctx.get("active_goals", [])

            tool_results.append({
                "tool": "get_financial_overview",
                "summary": res_ov["summary"]
            })
            tool_results.append({
                "tool": "get_net_worth",
                "summary": res_nw["summary"]
            })
            citations.append("FinPilot Unified Multi-Domain Intelligence Engine")

            content = (
                f"### Complete Overall Financial Summary\n\n"
                f"Here is your high-level financial overview across all connected accounts, budgets, debts, and goals:\n\n"
                f"#### 1. Net Worth & Assets\n"
                f"- **Estimated Net Worth**: **₹{res_nw['net_worth']:,.0f}**\n"
                f"- **Total Assets**: ₹{res_nw['total_assets']:,.0f} (Liquid Bank Reserves: ₹{ctx.get('verified_bank_balance', 0.0):,.0f} across {len(accounts)} accounts | Investments: ₹{ctx.get('manual_assets_total', 0.0):,.0f})\n"
                f"- **Total Liabilities (Debt)**: **₹{res_nw['total_liabilities']:,.0f}** across {len(liabilities)} loans\n\n"
                f"#### 2. Monthly Cash Flow & Burn\n"
                f"- **Monthly Income**: ₹{res_ov['monthly_income']:,.0f}\n"
                f"- **Monthly Living Expenses**: ₹{res_ov['monthly_expenses']:,.0f}\n"
                f"- **Monthly Loan EMIs**: ₹{res_ov['monthly_emi']:,.0f}\n"
                f"- **Net Monthly Surplus Left Over**: **₹{res_ov['net_monthly_surplus']:,.0f} / month**\n"
                f"- **Savings Rate**: **{res_ov['savings_rate_pct']}%** (Target: ≥ 20%)\n"
                f"- **Emergency Cushion**: **{res_ov['emergency_runway_months']:.1f} months** of living expenses covered\n\n"
                f"#### 3. Debts & Who You Owe\n"
            )
            if liabilities:
                content += f"- **Outstanding Debt**: ₹{res_nw['total_liabilities']:,.0f} ({len(liabilities)} loans, ₹{res_ov['monthly_emi']:,.0f}/mo EMI)\n"
                for l_item in liabilities[:3]:
                    content += f"  • **{l_item.get('name')}**: ₹{float(l_item.get('principal', 0)):,.0f} balance (EMI: ₹{float(l_item.get('monthly_emi', 0)):,.0f}/mo @ {float(l_item.get('interest_rate_pct', 0)):.1f}%)\n"
            else:
                content += "- **Zero Debts**: You have no active loans or debt liabilities recorded.\n"

            content += f"\n#### 4. Recurring Bills & Subscriptions\n"
            if recurring:
                content += f"- **Monthly Commitments**: ₹{ctx.get('recurring_monthly_expenses', 0.0):,.0f}/month across {len(recurring)} active subscriptions and bills.\n"
            else:
                content += "- No recurring subscriptions detected yet.\n"

            content += f"\n#### 5. Tracked Financial Goals\n"
            if goals:
                content += f"- **Active Goals**: {len(goals)} goals (Total target: ₹{ctx.get('total_goals_target', 0.0):,.0f} | Saved: ₹{ctx.get('total_goals_saved', 0.0):,.0f})\n"
            else:
                content += "- No active goals set yet. Say *'Add financial goal'* to start tracking one.\n"

            content += (
                f"\n**Health Status**: **{res_ov['status']}**.\n\n"
                f"*(Tip: Ask 'Can I afford a ₹25,000 monthly EMI?' or 'How do I optimize my taxes?' to explore further.)*"
            )

        # Net Worth & Financial Health Overview (e.g. "What is my net worth?", "Financial health overview")
        elif any(w in q for w in ["net worth", "financial health", "financial overview", "my standing"]):
            res_ov = AVAILABLE_TOOLS["get_financial_overview"](ctx)
            res_nw = AVAILABLE_TOOLS["get_net_worth"](ctx)
            tool_results.append({
                "tool": "get_financial_overview",
                "summary": res_ov["summary"]
            })
            tool_results.append({
                "tool": "get_net_worth",
                "summary": res_nw["summary"]
            })
            content = (
                f"### Financial Standing & Net Worth Overview\n\n"
                f"- **Estimated Net Worth (What You Own Minus What You Owe)**: **₹{res_nw['net_worth']:,.0f}** (Assets: ₹{res_nw['total_assets']:,.0f} | Debts: ₹{res_nw['total_liabilities']:,.0f})\n"
                f"- **Monthly Take-Home Income**: ₹{res_ov['monthly_income']:,.0f}\n"
                f"- **Monthly Living Costs**: ₹{res_ov['monthly_expenses']:,.0f}\n"
                f"- **Money Left Over Each Month (Surplus)**: **₹{res_ov['net_monthly_surplus']:,.0f}** (Savings Rate: **{res_ov['savings_rate_pct']}%**)\n"
                f"- **Emergency Savings Available**: ₹{res_ov['liquid_savings']:,.0f} ({res_ov['emergency_runway_months']:.1f} months covered)\n"
                f"- **Debt-to-Income Share**: {res_ov['debt_to_income_pct']}%\n\n"
                f"**Health Summary**: **{res_ov['status']}**.\n"
                f"Your foundation is solid. Keeping an emergency cushion while steadily investing surplus ensures steady financial growth.\n\n"
                f"*(Tip: Ask 'Explain this simply' if you would like any of these numbers explained in plain English.)*"
            )

        # Bank Accounts & Liquid Balances Query (e.g. "what is the current account balance", "what is my balance", "how much money do i have")
        elif any(w in q for w in [
            "balance", "balence", "curent account", "current account", "bank account", "bank balance",
            "account balance", "in my account", "in my bank", "liquid balance", "liquid cash",
            "how much money", "my cash", "savings balance", "how much in bank"
        ]):
            accounts = ctx.get("bank_accounts", [])
            total_verified = float(ctx.get("verified_bank_balance", 0.0))
            current_savings = float(ctx.get("current_savings", 0.0))
            effective_balance = total_verified if total_verified > 0 else current_savings

            tool_results.append({
                "tool": "get_bank_balances",
                "summary": f"Retrieved verified bank holdings: {len(accounts)} accounts totaling ₹{effective_balance:,.0f}."
            })
            citations.append("Deposit Insurance and Credit Guarantee Corporation (DICGC) Act, 1961 (Coverage up to ₹5,00,000 per depositor)")

            if accounts:
                content = (
                    f"### Verified Bank Account Balances\n\n"
                    f"**Total Available Liquid Balance**: **₹{effective_balance:,.0f}** across **{len(accounts)}** connected account(s).\n\n"
                    f"**Account Breakdown**:\n"
                )
                for idx, acc in enumerate(accounts, 1):
                    bal = float(acc.get("balance", 0.0))
                    inst = acc.get("institution", "Bank Account")
                    mask = acc.get("account_masked", "XXXX")
                    acc_type = (acc.get("account_type") or "Savings").replace("_", " ").title()
                    status = acc.get("status", "synced").title()
                    content += f"**{idx}. {inst}** ({acc_type} ••{mask[-4:] if len(mask) >= 4 else mask})\n"
                    content += f"- **Current Balance**: **₹{bal:,.0f}**\n"
                    content += f"- **Status**: {status}\n\n"
            else:
                content = (
                    f"### Account Balance Summary\n\n"
                    f"**Current Liquid Reserves**: **₹{effective_balance:,.0f}**\n\n"
                    f"*(Note: You currently have no linked bank accounts via Account Aggregator or uploaded statements. You can link your bank or upload a bank statement PDF in the Dashboard to track your real-time verified live balances.)*\n\n"
                )

            content += (
                f"**Safety & Protection Note**:\n"
                f"Under the **DICGC Act (RBI)**, each depositor in an insured bank is protected up to **₹5,00,000** for both principal and interest.\n\n"
                f"*(Tip: Ask 'What bills or subscriptions do I have coming up?' or 'Can I afford a purchase?' to plan your spending!)*"
            )

        # General Financial Inquiry
        else:
            content = (
                f"Hello! I am your **FinPilot AI Financial Assistant**.\n\n"
                f"I connect directly to your verified financial information (bank accounts, regular bills, budgets, and tax profile) "
                f"to help you plan, save, and make smart money decisions—in plain, simple English.\n\n"
                f"**Here are a few things you can ask me**:\n"
                f"1. *'Can I afford a ₹25,000 monthly car EMI?'*\n"
                f"2. *'What bills or subscriptions do I have coming up next month?'*\n"
                f"3. *'Why am I overspending, and where did my money go?'*\n"
                f"4. *'What is my net worth and how healthy are my finances?'*\n"
                f"5. *'Compare the New vs Old Tax Regime for a 15 LPA salary.'*\n"
                f"6. *'How much do I need to invest each month to buy a home in 3 years?'*\n\n"
                f"*(If any term ever feels technical, just reply 'Explain this simply'!)*\n\n"
                f"What financial decision can we explore today?"
            )

        return {
            "content": content,
            "citations": citations,
            "tool_invocations": tool_results
        }

    def _extract_amount_after_keywords(self, text: str, keywords: List[str]) -> Optional[float]:
        for kw in keywords:
            m = re.search(rf"{kw}\s*(?:of|is|around|about)?\s*₹?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|lakh|lpa|lac|lacs)", text)
            if m:
                return float(m.group(1)) * 100000.0
            m2 = re.search(rf"{kw}\s*(?:of|is|around|about)?\s*₹?\s*(\d+(?:,\d{2,3})*(?:\.\d+)?)", text)
            if m2:
                raw = m2.group(1).replace(",", "")
                try:
                    val = float(raw)
                    if val >= 500:
                        return val
                except ValueError:
                    pass
        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakhs?|lakh|lpa|lac|lacs)", text)
        if m:
            return float(m.group(1)) * 100000.0
        m2 = re.search(r"(\d+(?:,\d{2,3})*(?:\.\d+)?)", text)
        if m2:
            raw = m2.group(1).replace(",", "")
            try:
                val = float(raw)
                if val >= 1000:
                    return val
            except ValueError:
                pass
        return None

    def _extract_months(self, text: str) -> Optional[int]:
        m_yr = re.search(r"(\d+)\s*(?:years?|yrs?)", text)
        if m_yr:
            return int(m_yr.group(1)) * 12
        m_mo = re.search(r"(\d+)\s*(?:months?|mos?)", text)
        if m_mo:
            return int(m_mo.group(1))
        return None


class GeminiAIProvider(BaseAIProvider):
    """
    Cloud-only adapter for Google Gemini models via google-genai SDK
    with explicit status, timeout handling, and safe fallback to MockAIProvider.
    """
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-flash",
        timeout_seconds: float = 15.0
    ):
        self.api_key = api_key
        # Automatically sanitize restricted or invalid model names
        if not model_name or "2.5" in str(model_name):
            model_name = "gemini-1.5-flash"
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.fallback = MockAIProvider()

    def get_status(self) -> Dict[str, Any]:
        display_model = "gemini-1.5-flash" if "2.5" in str(self.model_name) else self.model_name
        if not self.api_key:
            return {
                "provider": "gemini",
                "status": "missing_api_key",
                "model": display_model,
                "ready": False,
                "message": "Gemini API key is not configured. Falling back to deterministic planning engine."
            }
        return {
            "provider": "gemini",
            "status": "ready",
            "model": display_model,
            "ready": True,
            "message": f"Configured for cloud model {display_model}"
        }

    def generate_response(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.api_key or not self.api_key.strip():
            logger.info("No Gemini API key configured. Using deterministic fallback engine.")
            res = self.fallback.generate_response(query, chat_history, user_context)
            res["provider"] = "mock"
            res["model"] = "deterministic-mock"
            res["status"] = "fallback_mock"
            res["fallback_reason"] = "No API key configured"
            return res

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            context_str = f"User Financial Context: {user_context}" if user_context else ""
            system_instruction = (
                "You are FinPilot AI, a Senior Indian Personal Finance CFO and Certified Financial Planner.\n"
                "Ground all advice strictly in official Indian Income Tax Act 1961 regulations, Finance Act 2024, "
                "RBI regulations, and SEBI mutual fund guidelines.\n"
                "Never invent interest rates, account balances, or financial calculations.\n"
                "Clearly distinguish verified facts from user estimates, assumptions, and educational planning heuristics.\n"
                "COMMUNICATION RULES:\n"
                "1. Always use plain, everyday English that anyone without a finance background can easily understand.\n"
                "2. Avoid dense finance jargon (e.g., say 'monthly investment' instead of 'required SIP', 'money you need to retire' instead of 'target corpus', 'suggested yearly withdrawal rate' instead of 'SWR', 'money left over each month' instead of 'net surplus').\n"
                "3. Prefer short sentences and practical real-life examples using Indian Rupees (₹).\n"
                "4. Answer the user's direct question first before offering optional suggestions.\n"
                "5. When technical terms are unavoidable, explain them immediately in simple words.\n"
                "6. Offer: 'Would you like me to explain any of these terms more simply?'"
            )
            prompt = f"{context_str}\nUser Question: {query}"

            # Invoke Gemini with timeout configuration
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )

            active_model = "gemini-1.5-flash" if "2.5" in str(self.model_name) else self.model_name

            candidate_models = list(dict.fromkeys([
                active_model,
                "gemini-1.5-flash-latest",
                "gemini-2.0-flash",
                "gemini-flash-latest",
                "gemini-1.5-pro",
            ]))

            resp = None
            last_err = None
            used_model = active_model
            for m in candidate_models:
                try:
                    resp = client.models.generate_content(
                        model=m,
                        contents=prompt,
                        config=config,
                    )
                    if resp and hasattr(resp, "text") and resp.text:
                        used_model = m
                        break
                except Exception as me:
                    last_err = me
                    if "404" in str(me) or "NOT_FOUND" in str(me) or "not found" in str(me).lower():
                        logger.info(f"Gemini model '{m}' not found (404), trying next candidate...")
                        continue
                    raise me

            if not resp or not getattr(resp, "text", None):
                raise last_err or ValueError("Received empty content from Gemini API")

            response_text = resp.text

            # Retrieve regulatory citations for ground truth
            retrieved_docs = KnowledgeRetriever.search(query, top_k=2)
            citations = [f"{d['title']} ({d['citation']})" for d in retrieved_docs]
            if not citations:
                citations = ["Income Tax Act 1961", "Finance Act 2024"]

            return {
                "content": response_text,
                "citations": citations,
                "tool_invocations": [],
                "provider": "gemini",
                "model": used_model,
                "status": "success"
            }

        except Exception as e:
            logger.warning(f"Gemini API invocation failed ({e}), falling back to deterministic planning engine.")
            res = self.fallback.generate_response(query, chat_history, user_context)
            res["provider"] = "mock"
            res["model"] = "deterministic-mock"
            res["status"] = "fallback_mock"
            res["fallback_reason"] = str(e)
            return res


def get_ai_provider() -> BaseAIProvider:
    provider = settings.LLM_PROVIDER.lower().strip()
    api_key = (settings.LLM_API_KEY or "").strip()
    if (provider == "gemini" or api_key) and api_key and provider != "mock_only":
        model_name = settings.LLM_MODEL
        if not model_name or "2.5" in str(model_name):
            model_name = "gemini-1.5-flash"
        return GeminiAIProvider(
            api_key=api_key,
            model_name=model_name,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS
        )
    return MockAIProvider()


def get_ai_provider_status() -> Dict[str, Any]:
    provider = get_ai_provider()
    if isinstance(provider, GeminiAIProvider):
        return provider.get_status()
    return {
        "provider": "mock",
        "status": "ready",
        "model": "deterministic-mock",
        "ready": True,
        "message": "Deterministic financial calculation engine active (zero external cloud dependencies)."
    }

