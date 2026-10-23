# FinPilot AI — FIRE Forecasting & Planning Methodology

This document outlines the mathematical foundation, financial assumptions, regulatory references, and behavioral principles governing FinPilot AI's Financial Independence, Retire Early (FIRE) and 8-Pillar Financial Health Assessment engines.

---

## 1. Principles of Independence Calculation

1. **Deterministic Execution**: Calculations are strictly executed by Python financial services (`backend/app/finance/fire/`). Cloud LLMs never calculate financial sums or compounding trajectories.
2. **Exclusion of Illiquid Primary Residence**: Primary real estate equity is intentionally excluded from investable retirement assets to prevent the illusion of spendable liquidity while maintaining shelter.
3. **No Double-Counting**: Bank accounts, liquid mutual funds, equity mutual funds, sovereign bonds, and liabilities are isolated with deduplication guards (`provider_txn_ref` and internal transfer detection).
4. **Inflation Realities in India**: Unlike Western markets where inflation historically averages 2.0%–3.0%, long-term Indian retail Consumer Price Index (CPI) inflation ranges between 5.0% and 7.0%. Long-range retirement models require explicit inflation escalation.

---

## 2. Core Mathematical Formulas

### 2.1 Real Return ($r_{\text{real}}$) — Fisher Equation
To accurately reflect purchasing power growth after inflation:
$$r_{\text{real}} = \frac{1 + r_{\text{nominal}}}{1 + i} - 1$$
Where:
- $r_{\text{nominal}}$: Pre-retirement nominal portfolio return (default: 11.0% annualized, representing a diversified index/equity mutual fund allocation).
- $i$: Annual expected CPI inflation (default: 6.0% annualized).

### 2.2 FIRE Corpus Target in Today's Rupees
$$\text{Target}_{\text{today}} = \frac{\text{Annual Living Expenses}_{\text{today}} - \text{Guaranteed Other Retirement Income}}{\text{SWR}}$$
Where:
- $\text{SWR}$: Safe Withdrawal Rate (default: 3.5% for 35+ year Indian retirement horizons).

### 2.3 Inflation-Adjusted Future FIRE Target ($N = \text{Retirement Age} - \text{Current Age}$)
$$\text{Target}_{\text{future}} = \text{Target}_{\text{today}} \times (1 + i)^N$$

### 2.4 Portfolio Future Value ($FV$)
For an initial portfolio $P_0$ and recurring monthly contributions $PMT$:
$$FV = P_0 \times (1 + r_m)^{12N} + PMT \times \left[ \frac{(1 + r_m)^{12N} - 1}{r_m} \right] \times (1 + r_m)$$
Where:
- $r_m = \frac{r_{\text{nominal}}}{12}$ (monthly compounding rate).

### 2.5 Required Monthly Contribution ($PMT_{\text{required}}$)
To bridge any shortfall between projected portfolio growth and the inflation-adjusted target:
$$\text{Gap} = \max\left(0, \text{Target}_{\text{future}} - P_0 \times (1 + r_m)^{12N}\right)$$
$$PMT_{\text{required}} = \frac{\text{Gap} \times r_m}{\left((1 + r_m)^{12N} - 1\right) \times (1 + r_m)}$$

### 2.6 Coast FIRE Target
The lump sum invested today that will grow to the future target with **zero additional contributions**:
$$\text{Target}_{\text{Coast}} = \frac{\text{Target}_{\text{future}}}{(1 + r_{\text{nominal}})^N}$$

---

## 3. Supported FIRE Strategies

| Strategy | Lifestyle Spending Assumption | Primary Use Case |
| :--- | :--- | :--- |
| **Lean FIRE** | 70% of current living expenses (needs only) | Minimalist lifestyle covering essential groceries, healthcare, utilities, and modest shelter. |
| **Regular FIRE** | 100% of current middle-class lifestyle | Replicates current quality of life, discretionary spending, and domestic holidays. |
| **Fat FIRE** | 135% of current lifestyle expenditure | Enhanced lifestyle with generous provisions for international travel, luxury healthcare, and philanthropy. |
| **Coast FIRE** | Zero future retirement contributions needed | Current assets compound untouched to target age; earned income only needs to cover current expenses. |
| **Custom FIRE** | User-specified parameters | Tailored to custom retirement dates, partial pensions, and overseas expenses. |

---

## 4. The 8 Pillars of Financial Health Assessment

The financial health scoring engine evaluates 8 transparent, rule-based pillars:

1. **Emergency Fund Cushion (15% Weight)**: Evaluates months of living expenses held in instant liquid reserves (target: $\ge 6.0$ months).
2. **Cash Flow Surplus (15% Weight)**: Measures discretionary monthly surplus after living expenses and debt payments (benchmark: $\ge 25.0\%$ of net income).
3. **Savings Rate Discipline (15% Weight)**: Proportion of income channeled into long-term investments (benchmark: $\ge 30.0\%$ for FIRE candidates).
4. **Debt-to-Income Ratio (15% Weight)**: Measures EMI friction (safe ceiling: $\le 25.0\%$; critical: $> 40.0\%$).
5. **Age-Based Portfolio Multiple (10% Weight)**: Benchmark multiples of annual income accumulated by age (Age 30: 1x, Age 40: 3.5x, Age 50: 6x).
6. **Goal Funding Tracking (10% Weight)**: Proportion of designated family and life goals tracking on schedule.
7. **FIRE Corpus Progress (10% Weight)**: Ratio of current investable assets to today's full FIRE target.
8. **Retirement Readiness Gap (5% Weight)**: Projected surplus or shortfall at target retirement age.

---

## 5. Indian Statutory & Tax Context

1. **Equity Mutual Funds (Section 112A)**: Long-Term Capital Gains (>12 months) are taxed at 12.5% with an annual statutory exemption of ₹1,25,000 (Finance Act 2024).
2. **Debt & Arbitrage Funds (Section 50AA)**: Specified mutual funds with $\le 35\%$ domestic equity are taxed at the investor's marginal income tax slab.
3. **National Pension System (Section 10(12A))**: Up to 60% lump sum at superannuation is tax-free; remaining 40% purchases an annuity with monthly pension taxed at slab rates.
4. **Senior Citizen Relief (Section 80TTB)**: Resident senior citizens (aged 60+) receive up to ₹50,000 deduction on deposit interest without TDS up to ₹50,000 under Section 194A.
5. **DICGC Deposit Insurance**: Bank deposits are covered up to ₹5,00,000 per depositor per bank.
