export type UserRole = 'student' | 'salaried' | 'freelancer' | 'business_owner';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  auth_provider?: string;
  firebase_uid?: string;
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
  gross_income?: number;
  gross_total_income?: string | number;
  standard_deduction?: string | number;
  allowed_deductions?: Record<string, string | number>;
  total_deductions: string | number;
  taxable_income: string | number;
  tax_before_rebate?: string | number;
  tax_on_income?: string | number;
  rebate_87a: string | number;
  surcharge: string | number;
  cess?: string | number;
  health_and_education_cess?: string | number;
  total_tax_liability: string | number;
  effective_rate?: number;
  effective_tax_rate_pct?: number;
  marginal_relief?: string | number;
  slab_details?: Array<{
    slab_range: string;
    taxable_in_slab: string | number;
    rate_pct: string | number;
    tax_amount: string | number;
  }>;
  official_citations?: string[];
  notes?: string[];
}

export interface TaxComparisonResult {
  assessment_year: string;
  taxpayer_type?: string;
  recommended_regime: 'new' | 'old' | string;
  tax_savings?: string | number;
  savings_amount?: number;
  explanation?: string;
  summary_explanation?: string;
  new_regime: TaxRegimeBreakdown;
  old_regime: TaxRegimeBreakdown;
  citations?: string[];
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

export interface FinancialProfile {
  id?: string;
  user_id?: string;
  age?: number;
  dependents: number;
  monthly_income: number;
  monthly_expenses: number;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive' | string;
  emergency_fund_target_months: number;
  tax_regime_preference: 'auto' | 'new' | 'old' | string;
}

export interface Liability {
  id: string;
  user_id: string;
  name: string;
  principal: number;
  interest_rate: number;
  monthly_emi: number;
  tenure_months: number;
  remaining_months: number;
  created_at?: string;
}

export interface DebtRepaymentPlan {
  total_debt_principal: number;
  total_monthly_emi: number;
  extra_payment_applied: number;
  avalanche_priority: string[];
  snowball_priority: string[];
  strategy_recommendation: string;
}

export interface BankAccount {
  id: string;
  institution_name: string;
  account_number_masked: string;
  account_type: string;
  ifsc_code: string;
  currency: string;
  current_balance: number;
  balance_type: string;
  balance_timestamp: string;
  sync_status: 'synced' | 'pending' | 'failed' | 'stale';
  last_synced_at?: string;
}

export interface BankConsent {
  id: string;
  consent_handle: string;
  consent_id?: string;
  provider: string;
  status: 'PENDING' | 'ACTIVE' | 'REVOKED' | 'EXPIRED' | 'REJECTED';
  valid_to: string;
  fip_ids?: string[];
}

export interface BankSyncResult {
  account_id: string;
  institution_name: string;
  synced_count: number;
  current_balance: number;
  balance_timestamp: string;
  sync_status: string;
  message: string;
}

export interface FireStrategySummary {
  strategy_type: 'lean' | 'regular' | 'fat' | 'coast' | 'custom';
  name: string;
  description: string;
  monthly_expense_in_retirement: number;
  target_corpus_today: number;
  target_corpus_at_retirement: number;
  projected_fire_age?: number | null;
  years_to_fire?: number | null;
  required_monthly_investment: number;
  is_achievable_by_target_age: boolean;
  shortfall_or_surplus_at_retirement: number;
  assumptions_and_limitations: string;
}

export interface FireProjectionPoint {
  age: number;
  year: number;
  portfolio_conservative: number;
  portfolio_base: number;
  portfolio_optimistic: number;
  annual_contribution: number;
  annual_withdrawal: number;
  fire_target_curve: number;
  is_retired: boolean;
}

export interface FireCalculationResponse {
  current_age: number;
  planned_retirement_age: number;
  years_to_retirement: number;
  current_investable_assets: number;
  current_monthly_expenses: number;
  annual_expenses_today: number;
  savings_rate_pct: number;
  safe_withdrawal_rate_pct: number;
  real_return_pct: number;
  fire_target_today: number;
  fire_target_future: number;
  fire_progress_pct: number;
  projected_fire_age?: number | null;
  projected_portfolio_at_retirement: number;
  portfolio_surplus_or_shortfall: number;
  required_monthly_investment: number;
  current_monthly_investment: number;
  monthly_investment_gap: number;
  strategies: FireStrategySummary[];
  yearly_projections: FireProjectionPoint[];
  disclaimers: string[];
}

export interface FinancialHealthPillar {
  pillar_id: string;
  name: string;
  score: number;
  weight: number;
  status: 'excellent' | 'good' | 'fair' | 'critical' | 'provisional';
  metric_value: string;
  target_benchmark: string;
  description: string;
  action_priority: 'immediate' | 'medium_term' | 'long_term';
  recommendation: string;
}

export interface FinancialHealthAssessment {
  overall_score: number;
  status: string;
  is_provisional: boolean;
  summary: string;
  pillars: FinancialHealthPillar[];
  actionable_checklist_12_months: Array<{
    timeframe: string;
    action: string;
    detail: string;
    pillar: string;
  }>;
  disclaimer: string;
}

