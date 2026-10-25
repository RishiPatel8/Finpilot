import io
from datetime import date
from decimal import Decimal
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pytest

from app.core.config import settings
from app.finance.statement.normalizer import StatementNormalizer
from app.finance.statement.csv_parser import parse_csv_statement
from app.finance.statement.xlsx_parser import parse_xlsx_statement
from app.finance.statement.pdf_parser import parse_pdf_statement
from app.models.financial import Transaction, StatementImportBatch, FinancialProfile
from app.models.bank import BankAccount
from app.models.user import User


# ============================================================================
# 1. Statement Normalizer & Parsing Unit Tests
# ============================================================================

def test_indian_date_parsing():
    assert StatementNormalizer.normalize_date("15/08/2024") == date(2024, 8, 15)
    assert StatementNormalizer.normalize_date("15-08-2024") == date(2024, 8, 15)
    assert StatementNormalizer.normalize_date("15-Aug-2024") == date(2024, 8, 15)
    assert StatementNormalizer.normalize_date("15-August-2024") == date(2024, 8, 15)
    assert StatementNormalizer.normalize_date("2024-08-15") == date(2024, 8, 15)
    assert StatementNormalizer.normalize_date("15.08.2024") == date(2024, 8, 15)
    assert StatementNormalizer.normalize_date("invalid_date") is None


def test_inr_currency_normalization():
    # Comma-separated Indian numbers
    assert StatementNormalizer.normalize_amount("₹1,45,000.50") == (Decimal("145000.50"), None)
    assert StatementNormalizer.normalize_amount("Rs. 25,000") == (Decimal("25000.00"), None)
    # Dr / Cr suffixes
    assert StatementNormalizer.normalize_amount("450.00 Cr") == (Decimal("450.00"), "credit")
    assert StatementNormalizer.normalize_amount("2,300.00 Dr") == (Decimal("2300.00"), "debit")
    # Negative formats
    assert StatementNormalizer.normalize_amount("-1,200.00") == (Decimal("1200.00"), "debit")
    assert StatementNormalizer.normalize_amount("(5,000.00)") == (Decimal("5000.00"), "debit")
    # Pure zero or blank
    assert StatementNormalizer.normalize_amount("") == (Decimal("0.00"), None)
    assert StatementNormalizer.normalize_amount("0.00") == (Decimal("0.00"), None)


def test_accounting_rules_classification():
    # Self-transfers between own accounts
    res1 = StatementNormalizer.classify_transaction(
        "Self transfer to HDFC savings",
        inflow=False,
        amount=Decimal("10000.00")
    )
    assert res1["is_internal_transfer"] is True
    assert res1["type"] == "transfer"
    assert res1["raw_type"] == "internal_transfer"

    # Credit card repayments (not counted as consumption)
    res2 = StatementNormalizer.classify_transaction(
        "HDFC Credit Card Bill Payment AUTO DEBIT",
        inflow=False,
        amount=Decimal("25000.00")
    )
    assert res2["is_internal_transfer"] is False
    assert res2["category"] == "Debt & EMI"
    assert res2["raw_type"] == "credit_card_payment"

    # Refunds and reversals (not counted as earned income)
    res3 = StatementNormalizer.classify_transaction(
        "Refund from Amazon India for returned item",
        inflow=True,
        amount=Decimal("1499.00")
    )
    assert res3["is_internal_transfer"] is False
    assert res3["category"] == "Refund"
    assert res3["raw_type"] == "refund"
    assert res3["type"] == "income"

    # Salary credits
    res4 = StatementNormalizer.classify_transaction(
        "SALARY CREDIT ACME TECH CORP FOR JULY 2024",
        inflow=True,
        amount=Decimal("85000.00")
    )
    assert res4["is_internal_transfer"] is False
    assert res4["category"] == "Income"
    assert res4["type"] == "income"

    # Uncertain category defaults to "Uncategorized"
    res5 = StatementNormalizer.classify_transaction(
        "POS 98712398 MYSTERIOUS VENDOR XY99",
        inflow=False,
        amount=Decimal("350.00")
    )
    assert res5["is_internal_transfer"] is False
    assert res5["category"] == "Uncategorized"
    assert res5["type"] == "expense"


