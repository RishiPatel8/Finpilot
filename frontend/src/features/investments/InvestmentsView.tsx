import React, { useState } from 'react';
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
  Sparkles
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { InvestmentCompareResponse, InvestmentOptionComparison } from '../../types';

export const InvestmentsView: React.FC = () => {
  const [amount, setAmount] = useState<number>(300000);
  const [months, setMonths] = useState<number>(6);
  const [canLock, setCanLock] = useState<boolean>(false);
  const [taxSlab, setTaxSlab] = useState<number>(30);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InvestmentCompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<InvestmentCompareResponse>('/investments/compare', {
        method: 'POST',
        body: JSON.stringify({
          investment_amount: amount,
          time_horizon_months: months,
          user_tax_slab_pct: taxSlab,
          can_lock_funds: canLock,
          expected_inflation_pct: 6.0,
        }),
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Comparison failed. Please verify inputs.');
    } finally {
      setLoading(false);
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
      <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/40 border border-slate-800">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-emerald-400" />
          <h1 className="text-xl font-extrabold text-slate-100">
            Liquid Mutual Funds vs Bonds vs Fixed Deposits
          </h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Evaluate capital safety, T+1 liquidity, Section 50AA tax treatment, and interest rate sensitivity.
        </p>
      </div>

      {/* Input Parameters Box */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold text-slate-100">Investment Scenario Parameters</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Investment Amount (₹)</label>
            <input
              type="number"
              value={amount || ''}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Time Horizon (Months)</label>
            <select
              value={months}
              onChange={(e) => setMonths(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value={1}>1 Month (Ultra Short)</option>
              <option value={3}>3 Months (Quarterly)</option>
              <option value={6}>6 Months (Near Term)</option>
              <option value={12}>12 Months (1 Year)</option>
              <option value={24}>24 Months (2 Years)</option>
              <option value={36}>36 Months (3 Years)</option>
              <option value={60}>60 Months (5 Years)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Your Income Tax Slab</label>
            <select
              value={taxSlab}
              onChange={(e) => setTaxSlab(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value={0}>0% (Up to ₹7.75L New Regime)</option>
              <option value={10}>10% Slab</option>
              <option value={15}>15% Slab</option>
              <option value={20}>20% Slab</option>
              <option value={30}>30% Slab (Above ₹15L)</option>
            </select>
          </div>

          <div className="flex flex-col justify-end">
            <button
              type="button"
              onClick={() => setCanLock(!canLock)}
              className={`w-full py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                canLock
                  ? 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                  : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              {canLock ? <Lock className="w-3.5 h-3.5 text-purple-400" /> : <Unlock className="w-3.5 h-3.5 text-slate-500" />}
              <span>{canLock ? 'Can Lock Funds (No Pre-Exit)' : 'May Need Funds Early'}</span>
            </button>
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading}
          className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-sm rounded-xl transition-all shadow-md shadow-emerald-500/20"
        >
          {loading ? 'Analyzing Instruments...' : 'Compare Liquid Funds, Bonds & FDs'}
        </button>

        {error && (
          <p className="text-xs text-rose-400 bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20">
            {error}
          </p>
        )}
      </div>

      {/* Comparison Results */}
      {result ? (
        <div className="space-y-5 animate-in fade-in duration-200">
          {/* Top Recommendation Box */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/60 to-slate-900 border border-emerald-500/30 flex items-start gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase font-extrabold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Recommended: {result.top_recommendation}
                </span>
                <span className="text-xs text-slate-400">Horizon: {result.time_horizon_months} Months</span>
              </div>
              <p className="text-xs text-slate-200 mt-2 leading-relaxed font-medium">
                {result.rationale}
              </p>
            </div>
          </div>

          {/* 3 Columns: Liquid MF vs FD vs Bond */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {result.comparisons.map((c: InvestmentOptionComparison) => {
              const isTop = c.display_name.toLowerCase().includes(result.top_recommendation.toLowerCase());
              return (
                <div
                  key={c.category}
                  className={`p-5 rounded-2xl border flex flex-col justify-between space-y-4 transition-all ${
                    isTop
                      ? 'bg-slate-900/90 border-emerald-500/40 ring-1 ring-emerald-500/20'
                      : 'bg-slate-900/60 border-slate-800'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-base font-bold text-slate-100">{c.display_name}</h3>
                      {isTop && (
                        <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-bold px-2 py-0.5 rounded">
                          Top Fit
                        </span>
                      )}
                    </div>

                    <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                        Indicative Annualized Yield
                      </span>
                      <p className="text-xl font-black text-emerald-400 font-mono">
                        ~{c.indicative_annual_yield_pct}%
                      </p>
                      <p className="text-[11px] text-slate-300">
                        Projected Maturity: <strong>{formatINR(c.projected_maturity_value)}</strong>
                      </p>
                    </div>

                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="text-slate-400 font-medium">Liquidity: </span>
                        <span className="text-slate-200">{c.liquidity_mechanism}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 font-medium">Credit Safety: </span>
                        <span className="text-slate-200">{c.credit_risk_level}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 font-medium">Interest Rate Risk: </span>
                        <span className="text-slate-200">{c.interest_rate_risk}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 font-medium">Taxation: </span>
                        <span className="text-slate-300 text-[11px]">{c.tax_treatment_summary}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 font-medium">Exit Penalty: </span>
                        <span className="text-slate-300 text-[11px]">{c.exit_load_or_penalty}</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800/80">
                    <p className="text-[11px] text-emerald-300 font-medium italic">
                      &quot;{c.suitability_verdict}&quot;
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Legal Disclaimer */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p>{result.disclaimer}</p>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800/60 space-y-3">
          <Sparkles className="w-8 h-8 text-emerald-400 mx-auto opacity-70" />
          <h3 className="text-sm font-bold text-slate-200">Compare Instruments for Your Goal</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Choose an amount and time horizon above to see how Liquid Mutual Funds compare with Fixed Deposits
            and Government/AAA Bonds in yield, liquidity, and post-2023 taxation.
          </p>
        </div>
      )}
    </div>
  );
};
