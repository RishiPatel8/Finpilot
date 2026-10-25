import uuid
import logging
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.agent import PendingAction
from app.models.financial import (
    Transaction,
    Liability,
    RecurringTransaction,
    FinancialGoal,
    FinancialProfile,
    AssetHolding,
)
from app.finance.recurring.service import RecurringTransactionService
from app.schemas.agent import (
    PendingActionResponse,
    PendingActionPreview,
    ActionConfirmResponse,
    ActionCancelResponse,
)

logger = logging.getLogger("finpilot.ai.action_service")


class ActionPlanner:
    """
    Constructs validated pending actions awaiting explicit user authorization.
    All write commands are staged here; nothing is written to financial tables without confirmation.
    """

    @classmethod
    def create_pending_action(
        cls,
        user: User,
        action_type: str,
        target_entity: str,
        parameters: Dict[str, Any],
        db: Session,
        channel: str = "web"
    ) -> PendingAction:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=15)
        idempotency_key = f"{user.id}_{action_type}_{int(now.timestamp())}_{uuid.uuid4().hex[:8]}"

        preview = cls._generate_preview(action_type, parameters)

        pending = PendingAction(
            user_id=user.id,
            action_type=action_type,
            target_entity=target_entity,
            parameters=parameters,
            preview=preview.model_dump(),
            status="awaiting_confirmation",
            idempotency_key=idempotency_key,
            created_at=now,
            expires_at=expires_at,
            channel=channel
        )
        db.add(pending)
        db.commit()
        db.refresh(pending)
        return pending

    @classmethod
    def _generate_preview(cls, action_type: str, params: Dict[str, Any]) -> PendingActionPreview:
        items: List[Dict[str, str]] = []

        if action_type == "create_debt":
            amt = params.get("principal", 0.0)
            rate = params.get("interest_rate", 0.0)
            period = params.get("interest_period", "annual")
            tenure = params.get("tenure_months", 12)
            dtype = params.get("debt_type", "payable")
            counterparty = params.get("counterparty") or params.get("name", "Counterparty")
            is_receivable = (dtype == "receivable")
            type_label = "Money Lent (Receivable)" if is_receivable else "Debt / Loan (Payable)"

            rate_label = f"{rate}% {period}" if rate > 0 else "0% (Interest-Free)"
            emi_val = f"₹{params.get('monthly_emi', 0.0):,.0f}/month" if params.get("monthly_emi") else "N/A"

            items = [
                {"label": "Record Type", "value": type_label},
                {"label": "Counterparty", "value": str(counterparty)},
                {"label": "Principal Amount", "value": f"₹{amt:,.0f}"},
                {"label": "Interest Rate", "value": rate_label},
                {"label": "Monthly EMI", "value": emi_val},
                {"label": "Tenure", "value": f"{tenure} months"},
            ]
            if params.get("notes"):
                items.append({"label": "Notes", "value": str(params["notes"])})

            if is_receivable:
                summary = f"Record ₹{amt:,.0f} lent to {counterparty} at {rate_label} to track repayment."
                title = f"Record Money Lent: {counterparty}"
            else:
                summary = f"Record a debt of ₹{amt:,.0f} borrowed from {counterparty} at {rate_label}."
                title = f"Create Debt Record: {params.get('name', counterparty)}"

        elif action_type == "repay_debt":
            amt = params.get("amount")
            name = params.get("name", "Active Loan")
            counterparty = params.get("counterparty") or name
            items = [
                {"label": "Loan / Debt Name", "value": str(name)},
                {"label": "Counterparty", "value": str(counterparty)},
                {"label": "Repayment Amount", "value": f"₹{amt:,.0f}" if amt else "Full Balance"},
                {"label": "Updated Status", "value": "Repaid / Closed"},
            ]
            summary = f"Mark the loan/debt record with {counterparty} as fully repaid."
            title = f"Mark Loan Repaid: {counterparty}"

        elif action_type == "create_transaction":
            amt = params.get("amount", 0.0)
            ttype = params.get("type", "expense").title()
            cat = params.get("category", "General")
            items = [
                {"label": "Transaction Type", "value": ttype},
                {"label": "Amount", "value": f"₹{amt:,.0f}"},
                {"label": "Category", "value": cat},
                {"label": "Description", "value": str(params.get("description", f"{ttype} on {cat}"))},
                {"label": "Date", "value": str(params.get("date", date.today()))},
            ]
            summary = f"Record an authenticated {ttype.lower()} entry of ₹{amt:,.0f} under {cat}."
            title = f"Record {ttype}: ₹{amt:,.0f}"

        elif action_type == "create_recurring_commitment":
            amt = params.get("amount", 0.0)
            items = [
                {"label": "Commitment Name", "value": str(params.get("name", "Monthly Bill"))},
                {"label": "Amount", "value": f"₹{amt:,.0f}"},
                {"label": "Frequency", "value": str(params.get("frequency", "monthly")).capitalize()},
                {"label": "Category", "value": str(params.get("category", "Utilities"))},
                {"label": "Next Expected Date", "value": str(params.get("next_expected_date", date.today()))},
            ]
            summary = f"Add confirmed recurring commitment of ₹{amt:,.0f}/month to forward cash-flow scheduler."
            title = f"Add Recurring Bill: {params.get('name', 'Bill')}"

        elif action_type in ["pause_recurring_commitment", "cancel_recurring_commitment"]:
            name = params.get("name", "Subscription")
            action_verb = "Pause" if "pause" in action_type else "Cancel"
            items = [
                {"label": "Target Subscription", "value": name},
                {"label": "Proposed Status", "value": "Paused" if "pause" in action_type else "Cancelled"},
            ]
            summary = f"{action_verb} {name} to exclude it from upcoming 30-day cash flow projections."
            title = f"{action_verb} Subscription: {name}"

        elif action_type == "update_budget":
            cat = params.get("category", "Living Expenses")
            target = params.get("target_amount", 0.0)
            adj = params.get("adjustment_pct")
            if adj is not None:
                items = [
                    {"label": "Budget Category", "value": cat},
                    {"label": "Adjustment", "value": f"{adj:+}%"},
                ]
                summary = f"Adjust monthly budget for {cat} by {adj:+}%."
            else:
                items = [
                    {"label": "Budget Category", "value": cat},
                    {"label": "New Monthly Allocation", "value": f"₹{target:,.0f}"},
                ]
                summary = f"Update monthly budget allocation for {cat} to ₹{target:,.0f}."
            title = f"Update Budget: {cat}"

        elif action_type == "create_savings_goal":
            amt = params.get("target_amount", 100000.0)
            target_date = params.get("target_date", date.today())
            items = [
                {"label": "Goal Name", "value": str(params.get("name", "Financial Goal"))},
                {"label": "Target Amount", "value": f"₹{amt:,.0f}"},
                {"label": "Target Completion Date", "value": str(target_date)},
                {"label": "Priority", "value": str(params.get("priority", "medium")).capitalize()},
            ]
            summary = f"Create a tracked financial savings goal of ₹{amt:,.0f} by {target_date}."
            title = f"Create Goal: {params.get('name', 'Savings Goal')}"

        elif action_type == "create_asset_holding":
            amt = params.get("invested_value", 0.0)
            cur = params.get("current_value", amt)
            ret_rate = params.get("expected_return_rate", 8.0)
            cat = str(params.get("category", "equity_mf")).replace("_", " ").title()
            items = [
                {"label": "Investment / Asset", "value": str(params.get("name", "Investment"))},
                {"label": "Category", "value": cat},
                {"label": "Invested Amount", "value": f"₹{amt:,.0f}"},
                {"label": "Current Value", "value": f"₹{cur:,.0f}"},
                {"label": "Expected Return", "value": f"{ret_rate}% p.a."},
            ]
            summary = f"Record a new investment holding of ₹{amt:,.0f} ({cat}) in your portfolio."
            title = f"Add Investment: {params.get('name', 'Asset')}"

        elif action_type == "update_tax_regime":
            reg = str(params.get("tax_regime", "new")).upper()
            items = [
                {"label": "Tax Regime Preference", "value": f"{reg} Regime"},
                {"label": "Applicable AY", "value": "AY 2025-26 & Future"}
            ]
            summary = f"Update your default tax planning regime preference to the {reg} Tax Regime."
            title = f"Switch Tax Regime: {reg}"

        else:
            items = [{"label": k, "value": str(v)} for k, v in params.items()]
            summary = f"Execute {action_type} on {params.get('target_entity', 'financial record')}."
            title = f"Proposed Action: {action_type}"

        return PendingActionPreview(
            title=title,
            summary=summary,
            items=items,
            disclaimer="This will record a financial record in your FinPilot account. It does not execute a real bank transfer, loan disbursement, or payment."
        )