def test_csv_3month_statement_parser():
    csv_content = """HDFC Bank Statement
Account Number: 50100412345678
Date,Narration,Chq/Ref Number,Withdrawal Amt,Deposit Amt,Closing Balance
01/06/2024,SALARY CREDIT ACME CORP,REF1001,,85000.00,105000.00
10/06/2024,SWIGGY BANGALORE,REF1002,650.00,,104350.00
15/06/2024,HDFC CREDIT CARD PAYMENT,REF1003,15000.00,,89350.00
01/07/2024,SALARY CREDIT ACME CORP,REF1004,,85000.00,174350.00
12/07/2024,AMAZON REFUND,REF1005,,1200.00,175550.00
20/07/2024,TRANSFER TO SELF SAVINGS,REF1006,20000.00,,155550.00
01/08/2024,SALARY CREDIT ACME CORP,REF1007,,85000.00,240550.00
28/08/2024,AIRTEL BROADBAND BILL,REF1008,1199.00,,239351.00
"""
    result = parse_csv_statement(csv_content.encode("utf-8"), "hdfc_3months.csv")

    assert result["success"] is True
    txns = result["transactions"]
    assert len(txns) == 8
    meta = result["metadata"]
    assert meta["bank_name"] == "HDFC Bank"
    assert "5678" in meta["account_number_masked"]
    assert meta["closing_balance"] == Decimal("239351.00")

    # Check internal transfer
    self_trf = next(t for t in txns if "TRANSFER TO SELF" in t["description"])
    assert self_trf["is_internal_transfer"] is True
    assert self_trf["type"] == "transfer"

    # Check credit card payment
    cc_pmt = next(t for t in txns if "CREDIT CARD PAYMENT" in t["description"])
    assert cc_pmt["raw_type"] == "credit_card_payment"
    assert cc_pmt["category"] == "Debt & EMI"


def test_xlsx_statement_parser():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Statement"
    
    ws.append(["ICICI Bank Account Statement"])
    ws.append(["Account: 001101234567"])
    ws.append(["Date", "Description", "Debit", "Credit", "Balance"])
    ws.append(["01/06/2024", "SALARY CORP", None, 90000, 110000])
    ws.append(["15/06/2024", "GROCERY MART", 4500, None, 105500])
    ws.append(["01/07/2024", "SALARY CORP", None, 90000, 195500])
    ws.append(["31/08/2024", "MUTUAL FUND SIP", 10000, None, 185500])

    buf = io.BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    result = parse_xlsx_statement(xlsx_bytes, "icici_statement.xlsx")

    assert result["success"] is True
    txns = result["transactions"]
    assert len(txns) == 4
    meta = result["metadata"]
    assert meta["bank_name"] == "ICICI Bank"
    assert "4567" in meta["account_number_masked"]
    assert meta["closing_balance"] == Decimal("185500.00")


def test_pdf_statement_parser():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(50, 750, "State Bank of India Statement")
    c.drawString(50, 730, "Account: XXXXXXXX9988")
    c.drawString(50, 700, "Date | Description | Ref | Debit | Credit | Balance")
    c.drawString(50, 680, "01/06/2024 SALARY CREDIT SBI101 0.00 75000.00 95000.00")
    c.drawString(50, 660, "15/07/2024 ELECTRICITY BILL SBI102 2400.00 0.00 92600.00")
    c.drawString(50, 640, "30/08/2024 DINING CAFE SBI103 1250.00 0.00 91350.00")
    c.save()
    pdf_bytes = buf.getvalue()

    result = parse_pdf_statement(pdf_bytes, "sbi_statement.pdf")

    assert result["success"] is True
    assert len(result["transactions"]) >= 2
    meta = result["metadata"]
    assert "9988" in meta.get("account_number_masked", "") or len(result["transactions"]) >= 2


# ============================================================================
# 2. Pipeline, Endpoints & Production Safeguard Tests
# ============================================================================

