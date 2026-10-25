from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import calendar
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.financial import Transaction, RecurringTransaction
from app.schemas.recurring import (
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
    RecurringTransactionConfirmRequest,
    RecurringTransactionDismissRequest,
    UpcomingOccurrence,
    UpcomingSummary,
    RecurringSummary,
)
from app.finance.intelligence.engine import IntelligenceEngine


def _add_months(orig_date: date, months_to_add: int) -> date:
    """Adds months handling varying month lengths and leap years."""
    month = orig_date.month - 1 + months_to_add
    year = orig_date.year + month // 12
    month = month % 12 + 1
    day = min(orig_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class RecurringTransactionService:
    """
    Production service managing the lifecycle, persistence, confirmation,
    and forward scheduling of user recurring transactions.
    """

    @classmethod
    def sync_and_get_detections(cls, user: User, db: Session) -> List[RecurringTransaction]:
        """
        Runs the Intelligence Engine detection across user transactions,
        persists newly detected patterns into recurring_transactions table,
        and returns all unresolved ('detected') items.
        """
        # 1. Fetch raw detected patterns
        patterns = IntelligenceEngine.detect_recurring_transactions(user, db)

        # Also detect recurring income (e.g., Salary, recurring consulting credits)
        lookback = date.today() - timedelta(days=180)
        income_txns = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.type == "income",
            Transaction.is_internal_transfer == False,
            Transaction.date >= lookback
        ).order_by(Transaction.date.asc()).all()

        income_groups: Dict[str, List[Transaction]] = {}
        for t in income_txns:
            clean = re.sub(r"[^a-zA-Z\s]", "", t.description).strip().lower()
            tokens = [tok for tok in clean.split() if len(tok) > 2]
            key = " ".join(tokens[:2]) if tokens else clean[:12]
            if key:
                income_groups.setdefault(key, []).append(t)

        for key, grp in income_groups.items():
            if len(grp) >= 2:
                amounts = [g.amount for g in grp]
                avg_amt = sum(amounts) / Decimal(len(amounts))
                last_d = grp[-1].date
                patterns.append(type("Pattern", (), {
                    "merchant_or_desc": grp[-1].description,
                    "category": grp[-1].category or "Salary",
                    "estimated_amount": avg_amt.quantize(Decimal("1.00")),
                    "frequency": "monthly",
                    "next_expected_date": _add_months(last_d, 1),
                    "occurrence_count": len(grp),
                    "confidence": "high" if len(grp) >= 3 else "medium",
                    "is_income": True
                })())

        # 2. Existing recurring records for this user
        existing_records = db.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == user.id
        ).all()

        existing_names = {
            re.sub(r"[^a-zA-Z0-9]", "", r.name.lower()): r
            for r in existing_records
        }

        # 3. Insert newly discovered patterns if not already tracked
        new_records_added = False
        for p in patterns:
            norm_name = re.sub(r"[^a-zA-Z0-9]", "", p.merchant_or_desc.lower())
            if norm_name in existing_names:
                # Already tracked (confirmed, dismissed, paused, or detected)
                continue

            is_income = getattr(p, "is_income", False) or "salary" in p.merchant_or_desc.lower()
            txn_type = "income" if is_income else "expense"

            rec = RecurringTransaction(
                user_id=user.id,
                name=p.merchant_or_desc,
                merchant=p.merchant_or_desc,
                transaction_type=txn_type,
                amount=p.estimated_amount,
                category=p.category,
                frequency=p.frequency,
                status="detected",
                confidence=p.confidence,
                detection_source="intelligence_engine",
                explanation=f"Identified from {p.occurrence_count} historical occurrences with consistent amounts and timing.",
                next_expected_date=p.next_expected_date,
                occurrence_count=p.occurrence_count,
                last_occurrence_date=p.next_expected_date - timedelta(days=30 if p.frequency == "monthly" else 7) if p.next_expected_date else None,
            )
            db.add(rec)
            existing_names[norm_name] = rec
            new_records_added = True

        if new_records_added:
            db.commit()

        # Return all currently detected (unreviewed) items
        return db.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == user.id,
            RecurringTransaction.status == "detected"
        ).order_by(RecurringTransaction.confidence.desc(), RecurringTransaction.created_at.desc()).all()

    @classmethod
    def list_recurring(
        cls,
        user: User,
        db: Session,
        status_filter: Optional[str] = None,
        txn_type: Optional[str] = None
    ) -> List[RecurringTransaction]:
        query = db.query(RecurringTransaction).filter(RecurringTransaction.user_id == user.id)
        if status_filter:
            query = query.filter(RecurringTransaction.status == status_filter)
        if txn_type:
            query = query.filter(RecurringTransaction.transaction_type == txn_type)
        return query.order_by(RecurringTransaction.created_at.desc()).all()

    @classmethod
    def get_by_id(cls, user: User, db: Session, item_id: str) -> RecurringTransaction:
        item = db.query(RecurringTransaction).filter(
            RecurringTransaction.id == item_id,
            RecurringTransaction.user_id == user.id
        ).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recurring transaction not found or access denied."
            )
        return item

    @classmethod
    def create_recurring(cls, user: User, db: Session, data: RecurringTransactionCreate) -> RecurringTransaction:
        item = RecurringTransaction(
            user_id=user.id,
            bank_account_id=data.bank_account_id,
            name=data.name,
            merchant=data.merchant or data.name,
            transaction_type=data.transaction_type,
            amount=data.amount,
            category=data.category,
            frequency=data.frequency,
            status="confirmed",
            confidence="high",
            detection_source="manual",
            explanation="Manually registered recurring transaction.",
            next_expected_date=data.next_expected_date or _add_months(date.today(), 1),
            start_date=data.start_date or date.today(),
            end_date=data.end_date,
            user_confirmed_at=datetime.now(timezone.utc),
            user_notes=data.user_notes,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def confirm_recurring(
        cls,
        user: User,
        db: Session,
        item_id: str,
        data: Optional[RecurringTransactionConfirmRequest] = None
    ) -> RecurringTransaction:
        item = cls.get_by_id(user, db, item_id)
        if item.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot confirm a cancelled recurring item."
            )

        item.status = "confirmed"
        item.user_confirmed_at = datetime.now(timezone.utc)

        if data:
            if data.name:
                item.name = data.name
            if data.amount:
                item.amount = data.amount
            if data.category:
                item.category = data.category
            if data.frequency:
                item.frequency = data.frequency
            if data.next_expected_date:
                item.next_expected_date = data.next_expected_date
            if data.user_notes:
                item.user_notes = data.user_notes

        # Mark source matching transactions as recurring
        tokens = [tok for tok in re.sub(r"[^a-zA-Z\s]", "", item.name).lower().split() if len(tok) > 2]
        if tokens:
            prefix = tokens[0]
            db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.description.ilike(f"%{prefix}%")
            ).update({"is_recurring": True}, synchronize_session=False)

        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def update_recurring(
        cls,
        user: User,
        db: Session,
        item_id: str,
        data: RecurringTransactionUpdate
    ) -> RecurringTransaction:
        item = cls.get_by_id(user, db, item_id)
        if item.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a cancelled recurring transaction."
            )

        if data.name is not None:
            item.name = data.name
        if data.merchant is not None:
            item.merchant = data.merchant
        if data.transaction_type is not None:
            item.transaction_type = data.transaction_type
        if data.amount is not None:
            item.amount = data.amount
        if data.category is not None:
            item.category = data.category
        if data.frequency is not None:
            item.frequency = data.frequency
        if data.next_expected_date is not None:
            item.next_expected_date = data.next_expected_date
        if data.start_date is not None:
            item.start_date = data.start_date
        if data.end_date is not None:
            item.end_date = data.end_date
        if data.user_notes is not None:
            item.user_notes = data.user_notes

        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def dismiss_recurring(
        cls,
        user: User,
        db: Session,
        item_id: str,
        dismiss_data: Optional[RecurringTransactionDismissRequest] = None
    ) -> RecurringTransaction:
        item = cls.get_by_id(user, db, item_id)
        item.status = "dismissed"
        if dismiss_data and dismiss_data.user_feedback:
            item.user_feedback = dismiss_data.user_feedback
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def pause_recurring(cls, user: User, db: Session, item_id: str) -> RecurringTransaction:
        item = cls.get_by_id(user, db, item_id)
        if item.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot pause a cancelled recurring item."
            )
        item.status = "paused"
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def reactivate_recurring(cls, user: User, db: Session, item_id: str) -> RecurringTransaction:
        item = cls.get_by_id(user, db, item_id)
        if item.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permanently cancelled item cannot be reactivated directly. Please create a new record."
            )
        item.status = "confirmed"
        # If next date is past, roll forward
        today = date.today()
        if item.next_expected_date and item.next_expected_date < today:
            while item.next_expected_date < today:
                if item.frequency == "weekly":
                    item.next_expected_date += timedelta(days=7)
                elif item.frequency == "fortnightly":
                    item.next_expected_date += timedelta(days=14)
                elif item.frequency == "quarterly":
                    item.next_expected_date = _add_months(item.next_expected_date, 3)
                elif item.frequency == "yearly":
                    item.next_expected_date = _add_months(item.next_expected_date, 12)
                else:
                    item.next_expected_date = _add_months(item.next_expected_date, 1)

        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def cancel_recurring(cls, user: User, db: Session, item_id: str) -> RecurringTransaction:
        item = cls.get_by_id(user, db, item_id)
        item.status = "cancelled"
        item.end_date = date.today()
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def get_upcoming_occurrences(
        cls,
        user: User,
        db: Session,
        horizon_days: int = 30
    ) -> UpcomingSummary:
        """
        Calculates expected upcoming occurrences for active confirmed items over the horizon.
        Handles calendar month lengths, leap years, and overdue states.
        """
        today = date.today()
        end_horizon = today + timedelta(days=horizon_days)

        active_items = db.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == user.id,
            RecurringTransaction.status == "confirmed"
        ).all()

        occurrences: List[UpcomingOccurrence] = []
        total_exp = Decimal("0.00")
        total_inc = Decimal("0.00")

        for item in active_items:
            if not item.next_expected_date:
                continue

            current_date = item.next_expected_date

            # If end_date set and passed, skip
            if item.end_date and item.end_date < today:
                continue

            # Iterate occurrences within horizon
            while current_date <= end_horizon:
                # Check end_date boundary
                if item.end_date and current_date > item.end_date:
                    break

                is_overdue = current_date < today
                days_until = (current_date - today).days

                occ = UpcomingOccurrence(
                    expected_date=current_date,
                    recurring_id=item.id,
                    name=item.name,
                    merchant=item.merchant,
                    amount=item.amount,
                    transaction_type=item.transaction_type,
                    category=item.category,
                    frequency=item.frequency,
                    status=item.status,
                    is_overdue=is_overdue,
                    days_until=days_until
                )
                occurrences.append(occ)

                if item.transaction_type == "expense":
                    total_exp += item.amount
                else:
                    total_inc += item.amount

                # Advance according to frequency
                if item.frequency == "weekly":
                    current_date += timedelta(days=7)
                elif item.frequency == "fortnightly":
                    current_date += timedelta(days=14)
                elif item.frequency == "quarterly":
                    current_date = _add_months(current_date, 3)
                elif item.frequency == "yearly":
                    current_date = _add_months(current_date, 12)
                else:
                    current_date = _add_months(current_date, 1)

        # Sort occurrences chronologically
        occurrences.sort(key=lambda o: o.expected_date)

        return UpcomingSummary(
            horizon_days=horizon_days,
            total_upcoming_expenses=total_exp,
            total_upcoming_income=total_inc,
            net_upcoming_cash_flow=total_inc - total_exp,
            occurrences=occurrences
        )

    @classmethod
    def get_recurring_summary(cls, user: User, db: Session) -> RecurringSummary:
        """
        Computes monthly recurring statistics, counts, and nearest upcoming occurrences.
        """
        all_items = db.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == user.id
        ).all()

        active = [i for i in all_items if i.status == "confirmed"]
        paused = [i for i in all_items if i.status == "paused"]
        pending = [i for i in all_items if i.status == "detected"]

        monthly_exp = Decimal("0.00")
        monthly_inc = Decimal("0.00")

        for item in active:
            # Convert to monthly equivalent
            amt = item.amount
            if item.frequency == "weekly":
                m_amt = amt * Decimal("52") / Decimal("12")
            elif item.frequency == "fortnightly":
                m_amt = amt * Decimal("26") / Decimal("12")
            elif item.frequency == "quarterly":
                m_amt = amt / Decimal("3")
            elif item.frequency == "yearly":
                m_amt = amt / Decimal("12")
            else:
                m_amt = amt

            if item.transaction_type == "expense":
                monthly_exp += m_amt
            else:
                monthly_inc += m_amt

        upcoming = cls.get_upcoming_occurrences(user, db, horizon_days=60)
        next_pay = next((o for o in upcoming.occurrences if o.transaction_type == "expense"), None)
        next_inc = next((o for o in upcoming.occurrences if o.transaction_type == "income"), None)

        return RecurringSummary(
            monthly_recurring_expenses=monthly_exp.quantize(Decimal("1.00")),
            monthly_recurring_income=monthly_inc.quantize(Decimal("1.00")),
            net_recurring_cash_flow=(monthly_inc - monthly_exp).quantize(Decimal("1.00")),
            active_count=len(active),
            paused_count=len(paused),
            pending_review_count=len(pending),
            next_upcoming_payment=next_pay,
            next_upcoming_income=next_inc,
        )
