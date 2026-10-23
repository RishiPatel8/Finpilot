import pytest
from app.ai.adapter import MockAIProvider, get_ai_provider
from app.rag.knowledge import KnowledgeRetriever
from app.ai.tools import AVAILABLE_TOOLS


def test_rag_knowledge_retriever_tax_query():
    docs = KnowledgeRetriever.search("Section 115BAC standard deduction", top_k=2)
    assert len(docs) > 0
    assert any("115BAC" in d["citation"] or "Standard" in d["content"] for d in docs)


def test_rag_knowledge_retriever_liquid_funds():
    docs = KnowledgeRetriever.search("SEBI liquid mutual funds 91 days redemption", top_k=2)
    assert len(docs) > 0
    assert any("Liquid" in d["title"] for d in docs)


def test_mock_ai_provider_tax_intent():
    provider = MockAIProvider()
    res = provider.generate_response("Compare tax for 15 LPA salary in new regime vs old regime")
    assert "Tax Analysis" in res["content"]
    assert len(res["citations"]) > 0
    assert len(res["tool_invocations"]) > 0
    assert res["tool_invocations"][0]["tool"] == "calculate_tax"


def test_mock_ai_provider_investment_intent():
    provider = MockAIProvider()
    res = provider.generate_response("Should I invest 3 lakh in liquid fund or bond for 6 months?")
    assert "Investment Instrument Comparison" in res["content"]
    assert len(res["tool_invocations"]) > 0
    assert res["tool_invocations"][0]["tool"] == "compare_investments"


def test_mock_ai_provider_goal_intent():
    provider = MockAIProvider()
    res = provider.generate_response("How much to save per month for 20 lakh house downpayment in 3 years?")
    assert "Goal Contribution Projection" in res["content"]
    assert len(res["tool_invocations"]) > 0
    assert res["tool_invocations"][0]["tool"] == "calculate_goal_plan"


def test_get_ai_provider_default():
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)
