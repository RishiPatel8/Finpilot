import React, { useState, useEffect } from 'react';
import {
  Settings,
  User as UserIcon,
  Download,
  Trash2,
  Save,
  CheckCircle2,
  ShieldAlert,
  FileJson,
  KeyRound,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { User, FinancialProfile } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';

interface SettingsViewProps {
  user: User | null;
  onProfileUpdated: () => void;
  onLogout: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  user,
  onProfileUpdated,
  onLogout,
}) => {
  const [profile, setProfile] = useState<FinancialProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form Fields
  const [monthlyIncome, setMonthlyIncome] = useState<number>(120000);
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(55000);
  const [age, setAge] = useState<number>(28);
  const [dependents, setDependents] = useState<number>(0);
  const [riskTolerance, setRiskTolerance] = useState<string>('moderate');
  const [emergencyMonths, setEmergencyMonths] = useState<number>(6);
  const [taxRegime, setTaxRegime] = useState<string>('auto');

  // Deletion modal
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const data = await apiRequest<FinancialProfile>('/profile');
        setProfile(data);
        setMonthlyIncome(Number(data.monthly_income) || 120000);
        setMonthlyExpenses(Number(data.monthly_expenses) || 55000);
        setAge(data.age || 28);
        setDependents(data.dependents || 0);
        setRiskTolerance(data.risk_tolerance || 'moderate');
        setEmergencyMonths(data.emergency_fund_target_months || 6);
        setTaxRegime(data.tax_regime_preference || 'auto');
      } catch (err: any) {
        console.error('Failed to load profile:', err);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [user]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      await apiRequest<FinancialProfile>('/profile', {
        method: 'PUT',
        body: JSON.stringify({
          age,
          dependents,
          monthly_income: monthlyIncome,
          monthly_expenses: monthlyExpenses,
          risk_tolerance: riskTolerance,
          emergency_fund_target_months: emergencyMonths,
          tax_regime_preference: taxRegime,
        }),
      });
      setSaveSuccess(true);
      onProfileUpdated();
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to update financial profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleExportData = async () => {
    try {
      const data = await apiRequest('/auth/export-data');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `finpilot_data_export_${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message || 'Failed to export data.');
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE') return;
    setDeleting(true);
    try {
      await apiRequest('/auth/me', { method: 'DELETE' });
      setIsDeleteModalOpen(false);
      onLogout();
    } catch (err: any) {
      alert(err.message || 'Failed to delete account.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Page Header */}
      <PageHeader
        title="Account & Profile Settings"
        description="Update your baseline financial metrics, inspect account credentials, export personal data, and manage privacy settings."
        icon={<Settings className="w-4 h-4 text-[#6478E8]" />}
        badge={
          <Badge variant="neutral" size="sm">
            DPDP Act 2023 Compliant
          </Badge>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Financial Profile Editor (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="space-y-5">
            <div>
              <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
                <UserIcon className="w-4 h-4 text-[#6478E8]" />
                <span>Financial Profile Baseline</span>
              </h2>
              <p className="text-xs text-[#697386] mt-0.5">
                These figures calibrate your Dashboard health score, AI CFO contextual prompts, and emergency reserve targets.
              </p>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
                {error}
              </div>
            )}

            {saveSuccess && (
              <div className="p-3 rounded-xl bg-[#E5F7EF] border border-[#16865C]/20 text-xs text-[#16865C] flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Financial profile saved successfully! Dashboard metrics updated.</span>
              </div>
            )}

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="text-xs font-semibold text-[#172033] block mb-1">
                    Monthly Take-Home Income (₹)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-xs text-[#697386]">₹</span>
                    <input
                      type="number"
                      step="5000"
                      value={monthlyIncome}
                      onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                      required
                      className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl pl-7 pr-3 py-2 text-xs font-mono font-bold text-[#172033] focus:outline-none focus:border-[#6478E8]"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#172033] block mb-1">
                    Monthly Living Expenses (₹)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-xs text-[#697386]">₹</span>
                    <input
                      type="number"
                      step="2000"
                      value={monthlyExpenses}
                      onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                      required
                      className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl pl-7 pr-3 py-2 text-xs font-mono font-bold text-[#172033] focus:outline-none focus:border-[#6478E8]"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#172033] block mb-1">
                    Age
                  </label>
                  <input
                    type="number"
                    min="18"
                    max="100"
                    value={age}
                    onChange={(e) => setAge(Number(e.target.value))}
                    className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono text-[#172033] focus:outline-none focus:border-[#6478E8]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#172033] block mb-1">
                    Dependents
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={dependents}
                    onChange={(e) => setDependents(Number(e.target.value))}
                    className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono text-[#172033] focus:outline-none focus:border-[#6478E8]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#172033] block mb-1">
                    Emergency Fund Target (Months)
                  </label>
                  <select
                    value={emergencyMonths}
                    onChange={(e) => setEmergencyMonths(Number(e.target.value))}
                    className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-medium text-[#172033] focus:outline-none focus:border-[#6478E8]"
                  >
                    <option value={3}>3 Months (Aggressive / Low fixed liabilities)</option>
                    <option value={6}>6 Months (Standard Benchmark)</option>
                    <option value={9}>9 Months (High caution / Dependent family)</option>
                    <option value={12}>12 Months (Freelancer / Business Owner)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#172033] block mb-1">
                    Risk Tolerance
                  </label>
                  <select
                    value={riskTolerance}
                    onChange={(e) => setRiskTolerance(e.target.value)}
                    className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-medium text-[#172033] focus:outline-none focus:border-[#6478E8]"
                  >
                    <option value="conservative">Conservative (FDs, Bonds, Capital Protection)</option>
                    <option value="moderate">Moderate (Balanced, Index, Hybrid)</option>
                    <option value="aggressive">Aggressive (Pure Equity, High Growth)</option>
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="text-xs font-semibold text-[#172033] block mb-1">
                    Tax Regime Preference (AY 2025-26)
                  </label>
                  <select
                    value={taxRegime}
                    onChange={(e) => setTaxRegime(e.target.value)}
                    className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-medium text-[#172033] focus:outline-none focus:border-[#6478E8]"
                  >
                    <option value="auto">Auto-Recommend (Evaluates both regimes dynamically)</option>
                    <option value="new">Section 115BAC New Tax Regime</option>
                    <option value="old">Old Tax Regime (Section 80C/80D/HRA)</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t border-[#E6EAF0]">
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  loading={saving}
                  disabled={saving || !user}
                  icon={<Save className="w-3.5 h-3.5" />}
                >
                  Save Profile Changes
                </Button>
              </div>
            </form>
          </Card>
        </div>

        {/* Right Column: Account Info & Data Privacy (1 col) */}
        <div className="space-y-6">
          {/* Account Overview */}
          <Card className="space-y-4">
            <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-[#6478E8]" />
              <span>Account Credentials</span>
            </h2>

            {user ? (
              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between py-1 border-b border-[#F1F4F9]">
                  <span className="text-[#697386]">Name:</span>
                  <span className="font-semibold text-[#172033]">{user.full_name}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#F1F4F9]">
                  <span className="text-[#697386]">Email:</span>
                  <span className="font-semibold text-[#172033] truncate max-w-[180px]">{user.email}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#F1F4F9]">
                  <span className="text-[#697386]">Role:</span>
                  <span className="font-semibold text-[#172033] capitalize">{user.role}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#F1F4F9]">
                  <span className="text-[#697386]">Auth Provider:</span>
                  <Badge variant="lavender" size="sm">
                    {user.auth_provider}
                  </Badge>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-[#697386]">Status:</span>
                  <Badge variant="mint" size="sm">
                    Active & Verified
                  </Badge>
                </div>
              </div>
            ) : (
              <p className="text-xs text-[#697386]">
                You are currently browsing in Guest / Demo mode. Sign in to link and persist your account.
              </p>
            )}
          </Card>

          {/* Privacy & Data Portability */}
          <Card className="space-y-4">
            <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#16865C]" />
              <span>Data Privacy & Portability</span>
            </h2>

            <p className="text-xs text-[#697386] leading-relaxed">
              Your financial records are strictly isolated. In compliance with the Digital Personal Data Protection (DPDP) Act 2023, you have full ownership of your data.
            </p>

            <div className="space-y-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportData}
                disabled={!user}
                icon={<Download className="w-3.5 h-3.5" />}
                className="w-full justify-center"
              >
                Export All My Data (JSON)
              </Button>
            </div>
          </Card>

          {/* Danger Zone */}
          <Card className="space-y-3 border-[#D9485F]/30 bg-[#FDF2F4]/30">
            <h2 className="text-sm font-bold text-[#D9485F] flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" />
              <span>Danger Zone</span>
            </h2>
            <p className="text-[11px] text-[#697386] leading-relaxed">
              Permanently delete your user profile, transactions, loans, and all financial goals. This action cannot be undone.
            </p>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setIsDeleteModalOpen(true)}
              disabled={!user}
              icon={<Trash2 className="w-3.5 h-3.5" />}
              className="w-full justify-center"
            >
              Delete Account & Wipe Data
            </Button>
          </Card>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#172033]/50 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="w-full max-w-md bg-white rounded-3xl border border-[#D9485F]/30 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-3 text-[#D9485F]">
              <div className="w-10 h-10 rounded-2xl bg-[#FDF2F4] flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-[#D9485F]" />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#172033]">Confirm Permanent Deletion</h3>
                <p className="text-xs text-[#697386]">This action will purge all your records.</p>
              </div>
            </div>

            <p className="text-xs text-[#697386] leading-relaxed">
              All financial statements, transactions, liabilities, simulations, and saved goals associated with{' '}
              <strong className="text-[#172033]">{user?.email}</strong> will be permanently wiped.
            </p>

            <div>
              <label className="text-[11px] font-semibold text-[#172033] block mb-1">
                Type <strong>DELETE</strong> to confirm:
              </label>
              <input
                type="text"
                placeholder="DELETE"
                value={deleteConfirmation}
                onChange={(e) => setDeleteConfirmation(e.target.value)}
                className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono font-bold text-[#172033] focus:outline-none focus:border-[#D9485F]"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-[#E6EAF0]">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsDeleteModalOpen(false);
                  setDeleteConfirmation('');
                }}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleDeleteAccount}
                disabled={deleteConfirmation !== 'DELETE' || deleting}
                loading={deleting}
              >
                Permanently Delete Everything
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
