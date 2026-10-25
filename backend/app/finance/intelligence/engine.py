from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import re
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.financial import Transaction, FinancialProfile, AssetHolding, Liability, FinancialGoal, RecurringTransaction
from app.models.bank import BankAccount
from app.schemas.intelligence import (
    CanonicalFinancialSnapshot,
    RecurringTransactionPattern,
    SpendingAnomaly,
    CashFlowForecast,
    AdaptiveBudgetRecommendation,
    GoalFeasibility,
    FinancialInsight,
    IntelligenceFeedResponse,
    CategorizationPreviewResponse
)


# Deterministic Indian categorization dictionary
CATEGORY_RULES: List[Dict[str, Any]] = [
    {"pattern": r"(?i)\b(swiggy|zomato|starbucks|mcdonald|subway|restaurant|cafe|dining|pizza|burger)\b", "category": "Food & Dining"},
    {"pattern": r"(?i)\b(blinkit|zepto|instamart|bigbasket|supermarket|grocery|groceries|dmart|nature's\s*basket)\b", "category": "Groceries"},
    {"pattern": r"(?i)\b(uber|ola|rapido|metro|petrol|fuel|indian\s*oil|bharat\s*petroleum|hpcl|toll|fastag)\b", "category": "Transportation"},
    {"pattern": r"(?i)\b(rent|maintenance|landlord|society|housing|electricity|bescom|tata\s*power|adani\s*electricity|water|lpg|indane)\b", "category": "Housing & Utilities"},
    {"pattern": r"(?i)\b(netflix|spotify|prime|hotstar|disney|cinema|pvr|inox|bookmyshow|steam|playstation)\b", "category": "Entertainment"},
    {"pattern": r"(?i)\b(amazon|flipkart|myntra|ajio|zara|h&m|shopping|retail|croma|reliance\s*digital)\b", "category": "Shopping"},
    {"pattern": r"(?i)\b(pharmacy|apollo|pharmeasy|1mg|hospital|clinic|doctor|diagnostic|cult\.fit|gym)\b", "category": "Healthcare"},
    {"pattern": r"(?i)\b(salary|payroll|stipend|freelance|consulting|dividend|interest\s*credit)\b", "category": "Income"},
    {"pattern": r"(?i)\b(zerodha|groww|kuvera|mf\s*central|sip|mutual\s*fund|ppf|epf|nps|uti|nippon)\b", "category": "Investment"},
    {"pattern": r"(?i)\b(emi|loan|mortgage|credit\s*card\s*payment|hdfc\s*bank\s*loan|bajaj\s*finance)\b", "category": "Debt & EMI"},
]


