import logging
import re
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.financial import (
    Transaction,
    Liability,
    AssetHolding,
    FinancialGoal,
    RecurringTransaction,
    FinancialProfile
)
from app.models.bank import BankAccount
from app.core.config import settings

logger = logging.getLogger("finpilot.ai.context")


class FinancialContextService:
    """
    Authoritative, authenticated financial context aggregator for AI CFO 2.0.
    Gathers a canonical, structured representation of the authenticated user's
    entire financial standing across accounts, transactions, budgets, recurring
    commitments, savings goals, intelligence metrics, and active page context.
    """

    @classmethod
    def get_complete_financial_context(
        cls,
        user: Optional[User],
        db: Session,
        page_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a verified, user-scoped financial context dictionary.
        Safe for consumption by deterministic calculation tools and LLM prompt context.
        """
        if not user:
            return cls._build_guest_context(page_context)

        context: Dict[str, Any] = {
            "user_id": user.id,
            "user_name": user.full_name,
            "user_role": user.role,
            "auth_provider": user.auth_provider,
            "currency": "INR",
            "as_of_date": date.today().isoformat(),
        }

        # 1. Financial Profile & Baseline Figures
        profile_data = cls._get_profile_context(user)
        context.update(profile_data)

        # 2. Bank Accounts & Liquid Assets
        accounts_data = cls._get_accounts_context(user, db)
        context.update(accounts_data)

        # 3. Liabilities & Debt Commitments
        liabilities_data = cls._get_liabilities_context(user)
        context.update(liabilities_data)

        # 4. Recent Transactions & Category Aggregations
        transactions_data = cls._get_transactions_context(user, db)
        context.update(transactions_data)

        # 5. Budget Allocations & Performance
        budget_data = cls._get_budget_context(user, db)
        context.update(budget_data)

        # 6. Recurring Commitments & Forward Calendar
        recurring_data = cls._get_recurring_context(user, db)
        context.update(recurring_data)

        # 7. Savings Goals & Feasibility
        goals_data = cls._get_goals_context(user, db)
        context.update(goals_data)

        # 8. Intelligence Engine Canonical Snapshot & Anomalies
        intelligence_data = cls._get_intelligence_context(user, db)
        context.update(intelligence_data)

        # 9. Page & Interaction Context
        if page_context:
            context["active_page"] = page_context.get("page", "overview")
            context["page_metadata"] = {
                k: v for k, v in page_context.items()
                if k not in ["password", "token", "auth"]
            }
        else:
            context["active_page"] = "overview"
            context["page_metadata"] = {}

        return context

    @classmethod
    def _build_guest_context(cls, page_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Authentic empty context for unauthenticated guest sessions."""
        return {
            "user_id": "guest",
            "user_name": "Guest Visitor",
            "user_role": "guest",
            "currency": "INR",
            "is_guest_demo": False,
            "is_authenticated": False,
            "monthly_income": 0.0,
            "monthly_expenses": 0.0,
            "monthly_surplus": 0.0,
            "current_savings": 0.0,
            "verified_bank_balance": 0.0,
            "net_worth": 0.0,
            "total_debt": 0.0,
            "monthly_emi": 0.0,
            "savings_rate_pct": 0.0,
            "emergency_runway_months": 0.0,
            "bank_accounts": [],
            "recurring_monthly_expenses": 0.0,
            "recurring_commitments": [],
            "budget_categories": [],
            "data_sufficiency": {
                "status": "unauthenticated",
                "message": "User is not logged in. No financial statement or account data is connected."
            },
            "active_page": page_context.get("page", "overview") if page_context else "overview",
            "page_metadata": page_context or {},
        }

    @classmethod
    def _get_profile_context(cls, user: User) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "monthly_income": 0.0,
            "monthly_expenses": 0.0,
            "monthly_surplus": 0.0,
            "tax_regime": "new",
            "risk_profile": "moderate",
        }
        if user.profile:
            income = float(user.profile.monthly_income or 0.0)
            expenses = float(user.profile.monthly_expenses or 0.0)
            data["monthly_income"] = income
            data["monthly_expenses"] = expenses
            data["monthly_surplus"] = max(0.0, income - expenses)
            data["tax_regime"] = getattr(user.profile, "tax_regime_preference", "new")
            data["risk_profile"] = getattr(user.profile, "risk_tolerance", "moderate")
            if hasattr(user.profile, "age") and user.profile.age:
                data["age"] = user.profile.age
        return data

    @classmethod
    def _get_accounts_context(cls, user: User, db: Session) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "bank_accounts": [],
            "verified_bank_balance": 0.0,
            "manual_assets_total": 0.0,
            "current_savings": 0.0,
            "asset_breakdown": {},
        }
        # Linked bank accounts
        if user.bank_accounts:
            synced_total = 0.0
            accounts_list = []
            for acc in user.bank_accounts:
                bal = float(acc.current_balance or 0.0)
                if acc.sync_status == "synced":
                    synced_total += bal
                is_sandbox = getattr(settings, "BANK_PROVIDER", "sandbox") == "sandbox"
                accounts_list.append({
                    "id": acc.id,
                    "institution": f"{acc.institution_name} ({'Sandbox' if is_sandbox else 'Live FIU'})",
                    "account_masked": acc.account_number_masked,
                    "account_type": acc.account_type,
                    "balance": bal,
                    "status": acc.sync_status,
                    "last_synced": acc.last_synced_at.isoformat() if acc.last_synced_at else None,
                })
            data["bank_accounts"] = accounts_list
            data["verified_bank_balance"] = synced_total
            data["current_savings"] = synced_total

        # Manual investment assets
        if user.assets:
            total_assets = 0.0
            categories: Dict[str, float] = {}
            for asset in user.assets:
                val = float(asset.current_value or 0.0)
                total_assets += val
                cat = asset.category or "other"
                categories[cat] = categories.get(cat, 0.0) + val

            data["manual_assets_total"] = total_assets
            data["asset_breakdown"] = categories
            # Liquid MF, Cash, FD add to liquid savings
            liquid_manual = categories.get("liquid_mf", 0.0) + categories.get("cash", 0.0) + categories.get("fd", 0.0)
            data["current_savings"] = max(data["current_savings"], data["verified_bank_balance"] + liquid_manual)

        return data

    @classmethod
    def _get_liabilities_context(cls, user: User) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "total_debt": 0.0,
            "monthly_emi": 0.0,
            "debt_count": 0,
            "liabilities_list": [],
            "total_receivables": 0.0,
            "receivables_count": 0,
            "receivables_list": [],
        }
        if user.liabilities:
            total_principal = 0.0
            total_emi = 0.0
            total_receivables = 0.0
            items = []
            receivables = []
            for item in user.liabilities:
                principal = float(item.principal or 0.0)
                emi = float(item.monthly_emi or 0.0)
                dtype = getattr(item, "debt_type", "payable") or "payable"
                status = getattr(item, "status", "active") or "active"

                item_info = {
                    "id": item.id,
                    "name": item.name,
                    "principal": principal,
                    "monthly_emi": emi,
                    "interest_rate_pct": float(item.interest_rate or 0.0),
                    "interest_period": getattr(item, "interest_period", "annual"),
                    "tenure_months": getattr(item, "tenure_months", 12),
                    "remaining_months": getattr(item, "remaining_months", 12),
                    "debt_type": dtype,
                    "counterparty": getattr(item, "counterparty", None),
                    "status": status,
                    "notes": getattr(item, "notes", None)
                }

                if dtype == "receivable":
                    if status == "active":
                        total_receivables += principal
                    receivables.append(item_info)
                else:
                    if status == "active":
                        total_principal += principal
                        total_emi += emi
                    items.append(item_info)

            data["total_debt"] = total_principal
            data["monthly_emi"] = total_emi
            data["debt_count"] = len(items)
            data["liabilities_list"] = items
            data["total_receivables"] = total_receivables
            data["receivables_count"] = len(receivables)
            data["receivables_list"] = receivables
        return data

    @classmethod
    def _get_transactions_context(cls, user: User, db: Session) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "recent_transactions_count": 0,
            "total_transactions_count": 0,
            "last_30d_expenses": 0.0,
            "last_30d_income": 0.0,
            "last_90d_expenses": 0.0,
            "last_90d_income": 0.0,
            "category_spending_30d": {},
            "category_spending_90d": {},
            "uncategorized_count": 0,
            "statement_coverage": None,
            "recent_transactions_sample": []
        }
        try:
            today = date.today()
            ninety_days_ago = today - timedelta(days=90)
            thirty_days_ago = today - timedelta(days=30)

            all_txns = db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.is_internal_transfer == False
            ).order_by(Transaction.date.desc()).all()

            data["total_transactions_count"] = len(all_txns)

            if all_txns:
                min_d = min(t.date for t in all_txns)
                max_d = max(t.date for t in all_txns)
                cov_days = (max_d - min_d).days + 1
                data["statement_coverage"] = {
                    "start_date": str(min_d),
                    "end_date": str(max_d),
                    "days": cov_days,
                    "coverage_months": round(cov_days / 30.0, 1),
                    "total_transactions": len(all_txns)
                }

                # Sample for prompt grounding (last 8 txns)
                data["recent_transactions_sample"] = [
                    {
                        "date": str(t.date),
                        "desc": t.description,
                        "amount": float(t.amount or 0.0),
                        "type": t.type,
                        "category": t.category
                    }
                    for t in all_txns[:8]
                ]

            cat_30d: Dict[str, float] = {}
            cat_90d: Dict[str, float] = {}
            exp_30 = 0.0
            inc_30 = 0.0
            exp_90 = 0.0
            inc_90 = 0.0
            uncat_c = 0

            for t in all_txns:
                amt = float(t.amount or 0.0)
                cat = t.category or "Uncategorized"
                if cat == "Uncategorized":
                    uncat_c += 1

                # 90-day bucket
                if t.date >= ninety_days_ago:
                    if t.type == "expense":
                        exp_90 += amt
                        cat_90d[cat] = cat_90d.get(cat, 0.0) + amt
                    elif t.type == "income":
                        inc_90 += amt

                # 30-day bucket
                if t.date >= thirty_days_ago:
                    if t.type == "expense":
                        exp_30 += amt
                        cat_30d[cat] = cat_30d.get(cat, 0.0) + amt
                    elif t.type == "income":
                        inc_30 += amt

            data["last_30d_expenses"] = exp_30
            data["last_30d_income"] = inc_30
            data["last_90d_expenses"] = exp_90
            data["last_90d_income"] = inc_90
            data["category_spending_30d"] = cat_30d
            data["category_spending_90d"] = cat_90d
            data["uncategorized_count"] = uncat_c
            data["recent_transactions_count"] = len([t for t in all_txns if t.date >= thirty_days_ago])
        except Exception as e:
            logger.warning(f"Error reading transaction context: {e}")

        return data

    @classmethod
    def _get_budget_context(cls, user: User, db: Session) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "budget_categories": [],
            "total_budget_allocated": 0.0,
        }
        try:
            from app.finance.intelligence import IntelligenceEngine
            recs = IntelligenceEngine.compute_adaptive_budget_recommendations(user, db)
            b_list = []
            total_allocated = 0.0
            for r in recs:
                alloc = float(r.recommended_budget)
                total_allocated += alloc
                b_list.append({
                    "category": r.category,
                    "monthly_allocation": alloc,
                    "historical_average": float(r.historical_average),
                    "rationale": r.rationale
                })
            data["budget_categories"] = b_list
            data["total_budget_allocated"] = total_allocated
        except Exception as e:
            logger.warning(f"Error reading adaptive budget context: {e}")
        return data

    @classmethod
    def _get_recurring_context(cls, user: User, db: Session) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "confirmed_recurring_count": 0,
            "recurring_monthly_expenses": 0.0,
            "recurring_monthly_income": 0.0,
            "recurring_commitments": [],
            "unreviewed_detections_count": 0,
        }
        try:
            recurring_items = db.query(RecurringTransaction).filter(
                RecurringTransaction.user_id == user.id
            ).all()

            confirmed = [r for r in recurring_items if r.status == "confirmed"]
            unreviewed = [r for r in recurring_items if r.status == "detected"]

            data["confirmed_recurring_count"] = len(confirmed)
            data["unreviewed_detections_count"] = len(unreviewed)

            m_exp = 0.0
            m_inc = 0.0
            items_summary = []

            for r in confirmed:
                amt = float(r.amount)
                freq = r.frequency
                if freq == "weekly":
                    m_amt = amt * 52 / 12
                elif freq == "fortnightly":
                    m_amt = amt * 26 / 12
                elif freq == "quarterly":
                    m_amt = amt / 3
                elif freq == "yearly":
                    m_amt = amt / 12
                else:
                    m_amt = amt

                if r.transaction_type == "expense":
                    m_exp += m_amt
                else:
                    m_inc += m_amt

                items_summary.append({
                    "id": r.id,
                    "name": r.name,
                    "merchant": r.merchant,
                    "amount": amt,
                    "frequency": r.frequency,
                    "monthly_normalized": round(m_amt, 2),
                    "category": r.category,
                    "type": r.transaction_type,
                    "next_date": r.next_expected_date.isoformat() if r.next_expected_date else None,
                })

            data["recurring_monthly_expenses"] = round(m_exp, 2)
            data["recurring_monthly_income"] = round(m_inc, 2)
            data["recurring_commitments"] = items_summary
        except Exception as e:
            logger.warning(f"Error reading recurring context: {e}")

        return data

    @classmethod
    def _get_goals_context(cls, user: User, db: Session) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "goals_count": 0,
            "active_goals": [],
            "total_goals_target": 0.0,
            "total_goals_saved": 0.0,
        }
        try:
            goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == user.id).all()
            data["goals_count"] = len(goals)
            items = []
            t_target = 0.0
            t_saved = 0.0

            for g in goals:
                target = float(g.target_amount or 0.0)
                current = float(g.current_amount or 0.0)
                t_target += target
                t_saved += current

                months_remaining = 12
                if g.target_date:
                    days = (g.target_date - date.today()).days
                    months_remaining = max(1, int(days / 30.4))

                rem = max(0.0, target - current)
                req_sip = round(rem / months_remaining, 2) if months_remaining > 0 else rem

                items.append({
                    "id": g.id,
                    "name": g.name,
                    "target_amount": target,
                    "current_amount": current,
                    "target_date": g.target_date.isoformat() if g.target_date else None,
                    "months_remaining": months_remaining,
                    "required_monthly_savings": req_sip,
                    "progress_pct": round((current / target * 100) if target > 0 else 0.0, 1),
                })

            data["active_goals"] = items
            data["total_goals_target"] = t_target
            data["total_goals_saved"] = t_saved
        except Exception as e:
            logger.warning(f"Error reading goals context: {e}")

        return data

    @classmethod
    def _get_intelligence_context(cls, user: User, db: Session) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "net_worth": 0.0,
            "emergency_runway_months": 3.0,
            "savings_rate_pct": 20.0,
            "spending_anomalies": [],
            "projected_cash_flow_30d": 0.0,
        }
        try:
            from app.finance.intelligence import IntelligenceEngine
            snapshot = IntelligenceEngine.get_canonical_snapshot(user, db)
            data["net_worth"] = float(snapshot.net_worth)
            data["emergency_runway_months"] = snapshot.emergency_runway_months
            data["savings_rate_pct"] = snapshot.savings_rate_pct
            data["category_spending"] = {k: float(v) for k, v in snapshot.category_spending.items()}

            anomalies = IntelligenceEngine.detect_spending_anomalies(user, db)
            if anomalies:
                data["spending_anomalies"] = [
                    {
                        "category": a.category,
                        "deviation_pct": a.variance_pct,
                        "explanation": a.explanation,
                        "severity": a.severity,
                    }
                    for a in anomalies[:4]
                ]

            forecast = IntelligenceEngine.forecast_cash_flow(user, db, horizon_days=30)
            data["projected_cash_flow_30d"] = float(forecast.projected_net)
            data["projected_ending_balance"] = float(forecast.projected_ending_cash) if forecast.projected_ending_cash is not None else 0.0
        except Exception as e:
            logger.warning(f"Error reading intelligence context: {e}")

        return data
