from typing import Optional, Tuple, Dict, Any
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re


# Indian banking category dictionary
CATEGORY_PATTERNS = [
    (r"(?i)\b(swiggy|zomato|starbucks|mcdonald|subway|restaurant|cafe|dining|pizza|burger|haldiram|kfc|domino|bakery|canteen|hotel|tea|coffee|snack|sweets|juice)\b", "Food & Dining"),
    (r"(?i)\b(blinkit|zepto|instamart|bigbasket|supermarket|grocery|groceries|dmart|nature's\s*basket|more\s*retail|provisions|kirana)\b", "Groceries"),
    (r"(?i)\b(uber|ola|rapido|metro|petrol|fuel|indian\s*oil|bharat\s*petroleum|hpcl|toll|fastag|irctc|redbus|indigo|air\s*india|ksrtc|bmtc|bus|train|railway|auto|transit)\b", "Transportation"),
    (r"(?i)\b(rent|maintenance|landlord|society|housing|electricity|bescom|tata\s*power|adani\s*electricity|water|lpg|indane|gas|broadband|wifi|jio|airtel|vi\b|recharge|dth)\b", "Housing & Utilities"),
    (r"(?i)\b(netflix|spotify|prime|hotstar|disney|cinema|pvr|inox|bookmyshow|steam|playstation|youtube\s*premium|apple\.com|itunes)\b", "Entertainment"),
    (r"(?i)\b(amazon|flipkart|myntra|ajio|zara|h&m|shopping|retail|croma|reliance\s*digital|ikea|decathlon|tata\s*cliq|vyapar|bazaar|store|mart|clothing|fashion|jewell?ers?)\b", "Shopping"),
    (r"(?i)\b(pharmacy|apollo|pharmeasy|1mg|hospital|clinic|doctor|diagnostic|cult\.fit|gym|medplus|netmeds|medical|healthcare|dental)\b", "Healthcare"),
    (r"(?i)\b(salary|payroll|stipend|freelance|consulting|dividend|interest\s*credit|neft\s*salary|ach\s*salary)\b", "Income"),
    (r"(?i)\b(zerodha|groww|kuvera|mf\s*central|sip|mutual\s*fund|ppf|epf|nps|uti|nippon|habbits|smallcase|coin|stocks|equity)\b", "Investment"),
    (r"(?i)\b(emi|loan|mortgage|credit\s*card\s*payment|hdfc\s*bank\s*loan|bajaj\s*finance|cred|sbi\s*card|icici\s*card|amex)\b", "Debt & EMI"),
    (r"(?i)\b(amc|annual\s*maintenance|charge|charges|fee|fees|penalty|service\s*charge|gst\s*on|atm\s*pending)\b", "Bank Fees & Charges"),
]

# Patterns specifically identifying internal account transfers
INTERNAL_TRANSFER_PATTERNS = [
    r"(?i)\b(self\s*transfer|self\s*trf|own\s*acc|transfer\s*to\s*self|to\s*own\s*a/c|sweep\s*trf|auto\s*sweep|sweep\s*in|sweep\s*out|linked\s*acc)\b",
]

# Patterns identifying credit card repayments
CREDIT_CARD_PAYMENT_PATTERNS = [
    r"(?i)\b(cred|credit\s*card|cc\s*payment|hdfc\s*card|sbi\s*card|icici\s*card|amex|axis\s*card|onecard)\b",
]

# Patterns identifying refunds and reversals
REFUND_PATTERNS = [
    r"(?i)\b(refund|reversal|cashback|bhimcashba|chargeback|rtn\s*chq|returned\s*cheque|failed\s*txn\s*rev)\b",
]


