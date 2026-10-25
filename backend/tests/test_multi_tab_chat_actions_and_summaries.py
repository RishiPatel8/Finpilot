import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.financial import FinancialGoal, Liability, AssetHolding, FinancialProfile
from app.ai.intent_parser import AgentIntentParser
from app.ai.agent import FinancialAgent
from app.ai.action_service import ActionPlanner, ActionExecutor


import uuid

@pytest.fixture
def test_user(db_session: Session):
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"chat_actions_{uid}@example.com",
        full_name="Chat Actions Test User",
        role="salaried"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_intent_parser_finacial_goal_typo():
    # User phrasing from prompt: "add finacial goal"
    intent = AgentIntentParser.parse("add finacial goal")
    assert intent.intent_type == "WRITE_ACTION"
    assert intent.action_type == "create_savings_goal"
    assert intent.target_entity == "goal"
    assert intent.extracted_parameters["target_amount"] == 100000.0


def test_intent_parser_specific_goal():
    intent = AgentIntentParser.parse("create goal for emergency fund of 500000 by 2027")
    assert intent.intent_type == "WRITE_ACTION"
    assert intent.action_type == "create_savings_goal"
    assert intent.extracted_parameters["target_amount"] == 500000.0
    assert "Emergency Fund" in intent.extracted_parameters["name"]
    assert "2027" in intent.extracted_parameters["target_date"]


def test_intent_parser_investment_holding():
    intent = AgentIntentParser.parse("add investment of 50000 in mutual fund")
    assert intent.intent_type == "WRITE_ACTION"
    assert intent.action_type == "create_asset_holding"
    assert intent.extracted_parameters["invested_value"] == 50000.0
    assert intent.extracted_parameters["category"] == "equity_mf"


def test_intent_parser_debt_creation():
    intent = AgentIntentParser.parse("add debt car loan of 400000 at 9.5% for 3 years")
    assert intent.intent_type == "WRITE_ACTION"
    assert intent.action_type == "create_debt"
    assert intent.extracted_parameters["principal"] == 400000.0
    assert intent.extracted_parameters["interest_rate"] == 9.5
    assert intent.extracted_parameters["tenure_months"] == 36


def test_goal_creation_confirmation_and_execution(db_session: Session, test_user: User):
    # 1. User says "add finacial goal"
    res1 = FinancialAgent.process_message(
        message="add finacial goal",
        user=test_user,
        db=db_session
    )
    assert res1["status"] == "awaiting_confirmation"
    assert res1["pending_action"] is not None
    action_id = res1["pending_action"]["id"]
    assert res1["pending_action"]["action_type"] == "create_savings_goal"
    assert "Would you like me to confirm and execute this change" in res1["content"]

    # Verify nothing in FinancialGoal table yet
    goals_before = db_session.query(FinancialGoal).filter_by(user_id=test_user.id).all()
    assert len(goals_before) == 0

    # 2. User confirms with "confirm"
    res2 = FinancialAgent.process_message(
        message="confirm",
        user=test_user,
        db=db_session
    )
    assert res2["status"] == "succeeded"
    assert "Action Confirmed & Verified" in res2["content"]

    # Verify FinancialGoal table now has the persisted goal
    goals_after = db_session.query(FinancialGoal).filter_by(user_id=test_user.id).all()
    assert len(goals_after) == 1
    assert goals_after[0].target_amount == Decimal("100000")


def test_asset_holding_confirmation_and_execution(db_session: Session, test_user: User):
    res1 = FinancialAgent.process_message(
        message="add investment of 75000 in mutual fund",
        user=test_user,
        db=db_session
    )
    assert res1["status"] == "awaiting_confirmation"
    assert res1["pending_action"]["action_type"] == "create_asset_holding"

    res2 = FinancialAgent.process_message(
        message="confirm it",
        user=test_user,
        db=db_session
    )
    assert res2["status"] == "succeeded"

    assets = db_session.query(AssetHolding).filter_by(user_id=test_user.id).all()
    assert len(assets) == 1
    assert assets[0].invested_value == Decimal("75000")


def test_debt_summary_and_creditors_query(db_session: Session, test_user: User):
    # Setup test liabilities for user
    liab1 = Liability(
        user_id=test_user.id,
        name="HDFC Home Loan",
        principal=Decimal("2500000.00"),
        interest_rate=Decimal("8.50"),
        monthly_emi=Decimal("24675.00"),
        tenure_months=180,
        remaining_months=140
    )
    liab2 = Liability(
        user_id=test_user.id,
        name="ICICI Car Loan",
        principal=Decimal("450000.00"),
        interest_rate=Decimal("9.20"),
        monthly_emi=Decimal("11230.00"),
        tenure_months=48,
        remaining_months=24
    )
    db_session.add_all([liab1, liab2])
    db_session.commit()

    # User query from prompt: "telll me what is the debt amount and for whom i want to pay it"
    res = FinancialAgent.process_message(
        message="telll me what is the debt amount and for whom i want to pay it",
        user=test_user,
        db=db_session
    )
    assert res["status"] == "success"
    content = res["content"]
    # Must list both lenders/loans and amounts
    assert "HDFC" in content
    assert "ICICI" in content
    assert "29,50,000" in content or "25,00,000" in content


def test_overall_financial_summary_query(db_session: Session, test_user: User):
    res = FinancialAgent.process_message(
        message="tell me overall summary",
        user=test_user,
        db=db_session
    )
    assert res["status"] == "success"
    content = res["content"]
    assert any(term in content for term in ["Net Worth", "net worth", "Summary", "summary", "financial"])

