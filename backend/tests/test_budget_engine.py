from decimal import Decimal
import pytest
from app.finance.budget.engine import BudgetEngine


def test_analyze_cash_flow():
    income = Decimal("100000.00")
    expenses = Decimal("60000.00")
    fund = Decimal("180000.00")

    res = BudgetEngine.analyze_cash_flow(income, expenses, fund, target_months=6)

    assert res["monthly_surplus"] == Decimal("40000.00")
    assert res["savings_rate_pct"] == 40.0
    assert res["emergency_fund_target"] == Decimal("360000.00")
    assert res["emergency_fund_months_covered"] == 3.0
    assert res["is_emergency_fund_sufficient"] is False


def test_debt_repayment_avalanche_vs_snowball():
    debts = [
        {"name": "Home Loan", "principal": Decimal("4000000.00"), "interest_rate": Decimal("8.5"), "monthly_emi": Decimal("40000.00")},
        {"name": "Credit Card", "principal": Decimal("50000.00"), "interest_rate": Decimal("42.0"), "monthly_emi": Decimal("5000.00")},
        {"name": "Personal Loan", "principal": Decimal("200000.00"), "interest_rate": Decimal("14.0"), "monthly_emi": Decimal("7000.00")},
    ]

    res = BudgetEngine.debt_repayment_plan(debts)
    assert res["avalanche_priority"] == ["Credit Card", "Personal Loan", "Home Loan"]
    assert res["snowball_priority"] == ["Credit Card", "Personal Loan", "Home Loan"]


def test_csv_import_valid_and_duplicate_detection():
    sample_csv = """Date,Description,Amount,Type
2024-05-01,Swiggy Order,450.00,Debit
2024-05-02,Salary Credit,85000.00,Credit
2024-05-01,Swiggy Order,450.00,Debit
invalid-date,Bad Row,100,Debit
2024-05-05,Zero Amount,0,Debit
"""
    res = BudgetEngine.parse_csv_transactions(sample_csv)

    assert res.total_rows == 5
    assert res.valid_rows == 2
    assert res.invalid_rows == 2  # invalid date and zero amount
    assert res.duplicate_rows == 1  # 2nd Swiggy order marked duplicate

    # Categories should be inferred
    assert res.preview[0].category == "Food & Dining"
    assert res.preview[1].category == "Income"
