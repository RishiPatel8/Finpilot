import React, { useState, useEffect } from 'react';
import {
  SlidersHorizontal,
  CheckCircle2,
  AlertTriangle,
  Bookmark,
  ShieldCheck,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Calculator,
  RefreshCw,
  Info,
  DollarSign,
  Calendar,
  Layers,
  Car,
  Home,
  CreditCard,
  ShoppingBag,
  Plane,
  Briefcase,
  PiggyBank,
  Target,
  ArrowLeftRight,
  HelpCircle,
  Clock,
  Trash2,
  Edit2,
  X,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  AlertCircle
} from 'lucide-react';
import { apiRequest, getAuthToken } from '../../services/api';
import { Card, Badge, Button, PageHeader } from '../../components/ui';
import { KnowMore } from '../../components/KnowMore';

export interface BaselineData {
  monthly_income: number;
  essential_expenses: number;
  discretionary_expenses: number;
  total_monthly_expenses: number;
  existing_monthly_emi: number;
  existing_recurring_commitments: number;
  available_monthly_surplus: number;
  liquid_savings: number;
  emergency_fund_target_months: number;
  emergency_fund_target_amount: number;
  emergency_runway_months: number;
  total_debt: number;
  data_sources: Record<string, string>;
  is_verified_data: boolean;
  data_completeness_pct: number;
  missing_fields: string[];
}

export interface SavedScenarioItem {
  id: string;
  title: string;
  scenario_type: string;
  input_data: any;
  result_data: any;
  created_at: string;
}

