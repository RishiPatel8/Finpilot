import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Shield,
  Briefcase,
  IndianRupee,
  Compass,
} from 'lucide-react';
import { apiRequest } from '../services/api';
import { Card, Badge, Button } from './ui';
import { User, FinancialProfile } from '../types';

interface OnboardingModalProps {
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
  onComplete: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  user,
  onClose,
  onComplete,
}) => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Profile Form State
  const [role, setRole] = useState(user?.role || 'salaried');
  const [age, setAge] = useState<number>(28);
  const [dependents, setDependents] = useState<number>(0);
  const [monthlyIncome, setMonthlyIncome] = useState<number>(125000);
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(55000);
  const [emergencyTargetMonths, setEmergencyTargetMonths] = useState<number>(6);
  const [riskTolerance, setRiskTolerance] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate');
  const [taxRegime, setTaxRegime] = useState<'auto' | 'new' | 'old'>('auto');

  if (!isOpen) return null;

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    try {
      await apiRequest('/profile', {
        method: 'PUT',
        body: JSON.stringify({
          age,
          dependents,
          monthly_income: monthlyIncome,
          monthly_expenses: monthlyExpenses,
          risk_tolerance: riskTolerance,
          emergency_fund_target_months: emergencyTargetMonths,
          tax_regime_preference: taxRegime,
        }),
      });
      onComplete();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#172033]/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-white rounded-3xl border border-[#E6EAF0] shadow-2xl p-6 sm:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#EEF0FF] flex items-center justify-center text-[#6478E8]">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-[#172033]">
                Welcome to FinPilot, {user?.full_name?.split(' ')[0] || 'Planner'}!
              </h2>
              <p className="text-xs text-[#697386]">Step {step} of 3: Financial Foundation Setup</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-xs text-[#697386] hover:text-[#172033] font-medium"
          >
            Skip for now
          </button>
        </div>

        {/* Step Progress Bar */}
        <div className="flex items-center gap-2">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                s <= step ? 'bg-[#6478E8]' : 'bg-[#E6EAF0]'
              }`}
            />
          ))}
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
            {error}
          </div>
        )}

        {/* Step 1: Personal & Career Profile */}
        {step === 1 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div>
              <label className="text-xs font-semibold text-[#172033] block mb-1.5">
                Primary Income Source / Occupation
              </label>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {[
                  { id: 'salaried', label: 'Salaried Employee' },
                  { id: 'freelancer', label: 'Freelancer / Consultant' },
                  { id: 'business_owner', label: 'Business Owner' },
                  { id: 'student', label: 'Student / Early Career' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setRole(item.id as any)}
                    className={`p-3 rounded-xl border text-left font-medium transition-all ${
                      role === item.id
                        ? 'border-[#6478E8] bg-[#EEF0FF] text-[#6478E8] font-bold'
                        : 'border-[#E6EAF0] text-[#172033] hover:bg-[#F6F8FC]'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-[#172033] block mb-1">
                  Age (Years)
                </label>
                <input
                  type="number"
                  min="18"
                  max="100"
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                  className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-mono focus:outline-none focus:border-[#6478E8]"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-[#172033] block mb-1">
                  Financial Dependents
                </label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={dependents}
                  onChange={(e) => setDependents(Number(e.target.value))}
                  className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-mono focus:outline-none focus:border-[#6478E8]"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Income & Living Expenses */}
        {step === 2 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div>
              <label className="text-xs font-semibold text-[#172033] block mb-1">
                Net Monthly Take-Home Income (₹)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-xs text-[#697386]">₹</span>
                <input
                  type="number"
                  step="5000"
                  value={monthlyIncome}
                  onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                  className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl pl-7 pr-3 py-2 text-xs text-[#172033] font-mono font-bold focus:outline-none focus:border-[#6478E8]"
                />
              </div>
              <p className="text-[11px] text-[#697386] mt-1">
                Post-tax monthly bank credit from salary, clients, or business.
              </p>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#172033] block mb-1">
                Average Monthly Living Expenses (₹)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-xs text-[#697386]">₹</span>
                <input
                  type="number"
                  step="2000"
                  value={monthlyExpenses}
                  onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                  className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl pl-7 pr-3 py-2 text-xs text-[#172033] font-mono font-bold focus:outline-none focus:border-[#6478E8]"
                />
              </div>
              <p className="text-[11px] text-[#697386] mt-1">
                Rent, utilities, groceries, EMIs, dining, and discretionary costs.
              </p>
            </div>

            <div className="p-3 rounded-2xl bg-[#E5F7EF] border border-[#E5F7EF] text-xs flex justify-between items-center">
              <span className="text-[#16865C] font-semibold">Estimated Monthly Cash Surplus:</span>
              <span className="font-mono font-extrabold text-[#16865C]">
                ₹{(monthlyIncome - monthlyExpenses).toLocaleString('en-IN')} / mo
              </span>
            </div>
          </div>
        )}

        {/* Step 3: Emergency Runway & Strategy */}
        {step === 3 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div>
              <label className="text-xs font-semibold text-[#172033] block mb-1.5">
                Emergency Fund Target
              </label>
              <div className="grid grid-cols-4 gap-2 text-xs">
                {[3, 6, 9, 12].map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setEmergencyTargetMonths(m)}
                    className={`py-2 px-3 rounded-xl border text-center font-medium transition-all ${
                      emergencyTargetMonths === m
                        ? 'border-[#6478E8] bg-[#EEF0FF] text-[#6478E8] font-bold'
                        : 'border-[#E6EAF0] text-[#172033] hover:bg-[#F6F8FC]'
                    }`}
                  >
                    {m} mos
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-[#697386] mt-1">
                Recommended: 6 months for salaried, 9–12 months for freelancers or business owners.
              </p>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#172033] block mb-1.5">
                Investment Risk Appetite
              </label>
              <div className="grid grid-cols-3 gap-2 text-xs">
                {[
                  { id: 'conservative', label: 'Conservative', desc: 'FDs & Liquid' },
                  { id: 'moderate', label: 'Moderate', desc: 'Balanced & Index' },
                  { id: 'aggressive', label: 'Aggressive', desc: 'Equity & Growth' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setRiskTolerance(item.id as any)}
                    className={`p-2.5 rounded-xl border text-left transition-all ${
                      riskTolerance === item.id
                        ? 'border-[#6478E8] bg-[#EEF0FF] text-[#6478E8]'
                        : 'border-[#E6EAF0] text-[#172033] hover:bg-[#F6F8FC]'
                    }`}
                  >
                    <div className="font-bold text-xs">{item.label}</div>
                    <div className="text-[10px] text-[#697386]">{item.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#172033] block mb-1">
                Tax Regime Preference (AY 2025-26)
              </label>
              <select
                value={taxRegime}
                onChange={(e) => setTaxRegime(e.target.value as any)}
                className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-medium focus:outline-none focus:border-[#6478E8]"
              >
                <option value="auto">Auto-Recommend (Optimal Savings)</option>
                <option value="new">Section 115BAC New Regime</option>
                <option value="old">Old Tax Regime (with 80C/80D/HRA)</option>
              </select>
            </div>
          </div>
        )}

        {/* Modal Controls */}
        <div className="flex items-center justify-between pt-4 border-t border-[#E6EAF0]">
          {step > 1 ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setStep((step - 1) as any)}
              icon={<ArrowLeft className="w-3.5 h-3.5" />}
            >
              Back
            </Button>
          ) : (
            <div />
          )}

          {step < 3 ? (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setStep((step + 1) as any)}
              className="flex items-center gap-1.5"
            >
              <span>Continue</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          ) : (
            <Button
              variant="primary"
              size="sm"
              onClick={handleSave}
              loading={loading}
              disabled={loading}
              className="flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Save & Launch Dashboard</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
