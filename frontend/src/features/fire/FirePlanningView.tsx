import React, { useState, useEffect, useRef } from 'react';
import {
  Flame,
  TrendingUp,
  ShieldAlert,
  Sliders,
  Sparkles,
  Award,
  Calendar,
  Clock,
  ArrowUpRight,
  Coins,
  CheckCircle2,
  RefreshCw,
  Info,
  Wallet,
  Zap,
  Activity,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { Card, Button, Badge } from '../../components/ui';
import { KnowMore } from '../../components/KnowMore';
import { apiRequest, getAuthToken } from '../../services/api';
import {
  FireCalculationResponse,
  FinancialHealthAssessment,
} from '../../types';

export const FirePlanningView: React.FC = () => {
  // Inputs & Decisions
  const [currentAge, setCurrentAge] = useState<number>(28);
  const [retirementAge, setRetirementAge] = useState<number>(50);
  const [monthlyIncome, setMonthlyIncome] = useState<number>(100000);
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(50000);
  const [currentAssets, setCurrentAssets] = useState<number>(1500000);
  const [monthlyInvestment, setMonthlyInvestment] = useState<number>(35000);
  const [inflationRate, setInflationRate] = useState<number>(6.0);
  const [nominalReturn, setNominalReturn] = useState<number>(11.0);
  const [swr, setSwr] = useState<number>(3.5);
  const [essentialPct, setEssentialPct] = useState<number>(70);

  // States
  const [activeSubTab, setActiveSubTab] = useState<'forecaster' | 'health'>('forecaster');
  const [fireData, setFireData] = useState<FireCalculationResponse | null>(null);
  const [healthData, setHealthData] = useState<FinancialHealthAssessment | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [calculating, setCalculating] = useState<boolean>(false);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const isFirstLoad = useRef<boolean>(true);

  // Calculate or re-forecast FIRE data
  const calculateFire = async (overrides: Record<string, number> = {}) => {
    setCalculating(true);
    try {
      const payload = {
        current_age: overrides.currentAge ?? currentAge,
        retirement_age: overrides.retirementAge ?? retirementAge,
        monthly_expenses: overrides.monthlyExpenses ?? monthlyExpenses,
        monthly_income: overrides.monthlyIncome ?? monthlyIncome,
        current_investable_assets: overrides.currentAssets ?? currentAssets,
        monthly_investment: overrides.monthlyInvestment ?? monthlyInvestment,
        expected_annual_inflation_pct: overrides.inflationRate ?? inflationRate,
        expected_nominal_return_pct: overrides.nominalReturn ?? nominalReturn,
        withdrawal_rate_pct: overrides.swr ?? swr,
        essential_expenses_pct: overrides.essentialPct ?? essentialPct,
      };

      const data = await apiRequest<FireCalculationResponse>('/fire/calculate', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setFireData(data);
    } catch (err) {
      console.error('Failed to calculate FIRE data:', err);
    } finally {
      setCalculating(false);
      setLoading(false);
    }
  };

  // Fetch user profile-assembled FIRE projection
  const loadUserProfile = async () => {
    const token = getAuthToken();
    if (!token) return false;
    try {
      const profileData = await apiRequest<FireCalculationResponse>('/fire/profile');
      if (profileData && (profileData.fire_target_future || profileData.current_age)) {
        setFireData(profileData);
        if (profileData.current_age) {
          setCurrentAge(Number(profileData.current_age));
        }
        if (profileData.planned_retirement_age) {
          setRetirementAge(Number(profileData.planned_retirement_age));
        }
        if (profileData.current_monthly_income !== undefined && profileData.current_monthly_income !== null) {
          setMonthlyIncome(Number(profileData.current_monthly_income));
        }
        if (profileData.current_monthly_expenses) {
          setMonthlyExpenses(Number(profileData.current_monthly_expenses));
        }
        if (profileData.current_investable_assets !== undefined) {
          setCurrentAssets(Number(profileData.current_investable_assets));
        }
        if (profileData.current_monthly_investment !== undefined) {
          setMonthlyInvestment(Number(profileData.current_monthly_investment));
        }
        return true;
      }
    } catch (err) {
      console.warn('Could not load user FIRE profile:', err);
    }
    return false;
  };

  // Fetch Health Assessment
  const fetchHealthAssessment = async () => {
    try {
      const data = await apiRequest<FinancialHealthAssessment>('/fire/health-assessment');
      setHealthData(data);
    } catch (err) {
      console.error('Failed to fetch health assessment:', err);
    }
  };

  // Initial Load: auto-load real user profile if signed in, else calculate defaults
  useEffect(() => {
    const init = async () => {
      const loaded = await loadUserProfile();
      if (!loaded) {
        await calculateFire();
      }
      await fetchHealthAssessment();
      setLoading(false);
      isFirstLoad.current = false;
    };
    init();
  }, []);

  // Reactive Auto-Calculation whenever any decision parameter changes
  useEffect(() => {
    if (isFirstLoad.current) return;
    const timer = setTimeout(() => {
      calculateFire();
    }, 350);
    return () => clearTimeout(timer);
  }, [
    currentAge,
    retirementAge,
    monthlyIncome,
    monthlyExpenses,
    currentAssets,
    monthlyInvestment,
    inflationRate,
    nominalReturn,
    swr,
    essentialPct,
  ]);

  // Format INR in Crores or Lakhs
  const formatInr = (val: number) => {
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    } else if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)} L`;
    }
    return `₹${Math.round(val).toLocaleString('en-IN')}`;
  };

  // Quick preset handlers
  const applyPreset = (type: string) => {
    if (type === 'boost_sip') {
      const newSip = monthlyInvestment + 10000;
      setMonthlyInvestment(newSip);
    } else if (type === 'retire_early') {
      const newRetire = Math.max(currentAge + 5, 45);
      setRetirementAge(newRetire);
    } else if (type === 'high_inflation') {
      setInflationRate(7.5);
    } else if (type === 'surplus_to_sip') {
      const surplus = Math.max(0, monthlyIncome - monthlyExpenses);
      if (surplus > 0) {
        setMonthlyInvestment(surplus);
      }
    } else if (type === 'reset') {
      setCurrentAge(28);
      setRetirementAge(50);
      setMonthlyIncome(100000);
      setMonthlyExpenses(50000);
      setMonthlyInvestment(35000);
      setCurrentAssets(1500000);
      setInflationRate(6.0);
      setNominalReturn(11.0);
      setSwr(3.5);
    }
  };

  // Adopt a strategy directly into planning decisions
  const adoptStrategy = (targetAge: number | null | undefined, monthlyReq: number, monthlyExpenseRetirement: number) => {
    if (targetAge && targetAge <= 80) {
      setRetirementAge(targetAge);
    }
    if (monthlyReq > 0) {
      setMonthlyInvestment(Math.round(monthlyReq));
    }
  };

  const monthlySurplus = Math.max(0, monthlyIncome - monthlyExpenses);
  const savingsRatePct = monthlyIncome > 0 ? Math.round((monthlySurplus / monthlyIncome) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-[#111622]/95 border border-[rgba(212,175,55,0.2)] shadow-[0_4px_25px_-2px_rgba(0,0,0,0.6)]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-[rgba(212,175,55,0.15)] rounded-xl text-[#F5DE88] border border-[rgba(212,175,55,0.3)] shadow-[0_0_12px_rgba(212,175,55,0.2)]">
              <Flame className="w-5 h-5" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#F3F4F6] tracking-tight">
              Retirement & Financial Freedom Planner
            </h1>
            <KnowMore termId="financial_independence" variant="badge" label="Know More" />
          </div>
          <p className="text-xs sm:text-sm text-[#9CA3AF]">
            Clear, understandable projections to help you plan when you can retire and how much you need.
          </p>
        </div>

        {/* Sub-tab navigation */}
        <div className="flex items-center gap-2 bg-[#0A0D14] p-1.5 rounded-xl border border-white/10">
          <button
            onClick={() => setActiveSubTab('forecaster')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeSubTab === 'forecaster'
                ? 'bg-gradient-to-r from-[#ECC856] via-[#D4AF37] to-[#B89327] text-black font-bold shadow-sm'
                : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
            }`}
          >
            Retirement Planner
          </button>
          <button
            onClick={() => setActiveSubTab('health')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeSubTab === 'health'
                ? 'bg-gradient-to-r from-[#ECC856] via-[#D4AF37] to-[#B89327] text-black font-bold shadow-sm'
                : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
            }`}
          >
            Check My Financial Health
          </button>
        </div>
      </div>

      {/* Main Forecaster View */}
      {activeSubTab === 'forecaster' && (
        <div className="space-y-6">
          {/* Quick What-If Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-[#9CA3AF] mr-1">Instant What-Ifs:</span>
            <button
              onClick={() => applyPreset('boost_sip')}
              className="px-3 py-1.5 rounded-xl text-xs font-medium bg-[#111622] border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37] hover:text-[#F5DE88] transition-all text-[#F3F4F6] shadow-sm flex items-center gap-1.5"
            >
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              +₹10,000/mo Investment
            </button>
            <button
              onClick={() => applyPreset('retire_early')}
              className="px-3 py-1.5 rounded-xl text-xs font-medium bg-[#111622] border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37] hover:text-[#F5DE88] transition-all text-[#F3F4F6] shadow-sm flex items-center gap-1.5"
            >
              <Calendar className="w-3.5 h-3.5 text-[#F5DE88]" />
              Target Age 45
            </button>
            <button
              onClick={() => applyPreset('high_inflation')}
              className="px-3 py-1.5 rounded-xl text-xs font-medium bg-[#111622] border border-[rgba(212,175,55,0.2)] hover:border-[#F59E0B] hover:text-[#F59E0B] transition-all text-[#F3F4F6] shadow-sm flex items-center gap-1.5"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-[#F59E0B]" />
              What If Costs Rise? (7.5% Inflation)
            </button>
            {monthlySurplus > 0 && monthlyInvestment !== monthlySurplus && (
              <button
                onClick={() => applyPreset('surplus_to_sip')}
                className="px-3 py-1.5 rounded-xl text-xs font-medium bg-[#111622] border border-emerald-500/30 hover:border-emerald-500 text-emerald-400 hover:text-emerald-300 transition-all shadow-sm flex items-center gap-1.5"
              >
                <Zap className="w-3.5 h-3.5 text-emerald-400" />
                Invest Full Surplus ({formatInr(monthlySurplus)})
              </button>
            )}
            <button
              onClick={() => applyPreset('reset')}
              className="px-3 py-1.5 rounded-xl text-xs font-medium bg-[#111622] border border-white/10 hover:border-white/20 text-[#9CA3AF] hover:text-[#F3F4F6] transition-all ml-auto flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reset
            </button>
          </div>

          {/* Interactive Parameters Card */}
          <Card className="p-5 sm:p-6 space-y-4 border border-[rgba(212,175,55,0.25)] bg-[#111622]/95 backdrop-blur-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#ECC856]" />
                <h3 className="text-sm sm:text-base font-bold text-[#F3F4F6] tracking-tight">Planning Parameters & Monthly Decisions</h3>
                <KnowMore termId="retirement_target" variant="badge" label="About Target" />
              </div>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-xs font-semibold text-[#ECC856] hover:text-[#F5DE88] hover:underline"
              >
                {showAdvanced ? 'Hide Advanced Assumptions' : 'Show Advanced Assumptions'}
              </button>
            </div>

            {/* Live Cash Flow & Savings Rate Quick Banner */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 rounded-xl bg-[#0D111A] border border-[rgba(212,175,55,0.2)]">
              <div className="flex items-center justify-between sm:justify-start gap-2">
                <span className="text-[11px] text-[#9CA3AF] flex items-center gap-1">
                  <Wallet className="w-3 h-3 text-[#10B981]" />
                  Monthly Salary:
                </span>
                <span className="text-xs font-bold text-[#10B981] font-mono">{formatInr(monthlyIncome)}</span>
              </div>
              <div className="flex items-center justify-between sm:justify-start gap-2">
                <span className="text-[11px] text-[#9CA3AF]">Living Costs:</span>
                <span className="text-xs font-bold text-[#F43F5E] font-mono">{formatInr(monthlyExpenses)}</span>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-2">
                <span className="text-[11px] text-[#9CA3AF]">Surplus:</span>
                <span className="text-xs font-bold text-[#F5DE88] font-mono">
                  {formatInr(monthlySurplus)}
                </span>
                {monthlyIncome > 0 && (
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30">
                    {savingsRatePct}% saved
                  </span>
                )}
              </div>
            </div>

            {/* Core 6-Decision Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
              <div>
                <label className="text-[11px] font-semibold text-[#D1D5DB] block mb-1">Current Age</label>
                <input
                  type="number"
                  min="18"
                  max="70"
                  value={currentAge}
                  onChange={(e) => setCurrentAge(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-white/15 rounded-xl text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 font-mono transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Retire Age</label>
                  <KnowMore termId="retirement_target" />
                </div>
                <input
                  type="number"
                  min="30"
                  max="80"
                  value={retirementAge}
                  onChange={(e) => setRetirementAge(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-white/15 rounded-xl text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 font-mono transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Monthly Salary (₹)</label>
                  <KnowMore termId="cash_flow" />
                </div>
                <input
                  type="number"
                  step="5000"
                  value={monthlyIncome}
                  onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                  placeholder="e.g. 100000"
                  className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-emerald-500/30 rounded-xl text-[#10B981] font-bold focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400/50 font-mono transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Monthly Costs (₹)</label>
                  <KnowMore termId="cash_flow" />
                </div>
                <input
                  type="number"
                  step="5000"
                  value={monthlyExpenses}
                  onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-white/15 rounded-xl text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 font-mono transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Current Savings (₹)</label>
                  <KnowMore termId="investable_assets" />
                </div>
                <input
                  type="number"
                  step="50000"
                  value={currentAssets}
                  onChange={(e) => setCurrentAssets(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-white/15 rounded-xl text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 font-mono transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Monthly SIP (₹)</label>
                  <KnowMore termId="monthly_investment" />
                </div>
                <input
                  type="number"
                  step="5000"
                  value={monthlyInvestment}
                  onChange={(e) => setMonthlyInvestment(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-[#D4AF37]/40 rounded-xl text-[#F5DE88] font-bold focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 font-mono transition-colors"
                />
              </div>
            </div>

            {showAdvanced && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 pt-3 border-t border-white/10">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Expected Inflation (%)</label>
                    <KnowMore termId="inflation" />
                  </div>
                  <input
                    type="number"
                    step="0.5"
                    value={inflationRate}
                    onChange={(e) => setInflationRate(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-white/15 rounded-xl text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] font-mono"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Pre-Retire Return (%)</label>
                  </div>
                  <input
                    type="number"
                    step="0.5"
                    value={nominalReturn}
                    onChange={(e) => setNominalReturn(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-white/15 rounded-xl text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] font-mono"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Withdrawal Rate (%)</label>
                    <KnowMore termId="safe_withdrawal_rate" />
                  </div>
                  <input
                    type="number"
                    step="0.25"
                    value={swr}
                    onChange={(e) => setSwr(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-white/15 rounded-xl text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] font-mono"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-semibold text-[#D1D5DB] truncate">Basic Needs Ratio (%)</label>
                    <KnowMore termId="lean_fire" />
                  </div>
                  <input
                    type="number"
                    step="5"
                    value={essentialPct}
                    onChange={(e) => setEssentialPct(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-medium bg-[#141A26] border border-white/15 rounded-xl text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] font-mono"
                  />
                </div>
              </div>
            )}

            <div className="flex items-center justify-between pt-2 border-t border-white/10 text-xs">
              <span className="text-[#9CA3AF] flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${calculating ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`}></span>
                <span>{calculating ? 'Recalculating live forecast...' : 'Real-time sync active (changes update immediately)'}</span>
              </span>

              <Button
                variant="primary"
                size="sm"
                onClick={() => calculateFire()}
                disabled={calculating}
                className="flex items-center gap-2"
              >
                {calculating ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Recalculating...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Update My Retirement Estimate</span>
                  </>
                )}
              </Button>
            </div>
          </Card>

          {/* Top KPI Cards with Plain Language */}
          {fireData && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="p-4 space-y-2 border border-[rgba(212,175,55,0.2)] bg-[#111622]/95 backdrop-blur-md">
                <div className="flex items-center justify-between text-[#9CA3AF] text-xs">
                  <span className="font-semibold text-[#F3F4F6]">Money You Need to Retire</span>
                  <div className="flex items-center gap-1">
                    <KnowMore
                      termId="retirement_target"
                      contextualValue={{
                        label: "Money You Need to Retire (Today's Value)",
                        value: formatInr(fireData.fire_target_today),
                        isEstimate: true,
                      }}
                    />
                    <Coins className="w-4 h-4 text-[#D4AF37]" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-[#F5DE88] tracking-tight tabular-nums font-mono">
                  {formatInr(fireData.fire_target_today)}
                </div>
                <p className="text-[11px] text-[#9CA3AF]">
                  In today's value, assuming a {fireData.safe_withdrawal_rate_pct}% yearly withdrawal rate for {formatInr(fireData.current_monthly_expenses)}/mo costs
                </p>
              </Card>

              <Card className="p-4 space-y-2 border border-[rgba(212,175,55,0.2)] bg-[#111622]/95 backdrop-blur-md">
                <div className="flex items-center justify-between text-[#9CA3AF] text-xs">
                  <span className="font-semibold text-[#F3F4F6]">Money Needed by Age {fireData.planned_retirement_age}</span>
                  <div className="flex items-center gap-1">
                    <KnowMore
                      termId="inflation"
                      contextualValue={{
                        label: `Money Needed by Age ${fireData.planned_retirement_age} (Future Value)`,
                        value: formatInr(fireData.fire_target_future),
                        isEstimate: true,
                      }}
                    />
                    <Calendar className="w-4 h-4 text-emerald-400" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-[#F5DE88] tracking-tight tabular-nums font-mono">
                  {formatInr(fireData.fire_target_future)}
                </div>
                <p className="text-[11px] text-[#9CA3AF]">
                  Adjusted for {inflationRate}% annual inflation ({fireData.years_to_retirement} years until retirement)
                </p>
              </Card>

              <Card className="p-4 space-y-2 border border-[rgba(212,175,55,0.2)] bg-[#111622]/95 backdrop-blur-md">
                <div className="flex items-center justify-between text-[#9CA3AF] text-xs">
                  <span className="font-semibold text-[#F3F4F6]">Estimated Age You Can Retire</span>
                  <div className="flex items-center gap-1">
                    <KnowMore
                      termId="financial_independence"
                      contextualValue={{
                        label: 'Estimated Age You Can Retire',
                        value: fireData.projected_fire_age ? `Age ${fireData.projected_fire_age}` : 'Beyond 85',
                        isEstimate: true,
                      }}
                    />
                    <Flame className="w-4 h-4 text-amber-400" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-[#F3F4F6] tracking-tight flex items-baseline gap-2 tabular-nums font-mono">
                  <span className="text-[#F5DE88]">{fireData.projected_fire_age ? `Age ${fireData.projected_fire_age}` : 'Beyond 85'}</span>
                  {fireData.projected_fire_age && (
                    <span className="text-xs font-semibold text-emerald-400">
                      ({fireData.projected_fire_age - fireData.current_age} yrs left)
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#9CA3AF]">
                  Based on investing {formatInr(fireData.current_monthly_investment)} each month
                </p>
              </Card>

              <Card className="p-4 space-y-2 border border-[rgba(212,175,55,0.2)] bg-[#111622]/95 backdrop-blur-md">
                <div className="flex items-center justify-between text-[#9CA3AF] text-xs">
                  <span className="font-semibold text-[#F3F4F6]">Progress Towards Goal</span>
                  <div className="flex items-center gap-1">
                    <KnowMore
                      termId="retirement_shortfall"
                      contextualValue={{
                        label: 'Progress Towards Retirement Goal',
                        value: `${fireData.fire_progress_pct}%`,
                        isEstimate: true,
                      }}
                    />
                    <Activity className="w-4 h-4 text-[#D4AF37]" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-[#D4AF37] tracking-tight tabular-nums font-mono">
                  {fireData.fire_progress_pct}%
                </div>
                <div className="w-full bg-[#0A0D14] h-2.5 rounded-full overflow-hidden border border-white/10">
                  <div
                    className="bg-gradient-to-r from-[#D4AF37] to-[#ECC856] h-full rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(212,175,55,0.4)]"
                    style={{ width: `${Math.min(100, fireData.fire_progress_pct)}%` }}
                  />
                </div>
              </Card>
            </div>
          )}

          {/* Retirement Lifestyle Comparison Section */}
          {fireData && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm sm:text-base font-bold text-[#F3F4F6] flex items-center gap-2">
                  <Award className="w-4 h-4 text-[#D4AF37]" />
                  Retirement Lifestyle Comparisons (Interactive Forecasts)
                </h2>
                <KnowMore termId="regular_fire" variant="badge" label="About Lifestyles" />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {fireData.strategies.map((strat) => {
                  const strategyMeta: Record<string, { title: string; termId: string }> = {
                    lean: { title: 'Retirement With Basic Expenses', termId: 'lean_fire' },
                    standard: { title: 'Regular FIRE', termId: 'regular_fire' },
                    fat: { title: 'Retirement With More Spending and Comfort', termId: 'fat_fire' },
                    coast: { title: 'Investments Ready to Grow on Their Own', termId: 'coast_fire' },
                  };
                  const meta = strategyMeta[strat.strategy_type] || { title: strat.name, termId: 'financial_independence' };

                  return (
                    <Card
                      key={strat.strategy_type}
                      className="p-4 space-y-3 transition-all duration-200 border border-[rgba(212,175,55,0.22)] bg-[#141A26]/90 hover:bg-[#1A2232] hover:border-[#D4AF37]/50 shadow-md shadow-black/40 flex flex-col justify-between"
                    >
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-1">
                          <div>
                            <div className="flex items-center gap-1">
                              <h4 className="font-bold text-sm text-[#F3F4F6]">{meta.title}</h4>
                              <KnowMore termId={meta.termId} />
                            </div>
                            <span className="text-[10px] text-[#9CA3AF] font-mono">({strat.name})</span>
                          </div>
                          <Badge
                            variant={strat.is_achievable_by_target_age ? 'mint' : 'peach'}
                            size="sm"
                          >
                            {strat.is_achievable_by_target_age ? 'On Track' : 'Need to Build More'}
                          </Badge>
                        </div>

                        <p className="text-[11px] text-[#9CA3AF] leading-relaxed min-h-[44px]">
                          {strat.description}
                        </p>

                        <div className="space-y-1.5 pt-2 border-t border-white/10 text-xs">
                          <div className="flex justify-between items-center">
                            <span className="text-[#9CA3AF]">Monthly Living Cost:</span>
                            <span className="font-bold text-[#F3F4F6] font-mono">
                              {formatInr(strat.monthly_expense_in_retirement)}/mo
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-[#9CA3AF]">Goal in Today's Money:</span>
                            <span className="font-bold text-[#F5DE88] font-mono">{formatInr(strat.target_corpus_today)}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-[#9CA3AF]">Goal at Retirement Age:</span>
                            <span className="font-bold text-[#F3F4F6] font-mono">{formatInr(strat.target_corpus_at_retirement)}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-[#9CA3AF]">Estimated Age Achieved:</span>
                            <span className="font-bold text-[#ECC856] font-mono">
                              {strat.projected_fire_age ? `Age ${strat.projected_fire_age}` : 'Beyond 85'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-[#9CA3AF] flex items-center gap-1">
                              <span>Monthly Investment Needed:</span>
                              <KnowMore termId="required_monthly_investment" />
                            </span>
                            <span className="font-bold text-[#10B981] font-mono">
                              {formatInr(strat.required_monthly_investment)}/mo
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Quick Adopt Action Button */}
                      <button
                        onClick={() => adoptStrategy(strat.projected_fire_age, Number(strat.required_monthly_investment), Number(strat.monthly_expense_in_retirement))}
                        className="w-full mt-3 py-1.5 px-2.5 rounded-lg text-xs font-semibold bg-[#111622] hover:bg-[#D4AF37]/15 border border-[rgba(212,175,55,0.25)] hover:border-[#D4AF37] text-[#ECC856] transition-all flex items-center justify-center gap-1.5"
                      >
                        <Zap className="w-3 h-3 text-[#ECC856]" />
                        <span>Adopt This Plan Target</span>
                      </button>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          {/* Year-by-Year Multi-Scenario Growth Chart */}
          {fireData && (
            <Card className="p-5 sm:p-6 space-y-4 border border-[rgba(212,175,55,0.25)] bg-[#111622]/95 backdrop-blur-md">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm sm:text-base font-bold text-[#F3F4F6] tracking-tight">
                      How Your Money Could Grow Over Time (Age {fireData.current_age} to 80)
                    </h3>
                    <KnowMore termId="growth_chart" variant="button" label="How this works" />
                  </div>
                  <p className="text-xs text-[#9CA3AF]">
                    An estimate of how your savings may grow before retirement and how they may change when you begin using them.
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
                    <span className="text-[#9CA3AF]">Higher-return (+2%)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#ECC856]" />
                    <span className="text-[#F5DE88]">Base assumptions (11%)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#F43F5E]" />
                    <span className="text-[#9CA3AF]">Lower-return (-2.5%)</span>
                  </div>
                </div>
              </div>

              <div className="h-80 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={fireData.yearly_projections}
                    margin={{ top: 10, right: 20, left: 20, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.07)" />
                    <XAxis
                      dataKey="age"
                      tickFormatter={(age) => `Age ${age}`}
                      stroke="#9CA3AF"
                      fontSize={11}
                    />
                    <YAxis
                      tickFormatter={(val) => `₹${(val / 10000000).toFixed(1)}Cr`}
                      stroke="#9CA3AF"
                      fontSize={11}
                    />
                    <Tooltip
                      formatter={(val: any) => [`₹${(Number(val) / 10000000).toFixed(2)} Cr`, '']}
                      labelFormatter={(label) => `Age ${label}`}
                      contentStyle={{
                        backgroundColor: '#0D111A',
                        border: '1px solid rgba(212,175,55,0.3)',
                        borderRadius: '12px',
                        fontSize: '12px',
                        color: '#F3F4F6',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.8)',
                      }}
                    />
                    <ReferenceLine
                      x={fireData.planned_retirement_age}
                      stroke="#D4AF37"
                      strokeDasharray="4 4"
                      label={{
                        value: `Retirement Age ${fireData.planned_retirement_age}`,
                        fill: '#F5DE88',
                        fontSize: 10,
                        position: 'top',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="portfolio_optimistic"
                      name="Higher-return scenario"
                      fill="#10B981"
                      fillOpacity={0.08}
                      stroke="#10B981"
                      strokeWidth={1.5}
                    />
                    <Line
                      type="monotone"
                      dataKey="portfolio_base"
                      name="Base case estimate"
                      stroke="#ECC856"
                      strokeWidth={2.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="portfolio_conservative"
                      name="Lower-return scenario"
                      stroke="#F43F5E"
                      strokeWidth={1.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="fire_target_curve"
                      name="Target Line"
                      stroke="#9CA3AF"
                      strokeDasharray="3 3"
                      strokeWidth={1.5}
                      dot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              <div className="p-3 bg-[#0A0D14] rounded-xl border border-white/10 text-[11px] text-[#9CA3AF] flex items-center gap-2">
                <Info className="w-4 h-4 text-[#ECC856] shrink-0" />
                <span>
                  Notice the milestone at age {fireData.planned_retirement_age}: monthly investments stop and yearly living expenses begin to be drawn from savings. A sustainable plan stays steady or grows, while an underfunded plan declines toward zero.
                </span>
              </div>
            </Card>
          )}

          {/* Statutory Disclaimers */}
          {fireData && (
            <div className="p-4 rounded-2xl bg-[#0D111A] border border-white/10 text-xs space-y-2">
              <h4 className="font-bold text-[#F3F4F6] flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#ECC856]" />
                FIRE Methodology & Indian Regulatory Disclosures
              </h4>
              <ul className="list-disc pl-5 space-y-1 text-[#9CA3AF] text-[11px] leading-relaxed">
                {fireData.disclaimers.map((d, idx) => (
                  <li key={idx}>{d}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 8-Pillar Financial Health View */}
      {activeSubTab === 'health' && (
        <div className="space-y-6">
          {healthData && (
            <>
              {/* Overall Score Card */}
              <div className="p-6 rounded-2xl bg-[#111622]/95 border border-[rgba(212,175,55,0.2)] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-2 max-w-xl">
                  <div className="flex items-center gap-2">
                    <Badge variant="mint" size="sm" className="font-bold">
                      Transparent 8-Pillar Engine
                    </Badge>
                    <KnowMore termId="financial_health_score" variant="badge" label="Understand the 8 Pillars" />
                    <span className="text-xs text-[#9CA3AF]">Zero Black-Box AI Hallucinations</span>
                  </div>
                  <h2 className="text-2xl font-bold text-[#F3F4F6]">{healthData.status}</h2>
                  <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                    {healthData.summary}
                  </p>
                </div>

                <div className="flex items-center gap-4 bg-[#0A0D14] p-4 rounded-2xl border border-[rgba(212,175,55,0.25)] shrink-0">
                  <div className="text-center">
                    <div className="text-3xl font-extrabold text-[#F5DE88] font-mono">
                      {healthData.overall_score}
                      <span className="text-sm font-normal text-[#9CA3AF]">/100</span>
                    </div>
                    <div className="text-[11px] font-semibold text-[#ECC856] uppercase tracking-wider mt-0.5">
                      Health Index
                    </div>
                  </div>
                </div>
              </div>

              {/* 8 Pillars Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {healthData.pillars.map((p) => {
                  return (
                    <Card key={p.pillar_id} className="p-4 border border-[rgba(212,175,55,0.2)] space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-[#F3F4F6] truncate">{p.name}</span>
                        <Badge
                          variant={
                            p.status === 'excellent'
                              ? 'mint'
                              : p.status === 'good'
                              ? 'lavender'
                              : p.status === 'fair'
                              ? 'peach'
                              : 'danger'
                          }
                          size="sm"
                        >
                          {p.score}/100
                        </Badge>
                      </div>

                      <div className="space-y-1">
                        <div className="text-lg font-bold text-[#F5DE88] font-mono">{p.metric_value}</div>
                        <div className="text-[10px] text-[#9CA3AF]">Target: {p.target_benchmark}</div>
                      </div>

                      <p className="text-[11px] text-[#9CA3AF] leading-relaxed pt-1 border-t border-white/10">
                        {p.recommendation}
                      </p>
                    </Card>
                  );
                })}
              </div>

              {/* 12-Month Actionable Plan */}
              <Card className="p-5 border border-[rgba(212,175,55,0.2)] space-y-4">
                <h3 className="text-sm font-bold text-[#F3F4F6] flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                  Your 12-Month Actionable Financial Roadmap
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {healthData.actionable_checklist_12_months.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-[#0A0D14] border border-white/10 space-y-2"
                    >
                      <div className="text-[11px] font-bold text-[#ECC856] uppercase tracking-wider">
                        {item.timeframe}
                      </div>
                      <h4 className="text-xs font-bold text-[#F3F4F6]">{item.action}</h4>
                      <p className="text-[11px] text-[#9CA3AF] leading-relaxed">
                        {item.detail}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Assessment Disclaimer */}
              <div className="p-4 rounded-2xl bg-[#0D111A] border border-white/10 text-xs text-[#9CA3AF]">
                <p className="text-[11px] leading-relaxed">{healthData.disclaimer}</p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