export const ScenarioSimulatorView: React.FC = () => {
  // 1. Scenario Type
  const [scenarioType, setScenarioType] = useState<string>('vehicle');

  // 2. Baseline State (Initialized truthfully to 0, never mock values)
  const [baseline, setBaseline] = useState<BaselineData | null>(null);
  const [baselineLoading, setBaselineLoading] = useState<boolean>(true);
  const [isManualBaseline, setIsManualBaseline] = useState<boolean>(false);

  // Editable baseline inputs (defaults to 0 or verified numbers)
  const [monthlyIncome, setMonthlyIncome] = useState<number>(0);
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(0);
  const [currentSavings, setCurrentSavings] = useState<number>(0);
  const [existingEmi, setExistingEmi] = useState<number>(0);
  const [existingRecurring, setExistingRecurring] = useState<number>(0);

  // 3. Scenario-Specific Decision Fields
  const [purchasePrice, setPurchasePrice] = useState<number>(0);
  const [downPayment, setDownPayment] = useState<number>(0);
  const [loanInterestRate, setLoanInterestRate] = useState<number>(9.5);
  const [loanTenureMonths, setLoanTenureMonths] = useState<number>(60);
  const [monthlyOngoingCosts, setMonthlyOngoingCosts] = useState<number>(0);
  const [upfrontCosts, setUpfrontCosts] = useState<number>(0);
  const [timeHorizonMonths, setTimeHorizonMonths] = useState<number>(12);
  const [monthlyContribution, setMonthlyContribution] = useState<number>(0);
  const [expectedReturnRate, setExpectedReturnRate] = useState<number>(11.0);
  const [investmentYears, setInvestmentYears] = useState<number>(5);
  const [expectedRevenue, setExpectedRevenue] = useState<number>(0);
  const [monthsBeforeRevenue, setMonthsBeforeRevenue] = useState<number>(3);
  const [alreadySaved, setAlreadySaved] = useState<number>(0);
  const [customNotes, setCustomNotes] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // 4. Execution & Results State
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 5. Persistence & Management State
  const [savedScenarios, setSavedScenarios] = useState<SavedScenarioItem[]>([]);
  const [savedScenariosOpen, setSavedScenariosOpen] = useState<boolean>(false);
  const [saveModalOpen, setSaveModalOpen] = useState<boolean>(false);
  const [scenarioTitle, setScenarioTitle] = useState<string>('');
  const [saving, setSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [editingScenarioId, setEditingScenarioId] = useState<string | null>(null);
  const [editTitleText, setEditTitleText] = useState<string>('');
  const [comparisonScenario, setComparisonScenario] = useState<SavedScenarioItem | null>(null);

  // Fetch verified user baseline on component mount
  const fetchBaseline = async () => {
    setBaselineLoading(true);
    try {
      const data = await apiRequest<BaselineData>('/scenarios/baseline');
      setBaseline(data);
      if (data) {
        setMonthlyIncome(data.monthly_income || 0);
        setMonthlyExpenses(data.total_monthly_expenses || 0);
        setCurrentSavings(data.liquid_savings || 0);
        setExistingEmi(data.existing_monthly_emi || 0);
        setExistingRecurring(data.existing_recurring_commitments || 0);
        setIsManualBaseline(!data.is_verified_data);
      }
    } catch {
      // If unauthenticated or network error, fallback to honest manual mode
      setIsManualBaseline(true);
    } finally {
      setBaselineLoading(false);
    }
  };

  const fetchSavedScenarios = async () => {
    if (!getAuthToken()) return;
    try {
      const data = await apiRequest<SavedScenarioItem[]>('/scenarios/saved');
      setSavedScenarios(data || []);
    } catch {
      // Unauthenticated or empty
    }
  };

  useEffect(() => {
    fetchBaseline();
    fetchSavedScenarios();
  }, []);

  // Update default tenure / interest suggestions when decision type changes
  const handleScenarioTypeChange = (newType: string) => {
    setScenarioType(newType);
    setResult(null);
    if (newType === 'vehicle') {
      setLoanInterestRate(9.5);
      setLoanTenureMonths(60);
      setMonthlyOngoingCosts(3500); // Fuel, maintenance, insurance
    } else if (newType === 'house') {
      setLoanInterestRate(8.5);
      setLoanTenureMonths(240); // 20 years
      setMonthlyOngoingCosts(3000); // Maintenance, property tax
    } else if (newType === 'personal_loan') {
      setLoanInterestRate(12.5);
      setLoanTenureMonths(36);
      setMonthlyOngoingCosts(0);
    } else if (newType === 'expensive_product') {
      setLoanInterestRate(14.0);
      setLoanTenureMonths(12);
      setMonthlyOngoingCosts(0);
    } else if (newType === 'business') {
      setLoanInterestRate(11.0);
      setLoanTenureMonths(36);
      setMonthsBeforeRevenue(3);
    } else if (newType === 'increase_investment') {
      setExpectedReturnRate(11.0);
      setInvestmentYears(5);
    }
  };

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const payload: any = {
        scenario_type: scenarioType,
        monthly_income: monthlyIncome,
        monthly_expenses: monthlyExpenses,
        current_savings: currentSavings,
        existing_monthly_emi: existingEmi,
        existing_recurring_commitments: existingRecurring,
        purchase_price: purchasePrice > 0 ? purchasePrice : undefined,
        target_amount: purchasePrice > 0 ? purchasePrice : undefined,
        down_payment: downPayment > 0 ? downPayment : undefined,
        loan_interest_rate_pct: loanInterestRate > 0 ? loanInterestRate : undefined,
        loan_tenure_months: loanTenureMonths > 0 ? loanTenureMonths : undefined,
        monthly_ongoing_costs: monthlyOngoingCosts > 0 ? monthlyOngoingCosts : undefined,
        upfront_one_time_costs: upfrontCosts > 0 ? upfrontCosts : undefined,
        time_horizon_months: timeHorizonMonths > 0 ? timeHorizonMonths : undefined,
        additional_monthly_investment: monthlyContribution > 0 ? monthlyContribution : undefined,
        expected_annual_return_pct: expectedReturnRate,
        investment_horizon_years: investmentYears,
        expected_monthly_revenue: expectedRevenue > 0 ? expectedRevenue : undefined,
        months_before_revenue: monthsBeforeRevenue,
        already_saved_amount: alreadySaved > 0 ? alreadySaved : undefined,
        notes: customNotes || undefined,
      };

      const res = await apiRequest<any>('/scenarios/simulate', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setResult(res);
      setScenarioTitle(res.title || `Financial Decision Simulation`);
    } catch (err: any) {
      setError(err.message || 'Simulation failed. Please verify your inputs.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveScenario = async () => {
    if (!result) return;
    setSaving(true);
    try {
      await apiRequest('/scenarios/save', {
        method: 'POST',
        body: JSON.stringify({
          title: scenarioTitle || result.title,
          scenario_type: result.scenario_type,
          input_data: {
            scenarioType,
            monthlyIncome,
            monthlyExpenses,
            currentSavings,
            existingEmi,
            purchasePrice,
            downPayment,
            loanInterestRate,
            loanTenureMonths,
            monthlyOngoingCosts,
          },
          result_data: result,
        }),
      });
      setSaveSuccess(true);
      setSaveModalOpen(false);
      fetchSavedScenarios();
    } catch (err: any) {
      alert(err.message || 'Please log in to save scenarios to your profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleReopenScenario = (saved: SavedScenarioItem) => {
    setScenarioType(saved.scenario_type);
    setResult(saved.result_data);
    setScenarioTitle(saved.title);
    if (saved.input_data) {
      if (saved.input_data.monthlyIncome !== undefined) setMonthlyIncome(saved.input_data.monthlyIncome);
      if (saved.input_data.monthlyExpenses !== undefined) setMonthlyExpenses(saved.input_data.monthlyExpenses);
      if (saved.input_data.currentSavings !== undefined) setCurrentSavings(saved.input_data.currentSavings);
      if (saved.input_data.existingEmi !== undefined) setExistingEmi(saved.input_data.existingEmi);
      if (saved.input_data.purchasePrice !== undefined) setPurchasePrice(saved.input_data.purchasePrice);
      if (saved.input_data.downPayment !== undefined) setDownPayment(saved.input_data.downPayment);
      if (saved.input_data.loanInterestRate !== undefined) setLoanInterestRate(saved.input_data.loanInterestRate);
      if (saved.input_data.loanTenureMonths !== undefined) setLoanTenureMonths(saved.input_data.loanTenureMonths);
      if (saved.input_data.monthlyOngoingCosts !== undefined) setMonthlyOngoingCosts(saved.input_data.monthlyOngoingCosts);
    }
    setSavedScenariosOpen(false);
  };

  const handleRenameScenario = async (id: string) => {
    if (!editTitleText.trim()) return;
    try {
      await apiRequest(`/scenarios/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ title: editTitleText.trim() }),
      });
      setEditingScenarioId(null);
      fetchSavedScenarios();
    } catch (err: any) {
      alert(err.message || 'Failed to rename scenario.');
    }
  };

  const handleDeleteScenario = async (id: string) => {
    if (!confirm('Are you sure you want to delete this saved scenario?')) return;
    try {
      await apiRequest(`/scenarios/${id}`, {
        method: 'DELETE',
      });
      fetchSavedScenarios();
      if (comparisonScenario && comparisonScenario.id === id) {
        setComparisonScenario(null);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to delete scenario.');
    }
  };

  const formatINR = (val: number | null | undefined) => {
    if (val === null || val === undefined || isNaN(val)) return '₹0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getVerdictTheme = (category: string) => {
    switch (category) {
      case 'AFFORDABLE':
        return {
          bg: 'bg-[#E5F7EF]/80',
          border: 'border-[#16865C]/30',
          badge: 'mint' as const,
          text: 'text-[#16865C]',
          label: 'Appears Affordable Under Entered Assumptions',
          icon: <CheckCircle2 className="w-5 h-5 text-[#16865C]" />,
        };
      case 'TIGHT_CASH_FLOW':
        return {
          bg: 'bg-[#FFF8E6]',
          border: 'border-[#D9822B]/30',
          badge: 'peach' as const,
          text: 'text-[#B25E09]',
          label: 'Tight Monthly Cash Flow — Leaves Thin Margin',
          icon: <AlertTriangle className="w-5 h-5 text-[#B25E09]" />,
        };
      case 'EMERGENCY_FUND_AT_RISK':
        return {
          bg: 'bg-[#FFF0E5]',
          border: 'border-[#E06D53]/30',
          badge: 'peach' as const,
          text: 'text-[#C53030]',
          label: 'Emergency Reserve at Risk (< 3 Months Runway)',
          icon: <ShieldAlert className="w-5 h-5 text-[#C53030]" />,
        };
      case 'HIGH_RISK_DEFICIT':
        return {
          bg: 'bg-[#FDF2F4]',
          border: 'border-[#D9485F]/30',
          badge: 'danger' as const,
          text: 'text-[#D9485F]',
          label: 'High Risk — Monthly Deficit Projected',
          icon: <AlertCircle className="w-5 h-5 text-[#D9485F]" />,
        };
      case 'DATA_INCOMPLETE':
      default:
        return {
          bg: 'bg-[#EEF0FF]',
          border: 'border-[#6478E8]/30',
          badge: 'lavender' as const,
          text: 'text-[#4F5ECE]',
          label: 'Potentially Affordable, But Important Info Missing',
          icon: <Info className="w-5 h-5 text-[#4F5ECE]" />,
        };
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Financial Decision Planner"
        description="Test real financial decisions against your verified bank accounts, cash flow surplus, and debt obligations before committing."
        icon={<SlidersHorizontal className="w-4 h-4 text-[#6478E8]" />}
        badge={<KnowMore termId="cash_flow" variant="badge" label="About Cash Flow Planning" />}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setSavedScenariosOpen(true)}
              icon={<Bookmark className="w-3.5 h-3.5 text-[#6478E8]" />}
            >
              Saved Decisions ({savedScenarios.length})
            </Button>
            {result && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setSaveModalOpen(true)}
                disabled={saving || saveSuccess}
                icon={
                  <Bookmark
                    className={`w-3.5 h-3.5 ${
                      saveSuccess ? 'text-white' : 'text-white'
                    }`}
                  />
                }
              >
                {saveSuccess ? 'Saved' : 'Save Plan'}
              </Button>
            )}
          </div>
        }
      />

      {/* Safety & Educational Notice */}
      <div className="px-4 py-3 rounded-2xl bg-[#111622] border border-[rgba(212,175,55,0.2)] flex items-center justify-between text-xs text-[#9CA3AF] shadow-sm">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            <strong className="text-[#F3F4F6]">Safe Simulation Sandbox</strong>: Planning simulations use deterministic formulas and do not initiate bank transfers, loan applications, or purchases.
          </span>
        </div>
        <KnowMore termId="stress_testing" variant="link" label="Learn How We Calculate" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Decision Setup & Baseline (5 Cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* 1. Decision Type Selector */}
          <Card className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-[#F3F4F6] uppercase tracking-wider flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-[rgba(212,175,55,0.15)] text-[#F5DE88] border border-[rgba(212,175,55,0.3)] text-[11px] font-bold flex items-center justify-center">1</span>
                  Select Financial Decision
                </label>
                <span className="text-[11px] text-[#9CA3AF]">10 tailored planners</span>
              </div>
              <div className="relative">
                <select
                  value={scenarioType}
                  onChange={(e) => handleScenarioTypeChange(e.target.value)}
                  className="w-full bg-[#0B0F17] border border-[rgba(212,175,55,0.25)] rounded-xl px-3.5 py-3 text-xs sm:text-sm text-[#F3F4F6] font-semibold leading-normal focus:outline-none focus:border-[#D4AF37] focus:ring-2 focus:ring-[#D4AF37]/20 transition-all appearance-none cursor-pointer"
                >
                  <option value="vehicle">🚗 Buy a Car or Bike</option>
                  <option value="house">🏡 Buy a House or Make Down Payment</option>
                  <option value="personal_loan">💳 Take a Personal Loan</option>
                  <option value="expensive_product">💻 Buy an Expensive Product (Gadget / Appliance)</option>
                  <option value="major_trip">✈️ Plan a Major Trip or Vacation</option>
                  <option value="business">🚀 Start or Expand a Business</option>
                  <option value="increase_investment">📈 Increase Monthly Investments (SIP)</option>
                  <option value="financial_goal">🎯 Save for a Financial Goal</option>
                  <option value="cash_vs_loan">⚖️ Compare Paying Cash vs Taking a Loan</option>
                  <option value="custom">⚙️ Custom Financial Decision</option>
                </select>
                <ChevronDown className="w-4 h-4 text-[#D4AF37] absolute right-3 top-3.5 pointer-events-none" />
              </div>
            </div>

            {/* 2. Real Financial Baseline */}
            <div className="pt-4 border-t border-[#E6EAF0] space-y-3.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-[#EEF0FF] text-[#6478E8] text-[11px] font-bold flex items-center justify-center">2</span>
                  Your Financial Baseline
                </label>
                {baseline && baseline.is_verified_data ? (
                  <Badge variant="mint" size="sm" className="font-semibold">
                    ✓ Verified Records ({baseline.data_completeness_pct}%)
                  </Badge>
                ) : (
                  <Badge variant="peach" size="sm" className="font-semibold">
                    User-Provided Assumptions
                  </Badge>
                )}
              </div>

              {/* Data Verification Banner / Empty State */}
              {baseline && !baseline.is_verified_data && (
                <div className="p-3 rounded-xl bg-[#FFF8E6] border border-[#D9822B]/20 text-xs text-[#7A4100] space-y-1">
                  <div className="flex items-center gap-1.5 font-bold">
                    <Info className="w-3.5 h-3.5 text-[#B25E09]" />
                    <span>No verified bank statements connected</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-[#7A4100]/90">
                    We've initialized manual fields below. Enter your take-home pay and living costs to evaluate affordability accurately.
                  </p>
                </div>
              )}

              {/* Baseline Fields */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-[#697386]">
                      Monthly Net Income
                    </label>
                    <span className="text-[9px] text-[#8C9BAE]">
                      {baseline?.data_sources?.income ? 'Verified' : 'Assumption'}
                    </span>
                  </div>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs text-[#697386]">₹</span>
                    <input
                      type="number"
                      value={monthlyIncome || ''}
                      onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                      placeholder="0"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl pl-6 pr-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-[#697386]">
                      Monthly Living Costs
                    </label>
                    <span className="text-[9px] text-[#8C9BAE]">
                      {baseline?.data_sources?.expenses ? 'Verified' : 'Assumption'}
                    </span>
                  </div>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs text-[#697386]">₹</span>
                    <input
                      type="number"
                      value={monthlyExpenses || ''}
                      onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                      placeholder="0"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl pl-6 pr-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-[#697386]">
                      Liquid Bank Savings
                    </label>
                    <span className="text-[9px] text-[#8C9BAE]">
                      {baseline?.data_sources?.savings ? 'Verified' : 'Assumption'}
                    </span>
                  </div>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs text-[#697386]">₹</span>
                    <input
                      type="number"
                      value={currentSavings || ''}
                      onChange={(e) => setCurrentSavings(Number(e.target.value))}
                      placeholder="0"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl pl-6 pr-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-[#697386]">
                      Existing Monthly EMIs
                    </label>
                    <span className="text-[9px] text-[#8C9BAE]">
                      {baseline?.data_sources?.liabilities ? 'Verified' : 'Assumption'}
                    </span>
                  </div>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs text-[#697386]">₹</span>
                    <input
                      type="number"
                      value={existingEmi || ''}
                      onChange={(e) => setExistingEmi(Number(e.target.value))}
                      placeholder="0"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl pl-6 pr-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                </div>
              </div>

              {/* Monthly Surplus Math Badge */}
              <div className="p-2.5 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0] flex items-center justify-between text-xs">
                <span className="text-[#697386] font-medium">Available Monthly Surplus:</span>
                <span className={`font-mono font-bold ${monthlyIncome - monthlyExpenses - existingEmi >= 0 ? 'text-[#16865C]' : 'text-[#D9485F]'}`}>
                  {formatINR(monthlyIncome - monthlyExpenses - existingEmi)} / mo
                </span>
              </div>
            </div>

            {/* 3. Decision-Specific Inputs */}
            <div className="pt-4 border-t border-[#E6EAF0] space-y-3.5">
              <label className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-[#EEF0FF] text-[#6478E8] text-[11px] font-bold flex items-center justify-center">3</span>
                Decision Details
              </label>

              {/* Vehicle / Car / Bike */}
              {scenarioType === 'vehicle' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      On-Road Vehicle Price (₹)
                    </label>
                    <input
                      type="number"
                      value={purchasePrice || ''}
                      onChange={(e) => setPurchasePrice(Number(e.target.value))}
                      placeholder="e.g. 1000000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Upfront Down Payment (₹)
                      </label>
                      <input
                        type="number"
                        value={downPayment || ''}
                        onChange={(e) => setDownPayment(Number(e.target.value))}
                        placeholder="e.g. 200000"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Monthly Fuel & Maintenance (₹)
                      </label>
                      <input
                        type="number"
                        value={monthlyOngoingCosts || ''}
                        onChange={(e) => setMonthlyOngoingCosts(Number(e.target.value))}
                        placeholder="e.g. 4000"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* House / Real Estate */}
              {scenarioType === 'house' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Property Purchase Price (₹)
                    </label>
                    <input
                      type="number"
                      value={purchasePrice || ''}
                      onChange={(e) => setPurchasePrice(Number(e.target.value))}
                      placeholder="e.g. 6000000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Down Payment (e.g. 20%) (₹)
                      </label>
                      <input
                        type="number"
                        value={downPayment || ''}
                        onChange={(e) => setDownPayment(Number(e.target.value))}
                        placeholder="e.g. 1200000"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Monthly Maintenance & Taxes (₹)
                      </label>
                      <input
                        type="number"
                        value={monthlyOngoingCosts || ''}
                        onChange={(e) => setMonthlyOngoingCosts(Number(e.target.value))}
                        placeholder="e.g. 3500"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Personal Loan */}
              {scenarioType === 'personal_loan' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Proposed Loan Borrowing Amount (₹)
                    </label>
                    <input
                      type="number"
                      value={purchasePrice || ''}
                      onChange={(e) => setPurchasePrice(Number(e.target.value))}
                      placeholder="e.g. 300000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Loan Purpose / Note
                    </label>
                    <input
                      type="text"
                      value={customNotes}
                      onChange={(e) => setCustomNotes(e.target.value)}
                      placeholder="e.g. Home renovation, wedding, consolidation"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                </div>
              )}

              {/* Expensive Product */}
              {scenarioType === 'expensive_product' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Product Price (₹)
                    </label>
                    <input
                      type="number"
                      value={purchasePrice || ''}
                      onChange={(e) => setPurchasePrice(Number(e.target.value))}
                      placeholder="e.g. 150000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Initial Cash / Down Payment (₹)
                    </label>
                    <input
                      type="number"
                      value={downPayment || ''}
                      onChange={(e) => setDownPayment(Number(e.target.value))}
                      placeholder="0 for full EMI or full cash"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                </div>
              )}

              {/* Major Trip */}
              {scenarioType === 'major_trip' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Estimated Total Trip Budget (₹)
                    </label>
                    <input
                      type="number"
                      value={purchasePrice || ''}
                      onChange={(e) => setPurchasePrice(Number(e.target.value))}
                      placeholder="e.g. 250000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Months Until Trip Departure
                      </label>
                      <input
                        type="number"
                        value={timeHorizonMonths || ''}
                        onChange={(e) => setTimeHorizonMonths(Number(e.target.value))}
                        placeholder="e.g. 6"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Already Saved for Trip (₹)
                      </label>
                      <input
                        type="number"
                        value={alreadySaved || ''}
                        onChange={(e) => setAlreadySaved(Number(e.target.value))}
                        placeholder="0"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Business Expansion */}
              {scenarioType === 'business' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Initial Capital Investment (₹)
                    </label>
                    <input
                      type="number"
                      value={purchasePrice || ''}
                      onChange={(e) => setPurchasePrice(Number(e.target.value))}
                      placeholder="e.g. 500000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Monthly Operating Costs (₹)
                      </label>
                      <input
                        type="number"
                        value={monthlyOngoingCosts || ''}
                        onChange={(e) => setMonthlyOngoingCosts(Number(e.target.value))}
                        placeholder="e.g. 20000"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Expected Monthly Revenue (₹)
                      </label>
                      <input
                        type="number"
                        value={expectedRevenue || ''}
                        onChange={(e) => setExpectedRevenue(Number(e.target.value))}
                        placeholder="e.g. 35000"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Increase Monthly Investment */}
              {scenarioType === 'increase_investment' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Additional Monthly Contribution / SIP (₹)
                    </label>
                    <input
                      type="number"
                      value={monthlyContribution || ''}
                      onChange={(e) => setMonthlyContribution(Number(e.target.value))}
                      placeholder="e.g. 15000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Investment Horizon (Years)
                      </label>
                      <input
                        type="number"
                        value={investmentYears || ''}
                        onChange={(e) => setInvestmentYears(Number(e.target.value))}
                        placeholder="5"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Expected Annual Return (%)
                      </label>
                      <input
                        type="number"
                        value={expectedReturnRate || ''}
                        onChange={(e) => setExpectedReturnRate(Number(e.target.value))}
                        placeholder="11.0"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Save for Financial Goal */}
              {scenarioType === 'financial_goal' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Target Goal Amount (₹)
                    </label>
                    <input
                      type="number"
                      value={purchasePrice || ''}
                      onChange={(e) => setPurchasePrice(Number(e.target.value))}
                      placeholder="e.g. 500000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Target Horizon (Months)
                      </label>
                      <input
                        type="number"
                        value={timeHorizonMonths || ''}
                        onChange={(e) => setTimeHorizonMonths(Number(e.target.value))}
                        placeholder="24"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Already Saved Toward Goal (₹)
                      </label>
                      <input
                        type="number"
                        value={alreadySaved || ''}
                        onChange={(e) => setAlreadySaved(Number(e.target.value))}
                        placeholder="0"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Compare Cash vs Loan */}
              {scenarioType === 'cash_vs_loan' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Total Purchase Price (₹)
                    </label>
                    <input
                      type="number"
                      value={purchasePrice || ''}
                      onChange={(e) => setPurchasePrice(Number(e.target.value))}
                      placeholder="e.g. 500000"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Down Payment If Taking Loan (₹)
                      </label>
                      <input
                        type="number"
                        value={downPayment || ''}
                        onChange={(e) => setDownPayment(Number(e.target.value))}
                        placeholder="e.g. 100000"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Expected Return on Saved Cash (%)
                      </label>
                      <input
                        type="number"
                        value={expectedReturnRate || ''}
                        onChange={(e) => setExpectedReturnRate(Number(e.target.value))}
                        placeholder="11.0"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Custom Decision */}
              {scenarioType === 'custom' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Initial Upfront Outflow (₹)
                      </label>
                      <input
                        type="number"
                        value={purchasePrice || ''}
                        onChange={(e) => setPurchasePrice(Number(e.target.value))}
                        placeholder="0"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        New Monthly Recurring Cost (₹)
                      </label>
                      <input
                        type="number"
                        value={monthlyOngoingCosts || ''}
                        onChange={(e) => setMonthlyOngoingCosts(Number(e.target.value))}
                        placeholder="0"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                      Decision Notes & Description
                    </label>
                    <input
                      type="text"
                      value={customNotes}
                      onChange={(e) => setCustomNotes(e.target.value)}
                      placeholder="e.g. Higher education semester, parental support commitment"
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
                    />
                  </div>
                </div>
              )}

              {/* Expandable Advanced Options Section */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-xs font-bold text-[#6478E8] hover:text-[#4F5ECE] flex items-center gap-1.5 transition-colors"
                >
                  {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  <span>{showAdvanced ? 'Hide Advanced Financing Options' : 'Show Advanced Financing Options (Interest, Tenure, Fees)'}</span>
                </button>

                {showAdvanced && (
                  <div className="mt-3 p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0] space-y-3 animate-in fade-in duration-150">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <label className="text-[11px] font-semibold text-[#697386]">
                            Loan Interest Rate (% APR)
                          </label>
                          <KnowMore termId="reducing_interest" variant="icon" size="xs" />
                        </div>
                        <input
                          type="number"
                          step="0.1"
                          value={loanInterestRate || ''}
                          onChange={(e) => setLoanInterestRate(Number(e.target.value))}
                          placeholder="9.5"
                          className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033]"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                          Loan Tenure (Months)
                        </label>
                        <input
                          type="number"
                          value={loanTenureMonths || ''}
                          onChange={(e) => setLoanTenureMonths(Number(e.target.value))}
                          placeholder="60"
                          className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033]"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                        Upfront One-Time Charges (Registration, Stamp Duty, Fees) (₹)
                      </label>
                      <input
                        type="number"
                        value={upfrontCosts || ''}
                        onChange={(e) => setUpfrontCosts(Number(e.target.value))}
                        placeholder="0"
                        className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033]"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Run Analysis Action Button */}
            <Button
              variant="primary"
              size="lg"
              onClick={handleSimulate}
              loading={loading}
              className="w-full mt-4"
              icon={<Sparkles className="w-4 h-4" />}
            >
              {loading ? 'Evaluating Financial Impact...' : 'Evaluate Financial Affordability'}
            </Button>

            {error && (
              <div className="p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F] flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Complete Affordability Dashboard (7 Cols) */}
        <div className="lg:col-span-7 space-y-5">
          {result ? (
            <div className="space-y-5 animate-in fade-in duration-200">
              {/* 1. Rule-Based Verdict Banner */}
              {(() => {
                const theme = getVerdictTheme(result.verdict_category || 'AFFORDABLE');
                return (
                  <div className={`p-5 rounded-2xl border ${theme.bg} ${theme.border} space-y-2.5 shadow-sm`}>
                    <div className="flex items-start gap-3.5">
                      <div className="mt-0.5 shrink-0">{theme.icon}</div>
                      <div className="space-y-1 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant={theme.badge as any} size="sm" className="font-bold">
                            {theme.label}
                          </Badge>
                          <span className="text-xs text-[#697386]">
                            Surplus After: <strong>{formatINR(result.scenario_surplus)}/mo</strong>
                          </span>
                        </div>
                        <p className="text-xs sm:text-sm font-semibold text-[#172033] leading-relaxed">
                          {result.summary_verdict}
                        </p>
                      </div>
                    </div>

                    {/* Bullet reasons for assessment */}
                    {result.detailed_recommendations && result.detailed_recommendations.length > 0 && (
                      <div className="pt-2 border-t border-black/5 text-xs space-y-1">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[#697386] block">
                          Key Decision Factors:
                        </span>
                        <ul className="list-disc list-inside space-y-0.5 text-[#172033]/90 text-[11px]">
                          {result.detailed_recommendations.map((rec: string, idx: number) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* 2. Monthly Cash Flow Impact Breakdown */}
              <Card className="space-y-3.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-1.5">
                    <DollarSign className="w-4 h-4 text-[#6478E8]" />
                    <span>Monthly Cash Flow Impact</span>
                  </h3>
                  <KnowMore termId="debt_to_income" variant="badge" label="About DTI" />
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0]">
                    <span className="text-[10px] font-bold text-[#697386] uppercase block">Income</span>
                    <span className="text-xs sm:text-sm font-mono font-bold text-[#172033]">
                      {formatINR(result.cash_flow_impact?.monthly_income || result.monthly_income)}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0]">
                    <span className="text-[10px] font-bold text-[#697386] uppercase block">Living + Loans</span>
                    <span className="text-xs sm:text-sm font-mono font-bold text-[#172033]">
                      {formatINR((result.cash_flow_impact?.monthly_living_expenses || 0) + (result.cash_flow_impact?.existing_obligations || 0))}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-[#EEF0FF] border border-[#6478E8]/20">
                    <span className="text-[10px] font-bold text-[#4F5ECE] uppercase block">New Monthly Payment</span>
                    <span className="text-xs sm:text-sm font-mono font-bold text-[#4F5ECE]">
                      {formatINR(result.cash_flow_impact?.proposed_new_monthly_payment || 0)}
                    </span>
                  </div>
                  <div className={`p-3 rounded-xl border ${result.cash_flow_impact?.projected_surplus_after >= 0 ? 'bg-[#E5F7EF]/50 border-[#16865C]/20' : 'bg-[#FDF2F4] border-[#D9485F]/20'}`}>
                    <span className="text-[10px] font-bold text-[#697386] uppercase block">Net Surplus After</span>
                    <span className={`text-xs sm:text-sm font-mono font-bold ${result.cash_flow_impact?.projected_surplus_after >= 0 ? 'text-[#16865C]' : 'text-[#D9485F]'}`}>
                      {formatINR(result.cash_flow_impact?.projected_surplus_after || 0)}/mo
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-[#697386] leading-relaxed">
                  <strong>Formula</strong>: Available Surplus ({formatINR(result.cash_flow_impact?.available_surplus_before || 0)}) − New Commitment ({formatINR(result.cash_flow_impact?.proposed_new_monthly_payment || 0)}) − Ongoing Costs ({formatINR(result.cash_flow_impact?.additional_ongoing_costs || 0)}) = <strong>{formatINR(result.cash_flow_impact?.projected_surplus_after || 0)} remaining</strong>. Existing loan EMIs are not double-counted.
                </p>
              </Card>

              {/* 3. Savings & Emergency Fund Impact */}
              {result.savings_impact && (
                <Card className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-1.5">
                      <PiggyBank className="w-4 h-4 text-[#16865C]" />
                      <span>Savings & Emergency Fund Impact</span>
                    </h3>
                    <KnowMore termId="emergency_fund" variant="badge" label="About Emergency Runway" />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0]">
                      <span className="text-[10px] font-bold text-[#697386] uppercase block">Upfront Cash Outlay</span>
                      <span className="text-sm font-mono font-bold text-[#172033]">
                        {formatINR(result.savings_impact.initial_cash_required)}
                      </span>
                      <span className="text-[10px] text-[#697386] block mt-0.5">Down payment + fees</span>
                    </div>

                    <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0]">
                      <span className="text-[10px] font-bold text-[#697386] uppercase block">Remaining Liquid Savings</span>
                      <span className="text-sm font-mono font-bold text-[#172033]">
                        {formatINR(result.savings_impact.remaining_liquid_savings)}
                      </span>
                      <span className="text-[10px] text-[#697386] block mt-0.5">
                        Target: {formatINR(result.savings_impact.emergency_fund_target)}
                      </span>
                    </div>

                    <div className={`p-3 rounded-xl border ${result.savings_impact.is_emergency_fund_preserved ? 'bg-[#E5F7EF]/50 border-[#16865C]/20' : 'bg-[#FFF0E5] border-[#D9822B]/20'}`}>
                      <span className="text-[10px] font-bold text-[#697386] uppercase block">Emergency Runway</span>
                      <span className={`text-sm font-mono font-bold ${result.savings_impact.is_emergency_fund_preserved ? 'text-[#16865C]' : 'text-[#C53030]'}`}>
                        {result.savings_impact.projected_runway_months.toFixed(1)} Months
                      </span>
                      <span className="text-[10px] text-[#697386] block mt-0.5">
                        {result.savings_impact.is_emergency_fund_preserved ? '✓ Buffer Preserved' : '⚠️ Below 3-month target'}
                      </span>
                    </div>
                  </div>
                </Card>
              )}

              {/* 4. Loan Amortization Analysis (When Loan Involved) */}
              {result.loan_analysis && (
                <Card className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-1.5">
                      <CreditCard className="w-4 h-4 text-[#4F5ECE]" />
                      <span>Loan Amortization & Total Financing Cost</span>
                    </h3>
                    <KnowMore termId="reducing_interest" variant="badge" label="Reducing Amortization" />
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                    <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0]">
                      <span className="text-[10px] font-bold text-[#697386] uppercase block">Principal Borrowed</span>
                      <span className="text-xs sm:text-sm font-mono font-bold text-[#172033]">
                        {formatINR(result.loan_analysis.principal_borrowed)}
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#EEF0FF] border border-[#6478E8]/20">
                      <span className="text-[10px] font-bold text-[#4F5ECE] uppercase block">Monthly EMI</span>
                      <span className="text-xs sm:text-sm font-mono font-bold text-[#4F5ECE]">
                        {formatINR(result.loan_analysis.monthly_emi)} / mo
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0]">
                      <span className="text-[10px] font-bold text-[#697386] uppercase block">Total Interest Paid</span>
                      <span className="text-xs sm:text-sm font-mono font-bold text-[#B25E09]">
                        {formatINR(result.loan_analysis.total_interest_paid)}
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0]">
                      <span className="text-[10px] font-bold text-[#697386] uppercase block">Total Purchase Cost</span>
                      <span className="text-xs sm:text-sm font-mono font-bold text-[#172033]">
                        {formatINR(result.loan_analysis.total_purchase_cost)}
                      </span>
                    </div>
                  </div>

                  <p className="text-[11px] text-[#697386]">
                    Calculated using reducing-balance amortization at <strong>{result.loan_analysis.annual_interest_rate_pct}% APR</strong> over <strong>{result.loan_analysis.tenure_months} months</strong>. Includes ₹{result.loan_analysis.processing_fee.toLocaleString()} processing fee.
                  </p>
                </Card>
              )}

              {/* 5. 3-Way Alternative Options Comparison */}
              {result.alternative_options && result.alternative_options.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-1.5">
                      <ArrowLeftRight className="w-4 h-4 text-[#6478E8]" />
                      <span>Compare Alternative Options (A vs B vs C)</span>
                    </h3>
                    <KnowMore termId="opportunity_cost" variant="badge" label="Opportunity Cost" />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {result.alternative_options.map((opt: any, idx: number) => (
                      <div
                        key={idx}
                        className={`p-4 rounded-2xl bg-white border border-[#E6EAF0] shadow-sm space-y-2.5 flex flex-col justify-between hover:border-[#6478E8]/40 transition-all ${
                          idx === 0 ? 'ring-1 ring-[#6478E8]/30' : ''
                        }`}
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold text-[#6478E8] uppercase tracking-wider">
                              Option {String.fromCharCode(65 + idx)}
                            </span>
                            <Badge
                              variant={opt.feasibility?.toLowerCase().includes('affordable') || opt.feasibility?.toLowerCase().includes('feasible') ? 'mint' : 'peach'}
                              size="sm"
                            >
                              {opt.feasibility}
                            </Badge>
                          </div>
                          <h4 className="text-xs font-bold text-[#172033] leading-snug">
                            {opt.name}
                          </h4>
                          <p className="text-[11px] text-[#697386] leading-relaxed line-clamp-3">
                            {opt.description}
                          </p>
                        </div>

                        <div className="space-y-2 pt-2 border-t border-[#F1F4F9] text-[11px]">
                          {opt.initial_cash_required !== undefined && (
                            <div className="flex justify-between">
                              <span className="text-[#697386]">Upfront Cash:</span>
                              <span className="font-mono font-bold text-[#172033]">{formatINR(opt.initial_cash_required)}</span>
                            </div>
                          )}
                          <div className="flex justify-between">
                            <span className="text-[#697386]">Monthly Outflow:</span>
                            <span className="font-mono font-bold text-[#172033]">{formatINR(opt.monthly_commitment)}/mo</span>
                          </div>
                          {opt.total_estimated_cost !== undefined && (
                            <div className="flex justify-between">
                              <span className="text-[#697386]">Total Cost:</span>
                              <span className="font-mono font-bold text-[#172033]">{formatINR(opt.total_estimated_cost)}</span>
                            </div>
                          )}
                          {opt.pros && opt.pros.length > 0 && (
                            <div className="text-[10px] text-[#16865C] pt-1 border-t border-[#F1F4F9]">
                              <strong>Advantage</strong>: {opt.pros[0]}
                            </div>
                          )}
                          {opt.cons && opt.cons.length > 0 && (
                            <div className="text-[10px] text-[#697386]">
                              <strong>Trade-off</strong>: {opt.cons[0]}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 6. Stress Tests Sensitivity Grid */}
              {result.stress_tests && result.stress_tests.length > 0 && (
                <Card className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldAlert className="w-4 h-4 text-[#D9822B]" />
                      <span>Stress Tests: What If Things Go Wrong?</span>
                    </h3>
                    <KnowMore termId="stress_testing" variant="badge" label="About Stress Testing" />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                    {result.stress_tests.map((st: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0] space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-[#172033]">{st.name}</span>
                          <Badge
                            variant={st.verdict === 'Manageable' ? 'mint' : st.verdict === 'Strained' ? 'peach' : 'danger'}
                            size="sm"
                          >
                            {st.verdict}
                          </Badge>
                        </div>
                        <p className="text-[10px] text-[#697386] leading-tight">
                          {st.description}
                        </p>
                        <div className="pt-1 flex items-center justify-between text-[11px] font-mono">
                          <span className="text-[#697386]">Surplus:</span>
                          <span className={`font-bold ${st.projected_surplus >= 0 ? 'text-[#16865C]' : 'text-[#D9485F]'}`}>
                            {formatINR(st.projected_surplus)}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#697386] italic">
                          {st.impact_summary}
                        </p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* 7. Safety Guardrails & Next Steps */}
              <div className="p-4 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] text-xs text-[#697386] space-y-2">
                <p className="font-bold text-[#172033] flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#16865C]" />
                  <span>Model Safety Guardrails & Suggested Next Steps</span>
                </p>
                <ul className="list-disc list-inside space-y-1 text-[11px] leading-relaxed">
                  {result.risks_and_assumptions.map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            /* Empty State when no simulation run yet */
            <Card className="p-10 sm:p-14 text-center space-y-4 flex flex-col items-center justify-center">
              <div className="w-14 h-14 rounded-2xl bg-[rgba(212,175,55,0.15)] text-[#F5DE88] border border-[rgba(212,175,55,0.3)] flex items-center justify-center shadow-[0_0_20px_rgba(212,175,55,0.2)]">
                <Sparkles className="w-7 h-7" />
              </div>
              <div className="space-y-1.5 max-w-md">
                <h3 className="text-base font-bold text-[#F3F4F6]">
                  Ready to Evaluate Your Real Financial Decision
                </h3>
                <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                  Select your scenario on the left, verify your monthly surplus and liquid reserves, and run the simulator to answer:
                </p>
                <p className="text-xs font-semibold text-[#F5DE88] italic pt-1">
                  "Can I afford this, what happens to my finances if I proceed, and what alternatives should I consider?"
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 w-full max-w-lg pt-4 text-left">
                <div className="p-3 rounded-xl bg-white/[0.03] border border-[rgba(212,175,55,0.2)] text-xs space-y-1">
                  <span className="font-bold text-[#F3F4F6] block">Cash Flow Check</span>
                  <span className="text-[11px] text-[#9CA3AF]">Prevents monthly deficit and debt traps.</span>
                </div>
                <div className="p-3 rounded-xl bg-white/[0.03] border border-[rgba(212,175,55,0.2)] text-xs space-y-1">
                  <span className="font-bold text-[#F3F4F6] block">Emergency Buffer</span>
                  <span className="text-[11px] text-[#9CA3AF]">Protects your 3-6 month safety reserves.</span>
                </div>
                <div className="p-3 rounded-xl bg-white/[0.03] border border-[rgba(212,175,55,0.2)] text-xs space-y-1 col-span-2 sm:col-span-1">
                  <span className="font-bold text-[#F3F4F6] block">5 Stress Tests</span>
                  <span className="text-[11px] text-[#9CA3AF]">Tests salary cuts and expense surges.</span>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Save Scenario Dialog Modal */}
      {saveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-[#E6EAF0] animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#172033] flex items-center gap-2">
                <Bookmark className="w-4 h-4 text-[#6478E8]" />
                <span>Save Decision Plan</span>
              </h3>
              <button
                onClick={() => setSaveModalOpen(false)}
                className="text-[#697386] hover:text-[#172033] p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-[#697386] leading-relaxed">
              Give this scenario a name so you can compare it against other options or reopen it later from your saved decisions list.
            </p>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1">
                Scenario Name
              </label>
              <input
                type="text"
                value={scenarioTitle}
                onChange={(e) => setScenarioTitle(e.target.value)}
                placeholder="e.g. 2026 SUV Purchase — 20% Down Payment"
                className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setSaveModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveScenario}
                loading={saving}
                disabled={!scenarioTitle.trim()}
              >
                {saving ? 'Saving...' : 'Confirm & Save'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Saved Scenarios Slide-out Drawer */}
      {savedScenariosOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/30 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white h-full shadow-2xl p-6 space-y-5 overflow-y-auto border-l border-[#E6EAF0] animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-[#E6EAF0]">
              <div className="flex items-center gap-2">
                <Bookmark className="w-4 h-4 text-[#6478E8]" />
                <h3 className="text-sm font-bold text-[#172033]">Saved Decision Plans</h3>
              </div>
              <button
                onClick={() => setSavedScenariosOpen(false)}
                className="text-[#697386] hover:text-[#172033] p-1.5 rounded-lg hover:bg-[#F8FAFC]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {savedScenarios.length === 0 ? (
              <div className="py-12 text-center space-y-2">
                <Bookmark className="w-8 h-8 text-[#CBD5E1] mx-auto" />
                <p className="text-xs font-semibold text-[#172033]">No Saved Plans Yet</p>
                <p className="text-[11px] text-[#697386] max-w-xs mx-auto">
                  Run an affordability analysis on any decision and click "Save Plan" to revisit it anytime.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {savedScenarios.map((s) => (
                  <div
                    key={s.id}
                    className="p-3.5 rounded-2xl bg-[#F8FAFC] border border-[#E6EAF0] space-y-2 hover:border-[#6478E8]/40 transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      {editingScenarioId === s.id ? (
                        <div className="flex items-center gap-1.5 flex-1">
                          <input
                            type="text"
                            value={editTitleText}
                            onChange={(e) => setEditTitleText(e.target.value)}
                            className="text-xs bg-white border border-[#6478E8] rounded-lg px-2 py-1 w-full"
                          />
                          <Button size="sm" variant="primary" onClick={() => handleRenameScenario(s.id)}>
                            Save
                          </Button>
                          <button
                            onClick={() => setEditingScenarioId(null)}
                            className="text-xs text-[#697386] p-1"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <h4 className="text-xs font-bold text-[#172033] leading-snug flex-1">
                          {s.title}
                        </h4>
                      )}

                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => {
                            setEditingScenarioId(s.id);
                            setEditTitleText(s.title);
                          }}
                          className="p-1 text-[#697386] hover:text-[#172033]"
                          title="Rename"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteScenario(s.id)}
                          className="p-1 text-[#697386] hover:text-[#D9485F]"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-[#697386]">
                      <span className="capitalize">{s.scenario_type.replace('_', ' ')}</span>
                      <span>{new Date(s.created_at).toLocaleDateString()}</span>
                    </div>

                    <div className="pt-2 flex items-center justify-between border-t border-[#E6EAF0]">
                      <span className="text-[11px] font-mono font-bold text-[#172033]">
                        {s.result_data?.scenario_surplus !== undefined ? `${formatINR(s.result_data.scenario_surplus)}/mo surplus` : ''}
                      </span>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleReopenScenario(s)}
                      >
                        Reopen in Planner
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