class ActionExecutor:
    """
    Executes user-confirmed pending actions with strict authorization,
    expiration verification, idempotency protection, and database transactional integrity.
    """

    @classmethod
    def confirm_and_execute(
        cls,
        action_id: str,
        user: User,
        db: Session,
        idempotency_key: Optional[str] = None
    ) -> ActionConfirmResponse:
        now = datetime.now(timezone.utc)

        # 1. Fetch pending action strictly scoped to authenticated user
        action = db.query(PendingAction).filter(
            PendingAction.id == action_id,
            PendingAction.user_id == user.id
        ).first()

        if not action:
            logger.warning(f"Pending action {action_id} not found for user {user.id}")
            return ActionConfirmResponse(
                status="failed",
                action_id=action_id,
                action_type="unknown",
                message="Action not found or you are not authorized to execute it."
            )

        # 2. Idempotency Check: Already succeeded
        if action.status == "succeeded":
            logger.info(f"Action {action_id} already executed successfully (idempotent replay).")
            return ActionConfirmResponse(
                status="succeeded",
                action_id=action.id,
                action_type=action.action_type,
                message="Action was already executed and verified successfully.",
                result=action.execution_result,
                verified_at=action.executed_at.isoformat() if action.executed_at else now.isoformat()
            )

        # 3. Expiration Check
        # Ensure action.expires_at is timezone-aware for comparison
        expires_at = action.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            action.status = "expired"
            action.error_message = f"Action proposal expired at {expires_at.isoformat()}."
            db.commit()
            return ActionConfirmResponse(
                status="expired",
                action_id=action.id,
                action_type=action.action_type,
                message="This proposal has expired (proposals are valid for 15 minutes). Please request the action again."
            )

        # 4. Terminal State Check
        if action.status in ["cancelled", "failed"]:
            return ActionConfirmResponse(
                status=action.status,
                action_id=action.id,
                action_type=action.action_type,
                message=f"Action cannot be executed because it is currently in '{action.status}' state."
            )

        # 5. Transition to EXECUTING
        action.status = "executing"
        db.flush()

        try:
            result = cls._dispatch_execution(action, user, db)

            # Mark SUCCEEDED and verify persistence
            action.status = "succeeded"
            action.executed_at = now
            action.execution_result = result
            action.error_message = None
            db.commit()
            db.refresh(action)

            logger.info(f"Action {action.id} ({action.action_type}) succeeded for user {user.id}")
            return ActionConfirmResponse(
                status="succeeded",
                action_id=action.id,
                action_type=action.action_type,
                message=f"Successfully executed and persisted {action.preview.get('title', action.action_type)}.",
                result=result,
                verified_at=now.isoformat()
            )

        except Exception as e:
            db.rollback()
            logger.exception(f"Action {action_id} execution failed: {e}")
            action.status = "failed"
            action.error_message = str(e)
            db.commit()

            return ActionConfirmResponse(
                status="failed",
                action_id=action.id,
                action_type=action.action_type,
                message=f"Execution failed: {str(e)}"
            )

    @classmethod
    def cancel_action(cls, action_id: str, user: User, db: Session) -> ActionCancelResponse:
        action = db.query(PendingAction).filter(
            PendingAction.id == action_id,
            PendingAction.user_id == user.id
        ).first()

        if not action:
            return ActionCancelResponse(
                status="failed",
                action_id=action_id,
                message="Action not found or you are not authorized to cancel it."
            )

        if action.status in ["succeeded", "executing"]:
            return ActionCancelResponse(
                status="failed",
                action_id=action_id,
                message=f"Cannot cancel an action that is already in '{action.status}' state."
            )

        action.status = "cancelled"
        db.commit()
        return ActionCancelResponse(
            status="cancelled",
            action_id=action_id,
            message="Proposed action has been safely cancelled. No changes were made to your records."
        )

    # --- Authoritative Execution Handlers ---

    @classmethod
    def _dispatch_execution(cls, action: PendingAction, user: User, db: Session) -> Dict[str, Any]:
        p = action.parameters
        atype = action.action_type

        if atype == "create_transaction":
            txn_date = date.fromisoformat(p["date"]) if "date" in p else date.today()
            txn = Transaction(
                user_id=user.id,
                date=txn_date,
                amount=Decimal(str(p["amount"])),
                type=p.get("type", "expense"),
                category=p.get("category", "General"),
                description=p.get("description", "Manual record via AI CFO"),
                source="ai_agent",
                is_internal_transfer=False,
                is_recurring=p.get("is_recurring", False)
            )
            db.add(txn)
            db.flush()
            # Verify persistence
            persisted = db.query(Transaction).filter_by(id=txn.id, user_id=user.id).first()
            if not persisted:
                raise RuntimeError("Persistence verification failed for Transaction.")
            return {
                "entity": "transaction",
                "id": txn.id,
                "amount": float(txn.amount),
                "type": txn.type,
                "category": txn.category,
                "description": txn.description,
                "date": str(txn.date)
            }

        elif atype == "create_debt":
            principal = Decimal(str(p["principal"]))
            rate = Decimal(str(p.get("interest_rate", 0.0)))
            period = str(p.get("interest_period", "annual")).lower()
            dtype = str(p.get("debt_type", "payable")).lower()
            counterparty = p.get("counterparty")
            name = p.get("name")
            if not name:
                name = f"Money Lent to {counterparty}" if dtype == "receivable" and counterparty else (f"Debt to {counterparty}" if counterparty else "Personal Loan")

            emi = Decimal(str(p.get("monthly_emi", 0.0)))
            tenure = int(p.get("tenure_months", 12))
            notes = p.get("notes")

            liab = Liability(
                user_id=user.id,
                name=name,
                principal=principal,
                interest_rate=rate,
                monthly_emi=emi,
                tenure_months=tenure,
                remaining_months=tenure,
                debt_type=dtype,
                counterparty=counterparty,
                interest_period=period,
                status="active",
                notes=notes
            )
            db.add(liab)
            db.flush()
            # Verify persistence
            persisted = db.query(Liability).filter_by(id=liab.id, user_id=user.id).first()
            if not persisted:
                raise RuntimeError("Persistence verification failed for Liability.")
            return {
                "entity": "liability",
                "id": liab.id,
                "name": liab.name,
                "debt_type": liab.debt_type,
                "counterparty": liab.counterparty,
                "principal": float(liab.principal),
                "interest_rate": float(liab.interest_rate),
                "interest_period": liab.interest_period,
                "monthly_emi": float(liab.monthly_emi),
                "tenure_months": liab.tenure_months,
                "status": liab.status
            }

        elif atype == "repay_debt":
            amt = p.get("amount")
            name = p.get("name")
            counterparty = p.get("counterparty")
            loan_id = p.get("liability_id")

            query = db.query(Liability).filter(
                Liability.user_id == user.id,
                Liability.status == "active"
            )
            if loan_id:
                query = query.filter(Liability.id == loan_id)
            elif name:
                query = query.filter(Liability.name.ilike(f"%{name}%"))
            elif counterparty:
                query = query.filter(
                    (Liability.counterparty.ilike(f"%{counterparty}%")) |
                    (Liability.name.ilike(f"%{counterparty}%"))
                )
            elif amt is not None:
                query = query.filter(Liability.principal == Decimal(str(amt)))

            target_loan = query.first()
            if not target_loan:
                # If no direct match, check all active debts
                all_active = db.query(Liability).filter(
                    Liability.user_id == user.id,
                    Liability.status == "active"
                ).all()
                if amt is not None:
                    matched = [l for l in all_active if abs(float(l.principal) - float(amt)) < 1.0]
                    if matched:
                        target_loan = matched[0]
                elif len(all_active) == 1:
                    target_loan = all_active[0]

            if not target_loan:
                raise ValueError("No matching active loan or debt record was found to mark as repaid.")

            target_loan.status = "repaid"
            target_loan.remaining_months = 0
            db.flush()
            # Verify persistence
            verified = db.query(Liability).filter_by(id=target_loan.id, user_id=user.id, status="repaid").first()
            if not verified:
                raise RuntimeError("Persistence verification failed for loan repayment.")
            return {
                "entity": "liability",
                "id": target_loan.id,
                "name": target_loan.name,
                "counterparty": target_loan.counterparty,
                "principal": float(target_loan.principal),
                "status": "repaid"
            }

        elif atype == "create_recurring_commitment":
            next_d = date.fromisoformat(p["next_expected_date"]) if "next_expected_date" in p else date.today()
            rec = RecurringTransaction(
                user_id=user.id,
                name=p.get("name", "Monthly Bill"),
                transaction_type=p.get("transaction_type", "expense"),
                amount=Decimal(str(p["amount"])),
                category=p.get("category", "Utilities"),
                frequency=p.get("frequency", "monthly"),
                status="confirmed",
                confidence="high",
                detection_source="ai_agent",
                explanation=p.get("explanation", "Created via AI CFO agent confirmation"),
                next_expected_date=next_d,
                user_confirmed_at=datetime.now(timezone.utc)
            )
            db.add(rec)
            db.flush()
            # Verify persistence
            persisted = db.query(RecurringTransaction).filter_by(id=rec.id, user_id=user.id).first()
            if not persisted:
                raise RuntimeError("Persistence verification failed for RecurringTransaction.")
            return {
                "entity": "recurring_transaction",
                "id": rec.id,
                "name": rec.name,
                "amount": float(rec.amount),
                "category": rec.category,
                "status": rec.status,
                "next_expected_date": str(rec.next_expected_date)
            }

        elif atype in ["pause_recurring_commitment", "cancel_recurring_commitment"]:
            name = p.get("name", "").lower()
            rec = db.query(RecurringTransaction).filter(
                RecurringTransaction.user_id == user.id,
                RecurringTransaction.name.ilike(f"%{name}%")
            ).first()

            if not rec:
                raise ValueError(f"No active recurring commitment matching '{p.get('name')}' was found.")

            if atype == "pause_recurring_commitment":
                res = RecurringTransactionService.pause_recurring(rec.id, user, db)
            else:
                res = RecurringTransactionService.cancel_recurring(rec.id, user, db)

            return {
                "entity": "recurring_transaction",
                "id": rec.id,
                "name": rec.name,
                "new_status": res.status
            }

        elif atype == "update_budget":
            profile = db.query(FinancialProfile).filter_by(user_id=user.id).first()
            if not profile:
                profile = FinancialProfile(user_id=user.id)
                db.add(profile)

            if p.get("is_relative"):
                adj = Decimal(str(p.get("adjustment_pct", 0.0)))
                factor = Decimal("1.0") + (adj / Decimal("100.0"))
                profile.monthly_expenses = (Decimal(str(profile.monthly_expenses or 35000.0)) * factor).quantize(Decimal("0.01"))
            else:
                profile.monthly_expenses = Decimal(str(p.get("target_amount", 40000.0)))

            db.flush()
            return {
                "entity": "financial_profile",
                "monthly_expenses": float(profile.monthly_expenses),
                "category": p.get("category", "Living Expenses")
            }

        elif atype == "create_savings_goal":
            tdate = date.fromisoformat(p["target_date"]) if "target_date" in p else date.today() + timedelta(days=365)
            goal = FinancialGoal(
                user_id=user.id,
                name=p.get("name", "Savings Goal"),
                category=p.get("category", "custom"),
                target_amount=Decimal(str(p.get("target_amount", 100000.0))),
                current_amount=Decimal("0.00"),
                target_date=tdate,
                priority=p.get("priority", "medium")
            )
            db.add(goal)
            db.flush()
            persisted = db.query(FinancialGoal).filter_by(id=goal.id, user_id=user.id).first()
            if not persisted:
                raise RuntimeError("Persistence verification failed for FinancialGoal.")
            return {
                "entity": "financial_goal",
                "id": goal.id,
                "name": goal.name,
                "target_amount": float(goal.target_amount),
                "target_date": str(goal.target_date)
            }

        elif atype == "create_asset_holding":
            inv_val = Decimal(str(p.get("invested_value", 0.0)))
            cur_val = Decimal(str(p.get("current_value", inv_val)))
            asset = AssetHolding(
                user_id=user.id,
                name=p.get("name", "Investment Holding"),
                category=p.get("category", "equity_mf"),
                invested_value=inv_val,
                current_value=cur_val,
                expected_return_rate=Decimal(str(p.get("expected_return_rate", 12.0)))
            )
            db.add(asset)
            db.flush()
            persisted = db.query(AssetHolding).filter_by(id=asset.id, user_id=user.id).first()
            if not persisted:
                raise RuntimeError("Persistence verification failed for AssetHolding.")
            return {
                "entity": "asset_holding",
                "id": asset.id,
                "name": asset.name,
                "category": asset.category,
                "invested_value": float(asset.invested_value),
                "current_value": float(asset.current_value)
            }

        elif atype == "update_tax_regime":
            profile = db.query(FinancialProfile).filter_by(user_id=user.id).first()
            if not profile:
                profile = FinancialProfile(user_id=user.id)
                db.add(profile)
            reg = str(p.get("tax_regime", "new")).lower()
            profile.tax_regime_preference = reg
            db.flush()
            return {
                "entity": "financial_profile",
                "tax_regime_preference": profile.tax_regime_preference
            }

        else:
            raise NotImplementedError(f"Action type '{atype}' is not supported by the authoritative action executor.")
