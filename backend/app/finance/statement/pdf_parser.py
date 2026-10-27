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
    Robust multi-strategy parser for Indian bank statements (Canara, SBI, HDFC, ICICI, Axis, Kotak, etc.) using pypdf.
    Supports:
    1. Multi-line statements (e.g. Canara Bank, Syndicate, SBI, PNB) where Date starts the block,
       followed by multi-line narration, optional Chq/Ref, and terminated by amount rows:
       - [Amount] [Balance] (e.g. '50.00 5,264.02' or '25,000.00 29,852.02')
       - [Chq] [Debit] [Credit] [Balance] (e.g. '- 50.00 - 5,264.02')
    2. Single-line tabular statements (e.g. HDFC, ICICI) where Date, Narration,
       Amounts, and Balance exist on a single text line.
    3. UPI title extraction, Chq reference number parsing, and running balance reconciliation.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                return {
                    "success": False,
                    "error": "The PDF statement is password-protected. Please upload an unlocked PDF file.",
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
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            page_texts.append(txt)
            all_lines.extend(txt.splitlines())
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read PDF document: {str(e)}",
            "transactions": [],
            "metadata": {}
        }

    # 1. Bank and Account Metadata Extraction
    bank_name = None
    account_number = None
    opening_balance = None
    first_pages_text = "\n".join(page_texts[:2]).lower() if page_texts else ""

    if "canara" in first_pages_text or "syndicate" in first_pages_text or "cnrb" in first_pages_text:
        bank_name = "Canara Bank"
    elif "state bank of india" in first_pages_text or "sbin" in first_pages_text or "sbi" in first_pages_text:
        bank_name = "State Bank of India"
    elif "hdfc" in first_pages_text:
        bank_name = "HDFC Bank"
    elif "icici" in first_pages_text:
        bank_name = "ICICI Bank"
    elif "axis" in first_pages_text:
        bank_name = "Axis Bank"
    elif "kotak" in first_pages_text:
        bank_name = "Kotak Mahindra Bank"

    # Search for account number e.g. Statement for A/c XXXXXXXXX0626
    acc_match = re.search(r"(?i)(?:account\s*(?:no|number)?|a/c\s*(?:no)?)\s*[:\-\s]*([0-9Xx\*\-]{6,20})", first_pages_text)
    if acc_match:
        account_number = acc_match.group(1).strip()
    else:
        for l in all_lines[:80]:
            clean_l = l.strip()
            if re.fullmatch(r"\d{11,18}", clean_l):
                account_number = clean_l
                break

    # Search for Opening Balance in headers
    for l in all_lines[:60]:
        ob_m = re.search(r"(?i)opening\s+balance\s+([\d,]+\.\d{2})", l)
        if ob_m:
            opening_balance, _ = StatementNormalizer.normalize_amount(ob_m.group(1))
            break

    # 2. Parsing Engine: Try Multi-Line Strategy First
    parsed_records = _parse_multiline_sbi_format(all_lines, initial_balance=opening_balance)

    # If multi-line strategy found fewer than 2 transactions, fallback to single-line regex strategy
    if len(parsed_records) < 2:
        fallback_records = _parse_singleline_format(all_lines)
        if len(fallback_records) > len(parsed_records):
            parsed_records = fallback_records

    # 3. Determine Closing Balance
    closing_balance = None
    # Search for explicit Closing Balance line in footers
    for l in reversed(all_lines[-40:]):
        cb_m = re.search(r"(?i)closing\s+balance\s+([\d,]+\.\d{2})", l)
        if cb_m:
            closing_balance, _ = StatementNormalizer.normalize_amount(cb_m.group(1))
            break

    if not closing_balance:
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
            "opening_balance": float(opening_balance) if opening_balance else None,
            "closing_balance": float(closing_balance) if closing_balance else None,
        }
    }


