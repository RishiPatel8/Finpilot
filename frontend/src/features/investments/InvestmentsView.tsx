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
  Sparkles,
  Info,
  Layers,
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { InvestmentCompareResponse, InvestmentOptionComparison } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';

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
      {/* Page Header */}
      <PageHeader
        title="Liquid Funds vs Bonds vs FDs"
        description="Statutory investment comparator: Evaluate capital preservation, T+1 liquidity, Section 50AA tax treatment, and interest rate sensitivity."
        icon={<TrendingUp className="w-4 h-4 text-[#6478E8]" />}
        badge={
          <Badge variant="blue" size="sm">
            SEBI & Tax Norms
          </Badge>
        }
      />

      {/* Input Parameters Box */}
      <Card className="space-y-4">
        <h2 className="text-base font-bold text-[#172033]">
          Investment Scenario Parameters
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-[#172033] mb-1">
              Investment Amount (₹)
            </label>
            <input
              type="number"
              value={amount || ''}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#172033] mb-1">
              Time Horizon (Months)
            </label>
            <select
              value={months}
              onChange={(e) => setMonths(Number(e.target.value))}
              className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-medium focus:outline-none focus:border-[#6478E8] transition-all"
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
            <label className="block text-xs font-semibold text-[#172033] mb-1">
              Your Income Tax Slab (%)
            </label>
            <select
              value={taxSlab}
              onChange={(e) => setTaxSlab(Number(e.target.value))}
              className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-medium focus:outline-none focus:border-[#6478E8] transition-all"
            >
              <option value={0}>0% (Exempt)</option>
              <option value={5}>5% Slab</option>
              <option value={10}>10% Slab</option>
              <option value={15}>15% Slab</option>
              <option value={20}>20% Slab</option>
              <option value={30}>30% Slab (Highest)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#172033] mb-1">
              Lock-in Flexibility
            </label>
            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="canLock"
                checked={canLock}
                onChange={(e) => setCanLock(e.target.checked)}
                className="w-4 h-4 rounded text-[#6478E8] focus:ring-[#6478E8] border-[#E6EAF0]"
              />
              <label htmlFor="canLock" className="text-xs text-[#697386] cursor-pointer">
                Can lock funds until maturity
              </label>
            </div>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <Button
            variant="primary"
            size="md"
            onClick={handleCompare}
            loading={loading}
            icon={<Sparkles className="w-3.5 h-3.5" />}
          >
            {loading ? 'Comparing Instruments...' : 'Compare Instruments'}
          </Button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
            {error}
          </div>
        )}
      </Card>

      {/* Comparison Results */}
      {result && (
        <div className="space-y-5 animate-in fade-in duration-200">
          {/* Recommendation Banner */}
          <div className="p-5 rounded-2xl bg-[#E5F7EF]/70 border border-[#16865C]/20 flex items-start gap-3.5">
            <div className="w-8 h-8 rounded-xl bg-[#E5F7EF] text-[#16865C] flex items-center justify-center shrink-0 mt-0.5">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="mint" size="sm" className="font-extrabold uppercase">
                  Recommended: {result.top_recommendation}
                </Badge>
                <span className="text-xs font-semibold text-[#697386]">
                  Horizon: {result.time_horizon_months} Months
                </span>
              </div>
              <p className="text-xs sm:text-sm text-[#172033] font-medium leading-relaxed">
                {result.rationale}
              </p>
            </div>
          </div>

          {/* Instrument Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {result.comparisons.map((opt: InvestmentOptionComparison, idx: number) => {
              const isRecommended = opt.display_name === result.top_recommendation;
              return (
                <Card
                  key={idx}
                  className={`space-y-4 flex flex-col justify-between ${
                    isRecommended
                      ? 'border-[#16865C]/40 ring-1 ring-[#16865C]/20'
                      : ''
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between pb-2.5 border-b border-[#E6EAF0]">
                      <div>
                        <h3 className="text-sm font-bold text-[#172033]">{opt.display_name}</h3>
                        <span className="text-[11px] text-[#697386] capitalize">
                          {opt.category.replace('_', ' ')}
                        </span>
                      </div>
                      {isRecommended && (
                        <Badge variant="mint" size="sm">
                          Optimal
                        </Badge>
                      )}
                    </div>

                    {/* Return & Value Details */}
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Indicative Annual Yield:</span>
                        <span className="font-bold text-[#172033] tabular-nums">
                          ~{opt.indicative_annual_yield_pct}% p.a.*
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Projected Maturity Value:</span>
                        <span className="font-extrabold text-[#6478E8] tabular-nums">
                          {formatINR(opt.projected_maturity_value)}
                        </span>
                      </div>
                      <div className="flex justify-between text-[#16865C]">
                        <span>Inflation-Adjusted Value:</span>
                        <span className="font-semibold tabular-nums">
                          {formatINR(opt.inflation_adjusted_value)}
                        </span>
                      </div>
                      <div className="flex justify-between text-[#697386]">
                        <span>Horizon Fit:</span>
                        <span className="tabular-nums font-medium">
                          {opt.recommended_time_horizon}
                        </span>
                      </div>
                    </div>

                    {/* Operational Attributes */}
                    <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E6EAF0] space-y-1.5 text-[11px]">
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Credit Risk:</span>
                        <span className="font-semibold text-[#172033] capitalize">
                          {opt.credit_risk_level}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#697386]">Liquidity:</span>
                        <span className="font-semibold text-[#172033]">{opt.liquidity_mechanism}</span>
                      </div>
                      <div className="text-[10px] text-[#697386] pt-1 border-t border-[#E6EAF0]">
                        Tax: {opt.tax_treatment_summary}
                      </div>
                    </div>

                    {/* Pros and Cons */}
                    <div className="space-y-1 text-xs">
                      {opt.pros && opt.pros[0] && (
                        <p className="text-[#16865C] font-semibold text-[11px]">
                          ✓ {opt.pros[0]}
                        </p>
                      )}
                      {opt.cons && opt.cons[0] && (
                        <p className="text-[#697386] text-[11px]">
                          • {opt.cons[0]}
                        </p>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Statutory Disclaimer Box */}
          <div className="p-4 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] text-[11px] text-[#697386] space-y-1 leading-relaxed">
            <p className="font-bold text-[#172033] flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-[#6478E8]" />
              <span>Statutory Estimate Notice & Regulatory Disclosure</span>
            </p>
            <p>{result.disclaimer}</p>
            <p className="italic text-[10px] text-[#697386]/80 pt-1">
              *Expected yields are historical / indicative parameters for comparison models only and do not constitute guaranteed returns.
            </p>
          </div>
        </div>
      )}

    </div>
  );
};
