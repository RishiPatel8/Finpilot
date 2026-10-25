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
  Send,
  MessageSquare,
  Copy,
  Check,
  ExternalLink,
  Bell,
  RefreshCw,
  Unlink,
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { User, FinancialProfile, TelegramStatusResponse, TelegramLinkCodeResponse } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';
import { KnowMore } from '../../components/KnowMore';

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

  // Telegram Bot Integration State
  const [telegramStatus, setTelegramStatus] = useState<TelegramStatusResponse | null>(null);
  const [tgLoading, setTgLoading] = useState(false);
  const [linkCodeData, setLinkCodeData] = useState<TelegramLinkCodeResponse | null>(null);
  const [generatingCode, setGeneratingCode] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [countdownSeconds, setCountdownSeconds] = useState(0);
  const [unlinkingTg, setUnlinkingTg] = useState(false);
  const [updatingTgPrefs, setUpdatingTgPrefs] = useState(false);
  const [testingPing, setTestingPing] = useState(false);
  const [testPingSuccess, setTestPingSuccess] = useState<string | null>(null);
  const [tgError, setTgError] = useState<string | null>(null);

  const fetchTelegramStatus = async () => {
    if (!user) return;
    setTgLoading(true);
    try {
      const data = await apiRequest<TelegramStatusResponse>('/telegram/status');
      setTelegramStatus(data);
    } catch (err: any) {
      console.error('Failed to load telegram status:', err);
    } finally {
      setTgLoading(false);
    }
  };

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
      fetchTelegramStatus();
    } else {
      setLoading(false);
    }
  }, [user]);

  // Expiration Countdown Timer for Link Code
  useEffect(() => {
    if (countdownSeconds <= 0) return;
    const interval = setInterval(() => {
      setCountdownSeconds((prev) => {
        if (prev <= 1) {
          setLinkCodeData(null);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [countdownSeconds]);

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

  // Telegram Handlers
  const handleGenerateLinkCode = async () => {
    setGeneratingCode(true);
    setTgError(null);
    try {
      const data = await apiRequest<TelegramLinkCodeResponse>('/telegram/link-code', { method: 'POST' });
      setLinkCodeData(data);
      setCountdownSeconds(data.valid_for_seconds || 900);
    } catch (err: any) {
      setTgError(err.message || 'Failed to generate link code.');
    } finally {
      setGeneratingCode(false);
    }
  };

  const handleCopyCode = () => {
    if (!linkCodeData?.code) return;
    navigator.clipboard.writeText(linkCodeData.code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2500);
  };

  const handleToggleNotification = async (key: string, value: boolean) => {
    if (!telegramStatus?.is_linked) return;
    setUpdatingTgPrefs(true);
    try {
      const updated = await apiRequest<TelegramStatusResponse>('/telegram/notifications', {
        method: 'PUT',
        body: JSON.stringify({ [key]: value }),
      });
      setTelegramStatus(updated);
    } catch (err: any) {
      console.error('Failed to update notification preference:', err);
    } finally {
      setUpdatingTgPrefs(false);
    }
  };

  const handleSendTestAlert = async () => {
    setTestingPing(true);
    setTestPingSuccess(null);
    try {
      await apiRequest('/telegram/test-notification', { method: 'POST' });
      setTestPingSuccess('Test notification sent to your Telegram chat!');
      setTimeout(() => setTestPingSuccess(null), 4000);
    } catch (err: any) {
      setTgError(err.message || 'Failed to send test alert.');
    } finally {
      setTestingPing(false);
    }
  };

  const handleUnlinkTelegram = async () => {
    if (!confirm('Are you sure you want to disconnect this Telegram account from FinPilot?')) return;
    setUnlinkingTg(true);
    try {
      await apiRequest('/telegram/unlink', { method: 'POST' });
      setTelegramStatus({
        is_linked: false,
        notifications_enabled: true,
        notify_bills: true,
        notify_budget: true,
        notify_goals: true,
        notify_summary: false,
      });
      setLinkCodeData(null);
      setCountdownSeconds(0);
    } catch (err: any) {
      setTgError(err.message || 'Failed to unlink Telegram account.');
    } finally {
      setUnlinkingTg(false);
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
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
                    <UserIcon className="w-4 h-4 text-[#6478E8]" />
                    <span>Financial Profile Baseline</span>
                  </h2>
                  <KnowMore termId="emergency_fund" variant="badge" label="About Profile Baselines" />
                </div>
                <p className="text-xs text-[#697386] mt-0.5">
                  These figures calibrate your Dashboard health score, AI CFO contextual prompts, and emergency reserve targets.
                </p>
              </div>
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

          {/* Telegram Bot Integration Card */}
          <Card className="space-y-5 border border-[#E6EAF0]">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
                  <Send className="w-4 h-4 text-[#6478E8]" />
                  <span>Telegram Global AI CFO</span>
                </h2>
                <p className="text-xs text-[#697386] mt-0.5">
                  Connect FinPilot to Telegram to query spending, review budgets, manage debts, and confirm write actions directly from mobile.
                </p>
              </div>
              <div>
                {telegramStatus?.is_linked ? (
                  <Badge variant="mint" size="sm">
                    🟢 Connected
                  </Badge>
                ) : (
                  <Badge variant="neutral" size="sm">
                    Not Linked
                  </Badge>
                )}
              </div>
            </div>

            {tgError && (
              <div className="p-3.5 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/30 text-xs text-[#D9485F] space-y-2">
                <div className="font-semibold">{tgError}</div>
                {tgError.toLowerCase().includes('user account not found') && (
                  <div className="text-[11px] text-[#697386] space-y-2 pt-1 border-t border-[#D9485F]/20">
                    <p>
                      Your browser has a saved login session from your local database, but this server has a separate database.
                      Click below to log out and sign in again to register your account on this server.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={onLogout}
                      className="text-xs text-[#D9485F] border-[#D9485F]/40 hover:bg-[#D9485F]/10 font-bold"
                    >
                      Log Out & Sign In Again
                    </Button>
                  </div>
                )}
              </div>
            )}

            {testPingSuccess && (
              <div className="p-3 rounded-xl bg-[#E8F8F0] border border-[#16865C]/20 text-xs text-[#16865C] flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>{testPingSuccess}</span>
              </div>
            )}

            {telegramStatus?.is_linked ? (
              /* CONNECTED STATE */
              <div className="space-y-4">
                <div className="p-3.5 rounded-2xl bg-[#F8F9FE] border border-[#6478E8]/20 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#697386]">Linked Telegram User:</span>
                    <span className="font-semibold text-[#172033]">
                      {telegramStatus.telegram_username ? `@${telegramStatus.telegram_username}` : telegramStatus.telegram_first_name || 'Active User'}
                    </span>
                  </div>
                  {telegramStatus.linked_at && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[#697386]">Connected Since:</span>
                      <span className="font-mono text-[#697386]">
                        {new Date(telegramStatus.linked_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                  {telegramStatus.bot_username && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[#697386]">Bot Handle:</span>
                      <a
                        href={`https://t.me/${telegramStatus.bot_username}`}
                        target="_blank"
                        rel="noreferrer"
                        className="font-semibold text-[#6478E8] hover:underline flex items-center gap-1"
                      >
                        @{telegramStatus.bot_username}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                </div>

                {/* Granular Notification Preferences */}
                <div className="space-y-3 pt-2 border-t border-[#E6EAF0]">
                  <h3 className="text-xs font-bold text-[#172033] flex items-center gap-1.5">
                    <Bell className="w-3.5 h-3.5 text-[#6478E8]" />
                    <span>Opt-In Proactive Notifications</span>
                  </h3>

                  <div className="space-y-2.5">
                    <label className="flex items-center justify-between p-2.5 rounded-xl border border-[#E6EAF0] hover:bg-[#F8F9FE] cursor-pointer transition-colors">
                      <div>
                        <div className="text-xs font-semibold text-[#172033]">Master Notifications Switch</div>
                        <div className="text-[11px] text-[#697386]">Allow Telegram alerts for your account</div>
                      </div>
                      <input
                        type="checkbox"
                        checked={telegramStatus.notifications_enabled}
                        onChange={(e) => handleToggleNotification('notifications_enabled', e.target.checked)}
                        disabled={updatingTgPrefs}
                        className="w-4 h-4 accent-[#6478E8] cursor-pointer"
                      />
                    </label>

                    <label className="flex items-center justify-between p-2.5 rounded-xl border border-[#E6EAF0] hover:bg-[#F8F9FE] cursor-pointer transition-colors">
                      <div>
                        <div className="text-xs font-semibold text-[#172033]">Upcoming Recorded Bills</div>
                        <div className="text-[11px] text-[#697386]">Alerts 3 days before recurring payments and subscriptions</div>
                      </div>
                      <input
                        type="checkbox"
                        checked={telegramStatus.notify_bills}
                        disabled={!telegramStatus.notifications_enabled || updatingTgPrefs}
                        onChange={(e) => handleToggleNotification('notify_bills', e.target.checked)}
                        className="w-4 h-4 accent-[#6478E8] cursor-pointer"
                      />
                    </label>

                    <label className="flex items-center justify-between p-2.5 rounded-xl border border-[#E6EAF0] hover:bg-[#F8F9FE] cursor-pointer transition-colors">
                      <div>
                        <div className="text-xs font-semibold text-[#172033]">Monthly Budget Limits</div>
                        <div className="text-[11px] text-[#697386]">Warnings when monthly expenses reach 85% and 100% of target</div>
                      </div>
                      <input
                        type="checkbox"
                        checked={telegramStatus.notify_budget}
                        disabled={!telegramStatus.notifications_enabled || updatingTgPrefs}
                        onChange={(e) => handleToggleNotification('notify_budget', e.target.checked)}
                        className="w-4 h-4 accent-[#6478E8] cursor-pointer"
                      />
                    </label>

                    <label className="flex items-center justify-between p-2.5 rounded-xl border border-[#E6EAF0] hover:bg-[#F8F9FE] cursor-pointer transition-colors">
                      <div>
                        <div className="text-xs font-semibold text-[#172033]">Financial Goal Milestones</div>
                        <div className="text-[11px] text-[#697386]">Celebratory alerts when saving goals hit target completion</div>
                      </div>
                      <input
                        type="checkbox"
                        checked={telegramStatus.notify_goals}
                        disabled={!telegramStatus.notifications_enabled || updatingTgPrefs}
                        onChange={(e) => handleToggleNotification('notify_goals', e.target.checked)}
                        className="w-4 h-4 accent-[#6478E8] cursor-pointer"
                      />
                    </label>
                  </div>
                </div>

                {/* Actions: Send Test Ping & Unlink */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#E6EAF0]">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSendTestAlert}
                    loading={testingPing}
                    icon={<Bell className="w-3.5 h-3.5" />}
                  >
                    Send Test Alert
                  </Button>

                  <Button
                    variant="danger"
                    size="sm"
                    onClick={handleUnlinkTelegram}
                    loading={unlinkingTg}
                    icon={<Unlink className="w-3.5 h-3.5" />}
                  >
                    Disconnect Telegram
                  </Button>
                </div>
              </div>
            ) : (
              /* UNLINKED STATE */
              <div className="space-y-4">
                {linkCodeData ? (
                  <div className="p-4 rounded-2xl bg-[#F8F9FE] border border-[#6478E8]/30 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#172033]">Your Single-Use Link Code:</span>
                      <span className="text-[11px] font-mono text-[#D9485F] font-semibold">
                        Expires in {Math.floor(countdownSeconds / 60)}:{String(countdownSeconds % 60).padStart(2, '0')}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-white border border-[#E6EAF0] rounded-xl px-4 py-3 text-center">
                        <span className="font-mono text-xl font-black text-[#6478E8] tracking-widest">
                          {linkCodeData.code}
                        </span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCopyCode}
                        icon={copiedCode ? <Check className="w-3.5 h-3.5 text-[#16865C]" /> : <Copy className="w-3.5 h-3.5" />}
                      >
                        {copiedCode ? 'Copied!' : 'Copy'}
                      </Button>
                    </div>

                    <div className="text-xs text-[#697386] space-y-1">
                      <p className="font-semibold text-[#172033]">How to complete linking:</p>
                      <ol className="list-decimal list-inside space-y-0.5 text-[11px]">
                        <li>Click <strong>Open in Telegram</strong> below or open Telegram on your phone.</li>
                        <li>Send <code>/start {linkCodeData.code}</code> or <code>/link {linkCodeData.code}</code> in private chat.</li>
                        <li>Your account is securely verified and linked instantly.</li>
                      </ol>
                    </div>

                    <div className="flex items-center gap-3 pt-2">
                      {linkCodeData.deep_link_url ? (
                        <a
                          href={linkCodeData.deep_link_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex-1"
                        >
                          <Button variant="primary" size="sm" className="w-full justify-center" icon={<ExternalLink className="w-3.5 h-3.5" />}>
                            Open in Telegram
                          </Button>
                        </a>
                      ) : (
                        <a
                          href="https://t.me"
                          target="_blank"
                          rel="noreferrer"
                          className="flex-1"
                        >
                          <Button variant="primary" size="sm" className="w-full justify-center" icon={<ExternalLink className="w-3.5 h-3.5" />}>
                            Launch Telegram
                          </Button>
                        </a>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleGenerateLinkCode}
                        loading={generatingCode}
                        icon={<RefreshCw className="w-3.5 h-3.5" />}
                      >
                        New Code
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] space-y-3">
                    <p className="text-xs text-[#697386] leading-relaxed">
                      Link FinPilot with Telegram to access your Global AI CFO anywhere. Never link based on public usernames alone — generate a cryptographically secure, 15-minute single-use code to authorize your Telegram chat.
                    </p>
                    <div className="flex items-center gap-3">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleGenerateLinkCode}
                        loading={generatingCode}
                        disabled={!user}
                        icon={<Send className="w-3.5 h-3.5" />}
                      >
                        Generate Single-Use Link Code
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
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
