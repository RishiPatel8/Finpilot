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
                    "I operate strictly within authorized personal finance planning guidelines, Indian Income Tax Act rules, and SEBI/RBI statutory regulations. "
                    "How can I help you analyze your budget, optimize your taxes, compare investment instruments, or simulate a financial purchase today?"
                ),
                "citations": ["FinPilot AI Security & Grounding Policy"],
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

        # Scenario: Major Purchase / "What are my options" (e.g. Car purchase in 18 months)
        if any(w in q for w in ["car", "buy a", "options", "purchase", "afford"]) and ("month" in q or "year" in q or extracted_months):
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
                f"**Baseline Financial Diagnostics ({'Estimated Benchmark' if is_estimated_context else 'Authenticated Profile Context'})**:\n"
                f"- **Monthly Net Income**: ₹{income:,.0f}\n"
                f"- **Monthly Living Expenses**: ₹{expenses:,.0f}\n"
                f"- **Current Net Monthly Surplus**: **₹{res['baseline_surplus']:,.0f} / month**\n"
                f"- **Existing Liquid Savings**: **₹{savings:,.0f}** ({res['baseline_runway_months']:.1f} months essential runway)\n\n"
            )
            if is_estimated_context:
                content += "*(Note: Baseline figures were estimated using standard benchmarks because no profile data was found. Set up your Profile or include your income/expenses in your prompt for personalized accuracy.)*\n\n"
            content += (
                f"**Direct Feasibility Assessment**:\n"
                f"{res['summary_verdict']}\n\n"
                f"**Your 3 Strategic Options**:\n"
            )
            for idx, opt in enumerate(res["alternative_options"], 1):
                content += (
                    f"\n**Option {idx}: {opt['name']}** ({opt['feasibility']})\n"
                    f"- *Plan*: {opt['description']}\n"
                    f"- *Monthly Commitment*: ₹{opt['monthly_commitment']:,.0f}/month\n"
                    f"- *Advantage*: {opt['pros'][0]}\n"
                    f"- *Trade-off*: {opt['cons'][0]}\n"
                )

            content += (
                f"\n**CFO Next Step Recommendation**:\n"
                f"Do you have a specific on-road price or model in mind? We can also simulate how "
                f"trimming ₹3,000–₹5,000 in monthly lifestyle spending or extending your horizon to 24 months affects this purchase."
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
                f"(includes standard deduction of ₹{res['new_regime_std_deduction']:,.0f} and 4% cess).\n"
                f"- **Old Tax Regime**: Estimated tax is **₹{res['old_regime_tax']:,.0f}**.\n\n"
                f"**Recommendation**: **{res['recommended_regime'].upper()} TAX REGIME** is more beneficial, saving you **₹{res['tax_savings']:,.0f}**.\n\n"
                f"{res['explanation']}\n\n"
                f"*(Note: Salaried individuals earning up to ₹7,75,000 pay zero tax under the New Regime due to the ₹75,000 standard deduction and Section 87A rebate.)*"
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
                f"For **₹{amount:,.0f}** over a **{months}-month** time horizon:\n\n"
                f"- **Top Recommendation**: **{res['top_recommendation']}**\n"
                f"- **Rationale**: {res['rationale']}\n\n"
                f"**Key Comparisons**:\n"
            )
            for c in res["comparisons"]:
                content += (
                    f"- **{c['name']}**: Indicative Yield ~{c['yield_pct']}%, Projected Maturity Value: **₹{c['maturity_value']:,.0f}**. "
                    f"Liquidity: {c['liquidity']}. Risk: {c['credit_risk']}.\n"
                )
            content += f"\n> [!NOTE]\n> {res['disclaimer']}"

        # Goal Projection Query Detection
        elif any(w in q for w in ["goal", "save for", "downpayment", "education", "retirement"]):
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
                f"- **Inflation-Adjusted Target (at 6% inflation)**: **₹{res['inflation_adjusted_target']:,.0f}**\n"
                f"- **Required Monthly SIP**: **₹{res['required_monthly_sip']:,.0f}** per month (assuming an 8.0% annual growth rate).\n"
                f"- **Total Capital You Invest**: ₹{res['total_contributed']:,.0f}\n"
                f"- **Estimated Wealth Gain / Compounding**: ₹{res['projected_wealth_gain']:,.0f}\n\n"
                f"Starting your systematic investment early allows compound interest to fund a significant portion of your target."
            )

        # Budget / Emergency Fund Query
        elif any(w in q for w in ["emergency", "budget", "runway", "surplus", "savings rate"]):
            params = {
                "monthly_income": income,
                "monthly_expenses": expenses,
                "emergency_fund_current": savings
            }
            res = AVAILABLE_TOOLS["analyze_budget"](params)
            tool_results.append({
                "tool": "analyze_budget",
                "summary": "Analyzed emergency reserve runway and monthly cash flow."
            })
            content = (
                f"### Cash Flow & Emergency Fund Runway\n\n"
                f"- **Monthly Surplus**: ₹{res['monthly_surplus']:,.0f} (Savings Rate: **{res['savings_rate_pct']}%**)\n"
                f"- **Emergency Reserve**: Currently covers **{res['emergency_fund_months_covered']} months** of essential expenses.\n"
                f"- **Target (6 Months Runway)**: **₹{res['emergency_fund_target']:,.0f}**.\n\n"
                f"**Recommendation**: We recommend maintaining at least 6 months of mandatory living expenses in high-liquidity instruments "
                f"(such as Liquid Mutual Funds or sweep-in FDs) before committing surplus cash to long-term equity or lock-in bonds."
            )

        # General Financial Inquiry
        else:
            content = (
                f"Hello! I am your **Connected AI CFO** on FinPilot.\n\n"
                f"I connect directly to your verified financial context (income, expenses, emergency reserve, and tax profile) "
                f"to run scenario simulations and give grounded financial advice.\n\n"
                f"**Try asking questions like**:\n"
                f"1. *'I earn ₹60,000 per month, spend ₹35,000 and have ₹2 lakh in savings. I want to buy a car in 18 months. What are my options?'*\n"
                f"2. *'Compare AY 2025-26 New vs Old Tax Regime for a 15 LPA salary.'*\n"
                f"3. *'Should I park my emergency fund in a Liquid Mutual Fund or a Fixed Deposit?'*\n"
                f"4. *'How much do I need to invest each month for a ₹20 Lakh house down payment in 3 years?'*\n\n"
                f"What financial decision can we simulate today?"
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
    Adapter for Google Gemini models via google-genai SDK with safe fallback to MockAIProvider.
    """
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.fallback = MockAIProvider()

    def generate_response(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.generate_response(query, chat_history, user_context)

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            context_str = f"User Financial Context: {user_context}" if user_context else ""
            prompt = (
                f"You are FinPilot AI, a Senior Indian Personal Finance CFO. {context_str}\n"
                f"User Question: {query}\n"
                "Ground all numbers in official Indian Income Tax Act 1961 rules and SEBI/RBI regulations. "
                "Never invent returns or arithmetic."
            )
            resp = client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return {
                "content": resp.text,
                "citations": ["Finance Act 2024", "Income Tax Act 1961"],
                "tool_invocations": []
            }
        except Exception as e:
            logger.warning(f"Gemini API invocation failed ({e}), falling back to offline deterministic MockAIProvider.")
            return self.fallback.generate_response(query, chat_history, user_context)


class OllamaAIProvider(BaseAIProvider):
    """
    Adapter for local Ollama instances (e.g. llama3, mistral, deepseek-r1) via HTTP API
    with automatic fallback to deterministic MockAIProvider if Ollama is unreachable.
    """
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.fallback = MockAIProvider()

    def generate_response(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            import httpx
            context_str = f"User Financial Context: {user_context}" if user_context else ""
            prompt = (
                f"You are FinPilot AI, a Senior Indian Personal Finance CFO.\n{context_str}\n"
                f"User Question: {query}\n"
                "Ground all numbers in official Indian Income Tax Act 1961 rules and SEBI/RBI regulations. "
                "Never invent returns or arithmetic."
            )
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model_name, "prompt": prompt, "stream": False}
                )
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "content": data.get("response", ""),
                        "citations": ["Finance Act 2024", "Income Tax Act 1961"],
                        "tool_invocations": []
                    }
        except Exception as e:
            logger.warning(f"Ollama API call failed ({e}), falling back to offline deterministic MockAIProvider.")

        return self.fallback.generate_response(query, chat_history, user_context)


def get_ai_provider() -> BaseAIProvider:
    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "gemini" and settings.LLM_API_KEY:
        return GeminiAIProvider(api_key=settings.LLM_API_KEY, model_name=settings.LLM_MODEL)
    elif provider == "ollama":
        return OllamaAIProvider(base_url=settings.OLLAMA_BASE_URL, model_name=settings.LLM_MODEL)
    return MockAIProvider()

