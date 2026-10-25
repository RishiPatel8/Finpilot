import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  Plus,
  Trash2,
  TrendingDown,
  ShieldAlert,
  ArrowRight,
  Flame,
  Snowflake,
  Calculator,
  CheckCircle2,
  DollarSign,
} from 'lucide-react';
import { apiRequest, getAuthToken } from '../../services/api';
import { Liability, DebtRepaymentPlan } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';
import { KnowMore } from '../../components/KnowMore';

export const DebtManagementView: React.FC = () => {
  const [liabilities, setLiabilities] = useState<Liability[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Debt Form State
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [name, setName] = useState('');
  const [principal, setPrincipal] = useState<number | ''>('');
  const [interestRate, setInterestRate] = useState<number | ''>('');
  const [monthlyEmi, setMonthlyEmi] = useState<number | ''>('');
  const [tenureMonths, setTenureMonths] = useState<number | ''>('');
  const [remainingMonths, setRemainingMonths] = useState<number | ''>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Repayment Plan State
  const [extraPayment, setExtraPayment] = useState<number>(5000);
  const [repaymentPlan, setRepaymentPlan] = useState<DebtRepaymentPlan | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const fetchLiabilities = async () => {
    const token = getAuthToken();
    if (!token) {
      setLiabilities([]);
      setRepaymentPlan(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const data = await apiRequest<Liability[]>('/liabilities');
      setLiabilities(data);
      if (data.length > 0) {
        fetchPlan(data, extraPayment);
      } else {
        setRepaymentPlan(null);
      }
    } catch (err: any) {
      console.error('Failed to load liabilities:', err);
    } finally {
      setLoading(false);
    }
  };


  const fetchPlan = async (currentDebts: Liability[], extra: number) => {
    if (currentDebts.length === 0) return;
    setIsCalculating(true);
    try {
      const plan = await apiRequest<DebtRepaymentPlan>('/liabilities/repayment-plan', {
        method: 'POST',
        body: JSON.stringify({ extra_monthly_payment: extra }),
      });
      setRepaymentPlan(plan);
    } catch (err) {
      console.error('Failed to calculate debt plan:', err);
    } finally {
      setIsCalculating(false);
    }
  };

  useEffect(() => {
    fetchLiabilities();
  }, []);

  const handleAddDebt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !principal || !interestRate || !monthlyEmi) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await apiRequest<Liability>('/liabilities', {
        method: 'POST',
        body: JSON.stringify({
          name,
          principal: Number(principal),
          interest_rate: Number(interestRate),
          monthly_emi: Number(monthlyEmi),
          tenure_months: Number(tenureMonths || 36),
          remaining_months: Number(remainingMonths || tenureMonths || 36),
        }),
      });

      setName('');
      setPrincipal('');
      setInterestRate('');
      setMonthlyEmi('');
      setTenureMonths('');
      setRemainingMonths('');
      setIsAddOpen(false);
      await fetchLiabilities();
    } catch (err: any) {
      setError(err.message || 'Failed to add debt record.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteDebt = async (id: string) => {
    try {
      await apiRequest(`/liabilities/${id}`, { method: 'DELETE' });
      await fetchLiabilities();
    } catch (err: any) {
      alert(err.message || 'Failed to delete liability.');
    }
  };

  const totalPrincipal = liabilities.reduce((sum, l) => sum + Number(l.principal), 0);
  const totalEmi = liabilities.reduce((sum, l) => sum + Number(l.monthly_emi), 0);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Page Header */}
      <PageHeader
        title="Debt Management & Accelerated Payoff"
        description="Audit loans and credit cards, eliminate high-interest liabilities, and compare Debt Avalanche vs Debt Snowball strategies."
        icon={<CreditCard className="w-4 h-4 text-[#6478E8]" />}
        badge={<KnowMore termId="debt_payoff" variant="badge" label="About Payoff Strategies" />}
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#697386] font-medium">Total Outstanding Debt</span>
            <KnowMore termId="net_worth" />
          </div>
          <p className="text-2xl font-black text-[#172033] font-mono tabular-nums">
            {formatINR(totalPrincipal)}
          </p>
          <p className="text-[11px] text-[#697386]">Across {liabilities.length} active liabilities</p>
        </Card>

        <Card className="space-y-1">
          <span className="text-xs text-[#697386] font-medium">Total Monthly EMI Commitment</span>
          <p className="text-2xl font-black text-[#D9485F] font-mono tabular-nums">
            {formatINR(totalEmi)} <span className="text-xs font-normal text-[#697386]">/ mo</span>
          </p>
          <p className="text-[11px] text-[#697386]">Fixed monthly obligation</p>
        </Card>

        <Card className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#697386] font-medium">Recommended Strategy</span>
            <KnowMore termId="debt_payoff" />
          </div>
          <p className="text-xl font-bold text-[#6478E8] flex items-center gap-1.5 pt-1">
            <Flame className="w-4 h-4 text-[#D9485F]" />
            <span>Debt Avalanche</span>
          </p>
          <p className="text-[11px] text-[#697386]">Minimizes total interest paid</p>
        </Card>
      </div>

      {/* Liabilities List and Action Bar */}
      <Card className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[#172033]">Active Loans & Liabilities</h2>
            <p className="text-xs text-[#697386]">Track principal, interest rates, and remaining EMIs.</p>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddOpen(!isAddOpen)}
            icon={<Plus className="w-3.5 h-3.5" />}
          >
            {isAddOpen ? 'Close Form' : 'Add Loan / Debt'}
          </Button>
        </div>

        {/* Add Debt Modal / Accordion */}
        {isAddOpen && (
          <form
            onSubmit={handleAddDebt}
            className="p-4 sm:p-5 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] space-y-4 animate-in fade-in duration-150"
          >
            <h3 className="text-xs font-bold text-[#172033] uppercase tracking-wider">
              Add New Liability
            </h3>

            {error && (
              <div className="p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="text-xs font-semibold text-[#172033] block mb-1">
                  Liability Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g. HDFC Home Loan, Axis Card"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#172033] block mb-1">
                  Outstanding Principal (₹) *
                </label>
                <input
                  type="number"
                  placeholder="e.g. 500000"
                  value={principal}
                  onChange={(e) => setPrincipal(Number(e.target.value))}
                  required
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#172033] block mb-1">
                  Annual Interest Rate (% p.a.) *
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g. 8.5 or 42.0"
                  value={interestRate}
                  onChange={(e) => setInterestRate(Number(e.target.value))}
                  required
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#172033] block mb-1">
                  Monthly EMI (₹) *
                </label>
                <input
                  type="number"
                  placeholder="e.g. 15000"
                  value={monthlyEmi}
                  onChange={(e) => setMonthlyEmi(Number(e.target.value))}
                  required
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#172033] block mb-1">
                  Total Tenure (Months)
                </label>
                <input
                  type="number"
                  placeholder="e.g. 60"
                  value={tenureMonths}
                  onChange={(e) => setTenureMonths(Number(e.target.value))}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#172033] block mb-1">
                  Remaining Months
                </label>
                <input
                  type="number"
                  placeholder="e.g. 42"
                  value={remainingMonths}
                  onChange={(e) => setRemainingMonths(Number(e.target.value))}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#6478E8]"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                type="button"
                onClick={() => setIsAddOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                type="submit"
                loading={isSubmitting}
                disabled={isSubmitting}
              >
                Save Liability
              </Button>
            </div>
          </form>
        )}

        {/* Liabilities Table */}
        <div className="overflow-x-auto -mx-5 sm:mx-0">
          <table className="w-full text-left text-xs text-[#172033]">
            <thead className="bg-[#F6F8FC] text-[#697386] uppercase text-[10px] tracking-wider border-y border-[#E6EAF0]">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Loan / Debt Name</th>
                <th className="py-2.5 px-4 font-semibold text-right">Outstanding Principal</th>
                <th className="py-2.5 px-4 font-semibold text-center">Interest Rate</th>
                <th className="py-2.5 px-4 font-semibold text-right">Monthly EMI</th>
                <th className="py-2.5 px-4 font-semibold text-center">Remaining</th>
                <th className="py-2.5 px-4 font-semibold text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E6EAF0] font-medium">
              {liabilities.length > 0 ? (
                liabilities.map((l) => (
                  <tr key={l.id} className="hover:bg-[#F6F8FC] transition-colors">
                    <td className="py-3 px-4 font-semibold text-[#172033]">{l.name}</td>
                    <td className="py-3 px-4 text-right font-mono font-bold tabular-nums">
                      {formatINR(Number(l.principal))}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge
                        variant={Number(l.interest_rate) > 15 ? 'danger' : 'neutral'}
                        size="sm"
                      >
                        {Number(l.interest_rate)}% p.a.
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-[#D9485F] tabular-nums">
                      {formatINR(Number(l.monthly_emi))}
                    </td>
                    <td className="py-3 px-4 text-center text-[#697386] tabular-nums">
                      {l.remaining_months} mos
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleDeleteDebt(l.id)}
                        className="text-[#697386] hover:text-[#D9485F] hover:bg-[#FDF2F4] p-1.5 rounded-lg transition-colors"
                        title="Delete liability"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[#697386]">
                    No debts or liabilities recorded. Add your loans to run repayment optimization.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Payoff Strategy Optimizer (Avalanche vs Snowball) */}
      {liabilities.length > 0 && repaymentPlan && (
        <Card className="space-y-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
                <Calculator className="w-4 h-4 text-[#6478E8]" />
                <span>Accelerated Debt Payoff Strategy</span>
              </h2>
              <p className="text-xs text-[#697386]">
                Compare the mathematical savings of Debt Avalanche vs psychological momentum of Debt Snowball.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="text-[#697386] font-medium">Extra Monthly Prepayment:</span>
              <div className="relative w-32">
                <span className="absolute left-2.5 top-1.5 text-xs text-[#697386]">₹</span>
                <input
                  type="number"
                  step="1000"
                  value={extraPayment}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setExtraPayment(val);
                    fetchPlan(liabilities, val);
                  }}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl pl-6 pr-2 py-1 text-xs font-mono font-bold focus:outline-none focus:border-[#6478E8]"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Avalanche Strategy */}
            <div className="p-4 rounded-2xl bg-[#EEF0FF]/50 border border-[#EEF0FF] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#6478E8] flex items-center gap-1.5 uppercase tracking-wider">
                  <Flame className="w-4 h-4 text-[#D9485F]" />
                  <span>Debt Avalanche (Optimal Interest)</span>
                </span>
                <Badge variant="mint" size="sm">
                  Recommended
                </Badge>
              </div>

              <p className="text-xs text-[#697386] leading-relaxed">
                Pay minimum EMIs on all loans, then direct all extra cash to the liability with the{' '}
                <strong>highest interest rate</strong>.
              </p>

              <div className="space-y-1.5 pt-2">
                <span className="text-[11px] font-bold text-[#172033] block">Payoff Priority Order:</span>
                {repaymentPlan.avalanche_priority.map((name, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-white border border-[#E6EAF0] text-xs"
                  >
                    <span className="font-semibold text-[#172033]">
                      #{idx + 1} {name}
                    </span>
                    <Badge variant={idx === 0 ? 'lavender' : 'neutral'} size="sm">
                      {idx === 0 ? 'Target First' : 'Minimum EMI'}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>

            {/* Snowball Strategy */}
            <div className="p-4 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#2B6CB0] flex items-center gap-1.5 uppercase tracking-wider">
                  <Snowflake className="w-4 h-4 text-[#2B6CB0]" />
                  <span>Debt Snowball (Behavioral Wins)</span>
                </span>
                <Badge variant="blue" size="sm">
                  Psychological
                </Badge>
              </div>

              <p className="text-xs text-[#697386] leading-relaxed">
                Pay minimum EMIs on all loans, then direct all extra cash to the liability with the{' '}
                <strong>smallest balance</strong> to close accounts rapidly.
              </p>

              <div className="space-y-1.5 pt-2">
                <span className="text-[11px] font-bold text-[#172033] block">Payoff Priority Order:</span>
                {repaymentPlan.snowball_priority.map((name, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-white border border-[#E6EAF0] text-xs"
                  >
                    <span className="font-semibold text-[#172033]">
                      #{idx + 1} {name}
                    </span>
                    <Badge variant={idx === 0 ? 'blue' : 'neutral'} size="sm">
                      {idx === 0 ? 'Target First' : 'Minimum EMI'}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
