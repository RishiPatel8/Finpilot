import pytest
from unittest.mock import MagicMock
from app.ai.adapter import MockAIProvider, GeminiAIProvider, get_ai_provider, get_ai_provider_status
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


def test_get_ai_provider_default(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)


def test_gemini_provider_missing_api_key_safe_fallback():
    provider = GeminiAIProvider(api_key="", model_name="gemini-1.5-flash")
    status = provider.get_status()
    assert status["ready"] is False
    assert status["status"] == "missing_api_key"

    res = provider.generate_response("Compare tax for 15 LPA salary in new regime vs old regime")
    assert "Tax Analysis" in res["content"]
    assert res["status"] == "fallback_mock"
    assert res["provider"] == "mock"


def test_gemini_provider_api_error_safe_fallback(monkeypatch):
    provider = GeminiAIProvider(api_key="fake-key-for-test", model_name="gemini-1.5-flash")
    
    # Simulate a network/API failure in google.genai.Client
    def mock_client_init(*args, **kwargs):
        raise ConnectionError("Simulated Gemini API connection timeout")
    
    import google.genai
    monkeypatch.setattr(google.genai, "Client", mock_client_init)

    res = provider.generate_response("What is the standard deduction in AY 2025-26?")
    assert "Tax Analysis" in res["content"] or "standard deduction" in res["content"].lower()
    assert res["status"] == "fallback_mock"
    assert "Simulated Gemini API connection timeout" in res["fallback_reason"]


def test_gemini_provider_mocked_success(monkeypatch):
    provider = GeminiAIProvider(api_key="valid-test-key", model_name="gemini-1.5-flash")
    
    # Mock client and generate_content response
    mock_resp = MagicMock()
    mock_resp.text = "Under Section 115BAC, the standard deduction for AY 2025-26 is ₹75,000 for salaried employees."
    
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp
    
    import google.genai
    monkeypatch.setattr(google.genai, "Client", lambda **kwargs: mock_client)

    res = provider.generate_response("What is the standard deduction in AY 2025-26?")
    assert "₹75,000" in res["content"]
    assert res["provider"] == "gemini"
    assert res["status"] == "success"
    assert res["model"] == "gemini-1.5-flash"
    assert len(res["citations"]) > 0


def test_ai_provider_status_inspection():
    status = get_ai_provider_status()
    assert "status" in status
    assert "ready" in status
    assert "provider" in status


def test_mock_provider_bank_account_balance_query():
    provider = MockAIProvider()
    ctx = {
        "verified_bank_balance": 185000.0,
        "bank_accounts": [
            {
                "institution": "HDFC Bank",
                "account_masked": "XXXX5432",
                "account_type": "savings",
                "balance": 185000.0,
                "status": "synced"
            }
        ]
    }
    # Notice typo "curent" just like in user query
    res = provider.generate_response("what is the curent account balance", user_context=ctx)
    assert "₹185,000" in res["content"]
    assert "HDFC Bank" in res["content"]
    assert "DICGC" in str(res["citations"])


def test_gemini_provider_auto_sanitizes_2_5_model_name():
    # Pass legacy/restricted gemini-2.5-flash
    provider = GeminiAIProvider(api_key="valid-key", model_name="gemini-2.5-flash")
    # Must automatically sanitize to gemini-1.5-flash
    assert provider.model_name == "gemini-1.5-flash"
    assert provider.get_status()["model"] == "gemini-1.5-flash"
