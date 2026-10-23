export type UserRole = 'student' | 'salaried' | 'freelancer' | 'business_owner';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface FinancialHealthSummary {
  net_worth: number;
  total_assets: number;
  total_liabilities: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_surplus: number;
  savings_rate: number;
  emergency_fund_current: number;
  emergency_fund_target: number;
  emergency_fund_months: number;
}

export interface Transaction {
  id: string;
  date: string;
  amount: number;
  type: 'income' | 'expense';
  category: string;
  description: string;
  source: string;
  is_recurring: boolean;
}

export interface TaxRegimeBreakdown {
  regime: 'new' | 'old';
  assessment_year: string;
  gross_income: number;
  total_deductions: number;
  taxable_income: number;
  tax_before_rebate: number;
  rebate_87a: number;
  surcharge: number;
  cess: number;
  total_tax_liability: number;
  effective_rate: number;
  marginal_relief: number;
  slab_breakdown?: Array<{
    slab: string;
    rate: string;
    amount: number;
  }>;
  deduction_breakdown?: Record<string, number>;
  notes?: string[];
}

export interface TaxComparisonResult {
  assessment_year: string;
  recommended_regime: 'new' | 'old';
  savings_amount: number;
  new_regime: TaxRegimeBreakdown;
  old_regime: TaxRegimeBreakdown;
  summary_explanation?: string;
  citations: string[];
}

export interface InvestmentOptionComparison {
  category: string;
  display_name: string;
  indicative_annual_yield_pct: number;
  recommended_time_horizon: string;
  liquidity_mechanism: string;
  credit_risk_level: string;
  interest_rate_risk: string;
  tax_treatment_summary: string;
  exit_load_or_penalty: string;
  pros: string[];
  cons: string[];
  suitability_verdict: string;
  projected_maturity_value: number;
  inflation_adjusted_value: number;
}

export interface InvestmentCompareResponse {
  principal_amount: number;
  time_horizon_months: number;
  inflation_rate_pct: number;
  comparisons: InvestmentOptionComparison[];
  top_recommendation: string;
  rationale: string;
  disclaimer: string;
}

export interface FinancialGoal {
  id: string;
  name: string;
  category: 'emergency_fund' | 'home' | 'education' | 'retirement' | 'custom';
  target_amount: number;
  current_amount: number;
  target_date: string;
  monthly_required?: number;
  progress_pct?: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: string[];
  tool_invocations?: Array<{
    tool: string;
    summary: string;
  }>;
}