class StatementNormalizer:
    """
    Deterministic normalizer for Indian bank statements across CSV, XLSX, and PDF formats.
    Normalizes dates, Indian Rupee numbers, transaction types, accounting categories,
    and deduplication signatures.
    """

    @classmethod
    def normalize_date(cls, raw: Any) -> Optional[date]:
        """
        Parses dates in Indian formats:
        DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD/MM/YY, DD-MM-YY,
        YYYY-MM-DD, DD Mon YYYY, DD-Mon-YYYY.
        Also accepts existing date/datetime objects.
        """
        if raw is None:
            return None
        if isinstance(raw, datetime):
            return raw.date()
        if isinstance(raw, date):
            return raw

        s = str(raw).strip()
        if not s:
            return None

        # Clean trailing time if present e.g. "2024-03-15 10:30:00" or "15/03/2024 00:00"
        s = re.split(r"[\sT]", s)[0].strip()

        # Common format list
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%d/%m/%y", "%d-%m-%y",
            "%Y-%m-%d", "%Y/%m/%d",
            "%d %b %Y", "%d-%b-%Y", "%d-%b-%y",
            "%d %B %Y", "%d-%B-%Y",
            "%b %d, %Y", "%b %d %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue

        return None

    @classmethod
    def normalize_amount(cls, raw: Any) -> Tuple[Decimal, Optional[str]]:
        """
        Parses INR currency strings, stripping ₹, Rs, INR, commas, whitespace.
        Handles parentheses negative (1,500.00) -> Decimal("-1500.00").
        Handles suffix Cr/Dr e.g. "1,500.00 Cr" -> ("1500.00", "credit"), "1,500.00 Dr" -> ("1500.00", "debit").
        Returns (abs_amount, type_hint).
        """
        if raw is None:
            return Decimal("0.00"), None

        s = str(raw).strip()
        if not s:
            return Decimal("0.00"), None

        type_hint = None
        # Remove Dr / Cr indicators and record hint
        s_clean = re.sub(r"(?i)\bcr\b|\(cr\)", "", s).strip()
        if len(s_clean) < len(s):
            type_hint = "credit"
            s = s_clean

        s_clean = re.sub(r"(?i)\bdr\b|\(dr\)", "", s).strip()
        if len(s_clean) < len(s):
            type_hint = "debit"
            s = s_clean

        # Check for parentheses negative e.g. (5,000.00)
        is_parentheses_neg = False
        if s.startswith("(") and s.endswith(")"):
            is_parentheses_neg = True
            s = s[1:-1].strip()

        # Remove currency symbols (₹, Rs, INR) and commas and extra whitespace
        cleaned = re.sub(r"(?i)[₹,\s]|(?:rs|inr)\.?", "", s).strip()
        # Keep only numbers, dot, minus
        cleaned = re.sub(r"[^\d\.\-]", "", cleaned).strip()

        try:
            val = Decimal(cleaned)
            if is_parentheses_neg:
                val = -abs(val)
            if val < 0:
                type_hint = "debit" if type_hint is None else type_hint
            return abs(val), type_hint
        except (InvalidOperation, ValueError):
            return Decimal("0.00"), type_hint

    @classmethod
    def classify_transaction(
        cls,
        description: str,
        inflow: bool,
        amount: Decimal
    ) -> Dict[str, Any]:
        """
        Normalizes transaction into correct internal accounting schema:
        - Separates income, expenses, refunds, transfers, fees.
        - Identifies internal transfers between user's own accounts.
        - Identifies credit card repayments.
        - Distinguishes refunds from regular income.
        - Defaults uncertain transactions to 'Uncategorized'.
        """
        desc_clean = description.strip()

        # 1. Check for Internal Transfers (Self account transfers)
        is_internal_transfer = any(
            re.search(pat, desc_clean) for pat in INTERNAL_TRANSFER_PATTERNS
        )

        # 2. Check for Credit Card Bill Payments
        is_cc_payment = any(
            re.search(pat, desc_clean) for pat in CREDIT_CARD_PAYMENT_PATTERNS
        )

        # 3. Check for Refunds / Reversals
        is_refund = any(
            re.search(pat, desc_clean) for pat in REFUND_PATTERNS
        )

        if is_internal_transfer:
            return {
                "type": "transfer",
                "category": "Transfer",
                "is_internal_transfer": True,
                "raw_type": "internal_transfer",
                "explanation": "Identified as transfer between own accounts or sweep deposit."
            }

        if is_refund:
            return {
                "type": "income",
                "category": "Refund",
                "is_internal_transfer": False,
                "raw_type": "refund",
                "explanation": "Identified as merchant refund or reversal."
            }

        if is_cc_payment:
            return {
                "type": "expense",
                "category": "Debt & EMI",
                "is_internal_transfer": False,
                "raw_type": "credit_card_payment",
                "explanation": "Credit card statement bill payment."
            }

        # Determine default type based on cash direction
        txn_type = "income" if inflow else "expense"

        # Match category rules
        matched_category = None
        for pattern, cat in CATEGORY_PATTERNS:
            if re.search(pattern, desc_clean):
                matched_category = cat
                break

        if not matched_category:
            # Do not invent arbitrary categories: mark as Uncategorized
            matched_category = "Income" if inflow else "Uncategorized"

        return {
            "type": txn_type,
            "category": matched_category,
            "is_internal_transfer": False,
            "raw_type": "credit" if inflow else "debit",
            "explanation": f"Categorized based on description pattern: {matched_category}"
        }

    @classmethod
    def generate_signature(
        cls,
        txn_date: Optional[date],
        amount: Decimal,
        description: str,
        reference_number: Optional[str] = None
    ) -> str:
        """
        Creates a deterministic hash signature to detect duplicate transactions
        across overlapping statement periods or re-uploads.
        """
        date_str = str(txn_date) if txn_date else "no_date"
        amt_str = f"{abs(Decimal(amount)):.2f}"
        clean_desc = re.sub(r"[^a-zA-Z0-9]", "", description.lower())[:30]
        ref_str = re.sub(r"[^a-zA-Z0-9]", "", (reference_number or "").lower())
        if ref_str:
            return f"{date_str}|{amt_str}|{ref_str}"
        return f"{date_str}|{amt_str}|{clean_desc}"

    @classmethod
    def mask_account_number(cls, raw: Optional[str]) -> str:
        """
        Masks bank account number: e.g. 123456789012 -> XXXX-XXXX-9012.
        """
        if not raw:
            return "XXXX-XXXX-XXXX"
        digits = re.sub(r"[^\d]", "", str(raw))
        if len(digits) >= 4:
            return f"XXXX-XXXX-{digits[-4:]}"
        return "XXXX-XXXX-XXXX"
