import pytest
from app.ai.adapter import MockAIProvider


def test_connected_ai_cfo_car_purchase_decision():
    provider = MockAIProvider()
    query = "I earn ₹60,000 per month, spend ₹35,000 and have ₹2 lakh in savings. I want to buy a car in 18 months. What are my options?"
    
    res = provider.generate_response(query)

    assert "AI CFO Strategic Financial Assessment" in res["content"]
    assert "₹25,000" in res["content"]  # Monthly surplus
    assert "Option 1" in res["content"]
    assert "Option 2" in res["content"]
    assert "Option 3" in res["content"]
    
    # Tool execution verified
    assert len(res["tool_invocations"]) > 0
    assert res["tool_invocations"][0]["tool"] == "simulate_scenario"

    # Regulatory citations verified
    assert len(res["citations"]) > 0
    assert any("SEBI" in c or "RBI" in c or "Liquid" in c for c in res["citations"])


def test_connected_ai_cfo_authorized_context_fallback():
    provider = MockAIProvider()
    query = "I want to buy a car in 18 months. What are my options?"
    authorized_context = {
        "monthly_income": 90000.0,
        "monthly_expenses": 40000.0,
        "current_savings": 350000.0
    }
    
    res = provider.generate_response(query, user_context=authorized_context)

    # Should use the injected user context (90k income, 40k expenses => 50k surplus)
    assert "₹50,000" in res["content"]
    assert "Option 1" in res["content"]
    assert res["tool_invocations"][0]["tool"] == "simulate_scenario"
