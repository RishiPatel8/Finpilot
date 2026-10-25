import pytest
import uuid
from decimal import Decimal
from app.models.financial import AssetHolding, InvestmentScenario, StatementImportBatch


def get_auth_token_and_user(client, email_prefix="inv_user"):
    unique_id = str(uuid.uuid4())[:8]
    email = f"{email_prefix}_{unique_id}@example.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": f"Investor {unique_id}",
        "password": "SecurePassword123!",
        "role": "salaried"
    })
    assert reg_res.status_code == 200 or reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    user_id = reg_res.json().get("user", {}).get("id") or reg_res.json().get("user_id")
    return token, email, user_id


def test_products_catalog_endpoint(client):
    # Test catalog list
    res = client.get("/api/v1/investments/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 15
    
    # Check that known statutory instruments exist
    prod_ids = [p["id"] for p in products]
    assert "savings_account" in prod_ids
    assert "liquid_mf" in prod_ids
    assert "bank_fd" in prod_ids
    assert "nifty50_index_fund" in prod_ids
    assert "ppf" in prod_ids
    assert "sovereign_gold_bond" in prod_ids
    assert "elss_tax_saving" in prod_ids

    # Verify provenance transparency
    for p in products:
        assert p["data_provenance"] is not None
        assert p["regulatory_authority"] is not None
        assert p["as_of_date"] is not None

    # Test filtering by category
    res_liquid = client.get("/api/v1/investments/products?category=liquid")
    assert res_liquid.status_code == 200
    for p in res_liquid.json():
        assert p["category"] == "liquid"

    # Test filtering by only_guaranteed
    res_guar = client.get("/api/v1/investments/products?only_guaranteed=true")
    assert res_guar.status_code == 200
    for p in res_guar.json():
        assert p["rate_type"] == "guaranteed"


def test_multi_product_comparison_lump_sum(client):
    payload = {
        "selected_product_ids": ["liquid_mf", "bank_fd", "nifty50_index_fund", "ppf"],
        "investment_mode": "lump_sum",
        "investment_amount": 500000.0,
        "time_horizon_months": 36,
        "user_tax_slab_pct": 30.0,
        "expected_inflation_pct": 6.0,
        "can_lock_funds": True
    }
    res = client.post("/api/v1/investments/multi-compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 4

    items_by_id = {it["product_id"]: it for it in data["items"]}
    
    # 1. Bank FD: DICGC covered up to 5L, quarterly compounding, slab rate tax
    fd = items_by_id["bank_fd"]
    assert fd["dicgc_insured"] is True
    assert float(fd["dicgc_coverage_amount"]) == 500000.0
    assert fd["compounding_frequency"] == "quarterly"
    assert float(fd["estimated_tax"]) > 0

    # 2. PPF: EEE status, ₹0 tax
    ppf = items_by_id["ppf"]
    assert float(ppf["estimated_tax"]) == 0.0
    assert "EEE" in ppf["tax_rules_applied"]
    assert ppf["lock_in_months"] == 180

    # 3. Nifty 50: Finance Act 2024 LTCG (12.5% beyond 1.25L exemption)
    equity = items_by_id["nifty50_index_fund"]
    assert "12.5%" in equity["tax_rules_applied"]
    assert float(equity["gross_maturity_value"]) > float(equity["invested_principal"])

    # 4. Liquid MF: Section 50AA slab rate
    liquid = items_by_id["liquid_mf"]
    assert "Section 50AA" in liquid["tax_rules_applied"]


def test_multi_product_comparison_monthly_sip(client):
    payload = {
        "selected_product_ids": ["nifty50_index_fund", "flexi_cap_mf"],
        "investment_mode": "monthly_sip",
        "investment_amount": 10000.0,  # 10k/month
        "time_horizon_months": 24,
        "user_tax_slab_pct": 30.0,
        "expected_inflation_pct": 6.0,
        "can_lock_funds": True
    }
    res = client.post("/api/v1/investments/multi-compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["investment_mode"] == "monthly_sip"
    for it in data["items"]:
        assert float(it["invested_principal"]) == 240000.0  # 10,000 * 24
        assert float(it["gross_maturity_value"]) > 240000.0


def test_lump_sum_vs_sip_comparison(client):
    payload = {
        "product_id": "nifty50_index_fund",
        "lump_sum_amount": 360000.0,
        "monthly_sip_amount": 10000.0,
        "time_horizon_months": 36,
        "expected_annual_return_pct": 12.0,
        "expected_annual_inflation_pct": 6.0,
        "user_tax_slab_pct": 30.0
    }
    res = client.post("/api/v1/investments/lumpsum-vs-sip", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert float(data["lump_sum_total_invested"]) == 360000.0
    assert float(data["sip_total_invested"]) == 360000.0
    assert float(data["lump_sum_gross_value"]) > 360000.0
    assert float(data["sip_gross_value"]) > 360000.0
    assert len(data["schedule"]) > 5
    assert data["rupee_cost_averaging_verdict"] != ""


def test_goal_investment_planning_with_cash_check(client, db_session):
    token, _, user_id = get_auth_token_and_user(client, "goal_plan_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Add a statement batch showing 4,50,000 closing balance
    batch = StatementImportBatch(
        user_id=user_id,
        filename="bank_stmt.csv",
        file_format="csv",
        closing_balance=Decimal("450000.00")
    )
    db_session.add(batch)
    db_session.commit()

    # Plan a goal for 10 Lakhs in 5 years (60 months)
    payload = {
        "goal_name": "Child Education Corpus",
        "target_amount": 1000000.0,
        "time_horizon_months": 60,
        "current_amount_allocated": 100000.0,
        "risk_profile": "moderate",
        "adjust_for_inflation": True
    }
    res = client.post("/api/v1/investments/goal-plan", headers=headers, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["goal_name"] == "Child Education Corpus"
    assert float(data["inflation_adjusted_target"]) > 1000000.0
    assert float(data["required_monthly_sip"]) > 0
    assert len(data["allocation_breakdown"]) == 3  # Equity, Debt, Gold
    assert data["verified_liquid_cash_available"] is not None
    assert "Cash Check" in data["cash_sufficiency_notice"] or "verified bank liquidity" in data["cash_sufficiency_notice"]


def test_stress_testing_scenarios(client):
    portfolio = [
        {"product_id": "nifty50_index_fund", "amount_invested": 600000.0},
        {"product_id": "bank_fd", "amount_invested": 300000.0},
        {"product_id": "sovereign_gold_bond", "amount_invested": 100000.0}
    ]

    # Test Market Crash -20%
    res_crash = client.post("/api/v1/investments/stress-test", json={
        "portfolio_items": portfolio,
        "time_horizon_months": 36,
        "stress_scenario": "market_crash_20"
    })
    assert res_crash.status_code == 200
    data_crash = res_crash.json()
    assert data_crash["stress_scenario"] == "market_crash_20"
    assert float(data_crash["drawdown_pct"]) > 0
    assert len(data_crash["vulnerable_assets"]) > 0
    assert len(data_crash["cushioning_assets"]) > 0

    # Test Premature Exit at Month 6
    res_exit = client.post("/api/v1/investments/stress-test", json={
        "portfolio_items": portfolio,
        "time_horizon_months": 36,
        "stress_scenario": "premature_emergency_exit"
    })
    assert res_exit.status_code == 200
    data_exit = res_exit.json()
    assert data_exit["stress_scenario"] == "premature_emergency_exit"


def test_portfolio_analysis_empty_and_populated(client, db_session):
    token, _, user_id = get_auth_token_and_user(client, "pf_user")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Empty portfolio
    res_empty = client.get("/api/v1/investments/portfolio-analysis", headers=headers)
    assert res_empty.status_code == 200
    assert float(res_empty.json()["total_portfolio_value"]) == 0.0

    # 2. Add real holdings
    h1 = AssetHolding(
        user_id=user_id,
        name="Nifty 50 Index Fund",
        category="equity_mf",
        invested_value=Decimal("500000.00"),
        current_value=Decimal("600000.00")
    )
    h2 = AssetHolding(
        user_id=user_id,
        name="HDFC 3-Yr Fixed Deposit",
        category="fd",
        invested_value=Decimal("300000.00"),
        current_value=Decimal("330000.00")
    )
    h3 = AssetHolding(
        user_id=user_id,
        name="Parag Parikh Liquid Fund",
        category="liquid_mf",
        invested_value=Decimal("100000.00"),
        current_value=Decimal("105000.00")
    )
    db_session.add_all([h1, h2, h3])
    db_session.commit()

    # 3. Analyze populated portfolio
    res_pop = client.get("/api/v1/investments/portfolio-analysis", headers=headers)
    assert res_pop.status_code == 200
    data = res_pop.json()
    assert float(data["total_portfolio_value"]) == 1035000.0
    assert float(data["equity_exposure_pct"]) > 50.0
    assert float(data["liquid_cash_pct"]) > 0.0
    assert len(data["categories_breakdown"]) == 4


def test_investment_scenarios_crud_and_isolation(client):
    token1, _, user1_id = get_auth_token_and_user(client, "user_one")
    token2, _, user2_id = get_auth_token_and_user(client, "user_two")
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates scenario
    create_res = client.post("/api/v1/investments/scenarios", headers=headers1, json={
        "name": "Retirement Corpus 2040",
        "scenario_mode": "multi_product",
        "notes": "Testing equity + debt allocation",
        "inputs": {"amount": 1000000, "horizon": 180},
        "results_summary": {"equity_cagr": 12.5, "net_maturity": 4500000}
    })
    assert create_res.status_code == 201
    sc_id = create_res.json()["id"]

    # User 1 lists scenarios
    list_res1 = client.get("/api/v1/investments/scenarios", headers=headers1)
    assert list_res1.status_code == 200
    assert len(list_res1.json()) == 1
    assert list_res1.json()[0]["id"] == sc_id

    # User 2 lists scenarios -> must be isolated (empty)
    list_res2 = client.get("/api/v1/investments/scenarios", headers=headers2)
    assert list_res2.status_code == 200
    assert len(list_res2.json()) == 0

    # User 2 tries to update User 1 scenario -> 404
    update_res_unauth = client.put(f"/api/v1/investments/scenarios/{sc_id}", headers=headers2, json={
        "name": "Hacked Name"
    })
    assert update_res_unauth.status_code == 404

    # User 1 updates scenario
    update_res = client.put(f"/api/v1/investments/scenarios/{sc_id}", headers=headers1, json={
        "name": "Retirement Corpus 2040 (Updated)"
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Retirement Corpus 2040 (Updated)"

    # User 2 tries to delete User 1 scenario -> 404
    del_res_unauth = client.delete(f"/api/v1/investments/scenarios/{sc_id}", headers=headers2)
    assert del_res_unauth.status_code == 404

    # User 1 deletes scenario
    del_res = client.delete(f"/api/v1/investments/scenarios/{sc_id}", headers=headers1)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Verify scenario list is now empty
    final_list = client.get("/api/v1/investments/scenarios", headers=headers1)
    assert len(final_list.json()) == 0
