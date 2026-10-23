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
  RefreshCw
} from 'lucide-react';
import { apiRequest } from '../../services/api';

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
          input_data: { monthlyIncome, monthlyExpenses, currentSavings, targetAmount, timeHorizonMonths },
          result_data: result,
        }),
      });
      setSaveSuccess(true);
    } catch (err: any) {
      alert(err.message || 'Please sign in to save scenarios to your account.');
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
      {/* Header */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/40 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-5 h-5 text-emerald-400" />
            <h1 className="text-xl font-extrabold text-slate-100">Financial Decision Simulator</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Simulate major purchases, emergency runway preservation, and cash flow reallocation with deterministic multi-scenario analysis.
          </p>
        </div>

        {result && (
          <button
            onClick={handleSaveScenario}
            disabled={saving || saveSuccess}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors"
          >
            <Bookmark className={`w-3.5 h-3.5 ${saveSuccess ? 'text-emerald-400' : 'text-slate-400'}`} />
            <span>{saveSuccess ? 'Scenario Saved' : saving ? 'Saving...' : 'Save Scenario'}</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column */}
        <div className="lg:col-span-5 space-y-5 p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Decision Scenario Type</label>
            <select
              value={scenarioType}
              onChange={(e) => {
                setScenarioType(e.target.value);
                setResult(null);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="major_purchase">Major Purchase (Car, Home Down Payment, Asset)</option>
              <option value="increase_savings">Increase Monthly Savings Rate</option>
              <option value="expense_reduction">Discretionary Expense Reduction</option>
              <option value="emergency_fund_builder">6-Month Emergency Fund Completion</option>
            </select>
          </div>

          <div className="space-y-3 pt-3 border-t border-slate-800/80">
            <p className="text-xs font-bold text-slate-300">Your Current Financial Baseline</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Monthly Net Income (₹)</label>
                <input
                  type="number"
                  value={monthlyIncome || ''}
                  onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Monthly Expenses (₹)</label>
                <input
                  type="number"
                  value={monthlyExpenses || ''}
                  onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">Current Liquid Savings / Reserves (₹)</label>
              <input
                type="number"
                value={currentSavings || ''}
                onChange={(e) => setCurrentSavings(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Dynamic Scenario Inputs */}
          {scenarioType === 'major_purchase' && (
            <div className="space-y-3 pt-3 border-t border-slate-800/80">
              <p className="text-xs font-bold text-slate-300">Purchase Goals</p>
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Target Purchase Price (e.g. Car ₹8,00,000)</label>
                <input
                  type="number"
                  value={targetAmount || ''}
                  onChange={(e) => setTargetAmount(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Desired Horizon (Months)</label>
                <input
                  type="number"
                  value={timeHorizonMonths || ''}
                  onChange={(e) => setTimeHorizonMonths(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
          )}

          {scenarioType === 'increase_savings' && (
            <div className="space-y-3 pt-3 border-t border-slate-800/80">
              <p className="text-xs font-bold text-slate-300">Target Savings Goal</p>
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Target Savings Rate (%)</label>
                <input
                  type="number"
                  value={targetSavingsRate || ''}
                  onChange={(e) => setTargetSavingsRate(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
          )}

          {scenarioType === 'expense_reduction' && (
            <div className="space-y-3 pt-3 border-t border-slate-800/80">
              <p className="text-xs font-bold text-slate-300">Discretionary Cutback</p>
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Monthly Reduction Amount (₹)</label>
                <input
                  type="number"
                  value={expenseReduction || ''}
                  onChange={(e) => setExpenseReduction(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
          )}

          <button
            onClick={handleSimulate}
            disabled={loading}
            className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-sm rounded-xl transition-all shadow-md shadow-emerald-500/20"
          >
            {loading ? 'Simulating Decisions...' : 'Simulate Decision Scenarios'}
          </button>

          {error && (
            <p className="text-xs text-rose-400 bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20">
              {error}
            </p>
          )}
        </div>

        {/* Results & Alternatives Column */}
        <div className="lg:col-span-7 space-y-5">
          {result ? (
            <div className="space-y-5 animate-in fade-in duration-200">
              {/* Verdict Banner */}
              <div className={`p-4 rounded-2xl border flex items-start gap-3 ${
                result.is_feasible
                  ? 'bg-gradient-to-r from-emerald-950/60 to-slate-900 border-emerald-500/30'
                  : 'bg-gradient-to-r from-amber-950/40 to-slate-900 border-amber-500/30'
              }`}>
                {result.is_feasible ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded ${
                      result.is_feasible
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    }`}>
                      {result.is_feasible ? 'Cash Flow Feasible' : 'Cash Flow Gap Detected'}
                    </span>
                    <span className="text-xs text-slate-400">
                      Baseline Surplus: {formatINR(result.baseline_surplus)}/mo
                    </span>
                  </div>
                  <p className="text-xs text-slate-200 mt-2 leading-relaxed">
                    {result.summary_verdict}
                  </p>
                </div>
              </div>

              {/* Metric Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {result.comparisons.map((c: any, idx: number) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                      {c.metric_name}
                    </span>
                    <p className="text-xs font-bold text-slate-100">{c.scenario_value}</p>
                    <span className={`text-[11px] font-medium block ${
                      c.impact_type === 'positive' ? 'text-emerald-400' : c.impact_type === 'negative' ? 'text-rose-400' : 'text-slate-400'
                    }`}>
                      {c.delta}
                    </span>
                  </div>
                ))}
              </div>

              {/* Strategic Options List */}
              {result.alternative_options && result.alternative_options.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Recommended Strategic Paths
                  </h3>
                  <div className="space-y-3">
                    {result.alternative_options.map((opt: any, idx: number) => (
                      <div key={idx} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-slate-100">{opt.name}</h4>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            opt.feasibility === 'Fully Feasible'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'bg-amber-500/20 text-amber-300'
                          }`}>
                            {opt.feasibility}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{opt.description}</p>
                        <div className="flex flex-wrap items-center gap-4 text-[11px] pt-1 text-slate-400">
                          <span className="text-emerald-400 font-semibold">Advantage: {opt.pros[0]}</span>
                          <span className="text-slate-400">Trade-off: {opt.cons[0]}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Assumptions & Citations Box */}
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 space-y-1.5">
                <p className="font-semibold text-slate-300">Model Assumptions & Safety Criteria:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {result.risks_and_assumptions.map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800/60 space-y-3">
              <Sparkles className="w-8 h-8 text-emerald-400 mx-auto opacity-70" />
              <h3 className="text-sm font-bold text-slate-200">Ready to Simulate Financial Decisions</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Configure your scenario parameters on the left (e.g. buying a car in 18 months or boosting savings)
                to compute cash flow feasibility, protect your emergency buffer, and explore trade-offs.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
