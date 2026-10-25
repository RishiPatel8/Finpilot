import io
import re
from typing import Dict, List, Any, Optional
from decimal import Decimal
import openpyxl
from app.finance.statement.normalizer import StatementNormalizer


def parse_xlsx_statement(
    file_bytes: bytes,
    filename: str = "statement.xlsx"
) -> Dict[str, Any]:
    """
    Parses XLSX/XLS bank statements (HDFC, SBI, ICICI, Axis, Kotak, etc.) using openpyxl.
    - Scans workbook sheets
    - Detects metadata header block
    - Identifies transaction table header row
    - Extracts cell values across native date, string, float formats
    - Normalizes amounts, debits, credits, balances, categories
    """
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read Excel workbook: {str(e)}",
            "transactions": [],
            "metadata": {}
        }

    sheet = wb.active
    if not sheet:
        return {
            "success": False,
            "error": "Workbook contains no active worksheet.",
            "transactions": [],
            "metadata": {}
        }

    rows_data: List[List[Any]] = []
    for row in sheet.iter_rows(values_only=True):
        rows_data.append(list(row))

    if not rows_data:
        return {
            "success": False,
            "error": "Excel worksheet is empty.",
            "transactions": [],
            "metadata": {}
        }

    # 1. Preamble scanning for bank name and account number
    bank_name = None
    account_number = None

    for r in rows_data[:30]:
        r_str = " ".join(str(cell or "") for cell in r).lower()
        if not bank_name:
            if "hdfc" in r_str:
                bank_name = "HDFC Bank"
            elif "sbi" in r_str or "state bank" in r_str:
                bank_name = "State Bank of India"
            elif "icici" in r_str:
                bank_name = "ICICI Bank"
            elif "axis" in r_str:
                bank_name = "Axis Bank"
            elif "kotak" in r_str:
                bank_name = "Kotak Mahindra Bank"

        if not account_number:
            acc_match = re.search(r"(?i)(?:account\s*(?:no|number)?|a/c\s*(?:no)?)\s*[:\-\s]*([0-9Xx\*\-]+)", r_str)
            if acc_match:
                account_number = acc_match.group(1).strip()

    # 2. Identify Header Row
    header_idx = -1
    header_cols: List[str] = []

    date_terms = ["date", "txn date", "trans date", "transaction date", "post date"]
    desc_terms = ["narration", "particulars", "description", "details", "remarks"]
    amt_terms = ["amount", "debit", "withdrawal", "credit", "deposit", "balance", "dr", "cr"]

    for idx, r in enumerate(rows_data[:40]):
        row_str_cols = [str(cell or "").strip().lower() for cell in r]
        has_date = any(any(dt in col for dt in date_terms) for col in row_str_cols)
        has_desc = any(any(dsc in col for dsc in desc_terms) for col in row_str_cols)
        has_amt = any(any(amt in col for amt in amt_terms) for col in row_str_cols)

        if (has_date and has_desc) or (has_date and has_amt):
            header_idx = idx
            header_cols = row_str_cols
            break

    if header_idx == -1:
        # Fallback to first non-empty row
        for idx, r in enumerate(rows_data):
            if any(cell is not None for cell in r):
                header_idx = idx
                header_cols = [str(cell or "").strip().lower() for cell in r]
                break

    if header_idx == -1:
        return {
            "success": False,
            "error": "Could not identify transaction table header in Excel sheet.",
            "transactions": [],
            "metadata": {}
        }

    # 3. Map Columns
    col_date = -1
    col_val_date = -1
    col_desc = -1
    col_ref = -1
    col_debit = -1
    col_credit = -1
    col_amount = -1
    col_type = -1
    col_balance = -1

    for i, col in enumerate(header_cols):
        clean = re.sub(r"[^a-z0-9]", " ", col).strip()
        if any(term in clean for term in ["value date", "val date"]):
            col_val_date = i
        elif any(term in clean for term in ["txn date", "trans date", "transaction date", "booking date", "post date", "date"]):
            if col_date == -1:
                col_date = i
        elif any(term in clean for term in ["narration", "particulars", "description", "details", "remarks", "memo"]):
            if col_desc == -1:
                col_desc = i
        elif any(term in clean for term in ["chq", "ref", "cheque", "utr", "txn id", "reference"]):
            if col_ref == -1:
                col_ref = i
        elif any(term in clean for term in ["withdrawal", "debit", "dr amt", "dr amount"]):
            col_debit = i
        elif any(term in clean for term in ["deposit", "credit", "cr amt", "cr amount"]):
            col_credit = i
        elif any(term in clean for term in ["amount", "txn amt"]):
            if col_amount == -1:
                col_amount = i
        elif any(term in clean for term in ["cr dr", "dr cr", "type"]):
            col_type = i
        elif any(term in clean for term in ["closing balance", "balance", "avail bal", "running bal"]):
            col_balance = i

    # Fallbacks
    if col_date == -1 and len(header_cols) > 0:
        col_date = 0
    if col_desc == -1 and len(header_cols) > 1:
        col_desc = 1
    if col_amount == -1 and col_debit == -1 and col_credit == -1 and len(header_cols) > 2:
        col_amount = 2

    parsed_records = []
    closing_balance = None
    data_rows = rows_data[header_idx + 1:]

    for offset, r in enumerate(data_rows):
        if not r or all(cell is None or str(cell).strip() == "" for cell in r):
            continue

        raw_date_cell = r[col_date] if col_date < len(r) else None
        txn_date = StatementNormalizer.normalize_date(raw_date_cell)
        if not txn_date:
            continue

        val_date = None
        if col_val_date != -1 and col_val_date < len(r):
            val_date = StatementNormalizer.normalize_date(r[col_val_date])

        desc_cell = str(r[col_desc] or "").strip() if col_desc < len(r) else "Unlabelled Transaction"
        ref_cell = str(r[col_ref] or "").strip() if col_ref != -1 and col_ref < len(r) and r[col_ref] is not None else None

        parsed_amount = Decimal("0.00")
        is_inflow = False

        if col_debit != -1 and col_credit != -1:
            raw_dr = r[col_debit] if col_debit < len(r) else None
            raw_cr = r[col_credit] if col_credit < len(r) else None
            amt_dr, _ = StatementNormalizer.normalize_amount(raw_dr)
            amt_cr, _ = StatementNormalizer.normalize_amount(raw_cr)

            if amt_cr > Decimal("0.00"):
                parsed_amount = amt_cr
                is_inflow = True
            elif amt_dr > Decimal("0.00"):
                parsed_amount = amt_dr
                is_inflow = False
        elif col_amount != -1 and col_amount < len(r):
            raw_amt = r[col_amount]
            amt_val, hint = StatementNormalizer.normalize_amount(raw_amt)
            parsed_amount = amt_val

            if col_type != -1 and col_type < len(r):
                t_val = str(r[col_type] or "").strip().lower()
                is_inflow = "cr" in t_val or "deposit" in t_val or "credit" in t_val
            elif hint == "credit":
                is_inflow = True
            elif hint == "debit":
                is_inflow = False
            else:
                is_inflow = not str(raw_amt).startswith("-")

        if parsed_amount <= Decimal("0.00"):
            continue

        balance_after = None
        if col_balance != -1 and col_balance < len(r):
            raw_bal = r[col_balance]
            bal_amt, _ = StatementNormalizer.normalize_amount(raw_bal)
            if bal_amt > Decimal("0.00"):
                balance_after = bal_amt
                closing_balance = bal_amt

        classification = StatementNormalizer.classify_transaction(desc_cell, is_inflow, parsed_amount)

        parsed_records.append({
            "source_row": header_idx + offset + 2,
            "date": txn_date,
            "value_date": val_date or txn_date,
            "description": desc_cell,
            "amount": parsed_amount,
            "type": classification["type"],
            "category": classification["category"],
            "raw_type": classification["raw_type"],
            "is_internal_transfer": classification["is_internal_transfer"],
            "reference_number": ref_cell,
            "balance_after": balance_after,
            "explanation": classification["explanation"],
        })

    return {
        "success": True,
        "filename": filename,
        "format": "xlsx",
        "total_parsed": len(parsed_records),
        "transactions": parsed_records,
        "metadata": {
            "bank_name": bank_name,
            "account_number_masked": StatementNormalizer.mask_account_number(account_number),
            "closing_balance": float(closing_balance) if closing_balance else None,
        }
    }
