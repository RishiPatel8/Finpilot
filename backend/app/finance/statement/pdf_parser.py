import io
import re
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from pypdf import PdfReader
from app.finance.statement.normalizer import StatementNormalizer


def parse_pdf_statement(
    file_bytes: bytes,
    filename: str = "statement.pdf"
) -> Dict[str, Any]:
    """
    Robust multi-strategy parser for Indian bank statements (SBI, HDFC, ICICI, Axis, Kotak, etc.) using pypdf.
    Supports:
    1. Multi-line statements (e.g. SBI, PNB, Canara) where Date starts the block,
       followed by multi-line narration, and terminated by an amount row [Chq] [Debit] [Credit] [Balance].
    2. Single-line tabular statements (e.g. HDFC, ICICI) where Date, Narration,
       Amounts, and Balance exist on a single text line.
    3. UPI title extraction and reference number parsing.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read PDF document: {str(e)}",
            "transactions": [],
            "metadata": {}
        }

    total_pages = len(reader.pages)
    if total_pages == 0:
        return {
            "success": False,
            "error": "The PDF document contains 0 pages.",
            "transactions": [],
            "metadata": {}
        }

    page_texts: List[str] = []
    all_lines: List[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        page_texts.append(txt)
        all_lines.extend(txt.splitlines())

    # 1. Bank and Account Metadata Extraction
    bank_name = None
    account_number = None
    opening_balance = None
    first_pages_text = "\n".join(page_texts[:2]).lower() if page_texts else ""

    if "state bank of india" in first_pages_text or "sbin" in first_pages_text or "sbi" in first_pages_text:
        bank_name = "State Bank of India"
    elif "hdfc" in first_pages_text:
        bank_name = "HDFC Bank"
    elif "icici" in first_pages_text:
        bank_name = "ICICI Bank"
    elif "axis" in first_pages_text:
        bank_name = "Axis Bank"
    elif "kotak" in first_pages_text:
        bank_name = "Kotak Mahindra Bank"

    # Search for account number
    acc_match = re.search(r"(?i)(?:account\s*(?:no|number)?|a/c\s*(?:no)?)\s*[:\-\s]*([0-9Xx\*\-]{6,20})", first_pages_text)
    if acc_match:
        account_number = acc_match.group(1).strip()
    else:
        # Check for standalone 11-18 digit account numbers common in Indian banking headers
        for l in all_lines[:80]:
            clean_l = l.strip()
            if re.fullmatch(r"\d{11,18}", clean_l):
                account_number = clean_l
                break

    # 2. Parsing Engine: Try Multi-Line Strategy First
    parsed_records = _parse_multiline_sbi_format(all_lines)

    # If multi-line strategy found fewer than 2 transactions, fallback to single-line regex strategy
    if len(parsed_records) < 2:
        fallback_records = _parse_singleline_format(all_lines)
        if len(fallback_records) > len(parsed_records):
            parsed_records = fallback_records

    # 3. Determine Closing Balance
    closing_balance = None
    for r in reversed(parsed_records):
        if r.get("balance_after") is not None and r["balance_after"] > Decimal("0.00"):
            closing_balance = r["balance_after"]
            break

    return {
        "success": True,
        "filename": filename,
        "format": "pdf",
        "total_pages": total_pages,
        "total_parsed": len(parsed_records),
        "transactions": parsed_records,
        "metadata": {
            "bank_name": bank_name or "Bank Account",
            "account_number_masked": StatementNormalizer.mask_account_number(account_number),
            "closing_balance": float(closing_balance) if closing_balance else None,
        }
    }


def _clean_merchant_and_ref(raw_desc: str) -> Tuple[str, Optional[str]]:
    """
    Extracts a clean merchant title and reference number from complex Indian banking narrations.
    Preserves original description details while providing clear names like:
    'KSRTC BA' or 'BMTC' or 'Zomato' or 'Swiggy'.
    """
    desc = raw_desc.strip()
    ref_no = None

    # Extract UPI RRN (12 digits)
    ref_m = re.search(r"\bUPI/(?:DR|CR)/(\d{12})", desc, re.IGNORECASE)
    if ref_m:
        ref_no = ref_m.group(1)

    # Extract clean merchant title from UPI format: UPI/DR/<rrn>/<merchant>/<bank>/...
    upi_merchant_m = re.search(r"UPI/(?:DR|CR)/\d+/([^/]+)", desc, re.IGNORECASE)
    if upi_merchant_m:
        merchant_token = upi_merchant_m.group(1).strip()
        # Clean trailing /Paid or /Sent or /BusB
        merchant_token = re.sub(r"(?i)\s*/\s*(?:paid|sent|busb|bus|no\s*r)$", "", merchant_token).strip()
        if len(merchant_token) >= 2:
            return f"UPI: {merchant_token}", ref_no

    # If starts with WDL TFR or DEP TFR, strip that transaction channel prefix
    cleaned = re.sub(r"^(?:WDL\s+TFR|DEP\s+TFR|NEFT|RTGS|IMPS|POS|ACH)\s+", "", desc, flags=re.IGNORECASE).strip()
    if cleaned:
        return cleaned, ref_no

    return desc or "Bank Transaction", ref_no


def _parse_multiline_sbi_format(all_lines: List[str]) -> List[Dict[str, Any]]:
    """
    Parses multi-line Indian bank statements (SBI, Canara, PNB, etc.):
    - Starts with Date line (e.g. '01/07/2026 01/07/2026' or '01/07/2026')
    - Followed by narration lines
    - Concluded by amount row matching: [Chq/Ref] [Debit or -] [Credit or -] [Balance]
    """
    date_regex = re.compile(r"^(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})(?:\s+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}))?(?:\s+(.*))?$")
    # Matches amount row e.g. '- 625.00 - 526.33' or '- - 39.00 380.33' or '1234 1,500.00 - 45,000.00'
    amt_line_regex = re.compile(r"^\s*(?:([0-9Xx\*\-]+|\-)\s+)?(?:([\d,]+\.\d{2}|\-)\s+)(?:([\d,]+\.\d{2}|\-)\s+)([\d,]+\.\d{2})(?:\s*(?:CR|DR|Cr|Dr))?\s*$")
    # Also handles single-line entries e.g. '18/08/2026 18/08/2026 ATM PENDING AMC - 236.00 - 1,334.24'
    single_line_amt_regex = re.compile(r"(.*?)(?:\s+([0-9Xx\*\-]+|\-))?\s+([\d,]+\.\d{2}|\-)\s+([\d,]+\.\d{2}|\-)\s+([\d,]+\.\d{2})(?:\s*(?:CR|DR|Cr|Dr))?\s*$")

    records = []
    i = 0
    row_counter = 1

    while i < len(all_lines):
        line = all_lines[i].strip()
        m = date_regex.match(line)
        if m:
            t_date_str = m.group(1)
            v_date_str = m.group(2) or t_date_str
            rest_of_line = m.group(3) or ""

            parsed_date = StatementNormalizer.normalize_date(t_date_str)
            parsed_vdate = StatementNormalizer.normalize_date(v_date_str)

            if not parsed_date:
                i += 1
                continue

            # Case A: Single line with date + description + amount line
            if rest_of_line:
                sm = single_line_amt_regex.match(rest_of_line)
                if sm:
                    desc_part, chq, deb, cred, bal = sm.groups()
                    is_debit = deb and deb != "-"
                    is_credit = cred and cred != "-"
                    if is_debit or is_credit:
                        amt_str = deb if is_debit else cred
                        amt_val, _ = StatementNormalizer.normalize_amount(amt_str)
                        bal_val, _ = StatementNormalizer.normalize_amount(bal) if bal else (None, None)
                        is_inflow = is_credit
                        title, ref = _clean_merchant_and_ref(desc_part)

                        classification = StatementNormalizer.classify_transaction(desc_part, is_inflow, amt_val)
                        records.append({
                            "source_row": row_counter,
                            "source_page": 1,
                            "date": parsed_date,
                            "value_date": parsed_vdate or parsed_date,
                            "description": title,
                            "raw_narration": desc_part.strip(),
                            "amount": amt_val,
                            "type": classification["type"],
                            "category": classification["category"],
                            "raw_type": classification["raw_type"],
                            "is_internal_transfer": classification["is_internal_transfer"],
                            "reference_number": ref,
                            "balance_after": bal_val,
                            "explanation": classification["explanation"],
                        })
                        row_counter += 1
                        i += 1
                        continue

            # Case B: Multi-line transaction
            desc_parts = [rest_of_line] if rest_of_line else []
            i += 1
            found = False
            while i < len(all_lines):
                s_line = all_lines[i].strip()
                # Skip page headers and footers
                if not s_line or "Page no." in s_line or s_line == "Balance" or s_line.startswith("Txn Date") or s_line.startswith("STATEMENT OF ACCOUNT"):
                    i += 1
                    continue

                amt_m = amt_line_regex.match(s_line)
                if amt_m:
                    chq, deb, cred, bal = amt_m.groups()
                    is_debit = deb and deb != "-"
                    is_credit = cred and cred != "-"
                    if is_debit or is_credit:
                        amt_str = deb if is_debit else cred
                        amt_val, _ = StatementNormalizer.normalize_amount(amt_str)
                        bal_val, _ = StatementNormalizer.normalize_amount(bal) if bal else (None, None)
                        is_inflow = is_credit
                        full_desc = " ".join(p for p in desc_parts if p).strip()
                        title, ref = _clean_merchant_and_ref(full_desc)

                        classification = StatementNormalizer.classify_transaction(full_desc, is_inflow, amt_val)
                        records.append({
                            "source_row": row_counter,
                            "source_page": 1,
                            "date": parsed_date,
                            "value_date": parsed_vdate or parsed_date,
                            "description": title,
                            "raw_narration": full_desc,
                            "amount": amt_val,
                            "type": classification["type"],
                            "category": classification["category"],
                            "raw_type": classification["raw_type"],
                            "is_internal_transfer": classification["is_internal_transfer"],
                            "reference_number": ref,
                            "balance_after": bal_val,
                            "explanation": classification["explanation"],
                        })
                        row_counter += 1
                        found = True
                        i += 1
                        break
                elif date_regex.match(s_line):
                    # Next transaction date reached without finding amount line
                    break
                else:
                    desc_parts.append(s_line)
                    i += 1
        else:
            i += 1

    return records


def _parse_singleline_format(all_lines: List[str]) -> List[Dict[str, Any]]:
    """
    Fallback parser for standard single-line Indian bank tables (HDFC, ICICI, Kotak).
    Matches lines starting with a date and containing amounts.
    """
    date_regex = r"^(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2})"
    records = []
    row_counter = 1

    for line in all_lines:
        line_clean = line.strip()
        m = re.match(date_regex, line_clean)
        if not m:
            continue

        raw_date_str = m.group(1)
        parsed_date = StatementNormalizer.normalize_date(raw_date_str)
        if not parsed_date:
            continue

        remainder = line_clean[len(raw_date_str):].strip()
        # Find amounts that end with optional Dr/Cr
        num_matches = list(re.finditer(r"(?:\b|₹|\()(?P<val>[0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{2}))(?:\)|(?:\s*(?:cr|dr|Cr|Dr)))?", remainder))
        if len(num_matches) >= 2:
            amt_match = num_matches[-2]
            bal_match = num_matches[-1]
            raw_amt_str = amt_match.group(0)
            raw_bal_str = bal_match.group(0)
            desc_part = remainder[:amt_match.start()].strip()

            amt_val, hint = StatementNormalizer.normalize_amount(raw_amt_str)
            bal_val, _ = StatementNormalizer.normalize_amount(raw_bal_str)

            if amt_val > Decimal("0.00"):
                is_inflow = hint == "credit" or " cr" in line_clean.lower() or "deposit" in line_clean.lower()
                title, ref = _clean_merchant_and_ref(desc_part)
                classification = StatementNormalizer.classify_transaction(desc_part, is_inflow, amt_val)

                records.append({
                    "source_row": row_counter,
                    "source_page": 1,
                    "date": parsed_date,
                    "value_date": parsed_date,
                    "description": title,
                    "raw_narration": desc_part,
                    "amount": amt_val,
                    "type": classification["type"],
                    "category": classification["category"],
                    "raw_type": classification["raw_type"],
                    "is_internal_transfer": classification["is_internal_transfer"],
                    "reference_number": ref,
                    "balance_after": bal_val,
                    "explanation": classification["explanation"],
                })
                row_counter += 1

    return records
