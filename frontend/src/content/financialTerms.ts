export interface FinancialTermExplanation {
  id: string;
  title: string;
  technicalTerm?: string;
  category: 'retirement' | 'overview' | 'budget' | 'debt' | 'tax' | 'investment' | 'health' | 'bank';
  simpleMeaning: string;
  whyItMatters: string;
  example: string;
  calculation: string;
  limitations: string;
  actionableTip?: string;
}

export const FINANCIAL_TERMS_REGISTRY: Record<string, FinancialTermExplanation> = {
  // A. Financial Independence / FIRE
  financial_independence: {
    id: 'financial_independence',
    title: 'Financial Freedom & Independence',
    technicalTerm: 'FIRE (Financial Independence, Retire Early)',
    category: 'retirement',
    simpleMeaning:
      'Having enough money saved and invested so that the returns from your investments cover all your living costs, without depending entirely on a monthly salary or active job.',
    whyItMatters:
      'It gives you the freedom to choose how you spend your time—whether that means retiring completely, switching to lower-stress work, starting a venture, or pursuing personal passions.',
    example:
      'If your household spends ₹50,000 every month (₹6,00,000 a year), reaching financial independence means having an investment corpus large enough that annual withdrawals of ₹6,00,000 (adjusted for inflation) will not exhaust your savings over your lifetime.',
    calculation:
      'FinPilot calculates this by comparing your annual living expenses against your investable assets, compounding monthly contributions at your expected return rate, factoring in inflation until your target age.',
    limitations:
      'Reaching financial freedom depends on actual future investment returns, inflation rates, unpredictable medical or family emergencies, tax law changes, and how long you live in retirement. Projections are guidance, not guaranteed outcomes.',
    actionableTip:
      'Focus first on knowing your genuine annual living expenses and consistently saving a portion of your income each month.',
  },

  // B. Retirement Target
  retirement_target: {
    id: 'retirement_target',
    title: 'Money You Need to Retire',
    technicalTerm: "FIRE Target / Retirement Corpus Target (Today's vs Future Value)",
    category: 'retirement',
    simpleMeaning:
      'The estimated total sum of money you need in your investments at the moment you stop working to support your lifestyle for the rest of your life.',
    whyItMatters:
      'Without a clear target number, it is impossible to know whether you are saving enough, investing appropriately, or on track to retire comfortably.',
    example:
      'If you need ₹6,00,000 per year today, at a 3.5% withdrawal rate you need ₹1.71 Crore in today\'s money. But if you plan to retire in 20 years with 6% annual inflation, that same lifestyle will cost ₹19.24 Lakhs per year, requiring a future corpus of approximately ₹5.50 Crore.',
    calculation:
      'Today\'s target = (Annual Expenses ÷ Suggested Withdrawal Rate). Future target = Today\'s target × (1 + Inflation Rate) ^ (Years to Retirement). Both figures are calculated deterministically from your profile inputs.',
    limitations:
      'This calculation assumes a steady rate of inflation and constant spending patterns. Major lifestyle upgrades, healthcare spikes, or market crashes right after retirement will alter the required target.',
  },

  // C. Investable Assets
  investable_assets: {
    id: 'investable_assets',
    title: 'Money Already Available for Investing',
    technicalTerm: 'Current Investable Assets / Liquid Corpus',
    category: 'investment',
    simpleMeaning:
      'The money and financial investments you currently own that can realistically be used to generate retirement income or be sold when needed.',
    whyItMatters:
      'Counting non-liquid possessions (like the house you live in or personal jewellery) can give you a false sense of security, because you cannot easily spend them to buy groceries in retirement.',
    example:
      'If you have ₹10 Lakh in mutual funds, ₹5 Lakh in fixed deposits, and ₹2 Lakh in bank savings, your investable assets are ₹17 Lakh. A residential flat worth ₹80 Lakh that you live in is excluded from this figure.',
    calculation:
      'FinPilot sums verified bank balances (from linked accounts or bank statements) and eligible investment holdings recorded in the database (mutual funds, stocks, provident funds, fixed deposits, and liquid gold). Your primary residence is excluded.',
    limitations:
      'Asset valuations are based on the latest recorded balances. Fluctuations in stock market prices and exit loads or capital gains taxes upon withdrawal will affect the net cash realized.',
  },

  // D. Monthly Investment / SIP
  monthly_investment: {
    id: 'monthly_investment',
    title: 'Amount You Invest Each Month',
    technicalTerm: 'Systematic Investment Plan (SIP) / Monthly Capital Addition',
    category: 'budget',
    simpleMeaning:
      'The portion of your regular monthly income that you set aside into investments (such as mutual funds, PPF, NPS, or stocks) to build wealth over time.',
    whyItMatters:
      'Regular monthly investing harnesses compounding—earning returns on your previous returns—which does most of the heavy lifting over 10 to 30 years.',
    example:
      'Investing ₹15,000 every month equals ₹1,80,000 a year. Over 15 years at an assumed 11% average annual return, your total investment of ₹27 Lakh could grow to approximately ₹65 Lakh.',
    calculation:
      'FinPilot uses your observed monthly cash surplus (Income minus Expenses) or your explicitly configured monthly investment figure as the regular monthly contribution in future projection models.',
    limitations:
      'Investment returns in equities and debt are never guaranteed or linear. An SIP does not prevent short-term market losses, and historical returns do not guarantee future gains.',
  },

  // E. Safe Withdrawal Rate
  safe_withdrawal_rate: {
    id: 'safe_withdrawal_rate',
    title: 'Suggested Yearly Withdrawal Rate',
    technicalTerm: 'Safe Withdrawal Rate (SWR)',
    category: 'retirement',
    simpleMeaning:
      'The percentage of your total retirement savings that you can withdraw in your first year of retirement (and then adjust for inflation each year) without running out of money.',
    whyItMatters:
      'Withdrawing too much will drain your savings too quickly. Withdrawing too little forces you to work unnecessary extra years.',
    example:
      'If your retirement fund is ₹2 Crore and you choose a 3.5% withdrawal rate, you withdraw ₹7,00,000 in your first retirement year (about ₹58,333 per month). Next year, this amount is increased slightly to keep up with inflation.',
    calculation:
      'FinPilot defaults to 3.5% for Indian long-term retirements (spanning 30 to 45 years), which is more conservative than the traditional Western 4% rule due to historically higher inflation in India.',
    limitations:
      'No single rate is 100% foolproof. Extreme sequence-of-returns risk (severe market drops in your first few years of retirement) can threaten retirement longevity.',
  },

  // F. Inflation
  inflation: {
    id: 'inflation',
    title: 'Rising Cost of Living Over Time',
    technicalTerm: 'Annual Inflation Rate',
    category: 'overview',
    simpleMeaning:
      'The steady increase in prices of goods and services over time, which means ₹100 today buys fewer goods in the future.',
    whyItMatters:
      'Ignoring inflation is the #1 mistake in retirement planning. If prices double every 12 years at 6% inflation, a ₹50,000 monthly expense today will require ₹2,00,000 per month in 24 years just to buy the same things.',
    example:
      'A basket of monthly groceries costing ₹10,000 today will cost approximately ₹17,908 after 10 years at a 6% annual inflation rate.',
    calculation:
      'FinPilot applies compounding annual inflation: Future Cost = Current Cost × (1 + Inflation Rate) ^ Years. We use the configurable inflation rate (default 6.0% for India) across all projections.',
    limitations:
      'Personal inflation can differ from national indexes. Healthcare and education often inflate at 8–10% annually, while electronic goods may inflate more slowly.',
  },

  // G. Lean FIRE
  lean_fire: {
    id: 'lean_fire',
    title: 'Retirement With Basic Expenses',
    technicalTerm: 'Lean FIRE',
    category: 'retirement',
    simpleMeaning:
      'A retirement milestone where your investments are sufficient to cover only your core, essential needs (food, housing, utilities, basic healthcare) with minimal discretionary spending.',
    whyItMatters:
      'It acts as an early safety net. Reaching this milestone means you are no longer at financial risk of destitution if you lose your job.',
    example:
      'If your total monthly budget is ₹60,000 but your essential survival expenses are ₹40,000, your Lean retirement target is based on funding that ₹40,000 per month (approx. ₹1.14 Cr in today\'s value).',
    calculation:
      'FinPilot computes this by multiplying your monthly expenses by your configured Essential Expenses Percentage (default 70%), then applying your withdrawal rate.',
    limitations:
      'Leaves very little buffer for unexpected emergencies, family assistance, travel, or lifestyle upgrades.',
  },

  // H. Regular FIRE
  regular_fire: {
    id: 'regular_fire',
    title: 'Retirement With Current Lifestyle',
    technicalTerm: 'Standard FIRE',
    category: 'retirement',
    simpleMeaning:
      'Planning to retire while fully maintaining your current standard of living, including regular dining out, entertainment, vacations, and family comforts.',
    whyItMatters:
      'It is the standard benchmark for most working professionals who want financial freedom without making lifestyle sacrifices.',
    example:
      'If you currently spend ₹70,000 per month on both essentials and comforts, your Regular retirement plan aims to fund ₹8,40,000 per year adjusted for inflation.',
    calculation:
      'Computed directly on 100% of your current monthly living expenses divided by your suggested withdrawal rate.',
    limitations:
      'Assumes your post-retirement spending matches your pre-retirement spending. In reality, commuting expenses decrease while healthcare and leisure spending often rise.',
  },

  // I. Fat FIRE
  fat_fire: {
    id: 'fat_fire',
    title: 'Retirement With More Spending and Comfort',
    technicalTerm: 'Fat FIRE',
    category: 'retirement',
    simpleMeaning:
      'A retirement plan designed for an abundant lifestyle, with higher discretionary spending, frequent travel, luxury hobbies, and a substantial cushion for medical or family support.',
    whyItMatters:
      'Gives total financial peace of mind and luxury without ever worrying about frugality or minor market downturns.',
    example:
      'If your current spending is ₹70,000 per month, Fat retirement models an upgraded lifestyle spending 130% to 150% (₹91,000 to ₹1,05,000 per month) in retirement.',
    calculation:
      'FinPilot computes this by modeling 130% of your current monthly living expenses divided by your suggested withdrawal rate.',
    limitations:
      'Requires a significantly larger corpus and either a higher monthly investment, higher returns, or more working years to achieve.',
  },

  // J. Coast FIRE
  coast_fire: {
    id: 'coast_fire',
    title: 'Investments Ready to Grow on Their Own',
    technicalTerm: 'Coast FIRE',
    category: 'retirement',
    simpleMeaning:
      'The milestone where your existing savings are already large enough that, without investing a single rupee more, compound interest could grow them to your retirement target by your chosen retirement age.',
    whyItMatters:
      'Once you reach this point, you only need to earn enough from your job to cover your day-to-day living costs—you can stop stressing about aggressive retirement saving.',
    example:
      'A 30-year-old who needs ₹3 Crore at age 60 and already has ₹17 Lakh invested. At 10% annual return, that ₹17 Lakh could compound to ₹3 Crore in 30 years on its own.',
    calculation:
      'Coast Target = Future Retirement Target ÷ (1 + Expected Return Rate) ^ (Years to Retirement). If your current investable assets exceed this figure, you have reached Coast status.',
    limitations:
      'Does not mean you can retire today—you still need to earn money to pay for today\'s living expenses. It also relies heavily on long-term compound growth occurring as expected.',
  },

  // K. Required Monthly Investment
  required_monthly_investment: {
    id: 'required_monthly_investment',
    title: 'Monthly Investment Needed to Reach Your Goal',
    technicalTerm: 'Required SIP (Systematic Investment Plan)',
    category: 'retirement',
    simpleMeaning:
      'The estimated amount of money you need to invest every month between now and your retirement age to build your required retirement corpus.',
    whyItMatters:
      'It translates an intimidating multi-crore target into a concrete, manageable monthly savings goal you can budget for today.',
    example:
      'If your future target is ₹4 Crore in 20 years and your existing ₹15 Lakh will grow to ₹1.2 Crore, you need an additional ₹2.8 Crore. At 11% return, this requires investing approximately ₹32,500 every month.',
    calculation:
      'FinPilot uses the standard financial sinking-fund formula: Required Monthly Addition = (Future Shortfall × r) ÷ ((1 + r)^n - 1), where r is the monthly return rate and n is the number of months until retirement.',
    limitations:
      'Assumes a constant monthly investment amount and steady investment returns. In reality, stepping up your investment as your salary grows reduces the required initial monthly amount.',
  },

  // L. Retirement Shortfall
  retirement_shortfall: {
    id: 'retirement_shortfall',
    title: 'Amount You Still Need to Build',
    technicalTerm: 'Corpus Shortfall / Funding Deficit',
    category: 'retirement',
    simpleMeaning:
      'The gap between what your plan estimates you will need and what your existing investments plus scheduled monthly contributions are projected to reach.',
    whyItMatters:
      'Knowing this gap lets you take corrective action early—such as increasing your monthly savings, cutting non-essential expenses, or working an extra year or two.',
    example:
      'If you need ₹3 Crore at age 50, but your current pace is projected to accumulate ₹2.4 Crore by age 50, your shortfall is ₹60 Lakh.',
    calculation:
      'Retirement Shortfall = Target Corpus at Retirement Age minus Projected Corpus at Retirement Age. If positive, a gap exists; if zero or negative, your goal is fully funded.',
    limitations:
      'Both figures are estimates based on assumed rates of return and inflation. A favorable market cycle can erase a shortfall, while an unfavorable cycle can widen it.',
  },

  // M. Financial Health Score
  financial_health_score: {
    id: 'financial_health_score',
    title: 'Financial Health Check (8 Pillars)',
    technicalTerm: 'Holistic 8-Pillar Financial Health Assessment',
    category: 'health',
    simpleMeaning:
      'A comprehensive 0 to 100 score that grades how well-balanced and resilient your personal finances are across eight essential building blocks.',
    whyItMatters:
      'Retirement planning is useless if a single emergency or high-interest debt wipes you out. This score highlights blind spots before they cause financial harm.',
    example:
      'A user earning ₹1 Lakh/month with ₹20 Lakh in investments but zero emergency fund and 60% income going to debt might score 45/100, showing critical vulnerability in liquidity and debt safety.',
    calculation:
      'FinPilot evaluates 8 deterministic pillars: Emergency Reserve (15%), Savings Rate (15%), Debt-to-Income (15%), Housing Ratio (10%), Investment Diversification (15%), Insurance/Protection (10%), Retirement Pace (10%), and Net Worth Velocity (10%).',
    limitations:
      'This score is an educational wellness diagnostic, not an official CIBIL credit score or regulated credit rating. It is strictly based on data you link or enter.',
  },

  // Net Worth
  net_worth: {
    id: 'net_worth',
    title: 'Estimated Net Worth',
    technicalTerm: 'Total Net Worth (Assets minus Liabilities)',
    category: 'overview',
    simpleMeaning:
      'The total value of everything you own (bank deposits, mutual funds, gold, property) minus everything you owe (loans, credit card balances, mortgages).',
    whyItMatters:
      'It is the single most accurate measure of your overall financial standing, showing whether you are genuinely growing wealth over time.',
    example:
      'If you own ₹25 Lakh in assets (₹5 Lakh bank savings + ₹15 Lakh mutual funds + ₹5 Lakh vehicle) and owe ₹10 Lakh on a car and personal loan, your net worth is ₹15 Lakh.',
    calculation:
      'FinPilot computes: Net Worth = Total Recorded Assets (verified bank accounts + logged holdings) minus Total Active Liabilities (outstanding loans and credit debts).',
    limitations:
      'Only includes accounts, holdings, and liabilities that have been linked via statements or entered into FinPilot.',
  },

  // Cash Flow / Surplus
  cash_flow: {
    id: 'cash_flow',
    title: 'Monthly Cash Surplus',
    technicalTerm: 'Net Cash Flow / Retained Surplus',
    category: 'budget',
    simpleMeaning:
      'The money left over in your pocket at the end of the month after paying all living expenses, bills, and loan EMIs from your total income.',
    whyItMatters:
      'Positive cash surplus is the fuel for wealth creation. Without surplus cash, you cannot invest for retirement or build an emergency fund.',
    example:
      'If your salary is ₹80,000 and your monthly rent, groceries, bills, and EMIs total ₹52,000, your monthly cash surplus is ₹28,000 (a 35% savings rate).',
    calculation:
      'FinPilot computes: Monthly Surplus = Total Monthly Income minus Total Monthly Expenses. In statement-verified mode, it uses the average observed cash flow from your bank transactions.',
    limitations:
      'Irregular expenses (like annual insurance premiums, festival spending, or vehicle servicing) can cause cash surplus to fluctuate from month to month.',
  },

  // Emergency Fund
  emergency_fund: {
    id: 'emergency_fund',
    title: 'Emergency Reserve Runway',
    technicalTerm: 'Emergency Fund / Liquidity Buffer',
    category: 'overview',
    simpleMeaning:
      'Money kept safely in accessible bank accounts or liquid funds, reserved strictly for unexpected emergencies like medical events, urgent repairs, or temporary job loss.',
    whyItMatters:
      'It prevents you from having to take high-interest personal loans or sell long-term mutual fund investments at a loss when life throws a surprise at you.',
    example:
      'If your essential monthly living costs are ₹45,000, a recommended 6-month emergency reserve is ₹2,70,000 kept in a savings account or liquid mutual fund.',
    calculation:
      'Emergency Runway = Total Liquid Assets (cash, savings bank balances, liquid funds) ÷ Monthly Living Expenses. Expressed in months of runway.',
    limitations:
      'Money in locked instruments like EPF, PPF, real estate, or ELSS cannot be counted because they cannot be immediately withdrawn in an emergency.',
  },

  // Recurring Payments / Subscriptions
  recurring_payment: {
    id: 'recurring_payment',
    title: 'Recurring Payments & Subscriptions',
    technicalTerm: 'Automated Standing Instructions & Periodic Charges',
    category: 'budget',
    simpleMeaning:
      'Bills and charges that repeat automatically every month, quarter, or year—such as OTT subscriptions, gym memberships, insurance premiums, software, or broadband.',
    whyItMatters:
      'Small monthly subscriptions easily go unnoticed, steadily draining thousands of rupees every year for services you may no longer use.',
    example:
      'Four unused streaming apps costing ₹499 each add up to ₹2,000 per month, or ₹24,000 per year—money that could have been invested in an SIP.',
    calculation:
      'FinPilot detects recurring transactions by analyzing transaction descriptions, merchant names, intervals (monthly, quarterly, annual), and consistent payment amounts.',
    limitations:
      'Irregularly timed utility bills (like electricity with variable amounts) may occasionally be classified as variable expenses rather than fixed recurring charges.',
  },

  // Debt Payoff / Avalanche vs Snowball
  debt_payoff: {
    id: 'debt_payoff',
    title: 'Debt Payoff Strategy',
    technicalTerm: 'Debt Elimination Strategy (Avalanche vs Snowball)',
    category: 'debt',
    simpleMeaning:
      'A structured, step-by-step plan to pay off your loans and credit card debts as quickly and cheaply as possible.',
    whyItMatters:
      'High-interest debts (like credit cards charging 36–42% annual interest) destroy wealth faster than any investment can build it.',
    example:
      'The "Avalanche" method tackles the highest-interest debt first (e.g. credit card at 36%) to save the most interest. The "Snowball" method tackles the smallest loan balance first (e.g. ₹15,000 loan) to give you quick psychological wins.',
    calculation:
      'FinPilot models your active liabilities, simulating monthly payments under both Avalanche (mathematically optimal) and Snowball (behaviorally motivating) strategies to show exact payoff dates and interest saved.',
    limitations:
      'Assumes you make all minimum payments on time and do not rack up additional debt while following the payoff plan.',
  },

  // Tax Planning / Old vs New Regime
  tax_regime: {
    id: 'tax_regime',
    title: 'Tax Planning: New vs Old Regime',
    technicalTerm: 'Income Tax Slab Optimization (FY 2024-25 / FY 2025-26)',
    category: 'tax',
    simpleMeaning:
      'A comparison between India\'s two tax systems to determine which one leaves you with more take-home pay after accounting for your salary and deductions.',
    whyItMatters:
      'Choosing the wrong regime can cost you ₹30,000 to ₹1,00,000 or more every year in unnecessary income tax.',
    example:
      'Under the New Regime, tax rates are lower but deductions like 80C, 80D, and HRA are not allowed. If you have high rent (HRA) and ₹1.5 Lakh in 80C investments, the Old Regime might save you more money; otherwise, the New Regime is often better.',
    calculation:
      'FinPilot calculates your tax liability under both the Old Regime (factoring in Standard Deduction, 80C, 80D, HRA, NPS, and home loan interest) and the New Regime (with standard deduction and rebate under Section 87A), showing the exact rupee difference.',
    limitations:
      'FinPilot provides deterministic educational tax estimations based on current Indian tax laws. It does not replace professional advice from a qualified Chartered Accountant (CA).',
  },

  // Asset Allocation
  asset_allocation: {
    id: 'asset_allocation',
    title: 'Asset Allocation & Diversification',
    technicalTerm: 'Portfolio Asset Allocation & Risk Rebalancing',
    category: 'investment',
    simpleMeaning:
      'How your total wealth is divided across different investment types—such as stocks (equity), fixed deposits/bonds (debt), gold, and cash.',
    whyItMatters:
      'Different assets behave differently. Stocks provide high growth but volatile swings; debt and fixed deposits provide stability and steady income; gold protects against currency drops.',
    example:
      'A balanced 30-year-old might keep 65% in equity mutual funds for growth, 25% in debt/EPF for safety, 5% in digital gold, and 5% in liquid bank cash.',
    calculation:
      'FinPilot categorizes each holding in your asset registry into Equity, Debt, Cash, Gold, or Real Estate, and calculates the exact percentage distribution.',
    limitations:
      'Asset allocation does not guarantee profit or eliminate the risk of market loss, but it significantly reduces the volatility of your overall portfolio.',
  },

  // How Money Grows Chart
  growth_chart: {
    id: 'growth_chart',
    title: 'How Your Money Could Grow Over Time',
    technicalTerm: 'Multi-Scenario Wealth Accumulation & Decumulation Projection',
    category: 'retirement',
    simpleMeaning:
      'An estimate of how your savings may grow before retirement through monthly investing and compound interest, and how they may change after retirement as you withdraw money for living expenses.',
    whyItMatters:
      'It lets you visualize whether your savings will continue to support you throughout your life or if they risk depleting in your later years.',
    example:
      'The chart plots three paths: Base Case (expected returns, e.g. 11%), Optimistic (higher returns, e.g. 13%), and Conservative (lower returns, e.g. 9%), showing the range of possible outcomes.',
    calculation:
      'FinPilot projects year-by-year cash flows: During working years, your balance compounds and grows with monthly additions. After retirement age, annual living expenses (adjusted for inflation) are withdrawn each year.',
    limitations:
      'In real life, investment returns fluctuate every day and never follow a smooth curve. Projections are models to test feasibility, not guaranteed promises.',
  },

  // Reducing Interest Rate & Loan Amortization
  reducing_interest: {
    id: 'reducing_interest',
    title: 'Reducing Balance Loan Amortization',
    technicalTerm: 'Monthly Reducing Balance EMI Calculation',
    category: 'debt',
    simpleMeaning:
      'A method of calculating loan interest where you only pay interest on the outstanding unpaid principal balance each month, rather than on the original full loan amount.',
    whyItMatters:
      'Flat-rate loans are deceptive: a 10% flat interest rate is actually equivalent to nearly 18% reducing interest. Reducing balance ensures you are only charged on what you actually owe.',
    example:
      'On an ₹8,00,000 car loan at 9.5% for 5 years, your monthly EMI is ₹16,798. In month 1, ₹6,333 goes to interest. By month 48, your remaining balance is lower, so only ₹1,400 goes to interest and the rest clears principal.',
    calculation:
      'FinPilot uses the standard mathematical amortization formula: EMI = [P × r × (1 + r)^n] / [(1 + r)^n - 1], where P is principal, r is monthly interest rate, and n is tenure in months.',
    limitations:
      'Prepayments, late fee charges, or floating interest rate resets will alter the total interest paid and effective tenure.',
    actionableTip:
      'Always ask the lender for the reducing-balance annual percentage rate (APR) and compare total interest paid rather than just the quoted rate.',
  },

  // Debt-to-Income Ratio
  debt_to_income: {
    id: 'debt_to_income',
    title: 'Debt-to-Income (DTI) Ratio',
    technicalTerm: 'Fixed Obligation to Income Ratio (FOIR / DTI)',
    category: 'debt',
    simpleMeaning:
      'The percentage of your total monthly income that goes toward paying loan EMIs and credit obligations.',
    whyItMatters:
      'Lenders and financial planners use this to measure your financial stress. When DTI exceeds 40%, any sudden income drop or emergency can quickly trigger defaults.',
    example:
      'If your monthly income is ₹1,00,000 and your home loan EMI is ₹30,000 plus a car EMI of ₹10,000, your DTI is 40%.',
    calculation:
      'DTI % = (Total Monthly Loan EMIs ÷ Total Gross Monthly Income) × 100.',
    limitations:
      'Does not account for non-debt essential living expenses like groceries, medical costs, or children\'s school fees.',
    actionableTip:
      'Keep your total DTI under 35-40% so you maintain an adequate monthly surplus for emergency savings and retirement investing.',
  },

  // Stress Testing
  stress_testing: {
    id: 'stress_testing',
    title: 'Financial Stress Testing',
    technicalTerm: 'What-If Sensitivity & Stress Analysis',
    category: 'overview',
    simpleMeaning:
      'Testing how resilient your financial plan is when difficult surprises happen—such as a 15% salary cut, a 15% cost-of-living spike, or an unexpected medical emergency.',
    whyItMatters:
      'Decisions that look affordable on paper during good times can quickly become financial traps if life delivers an unexpected shock right after you commit.',
    example:
      'Before taking a ₹20,000 monthly car EMI, testing a 15% salary drop shows whether you can still pay your rent and groceries without going into negative cash flow.',
    calculation:
      'FinPilot recalculates your monthly surplus and emergency fund runway under 5 specific adverse scenarios: income drop (-15%), expense surge (+15%), surprise emergency expense (₹50k), interest rate hike (+1.5%), and 6-month delay.',
    limitations:
      'Hypothetical simulations help understand resilience; they do not predict the exact timing or probability of future market or life events.',
  },

  // Opportunity Cost: Cash vs Loan
  opportunity_cost: {
    id: 'opportunity_cost',
    title: 'Paying Cash vs Taking a Loan',
    technicalTerm: 'Capital Opportunity Cost & Liquidity Trade-off',
    category: 'investment',
    simpleMeaning:
      'Comparing the money you save by not paying loan interest against the investment returns you give up by spending all your liquid savings upfront.',
    whyItMatters:
      'Draining all your cash to avoid a loan can leave you completely unprotected against emergencies, while taking a high-interest loan needlessly bleeds money in interest.',
    example:
      'If you pay ₹5,00,000 cash for a car, you save ₹1,00,000 in loan interest. But if that ₹5,00,000 was invested in a mutual fund earning 12% annually, it could have grown to ₹7,00,000 over 3 years, making a low-interest loan potentially advantageous if your emergency fund is preserved.',
    calculation:
      'FinPilot models the net cost of the loan (interest + fees) against the projected growth of the cash if kept invested at your assumed annual return rate over the loan tenure.',
    limitations:
      'Investment returns are never guaranteed, whereas loan interest payments are legally obligatory and guaranteed.',
  },
};

