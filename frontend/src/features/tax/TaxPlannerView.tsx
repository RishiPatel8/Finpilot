import React, { useState } from 'react';
import {
  ReceiptIndianRupee,
  ShieldCheck,
  Info,
  CheckCircle2,
  TrendingDown,
  Sparkles,
  BookOpen
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { TaxComparisonResult } from '../../types';

export const TaxPlannerView: React.FC = () => {
  const [assessmentYear, setAssessmentYear] = useState('2025-26');
  const [taxpayerType, setTaxpayerType] = useState('salaried');
  const [grossSalary, setGrossSalary] = useState<number>(1450000);
  const [otherIncome, setOtherIncome] = useState<number>(50000);
  const [businessTurnover, setBusinessTurnover] = useState<number>(0);

  // Old Regime Deductions
  const [section80c, setSection80c] = useState<number>(150000);
  const [section80d, setSection80d] = useState<number>(25000);
  const [section80ccd1b, setSection80ccd1b] = useState<number>(50000);
  const [homeLoanInterest, setHomeLoanInterest] = useState<number>(200000);
  const [hraExemption, setHraExemption] = useState<number>(120000);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaxComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const calculateTax = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<TaxComparisonResult>('/tax/compare', {
        method: 'POST',
        body: JSON.stringify({
          assessment_year: assessmentYear,
          taxpayer_type: taxpayerType,
          gross_annual_salary: grossSalary,
          other_income: otherIncome,
          business_turnover: businessTurnover,
          section_80c: section80c,
          section_80d: section80d,
          section_80ccd_1b: section80ccd1b,
          home_loan_interest_24b: homeLoanInterest,
          hra_exemption: hraExemption,
        }),
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Tax calculation failed. Please check inputs.');
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
          <ReceiptIndianRupee className="w-5 h-5 text-emerald-400" />
          <h1 className="text-xl font-extrabold text-slate-100">Indian Income Tax Regime Comparator</h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Accurate comparison between New Concessional Regime (Section 115BAC) and Old Tax Regime for AY 2025-26 & AY 2024-25.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Form Column */}
        <div className="lg:col-span-5 space-y-5 p-5 rounded-2xl bg-slate-900/70 border border-slate-800">
          <h2 className="text-sm font-bold text-slate-100 flex items-center justify-between">
            <span>Income & Deductions Inputs</span>
            <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              Finance Act 2024 Verified
            </span>
          </h2>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Assessment Year</label>
              <select
                value={assessmentYear}
                onChange={(e) => setAssessmentYear(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="2025-26">AY 2025-26 (FY 2024-25)</option>
                <option value="2024-25">AY 2024-25 (FY 2023-24)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Taxpayer Category</label>
              <select
                value={taxpayerType}
                onChange={(e) => setTaxpayerType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="salaried">Salaried Employee</option>
                <option value="freelancer">Freelancer / Professional (44ADA)</option>
                <option value="business_owner">Business Owner (44AD)</option>
                <option value="senior_citizen">Senior Citizen (60+ yrs)</option>
              </select>
            </div>
          </div>

          <div className="space-y-3 pt-2 border-t border-slate-800/80">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                {taxpayerType === 'freelancer' || taxpayerType === 'business_owner' ? 'Annual Gross Receipts / Turnover (₹)' : 'Gross Annual Salary (₹)'}
              </label>
              <input
                type="number"
                value={taxpayerType === 'freelancer' || taxpayerType === 'business_owner' ? businessTurnover || '' : grossSalary || ''}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  if (taxpayerType === 'freelancer' || taxpayerType === 'business_owner') {
                    setBusinessTurnover(val);
                  } else {
                    setGrossSalary(val);
                  }
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Other Income (Interest, Dividends, etc.) (₹)</label>
              <input
                type="number"
                value={otherIncome || ''}
                onChange={(e) => setOtherIncome(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Old Regime Deductions Section */}
          <div className="space-y-3 pt-2 border-t border-slate-800/80">
            <p className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <span>Chapter VI-A Deductions (Old Regime Only)</span>
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Section 80C (Max ₹1.5L)</label>
                <input
                  type="number"
                  value={section80c || ''}
                  onChange={(e) => setSection80c(Number(e.target.value))}
                  placeholder="EPF, PPF, ELSS"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Section 80D (Health)</label>
                <input
                  type="number"
                  value={section80d || ''}
                  onChange={(e) => setSection80d(Number(e.target.value))}
                  placeholder="Self & Parents"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">NPS 80CCD(1B) (Max ₹50k)</label>
                <input
                  type="number"
                  value={section80ccd1b || ''}
                  onChange={(e) => setSection80ccd1b(Number(e.target.value))}
                  placeholder="Additional NPS"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Home Loan Int 24(b)</label>
                <input
                  type="number"
                  value={homeLoanInterest || ''}
                  onChange={(e) => setHomeLoanInterest(Number(e.target.value))}
                  placeholder="Max ₹2,00,000"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">HRA Exemption (Section 10(13A))</label>
              <input
                type="number"
                value={hraExemption || ''}
                onChange={(e) => setHraExemption(Number(e.target.value))}
                placeholder="Exempt rent allowance"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <button
            onClick={calculateTax}
            disabled={loading}
            className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-sm rounded-xl transition-all shadow-md shadow-emerald-500/20"
          >
            {loading ? 'Computing Regimes...' : 'Calculate & Compare Regimes'}
          </button>

          {error && (
            <p className="text-xs text-rose-400 bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20">
              {error}
            </p>
          )}
        </div>

        {/* Results Column */}
        <div className="lg:col-span-7 space-y-5">
          {result ? (
            <div className="space-y-5 animate-in fade-in duration-200">
              {/* Recommendation Banner */}
              <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/60 to-slate-900 border border-emerald-500/30 flex items-start gap-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs uppercase font-extrabold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      Recommended: {result.recommended_regime.toUpperCase()} REGIME
                    </span>
                    <span className="text-xs font-bold text-slate-300">
                      Save {formatINR(result.savings_amount)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                    {result.summary_explanation || (result as any).explanation}
                  </p>
                </div>
              </div>

              {/* Side-by-side cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* New Regime Card */}
                <div className={`p-4 rounded-2xl border transition-all ${
                  result.recommended_regime === 'new'
                    ? 'bg-slate-900/90 border-emerald-500/40 ring-1 ring-emerald-500/20'
                    : 'bg-slate-900/60 border-slate-800'
                }`}>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div>
                      <h3 className="text-sm font-bold text-slate-100">New Tax Regime</h3>
                      <p className="text-[10px] text-slate-400">Section 115BAC (Default)</p>
                    </div>
                    {result.recommended_regime === 'new' && (
                      <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-bold px-2 py-0.5 rounded">
                        Lowest Tax
                      </span>
                    )}
                  </div>

                  <div className="py-3 space-y-2 text-xs">
                    <div className="flex justify-between text-slate-400">
                      <span>Gross Income</span>
                      <span className="text-slate-200 font-mono">{formatINR(result.new_regime.gross_income || (result.new_regime as any).gross_total_income)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Standard Deduction</span>
                      <span className="text-emerald-400 font-mono">-{formatINR((result.new_regime as any).standard_deduction || 75000)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Taxable Income</span>
                      <span className="text-slate-200 font-mono font-semibold">{formatINR(result.new_regime.taxable_income)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Section 87A Rebate</span>
                      <span className="text-emerald-400 font-mono">-{formatINR(result.new_regime.rebate_87a)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Health & Ed Cess (4%)</span>
                      <span className="text-slate-200 font-mono">{formatINR(result.new_regime.cess || (result.new_regime as any).health_and_education_cess)}</span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800 flex justify-between items-baseline">
                    <span className="text-xs font-semibold text-slate-300">Total Tax Liability</span>
                    <span className="text-lg font-black text-emerald-400 font-mono">
                      {formatINR(result.new_regime.total_tax_liability)}
                    </span>
                  </div>
                </div>

                {/* Old Regime Card */}
                <div className={`p-4 rounded-2xl border transition-all ${
                  result.recommended_regime === 'old'
                    ? 'bg-slate-900/90 border-emerald-500/40 ring-1 ring-emerald-500/20'
                    : 'bg-slate-900/60 border-slate-800'
                }`}>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div>
                      <h3 className="text-sm font-bold text-slate-100">Old Tax Regime</h3>
                      <p className="text-[10px] text-slate-400">Regular Slabs + Deductions</p>
                    </div>
                    {result.recommended_regime === 'old' && (
                      <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-bold px-2 py-0.5 rounded">
                        Lowest Tax
                      </span>
                    )}
                  </div>

                  <div className="py-3 space-y-2 text-xs">
                    <div className="flex justify-between text-slate-400">
                      <span>Gross Income</span>
                      <span className="text-slate-200 font-mono">{formatINR(result.old_regime.gross_income || (result.old_regime as any).gross_total_income)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Total Deductions</span>
                      <span className="text-emerald-400 font-mono">-{formatINR(result.old_regime.total_deductions)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Taxable Income</span>
                      <span className="text-slate-200 font-mono font-semibold">{formatINR(result.old_regime.taxable_income)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Section 87A Rebate</span>
                      <span className="text-emerald-400 font-mono">-{formatINR(result.old_regime.rebate_87a)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Health & Ed Cess (4%)</span>
                      <span className="text-slate-200 font-mono">{formatINR(result.old_regime.cess || (result.old_regime as any).health_and_education_cess)}</span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800 flex justify-between items-baseline">
                    <span className="text-xs font-semibold text-slate-300">Total Tax Liability</span>
                    <span className="text-lg font-black text-slate-100 font-mono">
                      {formatINR(result.old_regime.total_tax_liability)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Citations Box */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs space-y-2">
                <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
                  <BookOpen className="w-4 h-4 text-emerald-400" />
                  <span>Statutory Citations & Verification Notes</span>
                </div>
                <ul className="list-disc list-inside text-[11px] text-slate-400 space-y-1">
                  {(result.citations || (result.new_regime as any).official_citations || []).map((cite: string, idx: number) => (
                    <li key={idx}>{cite}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800/60 space-y-3">
              <Sparkles className="w-8 h-8 text-emerald-400 mx-auto opacity-70" />
              <h3 className="text-sm font-bold text-slate-200">Ready to Compare Regimes</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Adjust your salary and deductions on the left and click &apos;Calculate & Compare Regimes&apos; to view
                instant mathematical calculations and official statutory references.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
