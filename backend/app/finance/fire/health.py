from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from app.schemas.fire import (
    FinancialHealthAssessmentResponse,
    FinancialHealthPillar
)


class FinancialHealthEngine:
    """
    Transparent, rule-based Financial Health Assessment Engine.
    Evaluates 8 core pillars with mathematical rigor. Zero black-box AI scores.
    """

    @classmethod
    def assess_health(
        cls,
        age: Optional[int],
        monthly_income: Decimal,
        monthly_expenses: Decimal,
        liquid_assets: Decimal,
        investable_assets: Decimal,
        total_debt_principal: Decimal,
        total_monthly_emi: Decimal,
        goals_on_track_pct: float,
        fire_progress_pct: float,
        fire_shortfall: Decimal,
        target_emergency_months: int = 6
    ) -> FinancialHealthAssessmentResponse:
        pillars: List[FinancialHealthPillar] = []
        is_provisional = False

        if not age or monthly_income <= Decimal("0.00") or monthly_expenses <= Decimal("0.00"):
            is_provisional = True

        # 1. Emergency Fund Coverage (Weight: 15%)
        # Benchmark: target_emergency_months (typically 6 months)
        runway_months = Decimal("0.0")
        if monthly_expenses > Decimal("0.00"):
            runway_months = (liquid_assets / monthly_expenses).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        runway_float = float(runway_months)

        if runway_float >= target_emergency_months:
            p1_score = 100
            p1_status = "excellent"
            p1_priority = "long_term"
            p1_rec = f"Your emergency reserve of {runway_float:.1f} months exceeds the {target_emergency_months}-month statutory guideline. Maintain funds in high-liquidity arbitrage or liquid mutual funds."
        elif runway_float >= 3.0:
            p1_score = int(60 + (runway_float - 3.0) / (target_emergency_months - 3.0) * 35)
            p1_status = "good"
            p1_priority = "medium_term"
            p1_rec = f"You have {runway_float:.1f} months covered. Allocate ₹{(monthly_expenses * Decimal(str(target_emergency_months)) - liquid_assets):,.0f} more to reach complete 6-month safety."
        elif runway_float >= 1.0:
            p1_score = int(30 + runway_float * 10)
            p1_status = "fair"
            p1_priority = "immediate"
            p1_rec = "Your liquidity buffer is thin (under 3 months). Direct all discretionary cash flow to building an emergency cushion before aggressive long-term investing."
        else:
            p1_score = 10
            p1_status = "critical"
            p1_priority = "immediate"
            p1_rec = "CRITICAL: Less than 1 month of living expenses in reserve. High vulnerability to job loss, medical emergencies, or unexpected expenses."

        pillars.append(FinancialHealthPillar(
            pillar_id="emergency_fund",
            name="Emergency Fund Cushion",
            score=p1_score,
            weight=0.15,
            status=p1_status,
            metric_value=f"{runway_float:.1f} months",
            target_benchmark=f"{target_emergency_months}.0 months of expenses",
            description="Liquid savings available instantly in savings accounts, FDs, or liquid mutual funds.",
            action_priority=p1_priority,
            recommendation=p1_rec
        ))

        # 2. Monthly Cash-Flow Surplus (Weight: 15%)
        monthly_surplus = monthly_income - monthly_expenses
        if monthly_income > Decimal("0.00"):
            surplus_ratio = float((monthly_surplus / monthly_income) * 100)
        else:
            surplus_ratio = 0.0

        if surplus_ratio >= 30.0:
            p2_score = 100
            p2_status = "excellent"
            p2_priority = "long_term"
            p2_rec = f"Outstanding positive cash flow surplus of ₹{monthly_surplus:,.0f}/month ({surplus_ratio:.1f}% of income). Continue disciplined automated investing."
        elif surplus_ratio >= 15.0:
            p2_score = int(70 + (surplus_ratio - 15.0) * 2)
            p2_status = "good"
            p2_priority = "medium_term"
            p2_rec = f"Healthy monthly surplus of ₹{monthly_surplus:,.0f} ({surplus_ratio:.1f}%). Trim minor discretionary subscriptions to reach a 25%+ surplus."
        elif surplus_ratio > 0.0:
            p2_score = int(40 + surplus_ratio * 2)
            p2_status = "fair"
            p2_priority = "immediate"
            p2_rec = f"Thin surplus of ₹{monthly_surplus:,.0f}/month. High risk of sliding into debt if unexpected monthly expenses arise."
        else:
            p2_score = 10
            p2_status = "critical"
            p2_priority = "immediate"
            p2_rec = f"Cash flow deficit: expenses exceed income by ₹{abs(monthly_surplus):,.0f}/month. Immediate budgeting intervention required."

        pillars.append(FinancialHealthPillar(
            pillar_id="cash_flow_surplus",
            name="Cash Flow Surplus",
            score=p2_score,
            weight=0.15,
            status=p2_status,
            metric_value=f"₹{monthly_surplus:,.0f}/mo ({surplus_ratio:.1f}%)",
            target_benchmark=">= 25.0% surplus of net income",
            description="Net monthly savings capacity after all living expenses, utilities, and debt obligations.",
            action_priority=p2_priority,
            recommendation=p2_rec
        ))

        # 3. Savings Rate (Weight: 15%)
        if surplus_ratio >= 40.0:
            p3_score = 100
            p3_status = "excellent"
            p3_rec = f"Elite savings rate of {surplus_ratio:.1f}%. You are in the top tier for rapid FIRE wealth accumulation."
        elif surplus_ratio >= 25.0:
            p3_score = 80
            p3_status = "good"
            p3_rec = f"Solid savings rate of {surplus_ratio:.1f}%. Comfortably exceeds traditional financial planning benchmarks (20%)."
        elif surplus_ratio >= 10.0:
            p3_score = 50
            p3_status = "fair"
            p3_rec = f"Modest savings rate of {surplus_ratio:.1f}%. Target increasing savings by 1% every quarter."
        else:
            p3_score = 20
            p3_status = "critical"
            p3_rec = "Sub-10% savings rate severely restricts compounding and extends your retirement timeline by 15+ years."

        pillars.append(FinancialHealthPillar(
            pillar_id="savings_rate",
            name="Savings Rate Discipline",
            score=p3_score,
            weight=0.15,
            status=p3_status,
            metric_value=f"{surplus_ratio:.1f}%",
            target_benchmark=">= 30.0% for FIRE independence",
            description="Percentage of take-home income consistently saved or channeled into investment instruments.",
            action_priority="medium_term" if p3_score >= 70 else "immediate",
            recommendation=p3_rec
        ))

        # 4. Debt Burden / EMI-to-Income (Weight: 15%)
        dti_pct = 0.0
        if monthly_income > Decimal("0.00"):
            dti_pct = float((total_monthly_emi / monthly_income) * 100)

        if total_debt_principal == Decimal("0.00"):
            p4_score = 100
            p4_status = "excellent"
            p4_rec = "100% Debt-free! Zero monthly EMI burden frees up 100% of discretionary surplus for wealth compounding."
        elif dti_pct <= 20.0:
            p4_score = 85
            p4_status = "good"
            p4_rec = f"Conservative debt burden: total monthly EMIs consume {dti_pct:.1f}% of income (well under the 35% safe ceiling)."
        elif dti_pct <= 40.0:
            p4_score = 55
            p4_status = "fair"
            p4_rec = f"Elevated debt burden: EMIs consume {dti_pct:.1f}% of income. Use Debt Avalanche to aggressively repay high-interest loans."
        else:
            p4_score = 20
            p4_status = "critical"
            p4_rec = f"Dangerously high debt burden: {dti_pct:.1f}% of your monthly income is committed to EMIs. Suspend non-essential investments until consumer debt is cleared."

        pillars.append(FinancialHealthPillar(
            pillar_id="debt_burden",
            name="Debt-to-Income Burden",
            score=p4_score,
            weight=0.15,
            status=p4_status,
            metric_value=f"{dti_pct:.1f}% EMI ratio",
            target_benchmark="<= 25.0% of monthly income",
            description="Ratio of recurring loan and credit card EMIs relative to monthly take-home income.",
            action_priority="immediate" if p4_score < 70 else "long_term",
            recommendation=p4_rec
        ))

        # 5. Investment Progress & Net Worth Multiple (Weight: 10%)
        # Age-based multiple benchmarks: Age 30: 1x annual income, Age 40: 3x, Age 50: 6x
        annual_inc = monthly_income * Decimal("12.0")
        current_multiple = 0.0
        target_multiple = 1.0
        user_age = age or 30

        if user_age < 30:
            target_multiple = 0.5
        elif user_age < 35:
            target_multiple = 1.5
        elif user_age < 45:
            target_multiple = 3.5
        elif user_age < 55:
            target_multiple = 6.0
        else:
            target_multiple = 10.0

        if annual_inc > Decimal("0.00"):
            current_multiple = float(investable_assets / annual_inc)

        if current_multiple >= target_multiple:
            p5_score = 100
            p5_status = "excellent"
            p5_rec = f"Superb wealth accumulation: your investable portfolio represents {current_multiple:.1f}x your annual income (benchmark for age {user_age} is {target_multiple:.1f}x)."
        elif current_multiple >= target_multiple * 0.6:
            p5_score = 75
            p5_status = "good"
            p5_rec = f"Healthy portfolio multiple of {current_multiple:.1f}x annual income. On track to reach the {target_multiple:.1f}x milestone within 2-3 years."
        elif current_multiple >= target_multiple * 0.3:
            p5_score = 45
            p5_status = "fair"
            p5_rec = f"Current portfolio is {current_multiple:.1f}x annual income. Step up equity SIPs to accelerate compounding."
        else:
            p5_score = 25
            p5_status = "critical"
            p5_rec = f"Portfolio multiple ({current_multiple:.1f}x) lags significantly behind age-{user_age} benchmark ({target_multiple:.1f}x)."

        pillars.append(FinancialHealthPillar(
            pillar_id="investment_multiple",
            name="Age-Based Portfolio Multiple",
            score=p5_score,
            weight=0.10,
            status=p5_status,
            metric_value=f"{current_multiple:.1f}x annual income",
            target_benchmark=f"{target_multiple:.1f}x by age {user_age}",
            description="Accumulated investable assets relative to your annual gross earnings power.",
            action_priority="medium_term",
            recommendation=p5_rec
        ))

        # 6. Goal Funding Execution (Weight: 10%)
        if goals_on_track_pct >= 85.0:
            p6_score = 100
            p6_status = "excellent"
            p6_rec = f"{goals_on_track_pct:.0f}% of your designated life goals are fully funded or tracking on schedule."
        elif goals_on_track_pct >= 60.0:
            p6_score = 75
            p6_status = "good"
            p6_rec = f"{goals_on_track_pct:.0f}% goal funding. Rebalance surplus towards secondary goals."
        elif goals_on_track_pct >= 30.0:
            p6_score = 45
            p6_status = "fair"
            p6_rec = f"{goals_on_track_pct:.0f}% goal funding. Prioritize High-priority milestones over discretionary targets."
        else:
            p6_score = 20
            p6_status = "critical"
            p6_rec = "Goals are severely underfunded. Review deadlines and downscale target budgets where appropriate."

        pillars.append(FinancialHealthPillar(
            pillar_id="goal_funding",
            name="Goal Funding Tracking",
            score=p6_score,
            weight=0.10,
            status=p6_status,
            metric_value=f"{goals_on_track_pct:.0f}% funded",
            target_benchmark=">= 80% on-track status",
            description="Proportion of verified financial goals (home down payment, education, travel) funded on schedule.",
            action_priority="medium_term",
            recommendation=p6_rec
        ))

        # 7. FIRE Progress Percentage (Weight: 10%)
        if fire_progress_pct >= 80.0:
            p7_score = 100
            p7_status = "excellent"
            p7_rec = f"Exceptional: You are {fire_progress_pct:.1f}% toward your full financial independence corpus."
        elif fire_progress_pct >= 40.0:
            p7_score = 75
            p7_status = "good"
            p7_rec = f"{fire_progress_pct:.1f}% FIRE progress. Compounding returns now drive greater wealth growth than fresh contributions."
        elif fire_progress_pct >= 15.0:
            p7_score = 50
            p7_status = "fair"
            p7_rec = f"{fire_progress_pct:.1f}% progress. Continue consistent monthly SIP accumulation."
        else:
            p7_score = 25
            p7_status = "critical"
            p7_rec = f"Early stage ({fire_progress_pct:.1f}%). Focus on increasing income and automated index investing."

        pillars.append(FinancialHealthPillar(
            pillar_id="fire_progress",
            name="FIRE Corpus Progress",
            score=p7_score,
            weight=0.10,
            status=p7_status,
            metric_value=f"{fire_progress_pct:.1f}% of target",
            target_benchmark="100% of Today's Target",
            description="Accumulated investable assets compared to your full financial independence target corpus.",
            action_priority="long_term",
            recommendation=p7_rec
        ))

        # 8. Retirement Readiness & Shortfall Gap (Weight: 5%)
        if fire_shortfall <= Decimal("0.00"):
            p8_score = 100
            p8_status = "excellent"
            p8_rec = f"Surplus achieved! Your projected retirement corpus exceeds target by ₹{abs(fire_shortfall):,.0f}."
        else:
            shortfall_float = float(fire_shortfall)
            p8_score = max(20, min(80, int(100 - (shortfall_float / 1000000.0) * 5)))
            p8_status = "good" if p8_score >= 70 else ("fair" if p8_score >= 40 else "critical")
            p8_rec = f"Projected shortfall of ₹{shortfall_float:,.0f} at target retirement age. Increase monthly SIP or consider extending retirement age by 1-2 years."

        pillars.append(FinancialHealthPillar(
            pillar_id="retirement_readiness",
            name="Retirement Readiness Gap",
            score=p8_score,
            weight=0.05,
            status=p8_status,
            metric_value="Surplus" if fire_shortfall <= Decimal("0.00") else f"₹{fire_shortfall:,.0f} shortfall",
            target_benchmark="Zero shortfall at target age",
            description="Projected portfolio surplus or deficit at your planned retirement milestone.",
            action_priority="medium_term" if fire_shortfall > Decimal("0") else "long_term",
            recommendation=p8_rec
        ))

        # Weighted Overall Score
        total_score = sum(p.score * p.weight for p in pillars)
        overall_score = int(round(total_score))

        if overall_score >= 85:
            overall_status = "Robust Financial Fortress"
            summary = "Your financial position is exceptionally strong with healthy cash flow, minimal debt friction, and robust progress toward financial independence."
        elif overall_score >= 70:
            overall_status = "Solid Financial Health"
            summary = "Your financial foundation is solid with consistent savings and protected liquidity. Addressing minor gaps will optimize your FIRE timeline."
        elif overall_score >= 50:
            overall_status = "Moderate Financial Stability"
            summary = "You have established key financial habits, but vulnerabilities exist in debt, emergency cushion, or savings rate that need proactive attention."
        else:
            overall_status = "Vulnerable / Attention Required"
            summary = "Critical financial vulnerabilities detected. Prioritize liquidity protection, debt reduction, and budget stabilization immediately."

        # 12-Month Actionable Plan
        checklist = [
            {
                "timeframe": "Months 1 - 3 (Immediate Priorities)",
                "action": "Liquid Reserve Buffer",
                "detail": p1_rec if p1_score < 80 else "Review health insurance deductible and ensure emergency reserve is held in instant-redemption liquid funds.",
                "pillar": "emergency_fund"
            },
            {
                "timeframe": "Months 4 - 6 (Debt & Efficiency)",
                "action": "Debt Avalanche & Budget Optimization",
                "detail": p4_rec if p4_score < 80 else "Automate 50-30-20 budget envelopes and direct cash flow surplus into tax-efficient index investments.",
                "pillar": "debt_burden"
            },
            {
                "timeframe": "Months 7 - 12 (Wealth Compounding & FIRE)",
                "action": "Retirement Portfolio Escalation",
                "detail": p8_rec if fire_shortfall > Decimal("0") else "Review asset allocation between diversified equity mutual funds, PPF/EPF, and sovereign debt.",
                "pillar": "retirement_readiness"
            }
        ]

        disclaimer = (
            "Rule-based assessment model derived from statutory Indian personal finance benchmarks "
            "(RBI prudential debt guidelines, SEBI investment rules, and standard emergency runway principles). "
            "Educational evaluation only; not personalized financial or tax advice."
        )

        return FinancialHealthAssessmentResponse(
            overall_score=overall_score,
            status=overall_status,
            is_provisional=is_provisional,
            summary=summary,
            pillars=pillars,
            actionable_checklist_12_months=checklist,
            disclaimer=disclaimer
        )