class IntelligenceEngine:
    """
    Central deterministic financial intelligence engine for FinPilot AI.
    Produces canonical snapshots, recurring patterns, anomalies, forecasts,
    adaptive budgets, and prioritized actionable insight feeds.
    """

    @classmethod
    def get_canonical_snapshot(
        cls,
        user: User,
        db: Session,
        period: str = "current_month"
    ) -> CanonicalFinancialSnapshot:
        today = date.today()

        if period == "last_30_days":
            start_date = today - timedelta(days=30)
            end_date = today
        elif period == "last_month":
            # 1st of last month to last day of last month
            first_of_this_month = today.replace(day=1)
            last_day_of_last_month = first_of_this_month - timedelta(days=1)
            start_date = last_day_of_last_month.replace(day=1)
            end_date = last_day_of_last_month
        else:
            # Default: current_month (1st of month to today)
            start_date = today.replace(day=1)
            end_date = today

        # 1. Fetch user transactions (excluding internal transfers)
        txns = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.is_internal_transfer == False,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()

        total_txns_count = db.query(Transaction).filter(Transaction.user_id == user.id).count()

        # 2. Compute income and expenses
        income = sum((t.amount for t in txns if t.type == "income"), Decimal("0.00"))
        expenses = sum((t.amount for t in txns if t.type == "expense"), Decimal("0.00"))

        data_quality_flags: Dict[str, Any] = {
            "transactions_in_period": len(txns),
            "all_time_transactions": total_txns_count,
            "period": period,
            "is_sparse": len(txns) < 3,
        }

        # If zero transactions in period, check profile fallback
        if income == Decimal("0.00") and user.profile and user.profile.monthly_income > Decimal("0.00"):
            income = user.profile.monthly_income
            data_quality_flags["income_source"] = "profile_baseline"
        else:
            data_quality_flags["income_source"] = "transaction_verified"

        if expenses == Decimal("0.00") and user.profile and user.profile.monthly_expenses > Decimal("0.00"):
            expenses = user.profile.monthly_expenses
            data_quality_flags["expenses_source"] = "profile_baseline"
        else:
            data_quality_flags["expenses_source"] = "transaction_verified"

        # 3. Category spending breakdown
        category_spending: Dict[str, Decimal] = {}
        for t in txns:
            if t.type == "expense":
                cat = t.category or "Other"
                category_spending[cat] = category_spending.get(cat, Decimal("0.00")) + t.amount

        # 4. Net cash flow & savings rate
        net_cash_flow = income - expenses
        savings_rate_pct = float(round((net_cash_flow / income) * 100, 1)) if income > Decimal("0.00") else 0.0

        # 5. Asset holdings & bank accounts
        assets = db.query(AssetHolding).filter(AssetHolding.user_id == user.id).all()
        bank_accs = db.query(BankAccount).filter(BankAccount.user_id == user.id).all()
        liabilities = db.query(Liability).filter(Liability.user_id == user.id).all()

        holding_sum = sum((a.current_value for a in assets), Decimal("0.00"))
        bank_sum = sum((b.current_balance for b in bank_accs if b.current_balance > Decimal("0.00")), Decimal("0.00"))
        total_assets = holding_sum + bank_sum

        liquid_cats = ["liquid_mf", "cash", "fd"]
        liquid_holding_sum = sum((a.current_value for a in assets if a.category in liquid_cats), Decimal("0.00"))
        liquid_savings = liquid_holding_sum + bank_sum

        total_liabilities = sum((l.principal for l in liabilities), Decimal("0.00"))
        net_worth = total_assets - total_liabilities

        monthly_burn = expenses if expenses > Decimal("0.00") else (user.profile.monthly_expenses if user.profile else Decimal("50000.00"))
        emergency_runway_months = float(round(liquid_savings / monthly_burn, 1)) if monthly_burn > Decimal("0.00") else 0.0

        return CanonicalFinancialSnapshot(
            user_id=user.id,
            snapshot_timestamp=datetime.now(timezone.utc),
            period=period,
            start_date=start_date,
            end_date=end_date,
            income=income,
            expenses=expenses,
            net_cash_flow=net_cash_flow,
            savings_rate_pct=savings_rate_pct,
            category_spending=category_spending,
            liquid_savings=liquid_savings,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=net_worth,
            emergency_runway_months=emergency_runway_months,
            total_transactions_count=len(txns),
            data_quality_flags=data_quality_flags
        )

    @classmethod
    def detect_recurring_transactions(cls, user: User, db: Session) -> List[RecurringTransactionPattern]:
        """
        Identifies repeated payments (rent, EMIs, subscriptions, utility bills)
        using merchant similarity and interval periodicity.
        """
        lookback_date = date.today() - timedelta(days=180)
        txns = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.type == "expense",
            Transaction.is_internal_transfer == False,
            Transaction.date >= lookback_date
        ).order_by(Transaction.date.asc()).all()

        if len(txns) < 2:
            return []

        # Group transactions by normalized description key
        groups: Dict[str, List[Transaction]] = {}
        for t in txns:
            # Clean description: keep alphabetic/brand tokens
            clean_desc = re.sub(r"[^a-zA-Z\s]", "", t.description).strip().lower()
            tokens = [tok for tok in clean_desc.split() if len(tok) > 2]
            key = " ".join(tokens[:2]) if tokens else clean_desc[:12]
            if not key:
                continue
            groups.setdefault(key, []).append(t)

        # Check database for existing recurring items for this user
        existing_db = db.query(RecurringTransaction).filter(RecurringTransaction.user_id == user.id).all()
        db_map = {re.sub(r"[^a-zA-Z0-9]", "", r.name.lower()): r for r in existing_db}

        recurring_patterns: List[RecurringTransactionPattern] = []
        pattern_id = 1

        for key, group in groups.items():
            if len(group) < 2:
                continue

            display_name = group[-1].description
            norm_name = re.sub(r"[^a-zA-Z0-9]", "", display_name.lower())
            db_item = db_map.get(norm_name)

            # If dismissed by user, do not surface as an unresolved recurring pattern
            if db_item and db_item.status == "dismissed":
                continue

            # Check interval between consecutive occurrences
            intervals = []
            for i in range(1, len(group)):
                diff = (group[i].date - group[i - 1].date).days
                intervals.append(diff)

            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            amounts = [g.amount for g in group]
            avg_amount = sum(amounts) / Decimal(len(amounts))
            # Amount consistency check (variance within 25%)
            is_amount_consistent = all(abs(a - avg_amount) <= (avg_amount * Decimal("0.25")) for a in amounts)

            frequency = "monthly"
            if 20 <= avg_interval <= 40:
                frequency = "monthly"
            elif 5 <= avg_interval <= 10:
                frequency = "weekly"
            elif 80 <= avg_interval <= 100:
                frequency = "quarterly"
            else:
                months = {g.date.strftime("%Y-%m") for g in group}
                if len(months) >= 2 and is_amount_consistent:
                    frequency = "monthly"
                else:
                    continue

            # Estimate next expected date
            last_date = group[-1].date
            next_date = last_date + timedelta(days=30 if frequency == "monthly" else 7)
            confidence = "high" if len(group) >= 3 and is_amount_consistent else "medium"

            # If confirmed in DB, adopt confirmed values
            is_confirmed = group[-1].is_recurring
            if db_item and db_item.status == "confirmed":
                is_confirmed = True
                avg_amount = db_item.amount
                frequency = db_item.frequency
                if db_item.next_expected_date:
                    next_date = db_item.next_expected_date

            recurring_patterns.append(RecurringTransactionPattern(
                id=f"rec-{pattern_id}",
                merchant_or_desc=display_name,
                category=group[-1].category or "Recurring",
                estimated_amount=avg_amount.quantize(Decimal("1.00")),
                frequency=frequency,
                next_expected_date=next_date,
                occurrence_count=len(group),
                confidence=confidence,
                is_confirmed=is_confirmed
            ))
            pattern_id += 1

        return recurring_patterns

    @classmethod
    def detect_spending_anomalies(cls, user: User, db: Session) -> List[SpendingAnomaly]:
        """
        Detects categories with abnormal spending surges compared to prior moving baselines.
        """
        today = date.today()
        current_month_start = today.replace(day=1)
        prior_baseline_start = current_month_start - timedelta(days=60)

        # Current month spending by category
        current_txns = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.type == "expense",
            Transaction.is_internal_transfer == False,
            Transaction.date >= current_month_start
        ).all()

        # Prior 60-day spending by category
        prior_txns = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.type == "expense",
            Transaction.is_internal_transfer == False,
            Transaction.date >= prior_baseline_start,
            Transaction.date < current_month_start
        ).all()

        if not current_txns or not prior_txns:
            return []

        current_by_cat: Dict[str, Decimal] = {}
        for t in current_txns:
            cat = t.category or "Other"
            current_by_cat[cat] = current_by_cat.get(cat, Decimal("0.00")) + t.amount

        # Prior monthly average (divide 60-day sum by 2)
        prior_by_cat: Dict[str, Decimal] = {}
        for t in prior_txns:
            cat = t.category or "Other"
            prior_by_cat[cat] = prior_by_cat.get(cat, Decimal("0.00")) + t.amount

        anomalies: List[SpendingAnomaly] = []
        anomaly_idx = 1

        for cat, curr_val in current_by_cat.items():
            prior_total = prior_by_cat.get(cat, Decimal("0.00"))
            prior_monthly_avg = prior_total / Decimal("2.0")

            # Trigger anomaly if current spend exceeds baseline by > 30% and > ₹2,000
            if prior_monthly_avg > Decimal("0.00"):
                diff = curr_val - prior_monthly_avg
                pct = float((diff / prior_monthly_avg) * 100)
                if diff >= Decimal("2000.00") and pct >= 30.0:
                    severity = "critical" if pct >= 75.0 or diff >= Decimal("10000.00") else "elevated"
                    anomalies.append(SpendingAnomaly(
                        id=f"anom-{anomaly_idx}",
                        category=cat,
                        current_period_spend=curr_val.quantize(Decimal("1.00")),
                        baseline_spend=prior_monthly_avg.quantize(Decimal("1.00")),
                        variance_amount=diff.quantize(Decimal("1.00")),
                        variance_pct=round(pct, 1),
                        severity=severity,
                        explanation=f"{cat} spending is ₹{diff:,.0f} ({pct:.1f}%) higher than your prior 60-day monthly baseline."
                    ))
                    anomaly_idx += 1

        return anomalies

    @classmethod
    def forecast_cash_flow(
        cls,
        user: User,
        db: Session,
        horizon_days: int = 30
    ) -> CashFlowForecast:
        """
        Projects deterministic upcoming 30/90-day cash flow based on confirmed income run-rate
        and known recurring commitments.
        """
        snapshot = cls.get_canonical_snapshot(user, db, period="last_30_days")
        horizon_fraction = Decimal(str(horizon_days / 30.0))
        projected_income = snapshot.income * horizon_fraction

        # Check for confirmed active recurring records in database
        confirmed_db_items = db.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == user.id,
            RecurringTransaction.status == "confirmed"
        ).all()

        if confirmed_db_items:
            # User-confirmed recurring items take precedence over unconfirmed detections
            confirmed_exp = Decimal("0.00")
            confirmed_inc = Decimal("0.00")
            for item in confirmed_db_items:
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
                    confirmed_exp += m_amt
                else:
                    confirmed_inc += m_amt

            recurring_monthly_sum = confirmed_exp
            if snapshot.income == Decimal("0.00") and confirmed_inc > Decimal("0.00"):
                projected_income = confirmed_inc * horizon_fraction
        else:
            recurring = cls.detect_recurring_transactions(user, db)
            recurring_monthly_sum = sum(
                r.estimated_amount for r in recurring if r.frequency == "monthly"
            )

        non_recurring_burn = max(Decimal("0.00"), snapshot.expenses - recurring_monthly_sum)
        projected_expenses = (recurring_monthly_sum * horizon_fraction) + (non_recurring_burn * horizon_fraction)

        daily_burn = projected_expenses / Decimal(str(horizon_days)) if horizon_days > 0 else Decimal("0.00")
        projected_net = projected_income - projected_expenses
        projected_ending_cash = snapshot.liquid_savings + projected_net

        key_drivers = []
        if confirmed_db_items:
            key_drivers.append(f"Confirmed recurring commitments of ₹{recurring_monthly_sum:,.0f}/month across {len(confirmed_db_items)} active verified bills.")
        elif recurring_monthly_sum > Decimal("0.00"):
            key_drivers.append(f"Estimated recurring commitments of ₹{recurring_monthly_sum:,.0f}/month across detected patterns.")
        if snapshot.savings_rate_pct > 0:
            key_drivers.append(f"Baseline savings rate of {snapshot.savings_rate_pct:.1f}% retaining ~₹{snapshot.net_cash_flow:,.0f}/month.")

        assumptions = [
            f"Assumes income rate of ₹{snapshot.income:,.0f} repeats linearly over {horizon_days} days.",
            "Recurring obligations renew on scheduled monthly intervals without early prepayment.",
            "Excludes volatile discretionary outliers and one-time emergency expenses."
        ]

        insufficient_data = snapshot.data_quality_flags.get("is_sparse", False) and snapshot.income == Decimal("0.00")

        return CashFlowForecast(
            horizon_days=horizon_days,
            projected_income=projected_income.quantize(Decimal("1.00")),
            projected_expenses=projected_expenses.quantize(Decimal("1.00")),
            projected_net=projected_net.quantize(Decimal("1.00")),
            projected_ending_cash=projected_ending_cash.quantize(Decimal("1.00")),
            daily_burn_rate=daily_burn.quantize(Decimal("1.00")),
            key_drivers=key_drivers,
            assumptions=assumptions,
            confidence="high" if not insufficient_data else "low",
            insufficient_data=insufficient_data
        )

    @classmethod
    def compute_adaptive_budget_recommendations(
        cls,
        user: User,
        db: Session
    ) -> List[AdaptiveBudgetRecommendation]:
        """
        Calculates recommended category budget ceilings aligned with the 50-30-20 framework
        and user financial surplus targets.
        """
        snapshot = cls.get_canonical_snapshot(user, db, period="current_month")
        income = snapshot.income

        if income <= Decimal("0.00"):
            return []

        # Benchmark: 50% needs, 30% wants, 20% savings
        target_needs = income * Decimal("0.50")
        target_wants = income * Decimal("0.30")

        recs: List[AdaptiveBudgetRecommendation] = []
        for cat, spend in snapshot.category_spending.items():
            # Flag discretionary categories consuming high shares
            if cat in ["Food & Dining", "Shopping", "Entertainment"]:
                # If category exceeds 15% of income alone, recommend a 15% reduction
                if spend > (income * Decimal("0.12")):
                    recommended = (spend * Decimal("0.85")).quantize(Decimal("1.00"))
                    savings = spend - recommended
                    recs.append(AdaptiveBudgetRecommendation(
                        category=cat,
                        historical_average=spend.quantize(Decimal("1.00")),
                        current_budget=spend.quantize(Decimal("1.00")),
                        recommended_budget=recommended,
                        rationale=f"Reducing {cat} by 15% frees up ₹{savings:,.0f}/month toward your emergency fund and goal SIPs.",
                        potential_savings=savings.quantize(Decimal("1.00"))
                    ))

        return recs

    @classmethod
    def assess_goals_feasibility(
        cls,
        user: User,
        db: Session
    ) -> List[GoalFeasibility]:
        """
        Evaluates active milestones against cash flow surplus, identifying delays and sensitivity levers.
        """
        goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == user.id).all()
        if not goals:
            return []

        snapshot = cls.get_canonical_snapshot(user, db, period="current_month")
        monthly_surplus = max(Decimal("0.00"), snapshot.net_cash_flow)
        results: List[GoalFeasibility] = []
        today = date.today()

        for g in goals:
            months_left = max(1, (g.target_date.year - today.year) * 12 + (g.target_date.month - today.month))
            remaining_corpus = max(Decimal("0.00"), g.target_amount - g.current_amount)
            required_sip = (remaining_corpus / Decimal(str(months_left))).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)

            # Check if current surplus is enough to fund this goal alongside others
            is_on_track = monthly_surplus >= required_sip

            delay_months = 0
            projected_completion = g.target_date
            if not is_on_track and monthly_surplus > Decimal("0.00"):
                est_months_needed = int((remaining_corpus / monthly_surplus).to_integral_value(rounding=ROUND_HALF_UP))
                delay_months = max(0, est_months_needed - months_left)
                projected_completion = today + timedelta(days=est_months_needed * 30)
            elif not is_on_track and monthly_surplus <= Decimal("0.00"):
                delay_months = 12
                projected_completion = None

            remedial_actions = []
            if not is_on_track:
                shortfall = required_sip - monthly_surplus
                remedial_actions.append(f"Increase monthly savings by ₹{shortfall:,.0f} to achieve target on schedule by {g.target_date.strftime('%b %Y')}.")
                remedial_actions.append(f"Alternatively, extending the target date by {delay_months} months lowers required monthly contribution.")
            else:
                remedial_actions.append(f"Fully funded on track! Your current monthly cash surplus of ₹{monthly_surplus:,.0f} covers required ₹{required_sip:,.0f}/mo SIP.")

            results.append(GoalFeasibility(
                goal_id=g.id,
                goal_name=g.name,
                target_amount=g.target_amount,
                current_amount=g.current_amount,
                target_date=g.target_date,
                required_monthly_sip=required_sip,
                current_projected_monthly_savings=monthly_surplus,
                is_on_track=is_on_track,
                projected_completion_date=projected_completion,
                delay_months=delay_months,
                remedial_actions=remedial_actions
            ))

        return results

    @classmethod
    def generate_intelligence_feed(
        cls,
        user: User,
        db: Session
    ) -> IntelligenceFeedResponse:
        """
        Synthesizes prioritized, deduplicated financial insights across anomalies,
        budgets, recurring payments, cash runway, and savings milestones.
        """
        insights: List[FinancialInsight] = []
        snapshot = cls.get_canonical_snapshot(user, db, period="current_month")
        anomalies = cls.detect_spending_anomalies(user, db)
        recurring = cls.detect_recurring_transactions(user, db)
        forecast = cls.forecast_cash_flow(user, db, horizon_days=30)
        budget_recs = cls.compute_adaptive_budget_recommendations(user, db)
        goals_feasibility = cls.assess_goals_feasibility(user, db)

        # 1. Anomaly Insights (Critical / Warning)
        for anom in anomalies:
            insights.append(FinancialInsight(
                id=f"insight-{anom.id}",
                category="spending",
                title=f"Unusual Surge in {anom.category}",
                summary=anom.explanation,
                detail=f"Spent ₹{anom.current_period_spend:,.0f} vs monthly baseline of ₹{anom.baseline_spend:,.0f}. Audit recent transactions to prevent overspend.",
                severity="critical" if anom.severity == "critical" else "warning",
                confidence="high",
                metric_value=f"+{anom.variance_pct:.0f}%",
                baseline_value=f"₹{anom.baseline_spend:,.0f}/mo",
                action_label="Audit Category Transactions",
                action_tab="budget"
            ))

        # 2. Emergency Runway Health
        if snapshot.emergency_runway_months < 3.0 and snapshot.expenses > Decimal("0.00"):
            insights.append(FinancialInsight(
                id="insight-emergency-runway-low",
                category="cash_flow",
                title="Emergency Reserve Cushion Below Benchmark",
                summary=f"Current liquid reserves provide {snapshot.emergency_runway_months:.1f} months of living expenses (benchmark is 6 months).",
                detail="Financial planners recommend maintaining 3 to 6 months of mandatory living expenses in liquid mutual funds or savings deposits before aggressive equity SIP allocation.",
                severity="warning",
                confidence="high",
                metric_value=f"{snapshot.emergency_runway_months:.1f} Months",
                baseline_value="6.0 Months Target",
                action_label="Build Emergency Buffer",
                action_tab="goals"
            ))
        elif snapshot.emergency_runway_months >= 6.0:
            insights.append(FinancialInsight(
                id="insight-emergency-runway-healthy",
                category="savings",
                title="Strong Emergency Liquidity Cushion",
                summary=f"Your liquid buffer covers {snapshot.emergency_runway_months:.1f} months of expenses, exceeding the 6-month safety benchmark.",
                detail="With your capital preservation buffer secured, excess monthly surplus can be channeled into tax-saving ELSS or long-term retirement wealth compounding.",
                severity="success",
                confidence="high",
                metric_value=f"{snapshot.emergency_runway_months:.1f} Months",
                baseline_value="6.0 Months",
                action_label="Plan FIRE & Wealth",
                action_tab="fire"
            ))

        # 3. Goal Feasibility Insights
        delayed_goals = [g for g in goals_feasibility if not g.is_on_track]
        if delayed_goals:
            g = delayed_goals[0]
            insights.append(FinancialInsight(
                id=f"insight-goal-{g.goal_id}",
                category="goal",
                title=f"Milestone at Risk: {g.goal_name}",
                summary=f"Requires ₹{g.required_monthly_sip:,.0f}/month to achieve by {g.target_date.strftime('%b %Y')}. Projected delay: {g.delay_months} months at current cash flow.",
                detail=g.remedial_actions[0] if g.remedial_actions else "Reallocate discretionary budget surplus to cover the monthly SIP gap.",
                severity="warning",
                confidence="high",
                metric_value=f"Gap: ₹{g.required_monthly_sip:,.0f}/mo",
                baseline_value=f"Surplus: ₹{g.current_projected_monthly_savings:,.0f}",
                action_label="Adjust Goal SIP",
                action_tab="goals"
            ))

        # 4. Adaptive Budget Optimization Insight
        if budget_recs:
            rec = budget_recs[0]
            insights.append(FinancialInsight(
                id="insight-budget-optimization",
                category="budget",
                title=f"Optimization Opportunity in {rec.category}",
                summary=rec.rationale,
                detail=f"Trimming {rec.category} from ₹{rec.historical_average:,.0f} to recommended ceiling of ₹{rec.recommended_budget:,.0f} saves ₹{rec.potential_savings:,.0f}/month.",
                severity="info",
                confidence="medium",
                metric_value=f"Save ₹{rec.potential_savings:,.0f}/mo",
                baseline_value=f"Current: ₹{rec.historical_average:,.0f}",
                action_label="Review 50-30-20 Budget",
                action_tab="budget"
            ))

        # 5. Recurring Bills Upcoming
        if recurring:
            next_bill = recurring[0]
            insights.append(FinancialInsight(
                id="insight-recurring-bills",
                category="recurring",
                title=f"Upcoming Recurring Commitment: {next_bill.merchant_or_desc}",
                summary=f"Identified {next_bill.frequency} commitment of ~₹{next_bill.estimated_amount:,.0f} expected around {next_bill.next_expected_date.strftime('%b %d') if next_bill.next_expected_date else 'soon'}.",
                detail=f"Tracked across {next_bill.occurrence_count} historical payments with {next_bill.confidence} confidence.",
                severity="info",
                confidence="medium",
                metric_value=f"₹{next_bill.estimated_amount:,.0f}",
                baseline_value=f"{next_bill.frequency.capitalize()}",
                action_label="Review Recurring Bills",
                action_tab="recurring"
            ))

        # Sort insights by severity: critical -> warning -> info -> success
        severity_order = {"critical": 0, "warning": 1, "info": 2, "success": 3}
        insights.sort(key=lambda x: severity_order.get(x.severity, 4))

        high_priority = sum(1 for i in insights if i.severity in ["critical", "warning"])

        return IntelligenceFeedResponse(
            insights=insights,
            total_insights=len(insights),
            high_priority_count=high_priority,
            data_quality_summary=snapshot.data_quality_flags,
            generated_at=datetime.now(timezone.utc)
        )

    @classmethod
    def preview_categorization(cls, description: str) -> CategorizationPreviewResponse:
        """
        Deterministically classifies a transaction description into an Indian financial category.
        """
        for rule in CATEGORY_RULES:
            if re.search(rule["pattern"], description):
                return CategorizationPreviewResponse(
                    description=description,
                    suggested_category=rule["category"],
                    confidence="high",
                    matched_rule=rule["pattern"]
                )

        return CategorizationPreviewResponse(
            description=description,
            suggested_category="Other",
            confidence="low",
            matched_rule="default_fallback"
        )
