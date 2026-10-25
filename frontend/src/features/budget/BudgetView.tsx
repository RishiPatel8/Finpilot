import React, { useState, useEffect } from 'react';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  Search,
  Filter,
  Layers,
  ArrowDownUp,
  Download,
  Plus,
  X,
  Edit2,
  Check,
  RotateCcw,
  Sliders,
  DollarSign,
  Sparkles,
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { Transaction } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';
import { KnowMore } from '../../components/KnowMore';

interface BudgetViewProps {
  transactions: Transaction[];
  onRefresh: () => void;
  monthlyIncome: number;
  monthlyExpenses: number;
}

export const BudgetView: React.FC<BudgetViewProps> = ({
  transactions,
  onRefresh,
  monthlyIncome,
  monthlyExpenses,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<any | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'income' | 'expense'>('all');

  // Editable Budget Framework State
  const [isEditingFramework, setIsEditingFramework] = useState(false);
  const [customIncome, setCustomIncome] = useState<number>(() => {
    const saved = localStorage.getItem('finpilot_budget_framework');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.customIncome && parsed.customIncome > 0) return Number(parsed.customIncome);
      } catch {}
    }
    return monthlyIncome > 0 ? monthlyIncome : 0;
  });
  const [needsPct, setNeedsPct] = useState<number>(() => {
    const saved = localStorage.getItem('finpilot_budget_framework');
    if (saved) {
      try { return Number(JSON.parse(saved).needsPct ?? 50); } catch {}
    }
    return 50;
  });
  const [wantsPct, setWantsPct] = useState<number>(() => {
    const saved = localStorage.getItem('finpilot_budget_framework');
    if (saved) {
      try { return Number(JSON.parse(saved).wantsPct ?? 30); } catch {}
    }
    return 30;
  });
  const [savingsPct, setSavingsPct] = useState<number>(() => {
    const saved = localStorage.getItem('finpilot_budget_framework');
    if (saved) {
      try { return Number(JSON.parse(saved).savingsPct ?? 20); } catch {}
    }
    return 20;
  });
  const [isSavingFramework, setIsSavingFramework] = useState(false);
  const [frameworkSaveSuccess, setFrameworkSaveSuccess] = useState(false);

  useEffect(() => {
    if (monthlyIncome > 0 && customIncome === 0) {
      setCustomIncome(monthlyIncome);
    }
  }, [monthlyIncome]);

  const effectiveIncome = customIncome > 0 ? customIncome : (monthlyIncome > 0 ? monthlyIncome : 0);
  const totalPct = needsPct + wantsPct + savingsPct;
  const isTotalValid = totalPct === 100;
  const isCustomFramework = needsPct !== 50 || wantsPct !== 30 || savingsPct !== 20 || (customIncome > 0 && customIncome !== monthlyIncome);

  // Categorized spending tracking from verified transactions
  const needsCategories = ['rent', 'groceries', 'housing', 'utilities', 'bills', 'healthcare', 'medical', 'debt & emi', 'loan', 'insurance', 'emi'];
  const wantsCategories = ['food & dining', 'entertainment', 'shopping', 'travel', 'subscriptions', 'hobbies', 'personal care', 'lifestyle', 'dining'];
  const savingsCategories = ['investment', 'sip', 'mutual funds', 'savings', 'emergency fund', 'stocks', 'deposit', 'ppf'];

  const actualExpensesList = transactions.filter((t) => t.type === 'expense');
  const actualNeedsSpent = actualExpensesList
    .filter((t) => needsCategories.some((c) => (t.category || '').toLowerCase().includes(c)))
    .reduce((acc, t) => acc + Number(t.amount || 0), 0);
  const actualWantsSpent = actualExpensesList
    .filter((t) => wantsCategories.some((c) => (t.category || '').toLowerCase().includes(c)))
    .reduce((acc, t) => acc + Number(t.amount || 0), 0);
  const actualSavingsSpent = actualExpensesList
    .filter((t) => savingsCategories.some((c) => (t.category || '').toLowerCase().includes(c)))
    .reduce((acc, t) => acc + Number(t.amount || 0), 0);

  const needsTargetAmt = (effectiveIncome * needsPct) / 100;
  const wantsTargetAmt = (effectiveIncome * wantsPct) / 100;
  const savingsTargetAmt = (effectiveIncome * savingsPct) / 100;

  const handleSaveFramework = async () => {
    if (!isTotalValid) return;
    setIsSavingFramework(true);
    try {
      localStorage.setItem(
        'finpilot_budget_framework',
        JSON.stringify({
          needsPct,
          wantsPct,
          savingsPct,
          customIncome,
        })
      );

      // If user modified income, update their profile
      if (customIncome > 0 && customIncome !== monthlyIncome) {
        await apiRequest('/profile', {
          method: 'PUT',
          body: JSON.stringify({ monthly_income: customIncome }),
        });
        onRefresh();
      }

      setFrameworkSaveSuccess(true);
      setTimeout(() => setFrameworkSaveSuccess(false), 2500);
      setIsEditingFramework(false);
    } catch (err: any) {
      alert(err.message || 'Failed to save budget settings.');
    } finally {
      setIsSavingFramework(false);
    }
  };

  const handleResetFramework = () => {
    setNeedsPct(50);
    setWantsPct(30);
    setSavingsPct(20);
    if (monthlyIncome > 0) setCustomIncome(monthlyIncome);
    localStorage.removeItem('finpilot_budget_framework');
  };

  const applyPreset = (n: number, w: number, s: number) => {
    setNeedsPct(n);
    setWantsPct(w);
    setSavingsPct(s);
  };

  // Manual Transaction Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [manualDate, setManualDate] = useState(new Date().toISOString().slice(0, 10));
  const [manualAmount, setManualAmount] = useState<number | ''>('');
  const [manualType, setManualType] = useState<'income' | 'expense'>('expense');
  const [manualCategory, setManualCategory] = useState('Food & Dining');
  const [manualDescription, setManualDescription] = useState('');
  const [isSubmittingManual, setIsSubmittingManual] = useState(false);
  const [manualError, setManualError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setPreviewData(null);
      setError(null);
    }
  };

  const uploadAndPreview = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiRequest<any>('/statement/preview', {
        method: 'POST',
        headers: {}, // let browser set boundary
        body: formData,
      });
      setPreviewData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to parse CSV file. Ensure valid headers (Date, Description, Amount, Type).');
    } finally {
      setIsUploading(false);
    }
  };

  const confirmImport = async () => {
    const rows = previewData?.preview_transactions || previewData?.preview;
    if (!previewData || !rows) return;
    setIsConfirming(true);
    setError(null);

    const validTxns = rows.filter((p: any) => p.is_valid && !p.is_duplicate);

    try {
      await apiRequest('/statement/confirm', {
        method: 'POST',
        body: JSON.stringify({
          filename: previewData.filename || file?.name || 'statement.csv',
          file_format: previewData.file_format || 'csv',
          bank_name: previewData.bank_name || 'Bank Account',
          account_masked: previewData.account_masked || 'XXXX',
          closing_balance: previewData.closing_balance || null,
          transactions: validTxns,
        }),
      });
      setPreviewData(null);
      setFile(null);
      window.dispatchEvent(new CustomEvent('finpilot:statement-imported'));
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to save transactions.');
    } finally {
      setIsConfirming(false);
    }
  };

  const handleAddManualTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualAmount || Number(manualAmount) <= 0 || !manualDescription.trim()) return;

    setIsSubmittingManual(true);
    setManualError(null);
    try {
      await apiRequest('/transactions', {
        method: 'POST',
        body: JSON.stringify({
          date: manualDate,
          amount: Number(manualAmount),
          type: manualType,
          category: manualCategory,
          description: manualDescription.trim(),
          source: 'manual',
          is_recurring: false,
        }),
      });
      setShowAddModal(false);
      setManualAmount('');
      setManualDescription('');
      onRefresh();
    } catch (err: any) {
      setManualError(err.message || 'Failed to record transaction.');
    } finally {
      setIsSubmittingManual(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiRequest(`/transactions/${id}`, { method: 'DELETE' });
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to delete transaction.');
    }
  };

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const filteredTxns = transactions.filter((t) => {
    const matchesSearch =
      t.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || t.type === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Budget & Bank Statements"
        description="Analyze 50-30-20 cash flow allocations, import bank statements (CSV), and audit verified transactions with duplicate detection."
        icon={<Layers className="w-4 h-4 text-[#6478E8]" />}
        badge={
          <Badge variant="blue" size="sm">
            50-30-20 Allocation
          </Badge>
        }
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowAddModal(true)}
            icon={<Plus className="w-3.5 h-3.5" />}
          >
            Add Transaction
          </Button>
        }
      />

      {/* Editable Cash Flow Allocation Framework Widget */}
      <Card className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-bold text-[#F3F4F6] flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#ECC856]" />
                <span>
                  {isCustomFramework
                    ? `${needsPct} / ${wantsPct} / ${savingsPct} Cash Flow Allocation Framework`
                    : '50 / 30 / 20 Cash Flow Allocation Framework'}
                </span>
              </h2>
              <KnowMore termId="cash_flow" variant="badge" label="About Cash Flow" />
              {isCustomFramework && (
                <Badge variant="lavender" size="sm" className="font-semibold">
                  Custom Allocation
                </Badge>
              )}
              {frameworkSaveSuccess && (
                <Badge variant="mint" size="sm" className="font-semibold animate-in fade-in">
                  ✓ Targets Saved
                </Badge>
              )}
            </div>
            <p className="text-xs text-[#9CA3AF] mt-0.5">
              Standard recommended allocation benchmarked against your net monthly income of{' '}
              <strong className="text-[#F5DE88] font-mono">{formatINR(effectiveIncome)}</strong>.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {!isEditingFramework ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsEditingFramework(true)}
                icon={<Edit2 className="w-3.5 h-3.5 text-[#6478E8]" />}
              >
                Customize Budget
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsEditingFramework(false)}
                icon={<X className="w-3.5 h-3.5 text-[#697386]" />}
              >
                Cancel
              </Button>
            )}
          </div>
        </div>

        {/* View Mode: Interactive Allocation Cards */}
        {!isEditingFramework ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Needs */}
              <div className="p-4 rounded-2xl bg-[#141A26]/90 border border-sky-500/30 hover:border-sky-400/60 shadow-md shadow-black/40 space-y-2.5 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-sky-400">
                    Needs ({needsPct}% Target)
                  </span>
                  <span className="text-[10px] font-mono font-bold text-sky-300 bg-sky-500/15 border border-sky-500/30 px-2 py-0.5 rounded-md">
                    {needsPct}%
                  </span>
                </div>
                <div>
                  <p className="text-xl font-extrabold text-[#F3F4F6] font-mono tabular-nums">
                    {formatINR(needsTargetAmt)}
                  </p>
                  <p className="text-[11px] text-[#9CA3AF] mt-0.5">
                    Rent, Groceries, EMIs, Utilities & Healthcare
                  </p>
                </div>

                {/* Progress vs Actual Observed Spending */}
                {actualNeedsSpent > 0 && (
                  <div className="pt-2 border-t border-white/10 space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-[#9CA3AF]">Observed Spent:</span>
                      <span
                        className={`font-mono font-bold ${
                          actualNeedsSpent <= needsTargetAmt ? 'text-[#10B981]' : 'text-[#F43F5E]'
                        }`}
                      >
                        {formatINR(actualNeedsSpent)}
                      </span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-black/50 border border-white/5 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          actualNeedsSpent <= needsTargetAmt ? 'bg-sky-400' : 'bg-[#F43F5E]'
                        }`}
                        style={{
                          width: `${Math.min(100, needsTargetAmt > 0 ? (actualNeedsSpent / needsTargetAmt) * 100 : 0)}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Wants */}
              <div className="p-4 rounded-2xl bg-[#141A26]/90 border border-amber-500/30 hover:border-amber-400/60 shadow-md shadow-black/40 space-y-2.5 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-amber-400">
                    Wants ({wantsPct}% Target)
                  </span>
                  <span className="text-[10px] font-mono font-bold text-amber-300 bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 rounded-md">
                    {wantsPct}%
                  </span>
                </div>
                <div>
                  <p className="text-xl font-extrabold text-[#F3F4F6] font-mono tabular-nums">
                    {formatINR(wantsTargetAmt)}
                  </p>
                  <p className="text-[11px] text-[#9CA3AF] mt-0.5">
                    Dining out, Travel, Subscriptions & Hobbies
                  </p>
                </div>

                {/* Progress vs Actual Observed Spending */}
                {actualWantsSpent > 0 && (
                  <div className="pt-2 border-t border-white/10 space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-[#9CA3AF]">Observed Spent:</span>
                      <span
                        className={`font-mono font-bold ${
                          actualWantsSpent <= wantsTargetAmt ? 'text-[#10B981]' : 'text-[#F43F5E]'
                        }`}
                      >
                        {formatINR(actualWantsSpent)}
                      </span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-black/50 border border-white/5 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          actualWantsSpent <= wantsTargetAmt ? 'bg-amber-400' : 'bg-[#F43F5E]'
                        }`}
                        style={{
                          width: `${Math.min(100, wantsTargetAmt > 0 ? (actualWantsSpent / wantsTargetAmt) * 100 : 0)}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Savings & Investments */}
              <div className="p-4 rounded-2xl bg-[#141A26]/90 border border-emerald-500/30 hover:border-emerald-400/60 shadow-md shadow-black/40 space-y-2.5 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-emerald-400">
                    Savings & Investments ({savingsPct}% Target)
                  </span>
                  <span className="text-[10px] font-mono font-bold text-emerald-300 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-md">
                    {savingsPct}%
                  </span>
                </div>
                <div>
                  <p className="text-xl font-extrabold text-[#10B981] font-mono tabular-nums">
                    {formatINR(savingsTargetAmt)}
                  </p>
                  <p className="text-[11px] text-[#9CA3AF] mt-0.5">
                    Liquid funds, SIPs, PPF, Pre-payments
                  </p>
                </div>

                {/* Progress vs Actual Observed Spending */}
                {actualSavingsSpent > 0 && (
                  <div className="pt-2 border-t border-white/10 space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-[#9CA3AF]">Observed Saved:</span>
                      <span className="font-mono font-bold text-[#10B981]">
                        {formatINR(actualSavingsSpent)}
                      </span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-black/50 border border-white/5 overflow-hidden">
                      <div
                        className="h-full bg-[#10B981] rounded-full transition-all"
                        style={{
                          width: `${Math.min(100, savingsTargetAmt > 0 ? (actualSavingsSpent / savingsTargetAmt) * 100 : 0)}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Edit Mode: Interactive Customization Panel */
          <div className="p-5 rounded-2xl bg-[#F8FAFC] border border-[#E6EAF0] space-y-5 animate-in fade-in duration-200">
            {/* 1. Benchmark Income Field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-[#6478E8]" />
                  <span>Benchmark Monthly Net Income</span>
                </label>
                <span className="text-[11px] text-[#697386]">
                  Saving also syncs to your financial profile
                </span>
              </div>
              <div className="relative max-w-sm">
                <span className="absolute left-3.5 top-2.5 text-xs text-[#697386] font-semibold">₹</span>
                <input
                  type="number"
                  value={customIncome || ''}
                  onChange={(e) => setCustomIncome(Number(e.target.value))}
                  placeholder="e.g. 60000"
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl pl-8 pr-3 py-2 text-xs sm:text-sm font-mono tabular-nums text-[#172033] font-bold focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
                />
              </div>
            </div>

            {/* 2. Quick Allocation Presets */}
            <div className="space-y-1.5 pt-3 border-t border-[#E6EAF0]">
              <span className="text-xs font-bold text-[#172033] uppercase tracking-wider block">
                Quick Framework Presets
              </span>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => applyPreset(50, 30, 20)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    needsPct === 50 && wantsPct === 30 && savingsPct === 20
                      ? 'bg-[#EEF0FF] text-[#6478E8] border-[#6478E8]'
                      : 'bg-white text-[#697386] border-[#E6EAF0] hover:border-slate-300'
                  }`}
                >
                  50 / 30 / 20 (Standard)
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset(60, 20, 20)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    needsPct === 60 && wantsPct === 20 && savingsPct === 20
                      ? 'bg-[#EEF0FF] text-[#6478E8] border-[#6478E8]'
                      : 'bg-white text-[#697386] border-[#E6EAF0] hover:border-slate-300'
                  }`}
                >
                  60 / 20 / 20 (High Rent / Metros)
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset(40, 30, 30)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    needsPct === 40 && wantsPct === 30 && savingsPct === 30
                      ? 'bg-[#EEF0FF] text-[#6478E8] border-[#6478E8]'
                      : 'bg-white text-[#697386] border-[#E6EAF0] hover:border-slate-300'
                  }`}
                >
                  40 / 30 / 30 (Aggressive Wealth Builder)
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset(70, 20, 10)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    needsPct === 70 && wantsPct === 20 && savingsPct === 10
                      ? 'bg-[#EEF0FF] text-[#6478E8] border-[#6478E8]'
                      : 'bg-white text-[#697386] border-[#E6EAF0] hover:border-slate-300'
                  }`}
                >
                  70 / 20 / 10 (Single Earner / Families)
                </button>
              </div>
            </div>

            {/* 3. Interactive Sliders & Inputs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 border-t border-[#E6EAF0]">
              {/* Needs Slider */}
              <div className="p-4 rounded-xl bg-white border border-[#E6EAF0] space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-[#2B6CB0]">Needs Target (%)</label>
                  <span className="text-xs font-mono font-bold text-[#172033]">{needsPct}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="90"
                  value={needsPct}
                  onChange={(e) => setNeedsPct(Number(e.target.value))}
                  className="w-full accent-[#2B6CB0] cursor-pointer"
                />
                <div className="flex items-center justify-between pt-1 border-t border-[#F1F4F9] text-[11px]">
                  <span className="text-[#697386]">Target Sum:</span>
                  <span className="font-mono font-bold text-[#172033]">
                    {formatINR((effectiveIncome * needsPct) / 100)}
                  </span>
                </div>
              </div>

              {/* Wants Slider */}
              <div className="p-4 rounded-xl bg-white border border-[#E6EAF0] space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-[#B7791F]">Wants Target (%)</label>
                  <span className="text-xs font-mono font-bold text-[#172033]">{wantsPct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="80"
                  value={wantsPct}
                  onChange={(e) => setWantsPct(Number(e.target.value))}
                  className="w-full accent-[#B7791F] cursor-pointer"
                />
                <div className="flex items-center justify-between pt-1 border-t border-[#F1F4F9] text-[11px]">
                  <span className="text-[#697386]">Target Sum:</span>
                  <span className="font-mono font-bold text-[#172033]">
                    {formatINR((effectiveIncome * wantsPct) / 100)}
                  </span>
                </div>
              </div>

              {/* Savings Slider */}
              <div className="p-4 rounded-xl bg-white border border-[#E6EAF0] space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-[#16865C]">Savings & Investments (%)</label>
                  <span className="text-xs font-mono font-bold text-[#172033]">{savingsPct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="80"
                  value={savingsPct}
                  onChange={(e) => setSavingsPct(Number(e.target.value))}
                  className="w-full accent-[#16865C] cursor-pointer"
                />
                <div className="flex items-center justify-between pt-1 border-t border-[#F1F4F9] text-[11px]">
                  <span className="text-[#697386]">Target Sum:</span>
                  <span className="font-mono font-bold text-[#16865C]">
                    {formatINR((effectiveIncome * savingsPct) / 100)}
                  </span>
                </div>
              </div>
            </div>

            {/* 4. Total Validation & Actions */}
            <div className="pt-3 border-t border-[#E6EAF0] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                {isTotalValid ? (
                  <Badge variant="mint" size="sm" className="font-semibold">
                    ✓ Total: 100% (Balanced)
                  </Badge>
                ) : (
                  <Badge variant="peach" size="sm" className="font-semibold">
                    ⚠️ Total is {totalPct}% (
                    {100 - totalPct > 0
                      ? `${100 - totalPct}% unallocated`
                      : `${totalPct - 100}% over 100%`}
                    )
                  </Badge>
                )}
                <span className="text-[11px] text-[#697386]">
                  Allocations must sum exactly to 100%.
                </span>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResetFramework}
                  icon={<RotateCcw className="w-3.5 h-3.5" />}
                >
                  Reset 50/30/20
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsEditingFramework(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSaveFramework}
                  disabled={!isTotalValid || isSavingFramework}
                  loading={isSavingFramework}
                  icon={<Check className="w-3.5 h-3.5" />}
                >
                  Save Allocation
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* CSV Bank Statement Import Card */}
      <Card className="space-y-4">
        <div>
          <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-[#6478E8]" />
            <span>Import Bank Statement (CSV, XLSX, PDF)</span>
          </h2>
          <p className="text-xs text-[#697386] mt-0.5">
            Compatible with HDFC, ICICI, SBI, Axis, Kotak, and standard bank exports with automatic duplicate suppression.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.pdf"
            onChange={handleFileChange}
            className="w-full text-xs text-[#9CA3AF] file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border file:border-[rgba(212,175,55,0.3)] file:text-xs file:font-bold file:bg-[#141A26] file:text-[#ECC856] hover:file:bg-[#1A2232] cursor-pointer"
          />
          <Button
            variant="primary"
            size="md"
            onClick={uploadAndPreview}
            disabled={!file || isUploading}
            loading={isUploading}
            icon={<Upload className="w-3.5 h-3.5" />}
            className="w-full sm:w-auto shrink-0"
          >
            {isUploading ? 'Extracting & Validating Statement...' : 'Upload & Validate'}
          </Button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
            {error}
          </div>
        )}

        {/* CSV Preview Results Table */}
        {previewData && (
          <div className="mt-4 p-4 sm:p-5 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] space-y-4 animate-in fade-in duration-200">
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex flex-wrap items-center gap-3 sm:gap-4 font-medium">
                <span className="text-[#697386]">
                  Total Rows: <strong className="text-[#172033]">{previewData.total_rows}</strong>
                </span>
                <span className="text-[#16865C]">
                  Valid New: <strong>{(previewData.valid_new_rows ?? previewData.valid_rows ?? 0)}</strong>
                </span>
                <span className="text-[#B7791F]">
                  Duplicates: <strong>{previewData.duplicate_rows}</strong>
                </span>
                <span className="text-[#D9485F]">
                  Invalid: <strong>{previewData.invalid_rows}</strong>
                </span>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={confirmImport}
                disabled={(previewData.valid_new_rows ?? previewData.valid_rows ?? 0) === 0 || isConfirming}
                loading={isConfirming}
              >
                {isConfirming
                  ? 'Importing...'
                  : `Confirm Import (${(previewData.valid_new_rows ?? previewData.valid_rows ?? 0)} txns)`}
              </Button>
            </div>

            <div className="max-h-60 overflow-y-auto border border-[#E6EAF0] rounded-xl bg-white">
              <table className="w-full text-left text-xs text-[#172033]">
                <thead className="bg-[#F6F8FC] sticky top-0 text-[#697386] uppercase text-[10px] tracking-wider border-b border-[#E6EAF0]">
                  <tr>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Description</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3 text-right">Amount</th>
                    <th className="py-2.5 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E6EAF0] font-medium">
                  {(previewData.preview_transactions || previewData.preview || []).map((row: any, idx: number) => (
                    <tr key={idx} className="hover:bg-[#F6F8FC] transition-colors">
                      <td className="py-2.5 px-3 font-mono text-[#697386]">{row.date}</td>
                      <td className="py-2.5 px-3 text-[#172033] truncate max-w-xs">{row.description}</td>
                      <td className="py-2.5 px-3 text-[#697386]">{row.category}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-[#172033]">
                        {row.type === 'income' ? '+' : '-'} ₹{row.amount}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {row.is_duplicate ? (
                          <Badge variant="peach" size="sm">
                            Duplicate
                          </Badge>
                        ) : row.is_valid ? (
                          <Badge variant="mint" size="sm">
                            Ready
                          </Badge>
                        ) : (
                          <Badge variant="danger" size="sm" title={row.validation_error}>
                            Invalid
                          </Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      {/* Transaction History Filter & Table */}
      <Card className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[#172033]">
              Transaction History ({filteredTxns.length})
            </h2>
            <p className="text-xs text-[#697386]">Search and filter categorized transactions.</p>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-64">
              <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-[#697386]" />
              <input
                type="text"
                placeholder="Search transactions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-white border border-[#E6EAF0] rounded-xl pl-8 pr-3 py-1.5 text-xs text-[#172033] placeholder-[#697386]/60 focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
              />
            </div>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as any)}
              className="bg-white border border-[#E6EAF0] rounded-xl px-3 py-1.5 text-xs text-[#172033] font-medium focus:outline-none focus:border-[#6478E8] transition-all"
            >
              <option value="all">All Types</option>
              <option value="income">Income Only</option>
              <option value="expense">Expenses Only</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto -mx-5 sm:mx-0">
          <table className="w-full text-left text-xs text-[#172033]">
            <thead className="bg-[#F6F8FC] text-[#697386] uppercase text-[10px] tracking-wider border-y border-[#E6EAF0]">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Date</th>
                <th className="py-2.5 px-4 font-semibold">Description</th>
                <th className="py-2.5 px-4 font-semibold">Category</th>
                <th className="py-2.5 px-4 font-semibold">Source</th>
                <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                <th className="py-2.5 px-4 font-semibold text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E6EAF0] font-medium">
              {filteredTxns.length > 0 ? (
                filteredTxns.map((t) => (
                  <tr key={t.id} className="hover:bg-[#F6F8FC] transition-colors">
                    <td className="py-3 px-4 font-mono text-[#697386]">{t.date}</td>
                    <td className="py-3 px-4 text-[#172033] font-semibold">{t.description}</td>
                    <td className="py-3 px-4">
                      <Badge variant="neutral" size="sm">
                        {t.category}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-[#697386] capitalize">
                      {t.source.replace('_', ' ')}
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-mono font-bold tabular-nums ${
                        t.type === 'income' ? 'text-[#16865C]' : 'text-[#172033]'
                      }`}
                    >
                      {t.type === 'income' ? '+' : '-'} {formatINR(t.amount)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleDelete(t.id)}
                        className="text-[#697386] hover:text-[#D9485F] hover:bg-[#FDF2F4] p-1.5 rounded-lg transition-colors"
                        title="Delete transaction"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[#697386]">
                    No transactions match the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Manual Add Transaction Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl max-w-md w-full border border-[#E6EAF0] shadow-xl p-5 sm:p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-[#172033] flex items-center gap-2">
                <Plus className="w-4 h-4 text-[#6478E8]" />
                Record Transaction
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-[#697386] hover:text-[#172033] p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {manualError && (
              <div className="p-2.5 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
                {manualError}
              </div>
            )}

            <form onSubmit={handleAddManualTransaction} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                    Date
                  </label>
                  <input
                    type="date"
                    required
                    value={manualDate}
                    onChange={(e) => setManualDate(e.target.value)}
                    className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono text-[#172033] focus:outline-none focus:border-[#6478E8]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                    Type
                  </label>
                  <select
                    value={manualType}
                    onChange={(e) => setManualType(e.target.value as any)}
                    className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-medium focus:outline-none focus:border-[#6478E8]"
                  >
                    <option value="expense">Expense (-)</option>
                    <option value="income">Income (+)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Amount (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 1500"
                  value={manualAmount}
                  onChange={(e) => setManualAmount(Number(e.target.value))}
                  className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono font-bold text-[#172033] focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Category
                </label>
                <select
                  value={manualCategory}
                  onChange={(e) => setManualCategory(e.target.value)}
                  className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] font-medium focus:outline-none focus:border-[#6478E8]"
                >
                  <option value="Food & Dining">Food & Dining</option>
                  <option value="Housing">Housing & Rent</option>
                  <option value="Groceries">Groceries & Essentials</option>
                  <option value="Transportation">Transportation & Fuel</option>
                  <option value="Utilities">Utilities & Bills</option>
                  <option value="Healthcare">Healthcare & Insurance</option>
                  <option value="Shopping">Shopping & Discretionary</option>
                  <option value="Income">Salary / Freelance Income</option>
                  <option value="Investment">Mutual Funds / Equity SIP</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[#697386] mb-1">
                  Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Monthly Grocery Order at Swiggy Instamart"
                  value={manualDescription}
                  onChange={(e) => setManualDescription(e.target.value)}
                  className="w-full bg-[#F6F8FC] border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  type="button"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  loading={isSubmittingManual}
                  disabled={isSubmittingManual}
                >
                  {isSubmittingManual ? 'Saving...' : 'Save Transaction'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
