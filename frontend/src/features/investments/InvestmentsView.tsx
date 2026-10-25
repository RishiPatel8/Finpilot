import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Shield,
  Zap,
  Clock,
  AlertCircle,
  CheckCircle2,
  Lock,
  Unlock,
  Percent,
  Sparkles,
  Info,
  Layers,
  ArrowRight,
  Filter,
  BarChart2,
  Calendar,
  AlertTriangle,
  Bookmark,
  Trash2,
  Edit2,
  ExternalLink,
  ChevronRight,
  Plus,
  RefreshCw,
  HelpCircle,
  PiggyBank,
  Briefcase,
  Home,
  GraduationCap,
  Car,
  Compass,
  Check,
  Target
} from 'lucide-react';
import { apiRequest, getAuthToken } from '../../services/api';
import {
  InvestmentProductSummary,
  MultiProductCompareResponse,
  MultiProductCompareItem,
  LumpSumVsSipResponse,
  GoalInvestmentPlanResponse,
  InvestmentStressTestResponse,
  PortfolioAnalysisResponse,
  InvestmentScenarioItem
} from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';
import { KnowMore } from '../../components/KnowMore';

type TabMode = 'screener' | 'compare' | 'lumpsum_sip' | 'goal_plan' | 'stress_test' | 'portfolio' | 'saved_scenarios' | 'glossary';

