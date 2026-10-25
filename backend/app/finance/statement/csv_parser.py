import csv
import io
import re
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from app.finance.statement.normalizer import StatementNormalizer


def parse_csv_statement(
    file_bytes: bytes,
    filename: str = "statement.csv"
) -> Dict[str, Any]:
    """
    Robust CSV parser for Indian bank statements (HDFC, SBI, ICICI, Axis, Kotak, etc.).
    - Detects encodings (UTF-8, UTF-8-SIG, Latin1, CP1252)
    - Skips account/branch metadata preamble lines
    - Identifies table header row dynamically
    - Extracts Date, Value Date, Narration, Reference No, Debit, Credit, Amount, Balance
    - Captures bank name, masked account number, and closing balance if present
    """
    # 1. Decode text with encoding fallback
    text = None
    for enc in ["utf-8-sig", "utf-8", "latin1", "cp1252"]:
        try:
            text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        text = file_bytes.decode("utf-8", errors="replace")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {
            "success": False,
            "error": "The uploaded CSV file is empty.",
            "transactions": [],
            "metadata": {}
        }

    # 2. Extract bank name and masked account number from preamble if available
    bank_name = None
    account_number = None
    preamble_lines = lines[:25]

    for line in preamble_lines:
        line_lower = line.lower()
        if not bank_name:
            if "hdfc" in line_lower:
                bank_name = "HDFC Bank"
            elif "sbi" in line_lower or "state bank" in line_lower:
                bank_name = "State Bank of India"
            elif "icici" in line_lower:
                bank_name = "ICICI Bank"
            elif "axis" in line_lower:
                bank_name = "Axis Bank"
            elif "kotak" in line_lower:
                bank_name = "Kotak Mahindra Bank"

        if not account_number:
            acc_match = re.search(r"(?i)(?:account\s*(?:no|number)?|a/c\s*(?:no)?)\s*[:\-\s]*([0-9Xx\*\-]+)", line)
            if acc_match:
                account_number = acc_match.group(1).strip()

    # 3. Locate Header Row
    sniffer_sample = "\n".join(lines[:30])
    try:
        dialect = csv.Sniffer().sniff(sniffer_sample, delimiters=",\t;")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    header_idx = -1
    header_cols: List[str] = []

    date_terms = ["date", "txn date", "trans date", "transaction date", "post date", "booking date"]
    desc_terms = ["narration", "particulars", "description", "details", "remarks"]
    amt_terms = ["amount", "debit", "withdrawal", "credit", "deposit", "balance", "dr", "cr"]

    for idx, line in enumerate(lines[:35]):
        row = [c.strip().lower() for c in next(csv.reader([line], delimiter=delimiter))]
        has_date = any(any(dt in col for dt in date_terms) for col in row)
        has_desc = any(any(dsc in col for dsc in desc_terms) for col in row)
        has_amt = any(any(amt in col for amt in amt_terms) for col in row)

        if (has_date and has_desc) or (has_date and has_amt):
            header_idx = idx
            header_cols = row
            break

    # Fallback to first line if no header matched
    if header_idx == -1:
        header_idx = 0
        header_cols = [c.strip().lower() for c in next(csv.reader([lines[0]], delimiter=delimiter))]

    # 4. Map Column Indexes
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
        clean_col = re.sub(r"[^a-z0-9]", " ", col).strip()
        if any(term in clean_col for term in ["value date", "val date"]):
            col_val_date = i
        elif any(term in clean_col for term in ["txn date", "trans date", "transaction date", "booking date", "post date", "date"]):
            if col_date == -1:
                col_date = i
        elif any(term in clean_col for term in ["narration", "particulars", "description", "details", "remarks", "memo"]):
            if col_desc == -1:
                col_desc = i
        elif any(term in clean_col for term in ["chq", "ref", "cheque", "utr", "txn id", "reference"]):
            if col_ref == -1:
                col_ref = i
        elif any(term in clean_col for term in ["withdrawal", "debit", "dr amt", "dr amount"]):
            col_debit = i
        elif any(term in clean_col for term in ["deposit", "credit", "cr amt", "cr amount"]):
            col_credit = i
        elif any(term in clean_col for term in ["amount", "txn amt"]):
            if col_amount == -1:
                col_amount = i
        elif any(term in clean_col for term in ["cr dr", "dr cr", "type"]):
            col_type = i
        elif any(term in clean_col for term in ["closing balance", "balance", "avail bal", "running bal"]):
            col_balance = i

    # Fallbacks
    if col_date == -1 and len(header_cols) > 0:
        col_date = 0
    if col_desc == -1 and len(header_cols) > 1:
        col_desc = 1
    if col_amount == -1 and col_debit == -1 and col_credit == -1 and len(header_cols) > 2:
        col_amount = 2

    # 5. Parse Data Rows
    parsed_records = []
    closing_balance = None
    data_lines = lines[header_idx + 1:]

    for line_offset, line in enumerate(data_lines):
        try:
            row = next(csv.reader([line], delimiter=delimiter))
        except Exception:
            continue

        if not row or all(not c.strip() for c in row):
            continue

        raw_date_str = row[col_date].strip() if col_date < len(row) else ""
        txn_date = StatementNormalizer.normalize_date(raw_date_str)
        if not txn_date:
            continue  # Ignore footer / summary rows without dates

        val_date = None
        if col_val_date != -1 and col_val_date < len(row):
            val_date = StatementNormalizer.normalize_date(row[col_val_date].strip())

        description = row[col_desc].strip() if col_desc < len(row) else "Unlabelled Transaction"
        ref_num = row[col_ref].strip() if col_ref != -1 and col_ref < len(row) else None

        # Amount and direction detection
        parsed_amount = Decimal("0.00")
        is_inflow = False

        if col_debit != -1 and col_credit != -1:
            raw_dr = row[col_debit].strip() if col_debit < len(row) else ""
            raw_cr = row[col_credit].strip() if col_credit < len(row) else ""
            amt_dr, _ = StatementNormalizer.normalize_amount(raw_dr)
            amt_cr, _ = StatementNormalizer.normalize_amount(raw_cr)

            if amt_cr > Decimal("0.00"):
                parsed_amount = amt_cr
                is_inflow = True
            elif amt_dr > Decimal("0.00"):
                parsed_amount = amt_dr
                is_inflow = False
        elif col_amount != -1 and col_amount < len(row):
            raw_amt = row[col_amount].strip()
            amt_val, hint = StatementNormalizer.normalize_amount(raw_amt)
            parsed_amount = amt_val

            if col_type != -1 and col_type < len(row):
                t_val = row[col_type].strip().lower()
                is_inflow = "cr" in t_val or "deposit" in t_val or "credit" in t_val
            elif hint == "credit":
                is_inflow = True
            elif hint == "debit":
                is_inflow = False
            else:
                # If negative value was parsed
                is_inflow = not raw_amt.startswith("-")

        if parsed_amount <= Decimal("0.00"):
            continue

        # Balance after transaction
        balance_after = None
        if col_balance != -1 and col_balance < len(row):
            raw_bal = row[col_balance].strip()
            bal_amt, _ = StatementNormalizer.normalize_amount(raw_bal)
            if bal_amt > Decimal("0.00"):
                balance_after = bal_amt
                closing_balance = bal_amt

        # Accounting classification
        classification = StatementNormalizer.classify_transaction(description, is_inflow, parsed_amount)

        parsed_records.append({
            "source_row": header_idx + line_offset + 2,
            "date": txn_date,
            "value_date": val_date or txn_date,
            "description": description,
            "amount": parsed_amount,
            "type": classification["type"],
            "category": classification["category"],
            "raw_type": classification["raw_type"],
            "is_internal_transfer": classification["is_internal_transfer"],
            "reference_number": ref_num,
            "balance_after": balance_after,
            "explanation": classification["explanation"],
        })

    return {
        "success": True,
        "filename": filename,
        "format": "csv",
        "total_parsed": len(parsed_records),
        "transactions": parsed_records,
        "metadata": {
            "bank_name": bank_name,
            "account_number_masked": StatementNormalizer.mask_account_number(account_number),
            "closing_balance": float(closing_balance) if closing_balance else None,
        }
    }