def _clean_merchant_and_ref(raw_desc: str) -> Tuple[str, Optional[str]]:
    """
    Extracts a clean merchant title and reference number from complex Indian banking narrations.
    Preserves original description details while providing clear names like:
    'KOWSHI K' or 'SWIGGY' or 'MOHAN STIPEND' or 'BMTC'.
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
        # Clean trailing /Paid or /Sent or /BusB or newlines
        merchant_token = re.sub(r"(?i)\s*/\s*(?:paid|sent|busb|bus|no\s*r)$", "", merchant_token).strip()
        if len(merchant_token) >= 2:
            return f"UPI: {merchant_token}", ref_no

    # If starts with NEFT CR or RTGS CR or IMPS CR
    neft_m = re.search(r"(?:NEFT|RTGS|IMPS)\s*(?:CR|DR)[\s\-]+[A-Z0-9]+[\s\-]+[A-Z0-9]+[\s\-]+(.*?)(?:--|\s*$)", desc, re.IGNORECASE)
    if neft_m:
        party = neft_m.group(1).strip()
        if party:
            return party, ref_no

    # If starts with WDL TFR or DEP TFR, strip that transaction channel prefix
    cleaned = re.sub(r"^(?:WDL\s+TFR|DEP\s+TFR|NEFT|RTGS|IMPS|POS|ACH)\s+", "", desc, flags=re.IGNORECASE).strip()
    if cleaned:
        return cleaned, ref_no

    return desc or "Bank Transaction", ref_no


def _parse_multiline_sbi_format(
    all_lines: List[str],
    initial_balance: Optional[Decimal] = None
) -> List[Dict[str, Any]]:
    """
    Parses multi-line Indian bank statements (Canara, Syndicate, SBI, PNB, etc.):
    - Starts with Date line (e.g. '24-07-2026' or '01/07/2026 01/07/2026')
    - Followed by multi-line narration and optional Chq: <number>
    - Concluded by amount row matching:
      * 2-token: [Amount] [Balance] (e.g. '50.00 5,264.02' or '25,000.00 29,852.02')
      * 4-token: [Chq] [Debit] [Credit] [Balance]
      * 3-token: [Debit] [Credit] [Balance]
    """
    date_regex = re.compile(r"^(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})(?:\s+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}))?(?:\s+(.*))?$")
    
    # 4-token / 3-token row e.g. '- 625.00 - 526.33' or '1234 1,500.00 - 45,000.00'
    amt_4token_regex = re.compile(r"^\s*(?:([0-9Xx\*\-]+|\-)\s+)?(?:([\d,]+\.\d{2}|\-)\s+)(?:([\d,]+\.\d{2}|\-)\s+)([\d,]+\.\d{2})(?:\s*(?:CR|DR|Cr|Dr))?\s*$")
    
    # 2-token row e.g. '50.00 5,264.02' or '25,000.00 29,852.02' (Canara Bank e-Passbook)
    amt_2token_regex = re.compile(r"^\s*(?:([0-9Xx\*\-]+|\-)\s+)?([\d,]+\.\d{2})\s+([\d,]+\.\d{2})(?:\s*(?:CR|DR|Cr|Dr))?\s*$")

    # Header / noise patterns to skip cleanly
    SKIP_PATTERNS = [
        re.compile(r"^page\s+\d+$", re.IGNORECASE),
        re.compile(r"^Date\s+Particulars\s+Deposits", re.IGNORECASE),
        re.compile(r"^(?:Opening|Closing)\s+Balance\b", re.IGNORECASE),
        re.compile(r"^Statement\s+for\s+A/c\b", re.IGNORECASE),
        re.compile(r"^(?:Customer\s+Id|Name|Phone|Address|Branch\s+Code|Branch\s+Name|Product\s+Code|Product\s+Name|IFSC\s+Code)\b", re.IGNORECASE),
        re.compile(r"^(?:DISCLAIMER|UNLESS\s+THE\s+CONSTITUENT|BEWARE\s+OF\s+PHISHING|IMB\s+USERS|COMPUTER\s+OUTPUT|\-{5,})", re.IGNORECASE),
    ]

    def is_noise(text: str) -> bool:
        c = text.strip()
        if not c:
            return True
        return any(p.search(c) for p in SKIP_PATTERNS)

    records = []
    i = 0
    row_counter = 1
    running_balance = initial_balance

    while i < len(all_lines):
        line = all_lines[i].strip()
        if is_noise(line):
            i += 1
            continue

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

            # Case A: Check if the transaction is on a single line (e.g. '01/06/2024 SALARY CREDIT SBI101 0.00 75000.00 95000.00')
            if rest_of_line:
                sm = re.match(r"^(.*?)(?:\s+([0-9Xx\*\-]+|\-))?\s+([\d,]+\.\d{2}|\-)\s+([\d,]+\.\d{2}|\-)\s+([\d,]+\.\d{2})(?:\s*(?:CR|DR|Cr|Dr))?\s*$", rest_of_line)
                if sm:
                    desc_part, chq, deb, cred, bal = sm.groups()
                    is_debit = deb and deb != "-" and deb != "0.00" and deb != "0"
                    is_credit = cred and cred != "-" and cred != "0.00" and cred != "0"
                    if is_debit or is_credit:
                        amt_str = deb if is_debit else cred
                        amt_val, _ = StatementNormalizer.normalize_amount(amt_str)
                        bal_val, _ = StatementNormalizer.normalize_amount(bal) if bal else (None, None)
                        is_inflow = is_credit
                        running_balance = bal_val

                        title, ref = _clean_merchant_and_ref(desc_part)
                        final_ref = ref or (chq if (chq and chq != "-") else None)

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
                            "reference_number": final_ref,
                            "balance_after": bal_val,
                            "explanation": classification["explanation"],
                        })
                        row_counter += 1
                        i += 1
                        continue

            desc_parts = [rest_of_line] if rest_of_line else []
            chq_ref = None
            i += 1
            found = False

            while i < len(all_lines):
                s_line = all_lines[i].strip()
                if is_noise(s_line):
                    i += 1
                    continue

                # Check for Chq: line common in Canara e-Passbook (e.g. 'Chq: 620593156254' or 'Chq: 0')
                chq_m = re.match(r"(?i)^chq:\s*([0-9Xx\*\-]+)?", s_line)
                if chq_m:
                    val = chq_m.group(1)
                    if val and val != "0" and val != "-":
                        chq_ref = val
                    i += 1
                    continue

                # Strategy 1: Match 4-token / 3-token amount row
                amt_4m = amt_4token_regex.match(s_line)
                if amt_4m:
                    chq, deb, cred, bal = amt_4m.groups()
                    is_debit = deb and deb != "-"
                    is_credit = cred and cred != "-"
                    if is_debit or is_credit:
                        amt_str = deb if is_debit else cred
                        amt_val, _ = StatementNormalizer.normalize_amount(amt_str)
                        bal_val, _ = StatementNormalizer.normalize_amount(bal) if bal else (None, None)
                        is_inflow = is_credit
                        running_balance = bal_val

                        full_desc = " ".join(p for p in desc_parts if p).strip()
                        title, ref = _clean_merchant_and_ref(full_desc)
                        final_ref = ref or chq_ref or (chq if (chq and chq != "-") else None)

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
                            "reference_number": final_ref,
                            "balance_after": bal_val,
                            "explanation": classification["explanation"],
                        })
                        row_counter += 1
                        found = True
                        i += 1
                        break

                # Strategy 2: Match 2-token amount row [Amount] [Balance] (Canara Bank e-Passbook)
                amt_2m = amt_2token_regex.match(s_line)
                if amt_2m:
                    chq, amt_str, bal_str = amt_2m.groups()
                    amt_val, _ = StatementNormalizer.normalize_amount(amt_str)
                    bal_val, _ = StatementNormalizer.normalize_amount(bal_str) if bal_str else (None, None)

                    full_desc = " ".join(p for p in desc_parts if p).strip()
                    full_desc_upper = full_desc.upper()

                    # Determine Inflow (Credit) vs Outflow (Debit)
                    # Priority 1: Explicit transaction type markers in narration
                    if any(dr_kw in full_desc_upper for dr_kw in ["/DR/", "DR-", "DEBIT", "UPI/DR", "TO /", "WDL"]):
                        is_inflow = False
                    elif any(cr_kw in full_desc_upper for cr_kw in ["/CR/", "CR-", "NEFT CR", "IMPS CR", "RTGS CR", "CREDIT", "REFUND", "STIPEND", "SALARY", "INTEREST", "SBINT", "BY /"]):
                        is_inflow = True
                    # Priority 2: Mathematical running balance delta
                    elif running_balance is not None and bal_val is not None:
                        is_inflow = bal_val > running_balance
                    else:
                        is_inflow = False

                    running_balance = bal_val
                    title, ref = _clean_merchant_and_ref(full_desc)
                    final_ref = ref or chq_ref or (chq if (chq and chq != "-") else None)

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
                        "reference_number": final_ref,
                        "balance_after": bal_val,
                        "explanation": classification["explanation"],
                    })
                    row_counter += 1
                    found = True
                    i += 1
                    break

                # If reached next transaction date without finding amount row, break out
                if date_regex.match(s_line):
                    break

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
