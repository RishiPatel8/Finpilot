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
  monthly_history?: Array<{
    month_key: string;
    month: string;
    income: number;
    expenses: number;
    surplus: number;
  }>;
  statement_coverage?: {
    start_date: string;
    end_date: string;
    days: number;
    coverage_months: number;
    total_transactions: number;
  } | null;
  is_empty?: boolean;
  data_quality?: {
    has_statements: boolean;
    has_bank_accounts: boolean;
    has_liabilities: boolean;
    has_assets: boolean;
    total_transactions: number;
    statement_months: number;
  };
}

export interface StatementPreviewRow {
  source_row?: number;
  date: string;
  value_date?: string;
  description: string;
  amount: number;
  type: 'income' | 'expense' | 'transfer';
  category: string;
  raw_type?: string;
  is_internal_transfer: boolean;
  reference_number?: string | null;
  balance_after?: number | null;
  is_duplicate: boolean;
  is_valid: boolean;
  explanation?: string;
}

export interface StatementPreviewResponse {
  success: boolean;
  error?: string;
  filename: string;
  format: string;
  total_rows: number;
  valid_rows: number;
  duplicate_rows: number;
  invalid_rows: number;
  coverage: {
    start_date: string | null;
    end_date: string | null;
    coverage_days: number;
    coverage_months: number;
  };
  financial_summary: {
    total_credits: number;
    total_debits: number;
    net_cash_flow: number;
    category_breakdown: Record<string, number>;
  };
  metadata: {
    bank_name?: string | null;
    account_number_masked?: string | null;
    closing_balance?: number | null;
  };
  warnings: string[];
  preview: StatementPreviewRow[];
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

export interface InvestmentProductSummary {
  id: string;
  name: string;
  category: string;
  asset_class: string;
  indicative_annual_yield_pct: number;
  rate_type: string;
  compounding_frequency: string;
  recommended_horizon: string;
  minimum_investment: number;
  minimum_sip_amount?: number | null;
  maximum_annual_investment?: number | null;
  lock_in_months: number;
  liquidity_rating: string;
  liquidity_mechanism: string;
  credit_risk_level: string;
  market_risk_level: string;
  duration_risk_level: string;
  dicgc_insured: boolean;
  dicgc_limit: number;
  exit_penalty_rules: string;
  tax_treatment_summary: string;
  tax_category: string;
  ter_pct: number;
  data_provenance: string;
  regulatory_authority: string;
  as_of_date: string;
  suitability: string;
}

export interface MultiProductCompareItem {
  product_id: string;
  name: string;
  category: string;
  asset_class: string;
  rate_used_pct: number;
  rate_type: string;
  compounding_frequency: string;
  invested_principal: number;
  gross_maturity_value: number;
  estimated_gain: number;
  estimated_fees_ter: number;
  estimated_tax: number;
  tax_rules_applied: string;
  net_post_tax_proceeds: number;
  net_annualized_cagr_pct: number;
  inflation_adjusted_value: number;
  is_locked: boolean;
  lock_in_months: number;
  liquidity_rating: string;
  liquidity_mechanism: string;
  credit_risk_level: string;
  market_risk_level: string;
  dicgc_insured: boolean;
  dicgc_coverage_amount: number;
  premature_exit_penalty: string;
  premature_exit_haircut_estimate: number;
  data_provenance: string;
  as_of_date: string;
  pros: string[];
  cons: string[];
  suitability_verdict: string;
}

export interface MultiProductCompareResponse {
  investment_mode: string;
  investment_amount: number;
  time_horizon_months: number;
  user_tax_slab_pct: number;
  inflation_rate_pct: number;
  items: MultiProductCompareItem[];
  top_recommendation: string;
  rationale: string;
  regulatory_disclaimer: string;
}

export interface LumpSumVsSipSchedulePoint {
  month: number;
  lump_sum_value: number;
  lump_sum_invested: number;
  sip_value: number;
  sip_invested: number;
}

export interface LumpSumVsSipResponse {
  product_name: string;
  time_horizon_months: number;
  expected_return_pct: number;
  lump_sum_total_invested: number;
  lump_sum_gross_value: number;
  lump_sum_net_post_tax: number;
  lump_sum_real_purchasing_power: number;
  sip_total_invested: number;
  sip_gross_value: number;
  sip_net_post_tax: number;
  sip_real_purchasing_power: number;
  rupee_cost_averaging_verdict: string;
  schedule: LumpSumVsSipSchedulePoint[];
  recommendation: string;
}

export interface GoalAllocationSlice {
  asset_class: string;
  target_percentage: number;
  allocated_sip: number;
  allocated_lump_sum: number;
  suggested_product: string;
  indicative_rate_pct: number;
}

export interface GoalInvestmentPlanResponse {
  goal_name: string;
  nominal_target: number;
  inflation_adjusted_target: number;
  time_horizon_months: number;
  current_amount_allocated: number;
  required_monthly_sip: number;
  required_lump_sum_alternative: number;
  expected_blended_cagr_pct: number;
  allocation_breakdown: GoalAllocationSlice[];
  cash_sufficiency_notice: string;
  verified_liquid_cash_available?: number | null;
  is_fully_funded: boolean;
  disclaimer: string;
}

export interface InvestmentStressTestResponse {
  stress_scenario: string;
  scenario_title: string;
  scenario_description: string;
  total_capital_deployed: number;
  baseline_projected_value: number;
  stressed_projected_value: number;
  drawdown_amount: number;
  drawdown_pct: number;
  estimated_recovery_months: number;
  resilience_rating: 'High' | 'Moderate' | 'Vulnerable' | string;
  vulnerable_assets: string[];
  cushioning_assets: string[];
  safeguard_recommendations: string[];
  disclaimer: string;
}

export interface AssetCategorySlice {
  category: string;
  label: string;
  total_value: number;
  percentage: number;
  target_percentage: number;
  difference_pct: number;
}

export interface PortfolioAnalysisResponse {
  total_portfolio_value: number;
  categories_breakdown: AssetCategorySlice[];
  equity_exposure_pct: number;
  debt_fixed_income_pct: number;
  liquid_cash_pct: number;
  gold_alternatives_pct: number;
  risk_profile: string;
  risk_alignment_verdict: string;
  concentration_risks: string[];
  rebalancing_recommendations: string[];
  data_source: string;
}

export interface InvestmentScenarioItem {
  id: string;
  user_id: string;
  name: string;
  scenario_mode: string;
  notes?: string | null;
  inputs: Record<string, any>;
  results_summary: Record<string, any>;
  created_at: string;
  updated_at: string;
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

export interface ActionPreviewItem {
  label: string;
  value: string;
}

export interface ActionPreview {
  title: string;
  summary: string;
  items: ActionPreviewItem[];
  disclaimer: string;
}

export interface PendingActionData {
  id: string;
  action_type: string;
  target_entity: string;
  status: string;
  parameters: Record<string, any>;
  preview: ActionPreview;
  expires_at: string;
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
  pending_action?: PendingActionData | null;
  clarification?: {
    id?: string;
    question: string;
    options: Array<string | { id: string; label: string; action_type?: string; parameters?: any }>;
    expires_at?: string;
  } | null;
  feedback?: {
    rating?: number;
    submitted?: boolean;
  };
}

export interface ProactiveInsightItem {
  id: string;
  title: string;
  priority: 'high' | 'medium' | 'low' | 'positive' | string;
  category: string;
  message: string;
  evidence: string;
  suggested_prompt: string;
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
  debt_type?: 'payable' | 'receivable' | string;
  counterparty?: string | null;
  interest_period?: 'annual' | 'monthly' | string;
  status?: string;
  loan_date?: string | null;
  due_date?: string | null;
  repayment_frequency?: string;
  notes?: string | null;
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
  current_monthly_income?: number;
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

export interface FinancialInsight {
  id: string;
  category: 'spending' | 'budget' | 'recurring' | 'goal' | 'cash_flow' | 'savings' | 'anomaly' | string;
  title: string;
  summary: string;
  detail: string;
  severity: 'info' | 'success' | 'warning' | 'critical';
  confidence: 'high' | 'medium' | 'low';
  metric_value?: string;
  baseline_value?: string;
  action_label?: string;
  action_tab?: string;
  created_at: string;
}

export interface IntelligenceFeedResponse {
  insights: FinancialInsight[];
  total_insights: number;
  high_priority_count: number;
  data_quality_summary: Record<string, any>;
  generated_at: string;
}

export interface CashFlowForecast {
  horizon_days: number;
  projected_income: number;
  projected_expenses: number;
  projected_net: number;
  projected_ending_cash?: number;
  daily_burn_rate: number;
  key_drivers: string[];
  assumptions: string[];
  confidence: string;
  insufficient_data: boolean;
}

export interface AdaptiveBudgetRecommendation {
  category: string;
  historical_average: number;
  current_budget?: number;
  recommended_budget: number;
  rationale: string;
  potential_savings: number;
}

export interface GoalFeasibility {
  goal_id: string;
  goal_name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  required_monthly_sip: number;
  current_projected_monthly_savings: number;
  is_on_track: boolean;
  projected_completion_date?: string;
  delay_months: number;
  remedial_actions: string[];
}

export interface RecurringTransactionItem {
  id: string;
  user_id: string;
  bank_account_id?: string | null;
  name: string;
  merchant?: string | null;
  transaction_type: 'income' | 'expense';
  amount: number;
  category: string;
  frequency: 'weekly' | 'fortnightly' | 'monthly' | 'quarterly' | 'yearly';
  status: 'detected' | 'confirmed' | 'paused' | 'dismissed' | 'cancelled';
  confidence: 'high' | 'medium' | 'low';
  detection_source: string;
  explanation?: string | null;
  next_expected_date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  last_occurrence_date?: string | null;
  occurrence_count: number;
  user_confirmed_at?: string | null;
  user_feedback?: string | null;
  user_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpcomingOccurrenceItem {
  expected_date: string;
  recurring_id: string;
  name: string;
  merchant?: string | null;
  amount: number;
  transaction_type: 'income' | 'expense';
  category: string;
  frequency: string;
  status: string;
  is_overdue: boolean;
  days_until: number;
}

export interface UpcomingSummaryResponse {
  horizon_days: number;
  total_upcoming_expenses: number;
  total_upcoming_income: number;
  net_upcoming_cash_flow: number;
  occurrences: UpcomingOccurrenceItem[];
}

export interface RecurringSummaryData {
  monthly_recurring_expenses: number;
  monthly_recurring_income: number;
  net_recurring_cash_flow: number;
  active_count: number;
  paused_count: number;
  pending_review_count: number;
  next_upcoming_payment?: UpcomingOccurrenceItem | null;
  next_upcoming_income?: UpcomingOccurrenceItem | null;
}

export interface TelegramLinkCodeResponse {
  code: string;
  expires_at: string;
  valid_for_seconds: number;
  bot_username?: string | null;
  deep_link_url?: string | null;
}

export interface TelegramStatusResponse {
  is_linked: boolean;
  telegram_username?: string | null;
  telegram_first_name?: string | null;
  linked_at?: string | null;
  notifications_enabled: boolean;
  notify_bills: boolean;
  notify_budget: boolean;
  notify_goals: boolean;
  notify_summary: boolean;
  bot_username?: string | null;
}

export interface TelegramNotificationPrefsUpdate {
  notifications_enabled?: boolean;
  notify_bills?: boolean;
  notify_budget?: boolean;
  notify_goals?: boolean;
  notify_summary?: boolean;
}


