import React, { useState, useEffect } from 'react';
import {
  Flame,
  TrendingUp,
  ShieldAlert,
  Sliders,
  Sparkles,
  ChevronRight,
  Activity,
  Award,
  Calendar,
  AlertCircle,
  Clock,
  ArrowUpRight,
  Coins,
  CheckCircle2,
  RefreshCw,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { Card, Button, Badge } from '../../components/ui';
import {
  FireCalculationResponse,
  FinancialHealthAssessment,
} from '../../types';

export const FirePlanningView: React.FC = () => {
  // Inputs
  const [currentAge, setCurrentAge] = useState<number>(28);
  const [retirementAge, setRetirementAge] = useState<number>(50);
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(50000);
  const [monthlyIncome, setMonthlyIncome] = useState<number>(100000);
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

  // Fetch or calculate FIRE data
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

      const token = localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/fire/calculate', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        setFireData(data);
      }
    } catch (err) {
      console.error('Failed to calculate FIRE data:', err);
    } finally {
      setCalculating(false);
      setLoading(false);
    }
  };

  // Fetch Health Assessment
  const fetchHealthAssessment = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/fire/health-assessment', { headers });
      if (res.ok) {
        const data = await res.json();
        setHealthData(data);
      }
    } catch (err) {
      console.error('Failed to fetch health assessment:', err);
    }
  };

  // Initial Load
  useEffect(() => {
    calculateFire();
    fetchHealthAssessment();
  }, []);

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
      calculateFire({ monthlyInvestment: newSip });
    } else if (type === 'retire_early') {
      const newRetire = Math.max(currentAge + 5, 45);
      setRetirementAge(newRetire);
      calculateFire({ retirementAge: newRetire });
    } else if (type === 'high_inflation') {
      setInflationRate(7.5);
      calculateFire({ inflationRate: 7.5 });
    } else if (type === 'reset') {
      setCurrentAge(28);
      setRetirementAge(50);
      setMonthlyExpenses(50000);
      setMonthlyInvestment(35000);
      setInflationRate(6.0);
      setNominalReturn(11.0);
      setSwr(3.5);
      calculateFire({
        currentAge: 28,
        retirementAge: 50,
        monthlyExpenses: 50000,
        monthlyInvestment: 35000,
        inflationRate: 6.0,
        nominalReturn: 11.0,
        swr: 3.5,
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-white border border-[#E6EAF0] shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-[#EEF0FF] rounded-xl text-[#6478E8]">
              <Flame className="w-5 h-5" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#172033] tracking-tight">
              FIRE Forecaster & Financial Planning
            </h1>
            <Badge variant="lavender" size="sm" className="font-bold">
              v2.2 Complete
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-[#697386]">
            Mathematically exact compound projections, safe withdrawal analysis, and transparent 8-pillar health tracking.
          </p>
        </div>

        {/* Sub-tab navigation */}
        <div className="flex items-center gap-2 bg-[#F6F8FC] p-1.5 rounded-xl border border-[#E6EAF0]">
          <button
            onClick={() => setActiveSubTab('forecaster')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeSubTab === 'forecaster'
                ? 'bg-white text-[#6478E8] shadow-sm'
                : 'text-[#697386] hover:text-[#172033]'
            }`}
          >
            FIRE Dashboard
          </button>
          <button
            onClick={() => setActiveSubTab('health')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeSubTab === 'health'
                ? 'bg-white text-[#6478E8] shadow-sm'
                : 'text-[#697386] hover:text-[#172033]'
            }`}
          >
            Financial Health (8 Pillars)
          </button>
        </div>
      </div>

      {/* Main Forecaster View */}
      {activeSubTab === 'forecaster' && (
        <div className="space-y-6">
          {/* Quick What-If Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-[#697386] mr-1">Instant What-Ifs:</span>
            <button
              onClick={() => applyPreset('boost_sip')}
              className="px-3 py-1.5 rounded-xl text-xs font-medium bg-white border border-[#E6EAF0] hover:border-[#6478E8] hover:text-[#6478E8] transition-all text-[#172033] shadow-sm flex items-center gap-1.5"
            >
              <TrendingUp className="w-3.5 h-3.5 text-[#16865C]" />
              +₹10,000/mo Investment
            </button>
            <button
              onClick={() => applyPreset('retire_early')}
              className="px-3 py-1.5 rounded-xl text-xs font-medium bg-white border border-[#E6EAF0] hover:border-[#6478E8] hover:text-[#6478E8] transition-all text-[#172033] shadow-sm flex items-center gap-1.5"
            >
              <Calendar className="w-3.5 h-3.5 text-[#6478E8]" />
              Target Age 45
            </button>
            <button
              onClick={() => applyPreset('high_inflation')}
              className="px-3 py-1.5 rounded-xl text-xs font-medium bg-white border border-[#E6EAF0] hover:border-[#E56F4A] hover:text-[#E56F4A] transition-all text-[#172033] shadow-sm flex items-center gap-1.5"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-[#E56F4A]" />
              Stress Test (7.5% Inflation)
            </button>
            <button
              onClick={() => applyPreset('reset')}
              className="px-3 py-1.5 rounded-xl text-xs font-medium bg-white border border-[#E6EAF0] hover:bg-[#F6F8FC] text-[#697386] transition-all ml-auto flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reset Baselines
            </button>
          </div>

          {/* Interactive Parameters Card */}
          <Card className="p-5 bg-white border border-[#E6EAF0] shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#6478E8]" />
                <h3 className="text-sm font-bold text-[#172033]">Planning Parameters</h3>
              </div>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-xs font-semibold text-[#6478E8] hover:underline"
              >
                {showAdvanced ? 'Hide Advanced Assumptions' : 'Show Advanced Assumptions'}
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
              <div>
                <label className="text-[11px] font-semibold text-[#697386] block mb-1">Current Age</label>
                <input
                  type="number"
                  min="18"
                  max="70"
                  value={currentAge}
                  onChange={(e) => setCurrentAge(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[#697386] block mb-1">Target Retirement Age</label>
                <input
                  type="number"
                  min="30"
                  max="80"
                  value={retirementAge}
                  onChange={(e) => setRetirementAge(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[#697386] block mb-1">Monthly Expenses (₹)</label>
                <input
                  type="number"
                  step="5000"
                  value={monthlyExpenses}
                  onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[#697386] block mb-1">Investable Assets (₹)</label>
                <input
                  type="number"
                  step="50000"
                  value={currentAssets}
                  onChange={(e) => setCurrentAssets(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[#697386] block mb-1">Monthly Investment (₹)</label>
                <input
                  type="number"
                  step="5000"
                  value={monthlyInvestment}
                  onChange={(e) => setMonthlyInvestment(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                />
              </div>
            </div>

            {showAdvanced && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 pt-3 border-t border-[#E6EAF0]">
                <div>
                  <label className="text-[11px] font-semibold text-[#697386] block mb-1">Inflation Rate (%)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={inflationRate}
                    onChange={(e) => setInflationRate(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-[#697386] block mb-1">Pre-Retire Return (%)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={nominalReturn}
                    onChange={(e) => setNominalReturn(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-[#697386] block mb-1">Safe Withdrawal Rate (%)</label>
                  <input
                    type="number"
                    step="0.25"
                    value={swr}
                    onChange={(e) => setSwr(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-[#697386] block mb-1">Essential Needs Ratio (%)</label>
                  <input
                    type="number"
                    step="5"
                    value={essentialPct}
                    onChange={(e) => setEssentialPct(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-medium bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl focus:outline-none focus:border-[#6478E8]"
                  />
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2">
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
                    <span>Recalculate Projections</span>
                  </>
                )}
              </Button>
            </div>
          </Card>

          {/* Top KPI Cards */}
          {fireData && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="p-4 bg-white border border-[#E6EAF0] shadow-sm space-y-2">
                <div className="flex items-center justify-between text-[#697386] text-xs">
                  <span className="font-semibold">FIRE Target (Today's Value)</span>
                  <Coins className="w-4 h-4 text-[#6478E8]" />
                </div>
                <div className="text-2xl font-bold text-[#172033] tracking-tight">
                  {formatInr(fireData.fire_target_today)}
                </div>
                <p className="text-[11px] text-[#697386]">
                  At {fireData.safe_withdrawal_rate_pct}% SWR for ₹{Math.round(fireData.current_monthly_expenses).toLocaleString('en-IN')}/mo spending
                </p>
              </Card>

              <Card className="p-4 bg-white border border-[#E6EAF0] shadow-sm space-y-2">
                <div className="flex items-center justify-between text-[#697386] text-xs">
                  <span className="font-semibold">Target at Age {fireData.planned_retirement_age}</span>
                  <Calendar className="w-4 h-4 text-[#16865C]" />
                </div>
                <div className="text-2xl font-bold text-[#172033] tracking-tight">
                  {formatInr(fireData.fire_target_future)}
                </div>
                <p className="text-[11px] text-[#697386]">
                  Adjusted for {inflationRate}% annual inflation ({fireData.years_to_retirement} years)
                </p>
              </Card>

              <Card className="p-4 bg-white border border-[#E6EAF0] shadow-sm space-y-2">
                <div className="flex items-center justify-between text-[#697386] text-xs">
                  <span className="font-semibold">Projected FIRE Age</span>
                  <Flame className="w-4 h-4 text-[#E56F4A]" />
                </div>
                <div className="text-2xl font-bold text-[#172033] tracking-tight flex items-baseline gap-2">
                  <span>{fireData.projected_fire_age ? `Age ${fireData.projected_fire_age}` : 'Beyond 85'}</span>
                  {fireData.projected_fire_age && (
                    <span className="text-xs font-semibold text-[#16865C]">
                      ({fireData.projected_fire_age - fireData.current_age} yrs left)
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#697386]">
                  At current ₹{Math.round(fireData.current_monthly_investment).toLocaleString('en-IN')}/mo contribution
                </p>
              </Card>

              <Card className="p-4 bg-white border border-[#E6EAF0] shadow-sm space-y-2">
                <div className="flex items-center justify-between text-[#697386] text-xs">
                  <span className="font-semibold">FIRE Progress</span>
                  <Activity className="w-4 h-4 text-[#6478E8]" />
                </div>
                <div className="text-2xl font-bold text-[#172033] tracking-tight">
                  {fireData.fire_progress_pct}%
                </div>
                <div className="w-full bg-[#F6F8FC] h-2 rounded-full overflow-hidden border border-[#E6EAF0]">
                  <div
                    className="bg-[#6478E8] h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, fireData.fire_progress_pct)}%` }}
                  />
                </div>
              </Card>
            </div>
          )}

          {/* FIRE Strategy Comparison Section */}
          {fireData && (
            <div className="space-y-3">
              <h2 className="text-sm font-bold text-[#172033] flex items-center gap-2">
                <Award className="w-4 h-4 text-[#6478E8]" />
                FIRE Strategy Comparisons
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {fireData.strategies.map((strat) => (
                  <Card
                    key={strat.strategy_type}
                    className={`p-4 bg-white border rounded-2xl space-y-3 transition-all ${
                      strat.is_achievable_by_target_age
                        ? 'border-[#16865C]/30 shadow-sm'
                        : 'border-[#E6EAF0]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-sm text-[#172033]">{strat.name}</h4>
                      <Badge
                        variant={strat.is_achievable_by_target_age ? 'mint' : 'neutral'}
                        size="sm"
                      >
                        {strat.is_achievable_by_target_age ? 'Achievable' : 'Shortfall'}
                      </Badge>
                    </div>

                    <p className="text-[11px] text-[#697386] leading-relaxed min-h-[34px]">
                      {strat.description}
                    </p>

                    <div className="space-y-1.5 pt-2 border-t border-[#F6F8FC] text-xs">
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Retirement Spending:</span>
                        <span className="font-bold text-[#172033]">
                          ₹{Math.round(strat.monthly_expense_in_retirement).toLocaleString('en-IN')}/mo
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Target Today:</span>
                        <span className="font-bold text-[#172033]">{formatInr(strat.target_corpus_today)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Target at Ret.:</span>
                        <span className="font-bold text-[#172033]">{formatInr(strat.target_corpus_at_retirement)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Projected Age:</span>
                        <span className="font-bold text-[#6478E8]">
                          {strat.projected_fire_age ? `Age ${strat.projected_fire_age}` : 'Beyond 85'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Required SIP:</span>
                        <span className="font-bold text-[#16865C]">
                          ₹{Math.round(strat.required_monthly_investment).toLocaleString('en-IN')}/mo
                        </span>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Year-by-Year Multi-Scenario Chart */}
          {fireData && (
            <Card className="p-5 bg-white border border-[#E6EAF0] shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold text-[#172033]">
                    Accumulation & Post-Retirement Decumulation Curve (Age {fireData.current_age} to 80)
                  </h3>
                  <p className="text-xs text-[#697386]">
                    Simulating continuous compounding during work years and inflation-adjusted withdrawals during retirement.
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#16865C]" />
                    <span className="text-[#697386]">Optimistic (+2%)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#6478E8]" />
                    <span className="text-[#697386]">Base (11%)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#E56F4A]" />
                    <span className="text-[#697386]">Conservative (-2.5%)</span>
                  </div>
                </div>
              </div>

              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={fireData.yearly_projections}
                    margin={{ top: 10, right: 20, left: 20, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#F0F2F6" />
                    <XAxis
                      dataKey="age"
                      tickFormatter={(age) => `Age ${age}`}
                      stroke="#8E9CB2"
                      fontSize={11}
                    />
                    <YAxis
                      tickFormatter={(val) => `₹${(val / 10000000).toFixed(1)}Cr`}
                      stroke="#8E9CB2"
                      fontSize={11}
                    />
                    <Tooltip
                      formatter={(val: any) => [`₹${(Number(val) / 10000000).toFixed(2)} Cr`, '']}
                      labelFormatter={(label) => `Age ${label}`}
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        border: '1px solid #E6EAF0',
                        borderRadius: '12px',
                        fontSize: '12px',
                      }}
                    />
                    <ReferenceLine
                      x={fireData.planned_retirement_age}
                      stroke="#6478E8"
                      strokeDasharray="4 4"
                      label={{
                        value: `Retirement Age ${fireData.planned_retirement_age}`,
                        fill: '#6478E8',
                        fontSize: 10,
                        position: 'top',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="portfolio_optimistic"
                      name="Optimistic"
                      fill="#16865C"
                      fillOpacity={0.06}
                      stroke="#16865C"
                      strokeWidth={1.5}
                    />
                    <Line
                      type="monotone"
                      dataKey="portfolio_base"
                      name="Base Return"
                      stroke="#6478E8"
                      strokeWidth={2.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="portfolio_conservative"
                      name="Conservative"
                      stroke="#E56F4A"
                      strokeWidth={1.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="fire_target_curve"
                      name="Target Line"
                      stroke="#8E9CB2"
                      strokeDasharray="3 3"
                      strokeWidth={1.5}
                      dot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              <div className="p-3 bg-[#F6F8FC] rounded-xl text-[11px] text-[#697386] flex items-center gap-2">
                <Info className="w-4 h-4 text-[#6478E8] shrink-0" />
                <span>
                  Notice the inflection point at age {fireData.planned_retirement_age}: contributions stop and annual living expenses begin deducting. Sustainable portfolios remain flat or grow slightly; depleted portfolios slope downward toward zero.
                </span>
              </div>
            </Card>
          )}

          {/* Statutory Disclaimers */}
          {fireData && (
            <div className="p-4 rounded-2xl bg-white border border-[#E6EAF0] text-xs space-y-2">
              <h4 className="font-bold text-[#172033] flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#6478E8]" />
                FIRE Methodology & Indian Regulatory Disclosures
              </h4>
              <ul className="list-disc pl-5 space-y-1 text-[#697386] text-[11px] leading-relaxed">
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
              <div className="p-6 rounded-2xl bg-white border border-[#E6EAF0] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-2 max-w-xl">
                  <div className="flex items-center gap-2">
                    <Badge variant="mint" size="sm" className="font-bold">
                      Transparent 8-Pillar Engine
                    </Badge>
                    <span className="text-xs text-[#697386]">Zero Black-Box AI Hallucinations</span>
                  </div>
                  <h2 className="text-2xl font-bold text-[#172033]">{healthData.status}</h2>
                  <p className="text-xs sm:text-sm text-[#697386] leading-relaxed">
                    {healthData.summary}
                  </p>
                </div>

                <div className="flex items-center gap-4 bg-[#F6F8FC] p-4 rounded-2xl border border-[#E6EAF0] shrink-0">
                  <div className="text-center">
                    <div className="text-3xl font-extrabold text-[#172033]">
                      {healthData.overall_score}
                      <span className="text-sm font-normal text-[#697386]">/100</span>
                    </div>
                    <div className="text-[11px] font-semibold text-[#6478E8] uppercase tracking-wider mt-0.5">
                      Health Index
                    </div>
                  </div>
                </div>
              </div>

              {/* 8 Pillars Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {healthData.pillars.map((p) => {
                  const statusColors: Record<string, { bg: string; text: string; badge: 'mint' | 'peach' | 'danger' | 'lavender' }> = {
                    excellent: { bg: 'bg-[#16865C]/10', text: 'text-[#16865C]', badge: 'mint' },
                    good: { bg: 'bg-[#6478E8]/10', text: 'text-[#6478E8]', badge: 'lavender' },
                    fair: { bg: 'bg-[#F2A93B]/10', text: 'text-[#C47D14]', badge: 'peach' },
                    critical: { bg: 'bg-[#E56F4A]/10', text: 'text-[#D04D25]', badge: 'danger' },
                    provisional: { bg: 'bg-[#8E9CB2]/10', text: 'text-[#697386]', badge: 'lavender' },
                  };
                  const color = statusColors[p.status] || statusColors.good;

                  return (
                    <Card key={p.pillar_id} className="p-4 bg-white border border-[#E6EAF0] shadow-sm space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-[#172033] truncate">{p.name}</span>
                        <Badge variant={color.badge} size="sm">
                          {p.score}/100
                        </Badge>
                      </div>

                      <div className="space-y-1">
                        <div className="text-lg font-bold text-[#172033]">{p.metric_value}</div>
                        <div className="text-[10px] text-[#697386]">Target: {p.target_benchmark}</div>
                      </div>

                      <p className="text-[11px] text-[#697386] leading-relaxed pt-1 border-t border-[#F6F8FC]">
                        {p.recommendation}
                      </p>
                    </Card>
                  );
                })}
              </div>

              {/* 12-Month Actionable Plan */}
              <Card className="p-5 bg-white border border-[#E6EAF0] shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-[#172033] flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#16865C]" />
                  Your 12-Month Actionable Financial Roadmap
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {healthData.actionable_checklist_12_months.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-[#F6F8FC] border border-[#E6EAF0] space-y-2"
                    >
                      <div className="text-[11px] font-bold text-[#6478E8] uppercase tracking-wider">
                        {item.timeframe}
                      </div>
                      <h4 className="text-xs font-bold text-[#172033]">{item.action}</h4>
                      <p className="text-[11px] text-[#697386] leading-relaxed">
                        {item.detail}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Assessment Disclaimer */}
              <div className="p-4 rounded-2xl bg-white border border-[#E6EAF0] text-xs text-[#697386]">
                <p className="text-[11px] leading-relaxed">{healthData.disclaimer}</p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
