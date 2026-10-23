import React, { useState } from 'react';
import {
  ReceiptIndianRupee,
  ShieldCheck,
  Info,
  CheckCircle2,
  TrendingDown,
  Sparkles,
  BookOpen,
  ArrowRight,
  Calculator,
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { TaxComparisonResult } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';

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
      {/* Page Header */}
      <PageHeader
        title="Income Tax Regime Comparator"
        description="Statutory tax calculator comparing New Concessional Regime (Section 115BAC) vs Old Regime for AY 2025-26 (Finance Act 2024) and AY 2024-25."
        icon={<ReceiptIndianRupee className="w-4 h-4 text-[#6478E8]" />}
        badge={
          <Badge variant="lavender" size="sm">
            AY {assessmentYear} Verified
          </Badge>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Form Column */}
        <Card className="lg:col-span-5 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[#172033]">
              Income & Deductions
            </h2>
            <Badge variant="mint" size="sm">
              Section 288B Rounded
            </Badge>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1">
                Assessment Year
              </label>
              <select
                value={assessmentYear}
                onChange={(e) => setAssessmentYear(e.target.value)}
                className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-medium focus:outline-none focus:border-[#6478E8] transition-all"
              >
                <option value="2025-26">AY 2025-26 (FY 2024-25)</option>
                <option value="2024-25">AY 2024-25 (FY 2023-24)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1">
                Taxpayer Profile
              </label>
              <select
                value={taxpayerType}
                onChange={(e) => setTaxpayerType(e.target.value)}
                className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-medium focus:outline-none focus:border-[#6478E8] transition-all"
              >
                <option value="salaried">Salaried Employee</option>
                <option value="freelancer">Freelancer (44ADA)</option>
                <option value="business_owner">Business Owner (44AD)</option>
                <option value="senior_citizen">Senior Citizen (60+ yrs)</option>
              </select>
            </div>
          </div>

          {/* Income Inputs */}
          <div className="space-y-3.5 pt-3 border-t border-[#E6EAF0]">
            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1">
                {taxpayerType === 'freelancer' || taxpayerType === 'business_owner'
                  ? 'Annual Gross Receipts / Turnover (₹)'
                  : 'Gross Annual Salary (₹)'}
              </label>
              <input
                type="number"
                value={
                  taxpayerType === 'freelancer' || taxpayerType === 'business_owner'
                    ? businessTurnover || ''
                    : grossSalary || ''
                }
                onChange={(e) => {
                  const val = Number(e.target.value);
                  if (taxpayerType === 'freelancer' || taxpayerType === 'business_owner') {
                    setBusinessTurnover(val);
                  } else {
                    setGrossSalary(val);
                  }
                }}
                className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172033] mb-1">
                Other Income (Interest, Dividends) (₹)
              </label>
              <input
                type="number"
                value={otherIncome || ''}
                onChange={(e) => setOtherIncome(Number(e.target.value))}
                className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
              />
            </div>
          </div>

          {/* Old Regime Deductions Section */}
          <div className="space-y-3 pt-3 border-t border-[#E6EAF0]">
            <p className="text-xs font-bold text-[#172033] uppercase tracking-wider">
              Chapter VI-A Deductions (Old Regime)
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Section 80C (Max ₹1.5L)
                </label>
                <input
                  type="number"
                  value={section80c || ''}
                  onChange={(e) => setSection80c(Number(e.target.value))}
                  placeholder="EPF, PPF, ELSS"
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-1.5 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Section 80D (Health)
                </label>
                <input
                  type="number"
                  value={section80d || ''}
                  onChange={(e) => setSection80d(Number(e.target.value))}
                  placeholder="Self & Parents"
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-1.5 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  NPS 80CCD(1B) (Max ₹50k)
                </label>
                <input
                  type="number"
                  value={section80ccd1b || ''}
                  onChange={(e) => setSection80ccd1b(Number(e.target.value))}
                  placeholder="Tier-1 NPS"
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-1.5 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Home Loan Int 24(b)
                </label>
                <input
                  type="number"
                  value={homeLoanInterest || ''}
                  onChange={(e) => setHomeLoanInterest(Number(e.target.value))}
                  placeholder="Max ₹2,00,000"
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-1.5 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                HRA Exemption (Section 10(13A))
              </label>
              <input
                type="number"
                value={hraExemption || ''}
                onChange={(e) => setHraExemption(Number(e.target.value))}
                placeholder="Exempt rent allowance"
                className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-1.5 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
              />
            </div>
          </div>

          <Button
            variant="primary"
            size="lg"
            onClick={calculateTax}
            loading={loading}
            className="w-full"
            icon={<Calculator className="w-4 h-4" />}
          >
            {loading ? 'Evaluating Slabs...' : 'Calculate & Compare Regimes'}
          </Button>

          {error && (
            <div className="p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
              {error}
            </div>
          )}
        </Card>

        {/* Results Column */}
        <div className="lg:col-span-7 space-y-5">
          {result ? (
            <div className="space-y-5 animate-in fade-in duration-200">
              {/* Recommendation Banner */}
              <div className="p-5 rounded-2xl bg-[#E5F7EF]/70 border border-[#16865C]/20 flex items-start gap-3.5">
                <div className="w-8 h-8 rounded-xl bg-[#E5F7EF] text-[#16865C] flex items-center justify-center shrink-0 mt-0.5">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="mint" size="sm" className="font-extrabold uppercase">
                      Recommended: {result.recommended_regime} Regime
                    </Badge>
                    <span className="text-xs font-bold text-[#16865C]">
                      Save {formatINR(result.savings_amount)} annually
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm text-[#172033] font-medium leading-relaxed">
                    Under AY {result.assessment_year}, selecting the{' '}
                    <strong>{result.recommended_regime} Regime</strong> minimizes your total statutory tax liability
                    to <strong>{formatINR(result.recommended_regime.toLowerCase() === 'new' ? result.new_regime.total_tax_liability : result.old_regime.total_tax_liability)}</strong>.
                  </p>
                </div>
              </div>

              {/* Side-by-Side Comparison Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* New Regime Card */}
                <Card
                  className={`space-y-4 ${
                    result.recommended_regime.toLowerCase() === 'new'
                      ? 'border-[#16865C]/40 ring-1 ring-[#16865C]/20'
                      : ''
                  }`}
                >
                  <div className="flex items-center justify-between pb-2 border-b border-[#E6EAF0]">
                    <div>
                      <h3 className="text-sm font-bold text-[#172033]">New Regime (115BAC)</h3>
                      <p className="text-[11px] text-[#697386]">Concessional Slabs</p>
                    </div>
                    {result.recommended_regime.toLowerCase() === 'new' && (
                      <Badge variant="mint" size="sm">
                        Optimal
                      </Badge>
                    )}
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-[#697386]">Gross Total Income:</span>
                      <span className="font-semibold tabular-nums">{formatINR(result.new_regime.gross_income)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#697386]">Total Deductions:</span>
                      <span className="text-[#16865C] font-semibold tabular-nums">
                        - {formatINR(result.new_regime.total_deductions)}
                      </span>
                    </div>
                    <div className="flex justify-between font-bold pt-1 border-t border-[#F1F4F9]">
                      <span className="text-[#172033]">Taxable Income:</span>
                      <span className="text-[#172033] tabular-nums">{formatINR(result.new_regime.taxable_income)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#697386]">Tax Before Rebate:</span>
                      <span className="tabular-nums">{formatINR(result.new_regime.tax_before_rebate)}</span>
                    </div>
                    {result.new_regime.rebate_87a > 0 && (
                      <div className="flex justify-between text-[#16865C]">
                        <span>Section 87A Rebate:</span>
                        <span className="tabular-nums">- {formatINR(result.new_regime.rebate_87a)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-[#697386]">
                      <span>Health & Edu Cess (4%):</span>
                      <span className="tabular-nums">{formatINR(result.new_regime.cess)}</span>
                    </div>
                    <div className="flex justify-between text-sm font-extrabold pt-2 border-t border-[#E6EAF0] text-[#172033]">
                      <span>Net Tax Payable:</span>
                      <span className="tabular-nums text-[#6478E8]">{formatINR(result.new_regime.total_tax_liability)}</span>
                    </div>
                    <div className="text-[11px] text-[#697386] text-right">
                      Effective rate: <strong>{result.new_regime.effective_rate}%</strong>
                    </div>
                  </div>
                </Card>

                {/* Old Regime Card */}
                <Card
                  className={`space-y-4 ${
                    result.recommended_regime.toLowerCase() === 'old'
                      ? 'border-[#16865C]/40 ring-1 ring-[#16865C]/20'
                      : ''
                  }`}
                >
                  <div className="flex items-center justify-between pb-2 border-b border-[#E6EAF0]">
                    <div>
                      <h3 className="text-sm font-bold text-[#172033]">Old Tax Regime</h3>
                      <p className="text-[11px] text-[#697386]">With Chapter VI-A & HRA</p>
                    </div>
                    {result.recommended_regime.toLowerCase() === 'old' && (
                      <Badge variant="mint" size="sm">
                        Optimal
                      </Badge>
                    )}
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-[#697386]">Gross Total Income:</span>
                      <span className="font-semibold tabular-nums">{formatINR(result.old_regime.gross_income)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#697386]">Total Deductions:</span>
                      <span className="text-[#16865C] font-semibold tabular-nums">
                        - {formatINR(result.old_regime.total_deductions)}
                      </span>
                    </div>
                    <div className="flex justify-between font-bold pt-1 border-t border-[#F1F4F9]">
                      <span className="text-[#172033]">Taxable Income:</span>
                      <span className="text-[#172033] tabular-nums">{formatINR(result.old_regime.taxable_income)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#697386]">Tax Before Rebate:</span>
                      <span className="tabular-nums">{formatINR(result.old_regime.tax_before_rebate)}</span>
                    </div>
                    {result.old_regime.rebate_87a > 0 && (
                      <div className="flex justify-between text-[#16865C]">
                        <span>Section 87A Rebate:</span>
                        <span className="tabular-nums">- {formatINR(result.old_regime.rebate_87a)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-[#697386]">
                      <span>Health & Edu Cess (4%):</span>
                      <span className="tabular-nums">{formatINR(result.old_regime.cess)}</span>
                    </div>
                    <div className="flex justify-between text-sm font-extrabold pt-2 border-t border-[#E6EAF0] text-[#172033]">
                      <span>Net Tax Payable:</span>
                      <span className="tabular-nums text-[#172033]">{formatINR(result.old_regime.total_tax_liability)}</span>
                    </div>
                    <div className="text-[11px] text-[#697386] text-right">
                      Effective rate: <strong>{result.old_regime.effective_rate}%</strong>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Calculation Notes & Statutory References */}
              <div className="p-4 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] space-y-2 text-xs text-[#697386]">
                <p className="font-bold text-[#172033] flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4 text-[#6478E8]" />
                  <span>Statutory Notes & Formula Citations</span>
                </p>
                {result.summary_explanation && (
                  <p className="text-[11px] leading-relaxed text-[#172033]">
                    {result.summary_explanation}
                  </p>
                )}
                {result.citations && result.citations.length > 0 && (
                  <ul className="list-disc list-inside space-y-1 text-[11px] leading-relaxed">
                    {result.citations.map((cite: string, idx: number) => (
                      <li key={idx}>{cite}</li>
                    ))}
                  </ul>
                )}
              </div>

            </div>
          ) : (
            <Card className="p-10 sm:p-14 text-center space-y-3 flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-2xl bg-[#EEF0FF] text-[#6478E8] flex items-center justify-center shadow-sm">
                <ReceiptIndianRupee className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#172033]">
                Ready to Compare Income Tax Regimes
              </h3>
              <p className="text-xs sm:text-sm text-[#697386] max-w-md leading-relaxed">
                Enter your salary, business turnover, or Chapter VI-A deductions on the left and click Calculate to receive an instant, verified comparison under Finance Act statutory rules.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
