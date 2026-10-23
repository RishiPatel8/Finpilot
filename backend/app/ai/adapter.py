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
    Offline, deterministic AI provider that parses user financial questions,
    retrieves official knowledge citations, executes registered calculation tools,
    and returns grounded, explainable answers with zero external API dependencies.
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

        # 1. RAG Knowledge Retrieval
        retrieved_docs = KnowledgeRetriever.search(query, top_k=2)
        for doc in retrieved_docs:
            citations.append(f"{doc['title']} ({doc['citation']})")

        # 2. Intent Detection & Tool Invocation
        # Tax Query Detection
        if any(w in q for w in ["tax", "regime", "115bac", "slab", "87a", "standard deduction"]):
            salary = self._extract_amount(q) or 1200000.0  # default 12L if not mentioned
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
        elif any(w in q for w in ["goal", "save for", "house", "car", "downpayment", "education", "retirement"]):
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
                "monthly_income": 100000.0,
                "monthly_expenses": 55000.0,
                "emergency_fund_current": 150000.0
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
                f"Hello! I am **FinPilot AI**, your explainable personal finance intelligence assistant.\n\n"
                f"I can help you with:\n"
                f"1. **Indian Tax Planning**: Slabs, Section 115BAC New vs Old Regime comparisons for FY 24-25 / AY 25-26.\n"
                f"2. **Investment Comparisons**: Liquid Mutual Funds vs Bonds vs Fixed Deposits (liquidity, credit risk, Section 50AA taxes).\n"
                f"3. **Goal Planning**: Calculating exact monthly SIP contributions for home down payments, education, or emergency funds.\n"
                f"4. **Cash Flow & Budgeting**: Savings rate analysis, 50/30/20 budget framework, and debt payoff optimization (Avalanche vs Snowball).\n\n"
                f"How can I assist your financial journey today?"
            )

        return {
            "content": content,
            "citations": citations,
            "tool_invocations": tool_results
        }

    def _extract_amount(self, text: str) -> Optional[float]:
        # Matches formats: "12 LPA", "12lpa", "15 lakh", "15 lakhs", "15,00,000", "500000"
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakhs?|lakh|lpa|lac|lacs)", text)
        if m:
            return float(m.group(1)) * 100000.0
        m2 = re.search(r"(\d+(?:,\d{2,3})*(?:\.\d+)?)", text)
        if m2:
            raw = m2.group(1).replace(",", "")
            try:
                val = float(raw)
                if val >= 1000:  # filter out years or single digits
                    return val
            except ValueError:
                pass
        return None

    def _extract_months(self, text: str) -> Optional[int]:
        # Matches "6 months", "3 years", "2 yrs"
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
            # When google-genai is installed and key is present
            from google import genai
            client = genai.Client(api_key=self.api_key)
            prompt = (
                f"You are FinPilot AI, an Indian personal finance assistant. Respond to: {query}. "
                "Always ground numbers in deterministic Indian tax and investment rules. Do not fabricate returns."
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


def get_ai_provider() -> BaseAIProvider:
    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "gemini" and settings.LLM_API_KEY:
        return GeminiAIProvider(api_key=settings.LLM_API_KEY, model_name=settings.LLM_MODEL)
    # Default zero-cost offline mock provider
    return MockAIProvider()