export const InvestmentsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabMode>('screener');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // 1. Catalog State
  const [products, setProducts] = useState<InvestmentProductSummary[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [onlyGuaranteed, setOnlyGuaranteed] = useState<boolean>(false);
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([
    'liquid_mf',
    'bank_fd',
    'nifty50_index_fund',
    'ppf'
  ]);

  // 2. Multi-Product Compare Parameters
  const [investMode, setInvestMode] = useState<'lump_sum' | 'monthly_sip'>('lump_sum');
  const [compareAmount, setCompareAmount] = useState<number>(300000);
  const [compareMonths, setCompareMonths] = useState<number>(36);
  const [taxSlab, setTaxSlab] = useState<number>(30);
  const [expectedInflation, setExpectedInflation] = useState<number>(6.0);
  const [canLockFunds, setCanLockFunds] = useState<boolean>(true);
  const [compareResult, setCompareResult] = useState<MultiProductCompareResponse | null>(null);

  // 3. Lump Sum vs SIP Parameters
  const [lvsProductId, setLvsProductId] = useState<string>('nifty50_index_fund');
  const [lvsLumpSum, setLvsLumpSum] = useState<number>(360000);
  const [lvsMonthlySip, setLvsMonthlySip] = useState<number>(10000);
  const [lvsMonths, setLvsMonths] = useState<number>(36);
  const [lvsReturnPct, setLvsReturnPct] = useState<number>(12.0);
  const [lvsResult, setLvsResult] = useState<LumpSumVsSipResponse | null>(null);

  // 4. Goal Investment Planner Parameters
  const [goalName, setGoalName] = useState<string>('House Down Payment');
  const [goalTargetAmount, setGoalTargetAmount] = useState<number>(2500000);
  const [goalMonths, setGoalMonths] = useState<number>(60);
  const [goalCurrentAlloc, setGoalCurrentAlloc] = useState<number>(200000);
  const [goalRiskProfile, setGoalRiskProfile] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate');
  const [goalAdjustInflation, setGoalAdjustInflation] = useState<boolean>(true);
  const [goalResult, setGoalResult] = useState<GoalInvestmentPlanResponse | null>(null);

  // 5. Stress Testing Parameters
  const [stressScenario, setStressScenario] = useState<string>('market_crash_20');
  const [stressHorizon, setStressHorizon] = useState<number>(36);
  const [stressResult, setStressResult] = useState<InvestmentStressTestResponse | null>(null);

  // 6. Portfolio Analysis State
  const [portfolioData, setPortfolioData] = useState<PortfolioAnalysisResponse | null>(null);

  // 7. Saved Scenarios State
  const [savedScenarios, setSavedScenarios] = useState<InvestmentScenarioItem[]>([]);
  const [saveModalOpen, setSaveModalOpen] = useState<boolean>(false);
  const [scenarioNameInput, setScenarioNameInput] = useState<string>('');
  const [scenarioNotesInput, setScenarioNotesInput] = useState<string>('');

  const isLoggedIn = Boolean(getAuthToken());

  // Fetch product catalog
  const fetchProducts = async () => {
    try {
      const url = `/investments/products?category=${categoryFilter}&only_guaranteed=${onlyGuaranteed}`;
      const data = await apiRequest<InvestmentProductSummary[]>(url);
      setProducts(data);
    } catch (err: any) {
      console.error('Failed to load products', err);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [categoryFilter, onlyGuaranteed]);

  // Load Saved Scenarios & Portfolio if logged in
  const fetchUserData = async () => {
    if (!isLoggedIn) return;
    try {
      const [scenarios, portfolio] = await Promise.all([
        apiRequest<InvestmentScenarioItem[]>('/investments/scenarios').catch(() => []),
        apiRequest<PortfolioAnalysisResponse>('/investments/portfolio-analysis').catch(() => null)
      ]);
      setSavedScenarios(scenarios);
      if (portfolio) setPortfolioData(portfolio);
    } catch (err) {
      console.error('Error fetching user scenarios/portfolio', err);
    }
  };

  useEffect(() => {
    fetchUserData();
  }, [isLoggedIn]);

  // Execute Comparison
  const handleCompare = async () => {
    if (selectedProductIds.length === 0) {
      setError('Please select at least 1 investment instrument to compare.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<MultiProductCompareResponse>('/investments/multi-compare', {
        method: 'POST',
        body: JSON.stringify({
          selected_product_ids: selectedProductIds,
          investment_mode: investMode,
          investment_amount: compareAmount,
          time_horizon_months: compareMonths,
          user_tax_slab_pct: taxSlab,
          expected_inflation_pct: expectedInflation,
          can_lock_funds: canLockFunds,
        }),
      });
      setCompareResult(res);
      setActiveTab('compare');
    } catch (err: any) {
      setError(err.message || 'Comparison calculation failed.');
    } finally {
      setLoading(false);
    }
  };

  // Execute Lump Sum vs SIP
  const handleLumpSumVsSip = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<LumpSumVsSipResponse>('/investments/lumpsum-vs-sip', {
        method: 'POST',
        body: JSON.stringify({
          product_id: lvsProductId,
          lump_sum_amount: lvsLumpSum,
          monthly_sip_amount: lvsMonthlySip,
          time_horizon_months: lvsMonths,
          expected_annual_return_pct: lvsReturnPct,
          expected_annual_inflation_pct: expectedInflation,
          user_tax_slab_pct: taxSlab,
        }),
      });
      setLvsResult(res);
    } catch (err: any) {
      setError(err.message || 'Lump Sum vs SIP analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  // Execute Goal Plan
  const handleGoalPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<GoalInvestmentPlanResponse>('/investments/goal-plan', {
        method: 'POST',
        body: JSON.stringify({
          goal_name: goalName,
          target_amount: goalTargetAmount,
          time_horizon_months: goalMonths,
          current_amount_allocated: goalCurrentAlloc,
          risk_profile: goalRiskProfile,
          adjust_for_inflation: goalAdjustInflation,
          expected_annual_inflation_pct: expectedInflation,
          user_tax_slab_pct: taxSlab,
        }),
      });
      setGoalResult(res);
    } catch (err: any) {
      setError(err.message || 'Goal investment planning failed.');
    } finally {
      setLoading(false);
    }
  };

  // Execute Stress Test
  const handleStressTest = async () => {
    setLoading(true);
    setError(null);
    try {
      // Create portfolio sample from selected or default products
      const portfolioItems = [
        { product_id: 'nifty50_index_fund', amount_invested: compareAmount * 0.5 },
        { product_id: 'bank_fd', amount_invested: compareAmount * 0.35 },
        { product_id: 'sovereign_gold_bond', amount_invested: compareAmount * 0.15 },
      ];
      const res = await apiRequest<InvestmentStressTestResponse>('/investments/stress-test', {
        method: 'POST',
        body: JSON.stringify({
          portfolio_items: portfolioItems,
          time_horizon_months: stressHorizon,
          stress_scenario: stressScenario,
        }),
      });
      setStressResult(res);
    } catch (err: any) {
      setError(err.message || 'Stress test simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  // Save Scenario
  const handleSaveScenario = async () => {
    if (!scenarioNameInput.trim()) return;
    try {
      const newScenario = await apiRequest<InvestmentScenarioItem>('/investments/scenarios', {
        method: 'POST',
        body: JSON.stringify({
          name: scenarioNameInput,
          scenario_mode: activeTab,
          notes: scenarioNotesInput || null,
          inputs: {
            investMode,
            compareAmount,
            compareMonths,
            taxSlab,
            expectedInflation,
            selectedProductIds,
          },
          results_summary: compareResult
            ? {
                top_recommendation: compareResult.top_recommendation,
                item_count: compareResult.items.length,
              }
            : {},
        }),
      });
      setSavedScenarios([newScenario, ...savedScenarios]);
      setSaveModalOpen(false);
      setScenarioNameInput('');
      setScenarioNotesInput('');
      setSuccessMsg('Scenario saved successfully under your authenticated profile!');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to save scenario.');
    }
  };

  // Delete Scenario
  const handleDeleteScenario = async (id: string) => {
    if (!confirm('Are you sure you want to delete this saved scenario?')) return;
    try {
      await apiRequest(`/investments/scenarios/${id}`, { method: 'DELETE' });
      setSavedScenarios(savedScenarios.filter((s) => s.id !== id));
      setSuccessMsg('Scenario deleted.');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to delete scenario.');
    }
  };

  const toggleSelectProduct = (id: string) => {
    if (selectedProductIds.includes(id)) {
      if (selectedProductIds.length === 1) return; // Keep at least one
      setSelectedProductIds(selectedProductIds.filter((p) => p !== id));
    } else {
      if (selectedProductIds.length >= 6) {
        alert('You can compare a maximum of 6 investment instruments simultaneously.');
        return;
      }
      setSelectedProductIds([...selectedProductIds, id]);
    }
  };

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val || 0);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Page Header */}
      <PageHeader
        title="Indian Investment Research & Portfolio Planner"
        description="Comprehensive statutory research, scenario-driven comparison, goal planning, and portfolio stress testing across verified Indian asset classes. Zero fabricated live quotes."
        icon={<TrendingUp className="w-5 h-5 text-[#6478E8]" />}
        badge={<KnowMore termId="asset_allocation" variant="badge" label="Statutory Norms" />}
      />

      {/* Global Alerts */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Calculation Notice</p>
            <p className="text-xs text-red-700 mt-0.5">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700 text-xs">Dismiss</button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center space-x-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
          <p className="font-medium text-xs">{successMsg}</p>
        </div>
      )}

      {/* Main Tab Navigation */}
      <div className="flex items-center space-x-1 border-b border-[#E6EAF0] overflow-x-auto pb-2 scrollbar-none">
        {[
          { id: 'screener', label: '1. Product Screener', icon: Filter },
          { id: 'compare', label: '2. Multi-Product Compare', icon: BarChart2 },
          { id: 'lumpsum_sip', label: '3. Lump Sum vs. SIP', icon: ArrowRight },
          { id: 'goal_plan', label: '4. Goal Investment Planner', icon: Target },
          { id: 'stress_test', label: '5. Risk & Stress Test', icon: Shield },
          { id: 'portfolio', label: '6. Portfolio Allocation', icon: Layers },
          { id: 'saved_scenarios', label: `7. Saved Scenarios (${savedScenarios.length})`, icon: Bookmark },
          { id: 'glossary', label: '8. Financial Terms', icon: HelpCircle },
        ].map((tab) => {
          const Icon = tab.icon as any;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabMode)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-[#172033] text-white shadow-sm'
                  : 'text-[#697386] hover:bg-[#F1F4F9] hover:text-[#172033]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* =========================================================================
          TAB 1: PRODUCT SCREENER & CATALOG
         ========================================================================= */}
      {activeTab === 'screener' && (
        <div className="space-y-6">
          {/* Filter Bar */}
          <Card className="flex flex-wrap items-center justify-between gap-4 p-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-semibold text-[#172033]">Filter Category:</span>
              {[
                { id: 'all', label: 'All Instruments' },
                { id: 'liquid', label: 'Liquid & Cash' },
                { id: 'fixed_income', label: 'Fixed Deposits & Bonds' },
                { id: 'small_savings', label: 'Small Savings (PPF/EPF/NPS)' },
                { id: 'equity', label: 'Equities & Mutual Funds' },
                { id: 'alternatives', label: 'Gold & Real Estate' },
              ].map((c) => (
                <button
                  key={c.id}
                  onClick={() => setCategoryFilter(c.id)}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${
                    categoryFilter === c.id
                      ? 'bg-[#6478E8] text-white'
                      : 'bg-[#F1F4F9] text-[#697386] hover:bg-[#E6EAF0]'
                  }`}
                >
                  {c.label}
                </button>
              ))}
            </div>

            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2 text-xs font-semibold text-[#172033] cursor-pointer">
                <input
                  type="checkbox"
                  checked={onlyGuaranteed}
                  onChange={(e) => setOnlyGuaranteed(e.target.checked)}
                  className="rounded text-[#6478E8] focus:ring-[#6478E8]"
                />
                <span>Only Sovereign / Capital Guaranteed</span>
              </label>

              <Button
                variant="primary"
                size="sm"
                onClick={handleCompare}
                className="flex items-center space-x-1.5 bg-[#6478E8] hover:bg-[#5365CE]"
              >
                <BarChart2 className="w-3.5 h-3.5" />
                <span>Compare Selected ({selectedProductIds.length})</span>
              </Button>
            </div>
          </Card>

          {/* Product Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {products.map((p) => {
              const isSelected = selectedProductIds.includes(p.id);
              return (
                <Card
                  key={p.id}
                  className={`p-5 space-y-4 border-2 transition-all cursor-pointer relative ${
                    isSelected ? 'border-[#6478E8] shadow-md bg-white' : 'border-transparent bg-white hover:border-[#E6EAF0]'
                  }`}
                  onClick={() => toggleSelectProduct(p.id)}
                >
                  {/* Selection Checkbox */}
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#F1F4F9] text-[#697386]">
                          {p.category.replace('_', ' ')}
                        </span>
                        {p.dicgc_insured && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                            DICGC ₹5L Insured
                          </span>
                        )}
                      </div>
                      <h3 className="text-base font-bold text-[#172033] mt-1.5">{p.name}</h3>
                    </div>

                    <div
                      className={`w-5 h-5 rounded-md flex items-center justify-center border transition-all ${
                        isSelected ? 'bg-[#6478E8] border-[#6478E8] text-white' : 'border-[#CBD5E1]'
                      }`}
                    >
                      {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                    </div>
                  </div>

                  {/* Yield & Rate Type */}
                  <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] flex items-center justify-between">
                    <div>
                      <div className="text-[11px] text-[#64748B] font-medium">Indicative / Benchmark Yield</div>
                      <div className="text-xl font-mono font-bold text-[#1E293B]">
                        {p.indicative_annual_yield_pct}% <span className="text-xs font-normal text-[#64748B]">p.a.</span>
                      </div>
                    </div>
                    <Badge variant={p.rate_type === 'guaranteed' ? 'mint' : 'lavender'}>
                      {p.rate_type.toUpperCase()}
                    </Badge>
                  </div>

                  {/* Key Rules Matrix */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[#64748B] block text-[10px]">Compounding</span>
                      <span className="font-semibold text-[#1E293B] capitalize">{p.compounding_frequency.replace('_', ' ')}</span>
                    </div>
                    <div>
                      <span className="text-[#64748B] block text-[10px]">Lock-In Period</span>
                      <span className="font-semibold text-[#1E293B]">
                        {p.lock_in_months === 0 ? 'None (Liquid)' : `${p.lock_in_months} Months`}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#64748B] block text-[10px]">Credit / Market Risk</span>
                      <span className="font-semibold text-[#1E293B]">{p.credit_risk_level} / {p.market_risk_level}</span>
                    </div>
                    <div>
                      <span className="text-[#64748B] block text-[10px]">Liquidity Mechanism</span>
                      <span className="font-semibold text-[#1E293B] capitalize">{p.liquidity_rating.replace('_', ' ')}</span>
                    </div>
                  </div>

                  {/* Tax Treatment Summary */}
                  <div className="text-[11px] text-[#475569] bg-[#F1F5F9] p-2.5 rounded-lg border border-[#E2E8F0]">
                    <span className="font-bold text-[#1E293B] block mb-0.5">Statutory Tax Treatment:</span>
                    {p.tax_treatment_summary}
                  </div>

                  {/* Provenance Footer */}
                  <div className="pt-2 border-t border-[#E2E8F0] flex items-center justify-between text-[10px] text-[#64748B]">
                    <span>Source: {p.data_provenance}</span>
                    <span>As of: {p.as_of_date}</span>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: MULTI-PRODUCT COMPARISON MATRIX
         ========================================================================= */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          {/* Controls Card */}
          <Card className="space-y-4 p-5">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E6EAF0] pb-4">
              <h2 className="text-base font-bold text-[#172033]">Comparison Scenario Parameters</h2>

              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-[#64748B]">Mode:</span>
                <button
                  onClick={() => setInvestMode('lump_sum')}
                  className={`text-xs px-3 py-1.5 rounded-lg font-bold transition-all ${
                    investMode === 'lump_sum' ? 'bg-[#172033] text-white' : 'bg-[#F1F4F9] text-[#697386]'
                  }`}
                >
                  Lump Sum
                </button>
                <button
                  onClick={() => setInvestMode('monthly_sip')}
                  className={`text-xs px-3 py-1.5 rounded-lg font-bold transition-all ${
                    investMode === 'monthly_sip' ? 'bg-[#172033] text-white' : 'bg-[#F1F4F9] text-[#697386]'
                  }`}
                >
                  Monthly SIP
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-[#172033] mb-1">
                  {investMode === 'lump_sum' ? 'Investment Amount (₹)' : 'Monthly SIP (₹)'}
                </label>
                <input
                  type="number"
                  value={compareAmount || ''}
                  onChange={(e) => setCompareAmount(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 font-mono font-medium text-[#1E293B]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Time Horizon (Months)</label>
                <select
                  value={compareMonths}
                  onChange={(e) => setCompareMonths(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1E293B] font-medium"
                >
                  <option value={3}>3 Months (Short Term)</option>
                  <option value={6}>6 Months (Near Term)</option>
                  <option value={12}>12 Months (1 Year)</option>
                  <option value={36}>36 Months (3 Years)</option>
                  <option value={60}>60 Months (5 Years)</option>
                  <option value={120}>120 Months (10 Years)</option>
                  <option value={180}>180 Months (15 Years - PPF Term)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Your Tax Slab</label>
                <select
                  value={taxSlab}
                  onChange={(e) => setTaxSlab(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1E293B] font-medium"
                >
                  <option value={0}>0% (Tax Exempt / Low Income)</option>
                  <option value={5}>5% Marginal Slab</option>
                  <option value={10}>10% Slab</option>
                  <option value={15}>15% Slab</option>
                  <option value={20}>20% Slab</option>
                  <option value={30}>30% Highest Slab (Standard)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Expected Inflation (%)</label>
                <input
                  type="number"
                  step="0.5"
                  value={expectedInflation}
                  onChange={(e) => setExpectedInflation(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 font-mono font-medium text-[#1E293B]"
                />
              </div>

              <div className="flex flex-col justify-end">
                <Button
                  variant="primary"
                  onClick={handleCompare}
                  disabled={loading}
                  className="w-full bg-[#6478E8] hover:bg-[#5365CE] py-2 text-xs font-bold"
                >
                  {loading ? 'Calculating...' : 'Recalculate Matrix'}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <label className="flex items-center space-x-2 text-xs font-semibold text-[#172033] cursor-pointer">
                <input
                  type="checkbox"
                  checked={canLockFunds}
                  onChange={(e) => setCanLockFunds(e.target.checked)}
                  className="rounded text-[#6478E8]"
                />
                <span>I can lock these funds for the full tenure without premature withdrawal</span>
              </label>

              {isLoggedIn && compareResult && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setSaveModalOpen(true)}
                  className="flex items-center space-x-1.5 text-xs font-semibold border-[#CBD5E1]"
                >
                  <Bookmark className="w-3.5 h-3.5 text-[#6478E8]" />
                  <span>Save This Scenario</span>
                </Button>
              )}
            </div>
          </Card>

          {/* Top Recommendation Banner */}
          {compareResult && (
            <div className="p-5 rounded-2xl bg-gradient-to-r from-[#EEF0FF] via-[#F8FAFC] to-[#E5F7EF] border border-[#CBD5E1] shadow-sm">
              <div className="flex items-start space-x-3">
                <div className="w-9 h-9 rounded-xl bg-[#6478E8] text-white flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#6478E8]">
                      Algorithmic Verdict
                    </span>
                    <Badge variant="mint">Top Option: {compareResult.top_recommendation}</Badge>
                  </div>
                  <p className="text-sm font-semibold text-[#1E293B] mt-1">{compareResult.rationale}</p>
                </div>
              </div>
            </div>
          )}

          {/* Comparison Cards Grid */}
          {compareResult && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {compareResult.items.map((it) => (
                <Card key={it.product_id} className="p-5 space-y-4 border border-[#E2E8F0] bg-white flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
                          {it.category.replace('_', ' ')}
                        </span>
                        <h3 className="text-base font-bold text-[#1E293B] mt-0.5">{it.name}</h3>
                      </div>
                      <Badge variant={it.rate_type.includes('guaranteed') ? 'mint' : 'lavender'}>
                        {it.rate_used_pct}% p.a.
                      </Badge>
                    </div>

                    {/* Financial Figures */}
                    <div className="space-y-2 bg-[#F8FAFC] p-3 rounded-xl border border-[#E2E8F0] text-xs">
                      <div className="flex justify-between text-[#64748B]">
                        <span>Invested Principal:</span>
                        <span className="font-mono font-semibold text-[#1E293B]">{formatINR(it.invested_principal)}</span>
                      </div>
                      <div className="flex justify-between text-[#64748B]">
                        <span>Gross Maturity Value:</span>
                        <span className="font-mono font-semibold text-[#1E293B]">{formatINR(it.gross_maturity_value)}</span>
                      </div>
                      <div className="flex justify-between text-[#D9485F]">
                        <span>Estimated Tax (FA 2024):</span>
                        <span className="font-mono font-semibold">-{formatINR(it.estimated_tax)}</span>
                      </div>
                      <div className="pt-1.5 border-t border-[#E2E8F0] flex justify-between font-bold text-[#1E293B]">
                        <span>Net Post-Tax Proceeds:</span>
                        <span className="font-mono text-emerald-700">{formatINR(it.net_post_tax_proceeds)}</span>
                      </div>
                      <div className="flex justify-between text-[11px] text-[#64748B]">
                        <span>Real Purchasing Power:</span>
                        <span className="font-mono font-medium">{formatINR(it.inflation_adjusted_value)}</span>
                      </div>
                    </div>

                    {/* Tax Rules Breakdown */}
                    <div className="p-2.5 rounded-lg bg-[#EFF6FF] border border-[#BFDBFE] text-[11px] text-[#1E40AF]">
                      <span className="font-bold block">Tax Rules Applied:</span>
                      {it.tax_rules_applied}
                    </div>

                    {/* Safety / DICGC */}
                    {it.dicgc_insured && (
                      <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800 flex items-center space-x-2">
                        <Shield className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        <span>DICGC Protection: Covered up to ₹5,00,000 principal</span>
                      </div>
                    )}

                    {/* Pros and Cons */}
                    <div className="space-y-1.5 text-xs">
                      {it.pros.map((p, idx) => (
                        <div key={idx} className="flex items-start space-x-1.5 text-emerald-800 text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                          <span>{p}</span>
                        </div>
                      ))}
                      {it.cons.map((c, idx) => (
                        <div key={idx} className="flex items-start space-x-1.5 text-red-700 text-[11px]">
                          <AlertTriangle className="w-3.5 h-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                          <span>{c}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Provenance */}
                  <div className="pt-3 border-t border-[#E2E8F0] text-[10px] text-[#64748B]">
                    <span>Source: {it.data_provenance} ({it.as_of_date})</span>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {compareResult && (
            <p className="text-[11px] text-[#64748B] italic">{compareResult.regulatory_disclaimer}</p>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 3: LUMP SUM VS. MONTHLY INVESTING (SIP)
         ========================================================================= */}
      {activeTab === 'lumpsum_sip' && (
        <div className="space-y-6">
          <Card className="p-5 space-y-4">
            <h2 className="text-base font-bold text-[#172033]">Lump Sum Deployment vs Systematic Investment Plan (SIP)</h2>
            <p className="text-xs text-[#64748B]">
              Evaluate whether deploying an idle sum upfront outperforms dollar-cost / rupee-cost averaging across market cycles.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-[#172033] mb-1">Target Instrument</label>
                <select
                  value={lvsProductId}
                  onChange={(e) => setLvsProductId(e.target.value)}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1E293B] font-medium"
                >
                  <option value="nifty50_index_fund">Nifty 50 Index Fund / ETF (~12%)</option>
                  <option value="flexi_cap_mf">Flexi-Cap Mutual Fund (~13.5%)</option>
                  <option value="mid_small_cap_mf">Mid & Small Cap Fund (~15.5%)</option>
                  <option value="corporate_bond_fund">Corporate Bond Fund (~7.6%)</option>
                  <option value="bank_fd">Bank Fixed Deposit (~7.1%)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Upfront Lump Sum (₹)</label>
                <input
                  type="number"
                  value={lvsLumpSum || ''}
                  onChange={(e) => setLvsLumpSum(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 font-mono font-medium text-[#1E293B]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Monthly SIP Alternative (₹)</label>
                <input
                  type="number"
                  value={lvsMonthlySip || ''}
                  onChange={(e) => setLvsMonthlySip(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 font-mono font-medium text-[#1E293B]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Time Horizon (Months)</label>
                <input
                  type="number"
                  value={lvsMonths || ''}
                  onChange={(e) => setLvsMonths(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 font-mono font-medium text-[#1E293B]"
                />
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleLumpSumVsSip}
              disabled={loading}
              className="bg-[#6478E8] hover:bg-[#5365CE] text-xs font-bold"
            >
              {loading ? 'Comparing...' : 'Run Lump Sum vs. SIP Simulation'}
            </Button>
          </Card>

          {/* Results Comparison */}
          {lvsResult && (
            <div className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Lump Sum Card */}
                <Card className="p-5 space-y-3 bg-gradient-to-br from-white to-[#F8FAFC] border-[#CBD5E1]">
                  <Badge variant="blue">Lump Sum Route</Badge>
                  <h3 className="text-xl font-bold text-[#1E293B]">{formatINR(lvsResult.lump_sum_net_post_tax)}</h3>
                  <div className="text-xs text-[#64748B] space-y-1">
                    <div>Total Invested: <span className="font-semibold text-[#1E293B]">{formatINR(lvsResult.lump_sum_total_invested)}</span></div>
                    <div>Gross Projection: <span className="font-semibold text-[#1E293B]">{formatINR(lvsResult.lump_sum_gross_value)}</span></div>
                    <div>Real Purchasing Power: <span className="font-semibold text-[#1E293B]">{formatINR(lvsResult.lump_sum_real_purchasing_power)}</span></div>
                  </div>
                </Card>

                {/* SIP Card */}
                <Card className="p-5 space-y-3 bg-gradient-to-br from-white to-[#F8FAFC] border-[#CBD5E1]">
                  <Badge variant="mint">Monthly SIP Route</Badge>
                  <h3 className="text-xl font-bold text-[#1E293B]">{formatINR(lvsResult.sip_net_post_tax)}</h3>
                  <div className="text-xs text-[#64748B] space-y-1">
                    <div>Total Invested: <span className="font-semibold text-[#1E293B]">{formatINR(lvsResult.sip_total_invested)}</span></div>
                    <div>Gross Projection: <span className="font-semibold text-[#1E293B]">{formatINR(lvsResult.sip_gross_value)}</span></div>
                    <div>Real Purchasing Power: <span className="font-semibold text-[#1E293B]">{formatINR(lvsResult.sip_real_purchasing_power)}</span></div>
                  </div>
                </Card>
              </div>

              {/* Rupee-Cost Averaging Verdict */}
              <div className="p-4 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] text-xs text-[#166534] space-y-1">
                <span className="font-bold flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Rupee-Cost Averaging Analysis:</span>
                </span>
                <p>{lvsResult.rupee_cost_averaging_verdict}</p>
                <p className="font-semibold pt-1 text-emerald-900">{lvsResult.recommendation}</p>
              </div>

              {/* Schedule Table */}
              <Card className="p-5 space-y-3">
                <h4 className="text-xs font-bold text-[#172033]">Month-by-Month Wealth Accumulation Trajectory</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#E2E8F0] text-[#64748B]">
                        <th className="py-2">Month</th>
                        <th className="py-2">Lump Sum Invested</th>
                        <th className="py-2">Lump Sum Value</th>
                        <th className="py-2">SIP Total Invested</th>
                        <th className="py-2">SIP Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#F1F5F9] font-mono">
                      {lvsResult.schedule.map((pt) => (
                        <tr key={pt.month} className="hover:bg-[#F8FAFC]">
                          <td className="py-2 text-[#1E293B] font-semibold">{pt.month}</td>
                          <td className="py-2 text-[#64748B]">{formatINR(pt.lump_sum_invested)}</td>
                          <td className="py-2 text-[#2563EB] font-bold">{formatINR(pt.lump_sum_value)}</td>
                          <td className="py-2 text-[#64748B]">{formatINR(pt.sip_invested)}</td>
                          <td className="py-2 text-emerald-700 font-bold">{formatINR(pt.sip_value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 4: GOAL-BASED INVESTING PLANNER
         ========================================================================= */}
      {activeTab === 'goal_plan' && (
        <div className="space-y-6">
          <Card className="p-5 space-y-4">
            <h2 className="text-base font-bold text-[#172033]">Goal-Based Investment Planner with Cash Sufficiency Checks</h2>
            <p className="text-xs text-[#64748B]">
              Compute required monthly investments, target asset allocations (Equity/Debt/Gold), and verify against your real bank balance to avoid double-counting.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-[#172033] mb-1">Goal Name</label>
                <input
                  type="text"
                  value={goalName}
                  onChange={(e) => setGoalName(e.target.value)}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1E293B] font-medium"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Target Amount (₹)</label>
                <input
                  type="number"
                  value={goalTargetAmount || ''}
                  onChange={(e) => setGoalTargetAmount(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 font-mono font-medium text-[#1E293B]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Tenure (Months)</label>
                <input
                  type="number"
                  value={goalMonths || ''}
                  onChange={(e) => setGoalMonths(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 font-mono font-medium text-[#1E293B]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Risk Profile</label>
                <select
                  value={goalRiskProfile}
                  onChange={(e) => setGoalRiskProfile(e.target.value as any)}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1E293B] font-medium"
                >
                  <option value="conservative">Conservative (Capital Safety)</option>
                  <option value="moderate">Moderate (Balanced Growth)</option>
                  <option value="aggressive">Aggressive (Wealth Maximization)</option>
                </select>
              </div>
            </div>

            <div className="flex items-center space-x-6 text-xs">
              <label className="flex items-center space-x-2 font-semibold text-[#172033] cursor-pointer">
                <input
                  type="checkbox"
                  checked={goalAdjustInflation}
                  onChange={(e) => setGoalAdjustInflation(e.target.checked)}
                  className="rounded text-[#6478E8]"
                />
                <span>Adjust Target for Expected 6% Inflation</span>
              </label>

              <div>
                <span className="text-[#64748B] mr-2">Existing Savings Committed to this Goal:</span>
                <input
                  type="number"
                  value={goalCurrentAlloc || ''}
                  onChange={(e) => setGoalCurrentAlloc(Number(e.target.value))}
                  className="w-36 bg-white border border-[#CBD5E1] rounded-lg px-2.5 py-1 font-mono text-xs"
                />
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleGoalPlan}
              disabled={loading}
              className="bg-[#6478E8] hover:bg-[#5365CE] text-xs font-bold"
            >
              {loading ? 'Planning Goal...' : 'Generate Asset-Allocated Goal Plan'}
            </Button>
          </Card>

          {/* Goal Plan Results */}
          {goalResult && (
            <div className="space-y-5">
              {/* Cash Sufficiency Alert */}
              <div className="p-4 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] text-xs text-[#1E40AF] flex items-start space-x-3">
                <Shield className="w-5 h-5 text-[#2563EB] flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block">Liquid Cash Check & Double-Counting Safeguard:</span>
                  <p>{goalResult.cash_sufficiency_notice}</p>
                </div>
              </div>

              {/* Key Metric Summary */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card className="p-4">
                  <span className="text-[11px] text-[#64748B] font-medium">Inflation-Adjusted Target</span>
                  <h3 className="text-xl font-bold font-mono text-[#1E293B] mt-1">
                    {formatINR(goalResult.inflation_adjusted_target)}
                  </h3>
                </Card>

                <Card className="p-4 bg-emerald-50 border-emerald-200">
                  <span className="text-[11px] text-emerald-800 font-medium">Required Monthly SIP</span>
                  <h3 className="text-xl font-bold font-mono text-emerald-700 mt-1">
                    {formatINR(goalResult.required_monthly_sip)} /mo
                  </h3>
                </Card>

                <Card className="p-4">
                  <span className="text-[11px] text-[#64748B] font-medium">Or One-Time Lump Sum</span>
                  <h3 className="text-xl font-bold font-mono text-[#2563EB] mt-1">
                    {formatINR(goalResult.required_lump_sum_alternative)}
                  </h3>
                </Card>
              </div>

              {/* Recommended Asset Allocation Slices */}
              <Card className="p-5 space-y-4">
                <h3 className="text-sm font-bold text-[#172033]">
                  Recommended Asset Allocation (Blended Expected Return: {goalResult.expected_blended_cagr_pct}% p.a.)
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {goalResult.allocation_breakdown.map((slice, i) => (
                    <div key={i} className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-xs text-[#1E293B]">{slice.asset_class}</span>
                        <Badge variant="blue">{slice.target_percentage}%</Badge>
                      </div>
                      <div className="text-xs space-y-1 text-[#64748B]">
                        <div>Suggested Route: <span className="font-semibold text-[#1E293B]">{slice.suggested_product}</span></div>
                        <div>Monthly SIP Share: <span className="font-mono font-bold text-emerald-700">{formatINR(slice.allocated_sip)}</span></div>
                        <div>Benchmark Return: <span className="font-semibold text-[#1E293B]">{slice.indicative_rate_pct}% p.a.</span></div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 5: RISK & STRESS TESTING
         ========================================================================= */}
      {activeTab === 'stress_test' && (
        <div className="space-y-6">
          <Card className="p-5 space-y-4">
            <h2 className="text-base font-bold text-[#172033]">Portfolio Stress Testing & Macro Shock Analysis</h2>
            <p className="text-xs text-[#64748B]">
              Simulate how your proposed or existing investments would withstand sudden macro crises, bear markets, high inflation, or unexpected early exits.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-[#172033] mb-1">Select Stress Scenario</label>
                <select
                  value={stressScenario}
                  onChange={(e) => setStressScenario(e.target.value)}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1E293B] font-medium"
                >
                  <option value="market_crash_20">Immediate 20% Equity Market Correction</option>
                  <option value="severe_recession_35">Severe Recession & Bear Market (-35%)</option>
                  <option value="prolonged_stagnation">Prolonged Low Return / Stagnation</option>
                  <option value="high_inflation_shock">High Inflation Shock (9.5% Spike)</option>
                  <option value="premature_emergency_exit">Forced Premature Exit at Month 6</option>
                  <option value="paused_sip_6mo">Income Disruption / 6-Month SIP Pause</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Time Horizon (Months)</label>
                <input
                  type="number"
                  value={stressHorizon || ''}
                  onChange={(e) => setStressHorizon(Number(e.target.value))}
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 font-mono font-medium text-[#1E293B]"
                />
              </div>

              <div className="flex flex-col justify-end">
                <Button
                  variant="primary"
                  onClick={handleStressTest}
                  disabled={loading}
                  className="bg-[#D9485F] hover:bg-[#C23B51] text-white text-xs font-bold py-2"
                >
                  {loading ? 'Simulating...' : 'Run Shock Simulation'}
                </Button>
              </div>
            </div>
          </Card>

          {/* Stress Test Results */}
          {stressResult && (
            <div className="space-y-5">
              <Card className="p-5 space-y-4 border-2 border-red-100">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-base font-bold text-[#1E293B]">{stressResult.scenario_title}</h3>
                    <p className="text-xs text-[#64748B] mt-0.5">{stressResult.scenario_description}</p>
                  </div>
                  <Badge variant={stressResult.resilience_rating === 'High' ? 'mint' : 'danger'}>
                    Resilience: {stressResult.resilience_rating}
                  </Badge>
                </div>

                {/* Drawdown & Recovery Gauge */}
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-[#FFF1F2] border border-[#FECDD3] text-xs">
                  <div>
                    <span className="text-[#9F1239] block text-[11px]">Baseline Projected Value</span>
                    <span className="text-base font-bold font-mono text-[#1E293B]">{formatINR(stressResult.baseline_projected_value)}</span>
                  </div>
                  <div>
                    <span className="text-[#9F1239] block text-[11px]">Stressed Value</span>
                    <span className="text-base font-bold font-mono text-[#E11D48]">{formatINR(stressResult.stressed_projected_value)}</span>
                  </div>
                  <div>
                    <span className="text-[#9F1239] block text-[11px]">Maximum Drawdown</span>
                    <span className="text-base font-bold font-mono text-[#BE123C]">
                      -{formatINR(stressResult.drawdown_amount)} ({stressResult.drawdown_pct}%)
                    </span>
                  </div>
                  <div>
                    <span className="text-[#9F1239] block text-[11px]">Estimated Recovery</span>
                    <span className="text-base font-bold font-mono text-[#1E293B]">
                      {stressResult.estimated_recovery_months > 0 ? `${stressResult.estimated_recovery_months} Months` : 'N/A (Early Exit)'}
                    </span>
                  </div>
                </div>

                {/* Vulnerable vs Cushioning Assets */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-xl bg-red-50/60 border border-red-200 space-y-1.5">
                    <span className="font-bold text-red-900 block flex items-center space-x-1.5">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                      <span>Most Vulnerable Assets:</span>
                    </span>
                    {stressResult.vulnerable_assets.map((v, idx) => (
                      <div key={idx} className="text-red-800 text-[11px]">• {v}</div>
                    ))}
                  </div>

                  <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 space-y-1.5">
                    <span className="font-bold text-emerald-900 block flex items-center space-x-1.5">
                      <Shield className="w-4 h-4 text-emerald-600" />
                      <span>Cushioning / Resilient Assets:</span>
                    </span>
                    {stressResult.cushioning_assets.map((c, idx) => (
                      <div key={idx} className="text-emerald-800 text-[11px]">• {c}</div>
                    ))}
                  </div>
                </div>

                {/* Actionable Safeguards */}
                <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
                  <span className="font-bold text-xs text-[#1E293B] block">Concrete Safeguard Recommendations:</span>
                  {stressResult.safeguard_recommendations.map((rec, idx) => (
                    <div key={idx} className="text-xs text-[#475569] flex items-start space-x-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>

                <p className="text-[10px] text-[#64748B] italic">{stressResult.disclaimer}</p>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 6: PORTFOLIO ALLOCATION & HOLDINGS ANALYSIS
         ========================================================================= */}
      {activeTab === 'portfolio' && (
        <div className="space-y-6">
          {!isLoggedIn ? (
            <Card className="p-8 text-center space-y-3">
              <Lock className="w-8 h-8 text-[#6478E8] mx-auto" />
              <h3 className="text-base font-bold text-[#172033]">Sign in to Analyze Your Existing Holdings</h3>
              <p className="text-xs text-[#64748B] max-w-md mx-auto">
                Connect your account to inspect your actual AssetHolding portfolio records, asset class concentration risks, and rebalancing advice.
              </p>
            </Card>
          ) : portfolioData ? (
            <div className="space-y-5">
              <Card className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs text-[#64748B]">Total Verified Holdings Value</span>
                    <h2 className="text-2xl font-bold font-mono text-[#1E293B]">{formatINR(portfolioData.total_portfolio_value)}</h2>
                  </div>
                  <Badge variant="blue">Profile: {portfolioData.risk_profile}</Badge>
                </div>
                <p className="text-xs text-[#475569] bg-[#F8FAFC] p-3 rounded-lg border border-[#E2E8F0]">
                  {portfolioData.risk_alignment_verdict}
                </p>
              </Card>

              {/* Slices Breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {portfolioData.categories_breakdown.map((cat, idx) => (
                  <Card key={idx} className="p-4 space-y-2">
                    <span className="text-[11px] font-bold text-[#64748B] block uppercase tracking-wider">{cat.label}</span>
                    <div className="text-lg font-bold font-mono text-[#1E293B]">{formatINR(cat.total_value)}</div>
                    <div className="flex justify-between text-xs text-[#64748B]">
                      <span>Current: <b className="text-[#1E293B]">{cat.percentage}%</b></span>
                      <span>Target: <b className="text-[#6478E8]">{cat.target_percentage}%</b></span>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Concentration Risks & Rebalancing */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <Card className="p-5 space-y-3">
                  <h3 className="text-sm font-bold text-[#1E293B] flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    <span>Concentration & Allocation Risks</span>
                  </h3>
                  <div className="space-y-2">
                    {portfolioData.concentration_risks.map((risk, i) => (
                      <div key={i} className="text-xs text-[#475569] p-2.5 rounded-lg bg-amber-50/50 border border-amber-200">
                        {risk}
                      </div>
                    ))}
                  </div>
                </Card>

                <Card className="p-5 space-y-3">
                  <h3 className="text-sm font-bold text-[#1E293B] flex items-center space-x-2">
                    <TrendingUp className="w-4 h-4 text-emerald-600" />
                    <span>Actionable Rebalancing Steps</span>
                  </h3>
                  <div className="space-y-2">
                    {portfolioData.rebalancing_recommendations.map((step, i) => (
                      <div key={i} className="text-xs text-[#475569] p-2.5 rounded-lg bg-emerald-50/50 border border-emerald-200 flex items-start space-x-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          ) : (
            <Card className="p-6 text-center text-xs text-[#64748B]">Loading portfolio records...</Card>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 7: SAVED COMPARISON SCENARIOS (CRUD)
         ========================================================================= */}
      {activeTab === 'saved_scenarios' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[#172033]">Saved Scenarios & Hypothetical Plans</h2>
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchUserData}
              className="flex items-center space-x-1.5 text-xs font-semibold"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </Button>
          </div>

          {!isLoggedIn ? (
            <Card className="p-8 text-center space-y-3">
              <Bookmark className="w-8 h-8 text-[#6478E8] mx-auto" />
              <h3 className="text-base font-bold text-[#172033]">Login to Save & Reopen Scenarios</h3>
              <p className="text-xs text-[#64748B] max-w-md mx-auto">
                Persist custom comparison assumptions, goal plans, and stress tests under your private user profile.
              </p>
            </Card>
          ) : savedScenarios.length === 0 ? (
            <Card className="p-8 text-center space-y-2">
              <Bookmark className="w-8 h-8 text-[#94A3B8] mx-auto" />
              <h3 className="text-sm font-bold text-[#1E293B]">No Saved Scenarios Yet</h3>
              <p className="text-xs text-[#64748B]">
                Configure any scenario in the Compare, Goal Planner, or Stress Test tabs and click "Save This Scenario".
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savedScenarios.map((sc) => (
                <Card key={sc.id} className="p-5 space-y-3 flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between">
                      <h3 className="text-sm font-bold text-[#1E293B]">{sc.name}</h3>
                      <Badge variant="blue">{sc.scenario_mode}</Badge>
                    </div>
                    {sc.notes && <p className="text-xs text-[#64748B] mt-1">{sc.notes}</p>}
                    <div className="text-[11px] text-[#94A3B8] mt-2">
                      Saved: {new Date(sc.created_at).toLocaleDateString()}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between">
                    <span className="text-[10px] text-[#64748B]">Hypothetical Simulation</span>
                    <button
                      onClick={() => handleDeleteScenario(sc.id)}
                      className="text-xs text-red-600 hover:text-red-800 p-1 rounded hover:bg-red-50 flex items-center space-x-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Delete</span>
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 8: EDUCATIONAL GLOSSARY & STATUTORY TERMS
         ========================================================================= */}
      {activeTab === 'glossary' && (
        <div className="space-y-6">
          <Card className="p-5 space-y-4">
            <h2 className="text-base font-bold text-[#172033]">Indian Financial Terminology & Regulatory Explanations</h2>
            <p className="text-xs text-[#64748B]">
              Clear, practical explanations of key Indian investment mechanics, SEBI mandates, and Finance Act 2024 taxation laws.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-1">
                <span className="font-bold text-sm text-[#1E293B]">Net Asset Value (NAV)</span>
                <p className="text-[#475569]">
                  The market value of a single unit of a mutual fund scheme, calculated daily by AMCs after deducting expenses (TER). Unlike stock prices, NAV reflects underlying portfolio value rather than trading demand.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-1">
                <span className="font-bold text-sm text-[#1E293B]">Total Expense Ratio (TER)</span>
                <p className="text-[#475569]">
                  The annual fee charged by mutual funds for fund management, administration, and regulatory compliance. Direct plans have substantially lower TERs than regular plans because no distributor commissions are paid.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-1">
                <span className="font-bold text-sm text-[#1E293B]">Finance Act 2024 Equity Taxation</span>
                <p className="text-[#475569]">
                  For equity mutual funds and stocks (&gt;65% equity exposure): Long-Term Capital Gains (holding &gt; 12 months) are taxed at 12.5% on gains exceeding ₹1,25,000 exemption. Short-Term Capital Gains (&le; 12 months) are taxed at 20%.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-1">
                <span className="font-bold text-sm text-[#1E293B]">Section 50AA Debt Fund Taxation</span>
                <p className="text-[#475569]">
                  Introduced in Finance Act 2023: Specified mutual funds with &le; 35% equity exposure acquired on or after 1-Apr-2023 are deemed short-term capital assets, taxed at the investor's marginal income tax slab rate with zero indexation.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-1">
                <span className="font-bold text-sm text-[#1E293B]">DICGC Insurance Protection</span>
                <p className="text-[#475569]">
                  The Deposit Insurance and Credit Guarantee Corporation (a wholly-owned RBI subsidiary) insures bank deposits (savings, FD, RD) up to a maximum of ₹5,00,000 per depositor per bank in case of bank failure.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-1">
                <span className="font-bold text-sm text-[#1E293B]">Sovereign Gold Bonds (SGB)</span>
                <p className="text-[#475569]">
                  Government securities issued by RBI denominated in grams of gold. They pay 2.5% annual cash interest (taxable at slab) and offer 100% tax-free capital gains upon maturity redemption after 8 years.
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Save Scenario Modal */}
      {saveModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <Card className="w-full max-w-md p-6 space-y-4 bg-white shadow-xl">
            <h3 className="text-base font-bold text-[#1E293B]">Save Investment Comparison Scenario</h3>
            <p className="text-xs text-[#64748B]">
              Persist your current inputs and parameters. Note: This saves a plan only; no trade or purchase occurs.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-[#172033] mb-1">Scenario Name</label>
                <input
                  type="text"
                  value={scenarioNameInput}
                  onChange={(e) => setScenarioNameInput(e.target.value)}
                  placeholder="e.g. 3-Year Emergency vs FD vs Index Plan"
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1E293B]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Optional Notes</label>
                <textarea
                  value={scenarioNotesInput}
                  onChange={(e) => setScenarioNotesInput(e.target.value)}
                  placeholder="Notes about assumptions or allocations..."
                  className="w-full bg-white border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#1E293B] h-20"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <Button variant="secondary" size="sm" onClick={() => setSaveModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleSaveScenario} className="bg-[#6478E8]">
                Save Scenario
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
