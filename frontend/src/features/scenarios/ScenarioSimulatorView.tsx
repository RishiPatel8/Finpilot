import React, { useState } from 'react';
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
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { apiRequest } from '../../services/api';
import { Card, Badge, Button, PageHeader } from '../../components/ui';

export const ScenarioSimulatorView: React.FC = () => {
  const [scenarioType, setScenarioType] = useState('major_purchase');
  const [monthlyIncome, setMonthlyIncome] = useState<number>(60000);
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(35000);
  const [currentSavings, setCurrentSavings] = useState<number>(200000);

  // Major purchase params
  const [targetAmount, setTargetAmount] = useState<number>(800000);
  const [timeHorizonMonths, setTimeHorizonMonths] = useState<number>(18);

  // Other scenario params
  const [targetSavingsRate, setTargetSavingsRate] = useState<number>(40);
  const [expenseReduction, setExpenseReduction] = useState<number>(5000);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      };

      if (scenarioType === 'major_purchase') {
        payload.target_amount = targetAmount;
        payload.time_horizon_months = timeHorizonMonths;
      } else if (scenarioType === 'increase_savings') {
        payload.target_savings_rate_pct = targetSavingsRate;
      } else if (scenarioType === 'expense_reduction') {
        payload.expense_reduction_amount = expenseReduction;
      }

      const res = await apiRequest('/scenarios/simulate', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Simulation failed. Check inputs.');
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
          title: result.title,
          scenario_type: result.scenario_type,
          input_data: {
            monthlyIncome,
            monthlyExpenses,
            currentSavings,
            targetAmount,
            timeHorizonMonths,
          },
          result_data: result,
        }),
      });
      setSaveSuccess(true);
    } catch (err: any) {
      alert(err.message || 'Please sign in to save scenarios to your profile.');
    } finally {
      setSaving(false);
    }
  };

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Financial Decision Simulator"
        description="Flagship decision engine: Evaluate large asset acquisitions, emergency runway impacts, and multi-scenario trade-offs with deterministic arithmetic."
        icon={<SlidersHorizontal className="w-4 h-4 text-[#6478E8]" />}
        badge={
          <Badge variant="lavender" size="sm">
            AI CFO Engine
          </Badge>
        }
        actions={
          result && (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleSaveScenario}
              disabled={saving || saveSuccess}
              icon={
                <Bookmark
                  className={`w-3.5 h-3.5 ${
                    saveSuccess ? 'text-[#16865C]' : 'text-[#697386]'
                  }`}
                />
              }
            >
              {saveSuccess ? 'Scenario Saved' : saving ? 'Saving...' : 'Save Scenario'}
            </Button>
          )
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column */}
        <Card className="lg:col-span-5 space-y-5">
          <div>
            <label className="block text-xs font-bold text-[#172033] mb-1.5 uppercase tracking-wider">
              Decision Scenario Type
            </label>
            <select
              value={scenarioType}
              onChange={(e) => {
                setScenarioType(e.target.value);
                setResult(null);
              }}
              className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-[#172033] font-medium focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
            >
              <option value="major_purchase">Major Purchase (Car, Home Down Payment, Asset)</option>
              <option value="increase_savings">Increase Monthly Savings Rate</option>
              <option value="expense_reduction">Discretionary Expense Reduction</option>
              <option value="emergency_fund_builder">6-Month Emergency Fund Completion</option>
            </select>
          </div>

          {/* Baseline inputs */}
          <div className="space-y-3.5 pt-4 border-t border-[#E6EAF0]">
            <p className="text-xs font-bold text-[#172033] uppercase tracking-wider">
              Current Financial Baseline
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Monthly Net Income (₹)
                </label>
                <input
                  type="number"
                  value={monthlyIncome || ''}
                  onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Monthly Expenses (₹)
                </label>
                <input
                  type="number"
                  value={monthlyExpenses || ''}
                  onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                Current Liquid Savings / Reserves (₹)
              </label>
              <input
                type="number"
                value={currentSavings || ''}
                onChange={(e) => setCurrentSavings(Number(e.target.value))}
                className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
              />
            </div>
          </div>

          {/* Dynamic Scenario Inputs */}
          {scenarioType === 'major_purchase' && (
            <div className="space-y-3.5 pt-4 border-t border-[#E6EAF0]">
              <p className="text-xs font-bold text-[#172033] uppercase tracking-wider">
                Purchase Goals & Horizon
              </p>
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Target Purchase Price (e.g. Car ₹8,00,000)
                </label>
                <input
                  type="number"
                  value={targetAmount || ''}
                  onChange={(e) => setTargetAmount(Number(e.target.value))}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Desired Timeline (Months)
                </label>
                <input
                  type="number"
                  value={timeHorizonMonths || ''}
                  onChange={(e) => setTimeHorizonMonths(Number(e.target.value))}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
                />
              </div>
            </div>
          )}

          {scenarioType === 'increase_savings' && (
            <div className="space-y-3.5 pt-4 border-t border-[#E6EAF0]">
              <p className="text-xs font-bold text-[#172033] uppercase tracking-wider">
                Target Savings Rate
              </p>
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Target Savings Rate (%)
                </label>
                <input
                  type="number"
                  value={targetSavingsRate || ''}
                  onChange={(e) => setTargetSavingsRate(Number(e.target.value))}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
                />
              </div>
            </div>
          )}

          {scenarioType === 'expense_reduction' && (
            <div className="space-y-3.5 pt-4 border-t border-[#E6EAF0]">
              <p className="text-xs font-bold text-[#172033] uppercase tracking-wider">
                Discretionary Cutback
              </p>
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Monthly Reduction Amount (₹)
                </label>
                <input
                  type="number"
                  value={expenseReduction || ''}
                  onChange={(e) => setExpenseReduction(Number(e.target.value))}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
                />
              </div>
            </div>
          )}

          <Button
            variant="primary"
            size="lg"
            onClick={handleSimulate}
            loading={loading}
            className="w-full"
            icon={<Sparkles className="w-4 h-4" />}
          >
            {loading ? 'Evaluating Scenarios...' : 'Simulate Decision Scenarios'}
          </Button>

          {error && (
            <div className="p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
              {error}
            </div>
          )}
        </Card>

        {/* Results & Alternatives Column */}
        <div className="lg:col-span-7 space-y-5">
          {result ? (
            <div className="space-y-5 animate-in fade-in duration-200">
              {/* Verdict Banner */}
              <div
                className={`p-5 rounded-2xl border flex items-start gap-3.5 ${
                  result.is_feasible
                    ? 'bg-[#E5F7EF]/60 border-[#16865C]/20'
                    : 'bg-[#FFF0E5]/60 border-[#B7791F]/20'
                }`}
              >
                {result.is_feasible ? (
                  <div className="w-8 h-8 rounded-xl bg-[#E5F7EF] text-[#16865C] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-xl bg-[#FFF0E5] text-[#B7791F] flex items-center justify-center shrink-0 mt-0.5">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                )}
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge
                      variant={result.is_feasible ? 'mint' : 'peach'}
                      size="sm"
                      className="font-bold"
                    >
                      {result.is_feasible ? 'Cash Flow Feasible' : 'Cash Flow Gap Detected'}
                    </Badge>
                    <span className="text-xs text-[#697386]">
                      Baseline Surplus: {formatINR(result.baseline_surplus)}/month
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm text-[#172033] font-medium leading-relaxed">
                    {result.summary_verdict}
                  </p>
                </div>
              </div>

              {/* Metric Comparison Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {result.comparisons.map((c: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-white border border-[#E6EAF0] shadow-sm space-y-1.5"
                  >
                    <span className="text-[10px] font-bold text-[#697386] uppercase tracking-wider block">
                      {c.metric_name}
                    </span>
                    <p className="text-sm font-extrabold text-[#172033] tabular-nums">
                      {c.scenario_value}
                    </p>
                    <span
                      className={`text-[11px] font-semibold block tabular-nums ${
                        c.impact_type === 'positive'
                          ? 'text-[#16865C]'
                          : c.impact_type === 'negative'
                          ? 'text-[#D9485F]'
                          : 'text-[#697386]'
                      }`}
                    >
                      {c.delta}
                    </span>
                  </div>
                ))}
              </div>

              {/* Strategic Options List */}
              {result.alternative_options && result.alternative_options.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-[#172033] uppercase tracking-wider">
                    Recommended Strategic Paths & Trade-Offs
                  </h3>
                  <div className="space-y-3">
                    {result.alternative_options.map((opt: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-4 sm:p-5 rounded-2xl bg-white border border-[#E6EAF0] shadow-sm space-y-2.5 transition-all hover:border-[#D1D9E6]"
                      >
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs sm:text-sm font-bold text-[#172033]">
                            {opt.name}
                          </h4>
                          <Badge
                            variant={opt.feasibility === 'Fully Feasible' ? 'mint' : 'peach'}
                            size="sm"
                          >
                            {opt.feasibility}
                          </Badge>
                        </div>
                        <p className="text-xs text-[#697386] leading-relaxed">
                          {opt.description}
                        </p>
                        <div className="flex flex-wrap items-center gap-4 text-xs pt-1 border-t border-[#F1F4F9]">
                          <span className="text-[#16865C] font-semibold">
                            Advantage: {opt.pros[0]}
                          </span>
                          <span className="text-[#697386]">
                            Trade-off: {opt.cons[0]}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Assumptions & Citations Box */}
              <div className="p-4 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] text-xs text-[#697386] space-y-2">
                <p className="font-bold text-[#172033] flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#16865C]" />
                  <span>Model Assumptions & Safety Guardrails</span>
                </p>
                <ul className="list-disc list-inside space-y-1 text-[11px] leading-relaxed">
                  {result.risks_and_assumptions.map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <Card className="p-10 sm:p-14 text-center space-y-3 flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-2xl bg-[#EEF0FF] text-[#6478E8] flex items-center justify-center shadow-sm">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#172033]">
                Ready to Evaluate Decision Scenarios
              </h3>
              <p className="text-xs sm:text-sm text-[#697386] max-w-md leading-relaxed">
                Configure your scenario parameters on the left (such as acquiring a car in 18 months or boosting savings) to compute cash flow feasibility, protect your emergency buffer, and review alternative financial strategies.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
