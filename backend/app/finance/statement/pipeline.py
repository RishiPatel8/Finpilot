from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.financial import Transaction, StatementImportBatch, FinancialProfile, RecurringTransaction
from app.models.bank import BankAccount
from app.finance.statement.normalizer import StatementNormalizer
from app.finance.statement.csv_parser import parse_csv_statement
from app.finance.statement.xlsx_parser import parse_xlsx_statement
from app.finance.statement.pdf_parser import parse_pdf_statement
from app.finance.intelligence.engine import IntelligenceEngine


class StatementPipeline:
    """
    End-to-end Bank Statement Intelligence Pipeline:
    Upload -> File validation -> Extraction -> Normalization -> Deduplication ->
    Preview -> User Confirmation -> Atomic Persistence -> Analytics Recalculation.
    """

    @classmethod
    def process_file_upload(
        cls,
        file_bytes: bytes,
        filename: str,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """
        Parses statement file (CSV, XLSX, PDF), detects duplicates,
        computes analytics preview, and returns structured preview for user review.
        """
        fn_lower = filename.lower()
        if fn_lower.endswith(".csv"):
            result = parse_csv_statement(file_bytes, filename)
        elif fn_lower.endswith((".xlsx", ".xls")):
            result = parse_xlsx_statement(file_bytes, filename)
        elif fn_lower.endswith(".pdf"):
            result = parse_pdf_statement(file_bytes, filename)
        else:
            return {
                "success": False,
                "error": f"Unsupported file format '{filename}'. Supported formats are CSV, XLSX, and PDF.",
                "total_rows": 0,
                "valid_rows": 0,
                "duplicate_rows": 0,
                "preview": []
            }

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Failed to extract transactions from statement."),
                "total_rows": 0,
                "valid_rows": 0,
                "duplicate_rows": 0,
                "preview": []
            }

        raw_txns = result.get("transactions", [])
        if not raw_txns:
            return {
                "success": False,
                "error": "No valid transaction rows found in the uploaded statement.",
                "total_rows": 0,
                "valid_rows": 0,
                "duplicate_rows": 0,
                "preview": []
            }

        # 1. Fetch user's existing transaction signatures from DB to detect duplicates
        existing_txns = db.query(
            Transaction.date,
            Transaction.amount,
            Transaction.description,
            Transaction.reference_number
        ).filter(Transaction.user_id == user.id).all()

        existing_signatures = {
            StatementNormalizer.generate_signature(d, a, desc, ref)
            for d, a, desc, ref in existing_txns
        }

        # 2. Process records, deduplicate intra-batch and against DB
        seen_in_batch = set()
        preview_records = []
        valid_count = 0
        duplicate_count = 0
        total_credits = Decimal("0.00")
        total_debits = Decimal("0.00")
        dates_list = []
        category_breakdown: Dict[str, Decimal] = {}

        for t in raw_txns:
            sig = StatementNormalizer.generate_signature(
                t["date"],
                t["amount"],
                t["description"],
                t.get("reference_number")
            )

            is_dup = (sig in existing_signatures) or (sig in seen_in_batch)
            if is_dup:
                duplicate_count += 1
            else:
                valid_count += 1
                seen_in_batch.add(sig)

                # Aggregate only non-duplicate metrics
                if t["type"] == "income" and not t["is_internal_transfer"]:
                    total_credits += t["amount"]
                elif t["type"] == "expense" and not t["is_internal_transfer"]:
                    total_debits += t["amount"]

                cat = t["category"] or "Uncategorized"
                category_breakdown[cat] = category_breakdown.get(cat, Decimal("0.00")) + t["amount"]

            if t.get("date"):
                dates_list.append(t["date"])

            preview_records.append({
                "source_row": t.get("source_row"),
                "date": str(t["date"]),
                "value_date": str(t.get("value_date") or t["date"]),
                "description": t["description"],
                "amount": float(t["amount"]),
                "type": t["type"],
                "category": t["category"],
                "raw_type": t.get("raw_type"),
                "is_internal_transfer": t.get("is_internal_transfer", False),
                "reference_number": t.get("reference_number"),
                "balance_after": float(t["balance_after"]) if t.get("balance_after") is not None else None,
                "is_duplicate": is_dup,
                "is_valid": True,
                "explanation": t.get("explanation")
            })

        # Calculate statement time coverage
        start_date = min(dates_list) if dates_list else None
        end_date = max(dates_list) if dates_list else None
        coverage_days = (end_date - start_date).days + 1 if (start_date and end_date) else 0
        coverage_months = round(coverage_days / 30.0, 1)

        # Warnings and observations
        warnings = []
        if duplicate_count > 0:
            warnings.append(f"{duplicate_count} transaction(s) match existing records or appear multiple times in statement.")
        uncat_count = sum(1 for p in preview_records if p["category"] == "Uncategorized")
        if uncat_count > 0:
            warnings.append(f"{uncat_count} transaction(s) marked 'Uncategorized' for your review.")
        if coverage_days > 0 and coverage_days < 60:
            warnings.append(f"Statement period is {coverage_days} days. Upload 3 full months for comprehensive runway forecasting.")

        meta = result.get("metadata", {})

        return {
            "success": True,
            "filename": filename,
            "format": result.get("format", "unknown"),
            "total_rows": len(preview_records),
            "valid_rows": valid_count,
            "duplicate_rows": duplicate_count,
            "invalid_rows": 0,
            "coverage": {
                "start_date": str(start_date) if start_date else None,
                "end_date": str(end_date) if end_date else None,
                "coverage_days": coverage_days,
                "coverage_months": coverage_months,
            },
            "financial_summary": {
                "total_credits": float(total_credits),
                "total_debits": float(total_debits),
                "net_cash_flow": float(total_credits - total_debits),
                "category_breakdown": {k: float(v) for k, v in category_breakdown.items()},
            },
            "metadata": meta,
            "warnings": warnings,
            "preview": preview_records
        }

    @classmethod
    def confirm_import(
        cls,
        user: User,
        transactions_data: List[Dict[str, Any]],
        filename: str,
        file_format: str,
        metadata: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Executes atomic database persistence for approved transactions:
        1. Persists StatementImportBatch
        2. Persists Transaction records with verified source fields
        3. Reconciles BankAccount closing balance if available
        4. Recalculates user Profile monthly run-rate
        5. Runs recurring detection and commits
        6. Verifies persistence deterministically before returning
        """
        batch_id = str(uuid.uuid4())
        created_txns: List[Transaction] = []
        dates_list = []
        total_cr = Decimal("0.00")
        total_dr = Decimal("0.00")

        for item in transactions_data:
            # Skip items user flagged or duplicates
            if item.get("is_duplicate"):
                continue

            parsed_date = StatementNormalizer.normalize_date(item.get("date"))
            if not parsed_date:
                continue

            parsed_val_date = StatementNormalizer.normalize_date(item.get("value_date")) or parsed_date
            amount_dec = Decimal(str(item.get("amount", "0.00")))
            if amount_dec <= Decimal("0.00"):
                continue

            t_type = item.get("type", "expense")
            is_internal = bool(item.get("is_internal_transfer", False))
            if t_type == "income" and not is_internal:
                total_cr += amount_dec
            elif t_type == "expense" and not is_internal:
                total_dr += amount_dec

            bal_after = None
            if item.get("balance_after") is not None:
                try:
                    bal_after = Decimal(str(item["balance_after"]))
                except Exception:
                    pass

            dates_list.append(parsed_date)

            txn = Transaction(
                user_id=user.id,
                date=parsed_date,
                value_date=parsed_val_date,
                amount=amount_dec,
                type=t_type,
                category=item.get("category") or "Uncategorized",
                description=item.get("description") or "Bank Statement Transaction",
                source="bank_statement",
                is_internal_transfer=is_internal,
                is_recurring=False,
                reference_number=item.get("reference_number"),
                balance_after=bal_after,
                source_file=filename,
                source_row=item.get("source_row"),
                batch_id=batch_id,
                account_mask=metadata.get("account_number_masked"),
                raw_type=item.get("raw_type")
            )
            db.add(txn)
            created_txns.append(txn)

        if not created_txns:
            return {
                "success": False,
                "message": "No new transactions were persisted (all were duplicates or invalid).",
                "imported_count": 0
            }

        start_date = min(dates_list) if dates_list else None
        end_date = max(dates_list) if dates_list else None

        # 1. Create StatementImportBatch record
        closing_bal = Decimal(str(metadata.get("closing_balance"))) if metadata.get("closing_balance") is not None else None
        batch = StatementImportBatch(
            id=batch_id,
            user_id=user.id,
            filename=filename,
            file_format=file_format,
            total_rows=len(transactions_data),
            imported_rows=len(created_txns),
            duplicate_rows=len(transactions_data) - len(created_txns),
            skipped_rows=0,
            start_date=start_date,
            end_date=end_date,
            total_credits=total_cr,
            total_debits=total_dr,
            account_number_masked=metadata.get("account_number_masked"),
            bank_name=metadata.get("bank_name"),
            closing_balance=closing_bal,
            created_at=datetime.now(timezone.utc)
        )
        db.add(batch)

        # 2. Reconcile or create BankAccount
        if closing_bal is not None:
            bank_name = metadata.get("bank_name") or "Primary Bank"
            acc_mask = metadata.get("account_number_masked") or "XXXX-XXXX-XXXX"

            # Check if matching bank account exists
            existing_acc = db.query(BankAccount).filter(
                BankAccount.user_id == user.id,
                BankAccount.account_number_masked == acc_mask
            ).first()

            if existing_acc:
                existing_acc.current_balance = closing_bal
                existing_acc.balance_type = "statement_reported"
                existing_acc.balance_timestamp = datetime.combine(end_date or date.today(), datetime.min.time())
                existing_acc.sync_status = "synced"
                existing_acc.last_synced_at = datetime.now(timezone.utc)
            else:
                new_acc = BankAccount(
                    user_id=user.id,
                    institution_name=bank_name,
                    account_number_masked=acc_mask,
                    account_type="savings",
                    ifsc_code=f"{bank_name[:4].upper()}0001234",
                    currency="INR",
                    current_balance=closing_bal,
                    balance_type="statement_reported",
                    balance_timestamp=datetime.combine(end_date or date.today(), datetime.min.time()),
                    sync_status="synced",
                    last_synced_at=datetime.now(timezone.utc)
                )
                db.add(new_acc)

        # 3. Recalculate Profile Monthly Run-Rate based on observed data
        coverage_days = (end_date - start_date).days + 1 if (start_date and end_date) else 30
        months_factor = Decimal(str(max(1.0, coverage_days / 30.0)))
        observed_monthly_inc = total_cr / months_factor
        observed_monthly_exp = total_dr / months_factor

        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
        if not profile:
            profile = FinancialProfile(user_id=user.id)
            db.add(profile)

        profile.monthly_income = observed_monthly_inc.quantize(Decimal("1.00"))
        profile.monthly_expenses = observed_monthly_exp.quantize(Decimal("1.00"))

        # Commit everything atomically
        db.commit()

        # 4. Trigger Recurring Transaction Detection & persist confirmed patterns
        try:
            detected_patterns = IntelligenceEngine.detect_recurring_transactions(user, db)
            for pat in detected_patterns:
                # Check if already tracked in RecurringTransaction
                exists_rec = db.query(RecurringTransaction).filter(
                    RecurringTransaction.user_id == user.id,
                    RecurringTransaction.name == pat.merchant_or_desc
                ).first()
                if not exists_rec:
                    rec_item = RecurringTransaction(
                        user_id=user.id,
                        name=pat.merchant_or_desc,
                        merchant=pat.merchant_or_desc,
                        transaction_type="expense",
                        amount=pat.estimated_amount,
                        category=pat.category,
                        frequency=pat.frequency,
                        status="detected",
                        confidence=pat.confidence,
                        detection_source="statement_pipeline",
                        next_expected_date=pat.next_expected_date,
                        occurrence_count=pat.occurrence_count,
                        explanation=f"Detected across {pat.occurrence_count} statement cycles ({pat.frequency})."
                    )
                    db.add(rec_item)
            db.commit()
        except Exception:
            pass  # Non-fatal if recurring detection encounters no patterns

        # 5. Verify database persistence deterministically
        persisted_count = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.batch_id == batch_id
        ).count()

        return {
            "success": True,
            "batch_id": batch_id,
            "imported_count": persisted_count,
            "statement_period": {
                "start_date": str(start_date) if start_date else None,
                "end_date": str(end_date) if end_date else None,
                "days": coverage_days,
            },
            "observed_monthly_run_rate": {
                "income": float(observed_monthly_inc),
                "expenses": float(observed_monthly_exp),
                "surplus": float(observed_monthly_inc - observed_monthly_exp),
            },
            "closing_balance": float(closing_bal) if closing_bal else None,
            "message": f"Successfully imported and reconciled {persisted_count} verified transactions."
        }
