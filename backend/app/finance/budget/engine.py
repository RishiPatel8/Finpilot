from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from datetime import date
import io
import csv
import re
from app.schemas.financial import (
    TransactionCreate,
    CSVImportPreviewResponse,
    CSVImportRowPreview
)


class BudgetEngine:
    """
    Deterministic Cash Flow, Budgeting, Runway, and Debt Repayment Engine.
    """

    @classmethod
    def analyze_cash_flow(
        cls,
        monthly_income: Decimal,
        monthly_expenses: Decimal,
        emergency_fund_current: Decimal,
        target_months: int = 6
    ) -> Dict[str, Any]:
        """
        Calculates monthly surplus, savings rate, emergency reserve target, and runway months.
        """
        surplus = monthly_income - monthly_expenses
        savings_rate = Decimal("0.00")
        if monthly_income > Decimal("0"):
            savings_rate = ((surplus / monthly_income) * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        emergency_target = (monthly_expenses * Decimal(str(target_months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        runway_months = Decimal("0.0")
        if monthly_expenses > Decimal("0"):
            runway_months = (emergency_fund_current / monthly_expenses).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        # 50-30-20 Rule comparison
        needs_ideal = (monthly_income * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        wants_ideal = (monthly_income * Decimal("0.30")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        savings_ideal = (monthly_income * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "monthly_surplus": surplus,
            "savings_rate_pct": float(savings_rate),
            "emergency_fund_current": emergency_fund_current,
            "emergency_fund_target": emergency_target,
            "emergency_fund_months_covered": float(runway_months),
            "is_emergency_fund_sufficient": emergency_fund_current >= emergency_target,
            "fifty_thirty_twenty": {
                "needs_budget_50": needs_ideal,
                "wants_budget_30": wants_ideal,
                "savings_budget_20": savings_ideal,
            }
        }

    @classmethod
    def debt_repayment_plan(
        cls,
        debts: List[Dict[str, Any]],
        extra_monthly_payment: Decimal = Decimal("0.00")
    ) -> Dict[str, Any]:
        """
        Compares Debt Avalanche (highest interest rate first) vs Debt Snowball (lowest balance first).
        """
        if not debts:
            return {"avalanche": [], "snowball": [], "recommendation": "No active debts"}

        # Avalanche ordering: descending interest rate
        avalanche_sorted = sorted(debts, key=lambda d: d.get("interest_rate", Decimal("0")), reverse=True)
        # Snowball ordering: ascending principal
        snowball_sorted = sorted(debts, key=lambda d: d.get("principal", Decimal("0")))

        total_principal = sum(d["principal"] for d in debts)
        total_monthly_emi = sum(d["monthly_emi"] for d in debts)

        return {
            "total_debt_principal": total_principal,
            "total_monthly_emi": total_monthly_emi,
            "extra_payment_applied": extra_monthly_payment,
            "avalanche_priority": [d["name"] for d in avalanche_sorted],
            "snowball_priority": [d["name"] for d in snowball_sorted],
            "strategy_recommendation": (
                "Debt Avalanche is mathematically optimal to save maximum total interest, "
                "prioritizing high-interest liabilities first (e.g. credit cards and personal loans). "
                "Debt Snowball provides faster psychological wins by eliminating smaller balances first."
            )
        }

    @classmethod
    def parse_csv_transactions(
        cls,
        csv_content: str,
        existing_signatures: set = None
    ) -> CSVImportPreviewResponse:
        """
        Parses CSV bank or credit card statements, detects columns, validates rows,
        and identifies duplicates.
        """
        if existing_signatures is None:
            existing_signatures = set()

        f = io.StringIO(csv_content.strip())
        reader = csv.reader(f)
        rows = list(reader)

        if not rows:
            return CSVImportPreviewResponse(
                total_rows=0, valid_rows=0, invalid_rows=0, duplicate_rows=0, preview=[]
            )

        header = [c.strip().lower() for c in rows[0]]
        
        # Column index detection
        date_idx = -1
        desc_idx = -1
        amount_idx = -1
        credit_idx = -1
        debit_idx = -1
        type_idx = -1
        category_idx = -1

        for i, col in enumerate(header):
            if any(term in col for term in ["date", "txn_date", "trans_date", "transaction date"]):
                date_idx = i
            elif any(term in col for term in ["narration", "desc", "particulars", "description"]):
                desc_idx = i
            elif "credit" in col:
                credit_idx = i
            elif "debit" in col:
                debit_idx = i
            elif any(term in col for term in ["amount", "txn_amount"]):
                amount_idx = i
            elif any(term in col for term in ["type", "cr/dr", "dr_cr"]):
                type_idx = i
            elif any(term in col for term in ["category", "tag"]):
                category_idx = i

        # Fallbacks if columns not explicitly matched
        if date_idx == -1 and len(header) > 0:
            date_idx = 0
        if desc_idx == -1 and len(header) > 1:
            desc_idx = 1
        if amount_idx == -1 and credit_idx == -1 and debit_idx == -1 and len(header) > 2:
            amount_idx = 2

        previews: List[CSVImportRowPreview] = []
        valid_count = 0
        invalid_count = 0
        duplicate_count = 0

        for row_idx, row in enumerate(rows[1:], start=2):
            if not row or all(not cell.strip() for cell in row):
                continue

            raw_date = row[date_idx].strip() if date_idx < len(row) else ""
            raw_desc = row[desc_idx].strip() if desc_idx < len(row) else "Unlabelled transaction"
            
            raw_amount = "0.0"
            raw_type = "expense"

            if credit_idx != -1 and debit_idx != -1:
                cr_val = row[credit_idx].strip().replace(",", "") if credit_idx < len(row) else ""
                dr_val = row[debit_idx].strip().replace(",", "") if debit_idx < len(row) else ""
                try:
                    if cr_val and float(cr_val) > 0:
                        raw_amount = cr_val
                        raw_type = "income"
                    elif dr_val and float(dr_val) > 0:
                        raw_amount = dr_val
                        raw_type = "expense"
                except ValueError:
                    pass
            elif amount_idx != -1 and amount_idx < len(row):
                amt_str = row[amount_idx].strip().replace(",", "")
                raw_amount = amt_str
                if type_idx != -1 and type_idx < len(row):
                    t_str = row[type_idx].strip().lower()
                    if "cr" in t_str or "income" in t_str or "deposit" in t_str:
                        raw_type = "income"
                    else:
                        raw_type = "expense"
                else:
                    try:
                        val = float(amt_str)
                        if val < 0:
                            raw_amount = str(abs(val))
                            raw_type = "expense"
                    except ValueError:
                        pass

            raw_category = row[category_idx].strip() if (category_idx != -1 and category_idx < len(row)) else cls._infer_category(raw_desc)

            # Validation
            is_valid = True
            validation_error = None
            parsed_amount = 0.0

            try:
                parsed_amount = abs(float(raw_amount))
                if parsed_amount == 0.0:
                    is_valid = False
                    validation_error = "Amount cannot be zero"
            except ValueError:
                is_valid = False
                validation_error = f"Invalid amount format: '{raw_amount}'"

            # Date normalization check (YYYY-MM-DD or DD/MM/YYYY or DD-MM-YYYY)
            normalized_date = cls._normalize_date(raw_date)
            if not normalized_date:
                is_valid = False
                validation_error = f"Invalid date format: '{raw_date}'"

            # Duplicate signature
            sig = f"{normalized_date}|{parsed_amount}|{raw_desc.lower()}"
            is_dup = sig in existing_signatures
            if is_dup:
                duplicate_count += 1
            else:
                existing_signatures.add(sig)

            if is_valid and not is_dup:
                valid_count += 1
            elif not is_valid:
                invalid_count += 1

            previews.append(CSVImportRowPreview(
                row_number=row_idx,
                date=normalized_date or raw_date,
                amount=parsed_amount,
                type=raw_type,
                category=raw_category,
                description=raw_desc,
                is_valid=is_valid,
                validation_error=validation_error,
                is_duplicate=is_dup
            ))

        return CSVImportPreviewResponse(
            total_rows=len(previews),
            valid_rows=valid_count,
            invalid_rows=invalid_count,
            duplicate_rows=duplicate_count,
            preview=previews
        )

    @classmethod
    def _normalize_date(cls, raw: str) -> Optional[str]:
        if not raw:
            return None
        raw = raw.strip()
        # Check YYYY-MM-DD
        if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
            return raw
        # Check DD/MM/YYYY or DD-MM-YYYY
        m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", raw)
        if m:
            d, month, y = m.groups()
            return f"{y}-{int(month):02d}-{int(d):02d}"
        return None

    @classmethod
    def _infer_category(cls, desc: str) -> str:
        d = desc.lower()
        if any(w in d for w in ["salary", "payroll", "dividend", "interest cr", "freelance"]):
            return "Income"
        elif any(w in d for w in ["rent", "landlord", "maintenance"]):
            return "Housing"
        elif any(w in d for w in ["swiggy", "zomato", "groceries", "supermarket", "blinkit", "zepto", "restaurant"]):
            return "Food & Dining"
        elif any(w in d for w in ["uber", "ola", "metro", "fuel", "petrol", "fastag"]):
            return "Transportation"
        elif any(w in d for w in ["electricity", "bescom", "wifi", "broadband", "jio", "airtel", "water"]):
            return "Utilities"
        elif any(w in d for w in ["zerodha", "groww", "sip", "mutual fund", "ppf", "nps"]):
            return "Investment"
        elif any(w in d for w in ["emi", "loan", "hdfc bank loan", "sbi loan"]):
            return "Debt & EMI"
        elif any(w in d for w in ["amazon", "flipkart", "myntra", "shopping"]):
            return "Shopping"
        elif any(w in d for w in ["apollo", "pharmacy", "hospital", "doctor"]):
            return "Healthcare"
        return "General Expense"