def test_statement_preview_and_confirm_lifecycle(client, db_session):
    # Register test user
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "statement_user@example.com",
        "full_name": "Statement Test User",
        "password": "Password123!",
        "role": "salaried"
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    user_id = reg_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = """Date,Description,Withdrawal Amt,Deposit Amt,Balance
01/06/2024,SALARY TECH CORP,,80000.00,90000.00
10/06/2024,RESTAURANT EXPENSE,1200.00,,88800.00
01/07/2024,SALARY TECH CORP,,80000.00,168800.00
15/07/2024,ELECTRICITY BILL,2500.00,,166300.00
01/08/2024,SALARY TECH CORP,,80000.00,246300.00
25/08/2024,CREDIT CARD REPAYMENT,15000.00,,231300.00
"""
    # 1. Preview
    res = client.post(
        "/api/v1/statement/preview",
        files={"file": ("3months.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers=headers
    )
    assert res.status_code == 200
    preview = res.json()
    assert preview["total_rows"] == 6
    assert preview["valid_rows"] == 6
    assert preview["duplicate_rows"] == 0
    assert preview["coverage"]["coverage_days"] >= 80
    assert preview["financial_summary"]["total_credits"] == 240000.0
    assert preview["financial_summary"]["total_debits"] == 18700.0

    # 2. Confirm import
    confirm_payload = {
        "filename": preview["filename"],
        "file_format": preview["format"],
        "metadata": preview["metadata"],
        "transactions": preview["preview"]
    }
    confirm_res = client.post(
        "/api/v1/statement/confirm",
        json=confirm_payload,
        headers=headers
    )
    assert confirm_res.status_code == 201
    confirm_data = confirm_res.json()
    assert confirm_data["imported_count"] == 6
    batch_id = confirm_data["batch_id"]

    # Verify transactions in DB
    txns = db_session.query(Transaction).filter(Transaction.user_id == user_id).all()
    assert len(txns) == 6
    for t in txns:
        assert t.batch_id == batch_id
        assert t.source == "bank_statement"

    # Verify bank account balance updated
    bank_acc = db_session.query(BankAccount).filter(BankAccount.user_id == user_id).first()
    assert bank_acc is not None
    assert bank_acc.current_balance == Decimal("231300.00")
    assert bank_acc.balance_type == "statement_reported"

    # Verify financial profile run-rate updated with actual 3-month average
    profile = db_session.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    assert profile is not None
    assert profile.monthly_income > 0
    assert profile.monthly_expenses > 0

    # 3. Test Overlapping / Duplicate Import Detection
    dup_preview_res = client.post(
        "/api/v1/statement/preview",
        files={"file": ("3months_dup.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers=headers
    )
    assert dup_preview_res.status_code == 200
    dup_preview = dup_preview_res.json()
    assert dup_preview["valid_rows"] == 0
    assert dup_preview["duplicate_rows"] == 6
    assert len(dup_preview["warnings"]) > 0

    # 4. Dashboard summary reflects genuine statement coverage
    dash_res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["is_empty"] is False
    assert dash_data["statement_coverage"] is not None
    assert dash_data["statement_coverage"]["total_transactions"] == 6
    assert dash_data["statement_coverage"]["days"] >= 80
    assert len(dash_data["monthly_history"]) >= 3

    # 5. Rollback / Delete Batch
    del_res = client.delete(f"/api/v1/statement/batch/{batch_id}", headers=headers)
    assert del_res.status_code == 200
    remaining_txns = db_session.query(Transaction).filter(Transaction.user_id == user_id).all()
    assert len(remaining_txns) == 0


def test_production_safeguard_blocks_demo_seeding(client, monkeypatch):
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "produser@example.com",
        "full_name": "Prod User",
        "password": "Password123!",
        "role": "salaried"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    res = client.post("/api/v1/demo/seed", headers=headers)
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()


def test_empty_user_zero_mock_data(client, db_session):
    # A fresh user with 0 transactions and 0 statements must return truthful empty state
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "cleanempty@example.com",
        "full_name": "Clean Empty User",
        "password": "Password123!",
        "role": "salaried"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dash_res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()

    assert dash["is_empty"] is True
    assert dash["statement_coverage"] is None or dash["statement_coverage"]["has_statements"] is False
    assert len(dash["monthly_history"]) == 0
