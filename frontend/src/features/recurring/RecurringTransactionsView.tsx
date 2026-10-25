import React, { useState, useEffect } from 'react';
import {
  CalendarClock,
  CheckCircle2,
  AlertCircle,
  Pause,
  Play,
  XCircle,
  Edit2,
  Trash2,
  Plus,
  RefreshCw,
  Clock,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  TrendingDown,
  TrendingUp,
  Tag,
  Check,
  X,
  HelpCircle,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { apiRequest, getAuthToken } from '../../services/api';
import {
  RecurringTransactionItem,
  UpcomingOccurrenceItem,
  RecurringSummaryData,
  UpcomingSummaryResponse,
} from '../../types';
import { Card, Badge, Button, PageHeader, MetricCard } from '../../components/ui';
import { KnowMore } from '../../components/KnowMore';

interface RecurringTransactionsViewProps {
  onRefresh?: () => void;
}

export const RecurringTransactionsView: React.FC<RecurringTransactionsViewProps> = ({
  onRefresh,
}) => {
  const [summary, setSummary] = useState<RecurringSummaryData | null>(null);
  const [detections, setDetections] = useState<RecurringTransactionItem[]>([]);
  const [items, setItems] = useState<RecurringTransactionItem[]>([]);
  const [upcoming, setUpcoming] = useState<UpcomingOccurrenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'confirmed' | 'paused' | 'cancelled'>('all');
  const [typeFilter, setTypeFilter] = useState<'all' | 'expense' | 'income'>('all');

  // Modals state
  const [editingItem, setEditingItem] = useState<RecurringTransactionItem | null>(null);
  const [dismissingItem, setDismissingItem] = useState<RecurringTransactionItem | null>(null);
  const [dismissReason, setDismissReason] = useState('Not a recurring transaction');
  const [showAddModal, setShowAddModal] = useState(false);

  // Form State for Add / Edit
  const [formName, setFormName] = useState('');
  const [formAmount, setFormAmount] = useState<number | ''>('');
  const [formType, setFormType] = useState<'income' | 'expense'>('expense');
  const [formCategory, setFormCategory] = useState('Utilities');
  const [formFrequency, setFormFrequency] = useState<'weekly' | 'fortnightly' | 'monthly' | 'quarterly' | 'yearly'>('monthly');
  const [formNextDate, setFormNextDate] = useState(new Date().toISOString().slice(0, 10));
  const [formNotes, setFormNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const loadData = async () => {
    setLoading(true);
    const token = getAuthToken();

    if (!token) {
      setSummary(null);
      setDetections([]);
      setItems([]);
      setUpcoming([]);
      setLoading(false);
      return;
    }

    try {
      const [sumRes, detRes, itemsRes, upRes] = await Promise.all([
        apiRequest<RecurringSummaryData>('/recurring-transactions/summary'),
        apiRequest<RecurringTransactionItem[]>('/recurring-transactions/detections'),
        apiRequest<RecurringTransactionItem[]>('/recurring-transactions'),
        apiRequest<UpcomingSummaryResponse>('/recurring-transactions/upcoming?horizon_days=30'),
      ]);

      setSummary(sumRes);
      setDetections(detRes || []);
      setItems(itemsRes || []);
      setUpcoming(upRes?.occurrences || []);
    } catch (err) {
      console.error('Failed to load recurring data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Confirmation handler
  const handleConfirm = async (item: RecurringTransactionItem, edits?: any) => {
    setActionLoading(item.id);
    try {
      await apiRequest(`/recurring-transactions/${item.id}/confirm`, {
        method: 'POST',
        body: JSON.stringify(edits || {}),
      });
      await loadData();
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Failed to confirm recurring item: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoading(null);
      setEditingItem(null);
    }
  };

  // Dismiss handler
  const handleDismiss = async () => {
    if (!dismissingItem) return;
    setActionLoading(dismissingItem.id);
    try {
      await apiRequest(`/recurring-transactions/${dismissingItem.id}/dismiss`, {
        method: 'POST',
        body: JSON.stringify({ user_feedback: dismissReason }),
      });
      await loadData();
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Failed to dismiss item: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoading(null);
      setDismissingItem(null);
    }
  };

  // Pause handler
  const handlePause = async (id: string) => {
    setActionLoading(id);
    try {
      await apiRequest(`/recurring-transactions/${id}/pause`, { method: 'POST' });
      await loadData();
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Failed to pause: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Reactivate handler
  const handleReactivate = async (id: string) => {
    setActionLoading(id);
    try {
      await apiRequest(`/recurring-transactions/${id}/reactivate`, { method: 'POST' });
      await loadData();
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Failed to reactivate: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Cancel handler
  const handleCancel = async (id: string) => {
    if (!window.confirm('Are you sure you want to cancel this recurring commitment? It will be marked as cancelled and excluded from forward projections.')) {
      return;
    }
    setActionLoading(id);
    try {
      await apiRequest(`/recurring-transactions/${id}/cancel`, { method: 'POST' });
      await loadData();
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Failed to cancel: ${err?.message || 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Save Edit (for confirmed items or detection edit)
  const handleSaveEdit = async () => {
    if (!editingItem) return;
    if (!formName.trim()) {
      setFormError('Please enter a valid title.');
      return;
    }
    if (!formAmount || formAmount <= 0) {
      setFormError('Amount must be greater than zero.');
      return;
    }

    const payload = {
      name: formName.trim(),
      amount: Number(formAmount),
      category: formCategory,
      frequency: formFrequency,
      next_expected_date: formNextDate,
      user_notes: formNotes,
    };

    if (editingItem.status === 'detected') {
      await handleConfirm(editingItem, payload);
    } else {
      setActionLoading(editingItem.id);
      try {
        await apiRequest(`/recurring-transactions/${editingItem.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        });
        await loadData();
        if (onRefresh) onRefresh();
        setEditingItem(null);
      } catch (err: any) {
        setFormError(err?.message || 'Failed to update recurring item.');
      } finally {
        setActionLoading(null);
      }
    }
  };

  // Save New Manual Recurring
  const handleCreateNew = async () => {
    if (!formName.trim()) {
      setFormError('Please enter a valid title.');
      return;
    }
    if (!formAmount || formAmount <= 0) {
      setFormError('Amount must be greater than zero.');
      return;
    }

    setActionLoading('new');
    try {
      await apiRequest('/recurring-transactions', {
        method: 'POST',
        body: JSON.stringify({
          name: formName.trim(),
          transaction_type: formType,
          amount: Number(formAmount),
          category: formCategory,
          frequency: formFrequency,
          next_expected_date: formNextDate,
          user_notes: formNotes,
        }),
      });
      await loadData();
      if (onRefresh) onRefresh();
      setShowAddModal(false);
      resetForm();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create recurring transaction.');
    } finally {
      setActionLoading(null);
    }
  };

  const openEditModal = (item: RecurringTransactionItem) => {
    setEditingItem(item);
    setFormName(item.name);
    setFormAmount(item.amount);
    setFormType(item.transaction_type);
    setFormCategory(item.category);
    setFormFrequency(item.frequency);
    setFormNextDate(item.next_expected_date || new Date().toISOString().slice(0, 10));
    setFormNotes(item.user_notes || '');
    setFormError(null);
  };

  const resetForm = () => {
    setFormName('');
    setFormAmount('');
    setFormType('expense');
    setFormCategory('Utilities');
    setFormFrequency('monthly');
    setFormNextDate(new Date().toISOString().slice(0, 10));
    setFormNotes('');
    setFormError(null);
  };

  // Filter items
  const filteredItems = items.filter((item) => {
    if (statusFilter !== 'all' && item.status !== statusFilter) return false;
    if (typeFilter !== 'all' && item.transaction_type !== typeFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recurring Transactions & Bills"
        description="Review AI-detected subscriptions, manage confirmed commitments, and view your 30-day forward payment schedule."
        icon={<CalendarClock className="w-5 h-5 text-[#ECC856]" />}
        badge={<KnowMore termId="recurring_payment" variant="badge" label="About Recurring Payments" />}
        actions={
          <Button
            onClick={() => {
              resetForm();
              setShowAddModal(true);
            }}
            variant="primary"
            className="text-xs"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            Add Recurring Item
          </Button>
        }
      />

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label={
            <span className="inline-flex items-center gap-1.5">
              <span>Monthly Fixed Expenses</span>
              <KnowMore termId="recurring_payment" />
            </span>
          }
          value={formatINR(summary?.monthly_recurring_expenses || 0)}
          icon={<TrendingDown className="w-4 h-4 text-[#F43F5E]" />}
          iconTone="peach"
          subtext={
            <span className="text-xs text-[#9CA3AF]">
              {summary?.active_count || 0} active confirmed bills
            </span>
          }
        />
        <MetricCard
          label="Monthly Fixed Income"
          value={formatINR(summary?.monthly_recurring_income || 0)}
          icon={<TrendingUp className="w-4 h-4 text-[#10B981]" />}
          iconTone="mint"
          subtext={
            <span className="text-xs text-[#9CA3AF]">
              Verified salary & cash inflows
            </span>
          }
        />
        <MetricCard
          label={
            <span className="inline-flex items-center gap-1.5">
              <span>Net Recurring Cash Flow</span>
              <KnowMore termId="cash_flow" />
            </span>
          }
          value={formatINR(summary?.net_recurring_cash_flow || 0)}
          icon={<CheckCircle2 className="w-4 h-4 text-[#ECC856]" />}
          iconTone="lavender"
          subtext={
            <span className="text-xs text-[#10B981] font-semibold">
              Retained monthly surplus
            </span>
          }
        />
        <MetricCard
          label="Review Queue"
          value={`${detections.length} Detected`}
          icon={<Sparkles className="w-4 h-4 text-[#ECC856]" />}
          iconTone="lavender"
          subtext={
            <span className={`text-xs font-medium ${detections.length > 0 ? 'text-[#ECC856]' : 'text-[#9CA3AF]'}`}>
              {detections.length > 0 ? 'Action required' : 'All patterns reviewed'}
            </span>
          }
        />
      </div>

      {/* Review Queue: Unreviewed Detections */}
      {detections.length > 0 && (
        <Card className="p-5 sm:p-6 space-y-4 border border-[rgba(212,175,55,0.25)] bg-[#111622]/95 backdrop-blur-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/10">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-[#D4AF37]/15 text-[#ECC856] border border-[#D4AF37]/30 shadow-sm shadow-[#D4AF37]/10">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm sm:text-base font-bold text-[#F3F4F6] tracking-tight">
                    Review Detected Recurring Payments
                  </h2>
                  <Badge variant="lavender" className="text-[10px] py-0.5 px-2">
                    {detections.length} New
                  </Badge>
                </div>
                <p className="text-xs text-[#9CA3AF]">
                  The Intelligence Engine identified these patterns from your transaction history. Confirm them to ground forecasts.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {detections.map((det) => (
              <div
                key={det.id}
                className="p-4 rounded-xl border border-[rgba(212,175,55,0.22)] bg-[#141A26]/90 hover:bg-[#1A2232] hover:border-[#D4AF37]/50 shadow-md shadow-black/40 transition-all duration-200 space-y-3 group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5 min-w-0">
                    <h3 className="text-sm font-bold text-[#F3F4F6] tracking-tight truncate group-hover:text-[#F5DE88] transition-colors">
                      {det.name}
                    </h3>
                    <p className="text-xs text-[#9CA3AF] flex items-center gap-1.5">
                      <span className="truncate">{det.category}</span>
                      <span className="w-1 h-1 rounded-full bg-[#D4AF37]/50 shrink-0"></span>
                      <span className="capitalize shrink-0">{det.frequency}</span>
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-sm sm:text-base font-black text-[#F5DE88] font-mono tracking-tight tabular-nums">
                      {formatINR(det.amount)}
                    </div>
                    <Badge
                      variant={det.confidence === 'high' ? 'mint' : 'lavender'}
                      className="text-[9px] py-0 px-1.5 mt-0.5 uppercase font-semibold tracking-wider"
                    >
                      {det.confidence} confidence
                    </Badge>
                  </div>
                </div>

                {det.explanation && (
                  <p className="text-[11px] text-[#D1D5DB] bg-[#0A0D14]/90 p-2.5 rounded-lg border border-white/10 leading-relaxed font-sans">
                    {det.explanation}
                  </p>
                )}

                <div className="flex items-center justify-between pt-2 border-t border-white/10">
                  <span className="text-[11px] text-[#9CA3AF]">
                    Next: <strong className="text-[#F3F4F6] font-mono ml-1">{det.next_expected_date || 'Expected soon'}</strong>
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setDismissingItem(det)}
                      disabled={actionLoading === det.id}
                      className="px-2.5 py-1 text-xs text-[#9CA3AF] hover:text-[#F43F5E] hover:bg-[#F43F5E]/10 rounded-lg transition-colors font-medium"
                    >
                      Dismiss
                    </button>
                    <button
                      onClick={() => openEditModal(det)}
                      disabled={actionLoading === det.id}
                      className="px-2.5 py-1 text-xs text-[#ECC856] hover:text-[#F5DE88] hover:bg-[#D4AF37]/15 rounded-lg border border-[#D4AF37]/30 transition-colors font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleConfirm(det)}
                      disabled={actionLoading === det.id}
                      className="px-3 py-1 text-xs bg-gradient-to-r from-[#ECC856] via-[#D4AF37] to-[#B89327] hover:brightness-110 text-black rounded-lg transition-all font-bold flex items-center gap-1 shadow-sm shadow-[#D4AF37]/30 hover:scale-[1.02] active:scale-[0.98]"
                    >
                      <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                      Confirm
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Confirmed Recurring Obligations Table / Grid */}
      <Card className="p-5 sm:p-6 space-y-4 border border-[rgba(212,175,55,0.25)] bg-[#111622]/95 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
          <div>
            <h2 className="text-base font-bold text-[#F3F4F6] tracking-tight">
              Confirmed Recurring Records
            </h2>
            <p className="text-xs text-[#9CA3AF]">
              Active financial commitments that automatically feed into 30/90-day cash flow projections.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Status Filter */}
            <div className="flex rounded-xl border border-[rgba(212,175,55,0.2)] p-0.5 bg-[#0A0D14] text-xs">
              {(['all', 'confirmed', 'paused', 'cancelled'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-lg capitalize font-medium transition-all ${
                    statusFilter === st
                      ? 'bg-[#141A26] text-[#ECC856] border border-[#D4AF37]/30 shadow-xs font-semibold'
                      : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            {/* Type Filter */}
            <div className="flex rounded-xl border border-[rgba(212,175,55,0.2)] p-0.5 bg-[#0A0D14] text-xs">
              {(['all', 'expense', 'income'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTypeFilter(t)}
                  className={`px-2.5 py-1 rounded-lg capitalize font-medium transition-all ${
                    typeFilter === t
                      ? 'bg-[#141A26] text-[#ECC856] border border-[#D4AF37]/30 shadow-xs font-semibold'
                      : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-[#9CA3AF] animate-pulse">
            Loading recurring financial commitments...
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="py-10 text-center rounded-xl bg-[#0A0D14]/80 border border-white/10">
            <p className="text-sm font-semibold text-[#F3F4F6]">No recurring records found</p>
            <p className="text-xs text-[#9CA3AF] mt-1">
              Add custom recurring payments or import statement transactions to trigger detection.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-[#9CA3AF] font-semibold bg-white/[0.02]">
                  <th className="py-3 px-3">Title & Merchant</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Frequency</th>
                  <th className="py-3 px-3">Amount</th>
                  <th className="py-3 px-3">Next Due</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredItems.map((item) => {
                  const isIncome = item.transaction_type === 'income';
                  return (
                    <tr key={item.id} className="hover:bg-white/[0.03] transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-bold text-[#F3F4F6]">{item.name}</div>
                        {item.merchant && item.merchant !== item.name && (
                          <div className="text-[11px] text-[#9CA3AF]">{item.merchant}</div>
                        )}
                      </td>
                      <td className="py-3 px-3 text-[#D1D5DB]">{item.category}</td>
                      <td className="py-3 px-3 capitalize text-[#D1D5DB]">{item.frequency}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`font-mono font-bold ${
                            isIncome ? 'text-[#10B981]' : 'text-[#F5DE88]'
                          }`}
                        >
                          {isIncome ? '+' : '-'}
                          {formatINR(item.amount)}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-[#F3F4F6] font-mono">
                        {item.next_expected_date || '—'}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            item.status === 'confirmed'
                              ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30'
                              : item.status === 'paused'
                              ? 'bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30'
                              : 'bg-white/[0.06] text-[#9CA3AF] border border-white/10'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => openEditModal(item)}
                            title="Edit Details"
                            className="p-1 rounded-md text-[#9CA3AF] hover:text-[#ECC856] hover:bg-white/[0.06] transition-colors"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          {item.status === 'confirmed' && (
                            <button
                              onClick={() => handlePause(item.id)}
                              disabled={actionLoading === item.id}
                              title="Pause Subscription"
                              className="p-1 rounded-md text-[#F59E0B] hover:bg-[#F59E0B]/15 transition-colors"
                            >
                              <Pause className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {item.status === 'paused' && (
                            <button
                              onClick={() => handleReactivate(item.id)}
                              disabled={actionLoading === item.id}
                              title="Reactivate"
                              className="p-1 rounded-md text-[#10B981] hover:bg-[#10B981]/15 transition-colors"
                            >
                              <Play className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {item.status !== 'cancelled' && (
                            <button
                              onClick={() => handleCancel(item.id)}
                              disabled={actionLoading === item.id}
                              title="Cancel Permanently"
                              className="p-1 rounded-md text-[#F43F5E] hover:bg-[#F43F5E]/15 transition-colors"
                            >
                              <XCircle className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Upcoming 30-Day Activity Schedule */}
      <Card className="p-5 sm:p-6 space-y-4 border border-[rgba(212,175,55,0.25)] bg-[#111622]/95 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/10">
          <div>
            <h2 className="text-base font-bold text-[#F3F4F6] tracking-tight">
              Upcoming Payments & Inflows (Next 30 Days)
            </h2>
            <p className="text-xs text-[#9CA3AF]">
              Chronological schedule of confirmed obligations. Overdue items remain flagged until reconciled.
            </p>
          </div>
          <div className="text-xs text-[#9CA3AF]">
            Total Projected Outflow:{' '}
            <strong className="text-[#F43F5E] font-mono font-bold ml-1">
              {formatINR(upcoming.filter((u) => u.transaction_type === 'expense').reduce((acc, curr) => acc + curr.amount, 0))}
            </strong>
          </div>
        </div>

        {upcoming.length === 0 ? (
          <div className="py-6 text-center text-xs text-[#9CA3AF] rounded-xl bg-[#0A0D14]/80 border border-white/10">
            No upcoming recurring commitments in the next 30 days.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {upcoming.map((occ, idx) => {
              const isIncome = occ.transaction_type === 'income';
              return (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border space-y-2 backdrop-blur-md transition-all ${
                    occ.is_overdue
                      ? 'border-[#F43F5E]/40 bg-[#F43F5E]/10 shadow-sm shadow-[#F43F5E]/10'
                      : isIncome
                      ? 'border-[#10B981]/40 bg-[#10B981]/10 shadow-sm shadow-[#10B981]/10'
                      : 'border-[rgba(212,175,55,0.2)] bg-[#141A26]/90 shadow-sm shadow-black/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-[#9CA3AF] uppercase font-mono tracking-wider">
                      {new Date(occ.expected_date).toLocaleDateString('en-IN', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded tracking-wide ${
                        occ.is_overdue
                          ? 'bg-[#F43F5E]/20 text-[#F43F5E] border border-[#F43F5E]/40'
                          : occ.days_until <= 3
                          ? 'bg-[#F59E0B]/20 text-[#F59E0B] border border-[#F59E0B]/40'
                          : 'bg-white/[0.06] text-[#9CA3AF] border border-white/10'
                      }`}
                    >
                      {occ.is_overdue
                        ? 'Overdue'
                        : occ.days_until === 0
                        ? 'Due Today'
                        : `In ${occ.days_until} days`}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-[#F3F4F6] truncate">{occ.name}</h4>
                    <p className="text-[11px] text-[#9CA3AF] truncate">{occ.category}</p>
                  </div>

                  <div className="pt-2 border-t border-white/10 flex items-center justify-between">
                    <span className="text-[10px] text-[#9CA3AF] capitalize">{occ.frequency}</span>
                    <span
                      className={`text-xs font-mono font-bold ${
                        isIncome ? 'text-[#10B981]' : 'text-[#F5DE88]'
                      }`}
                    >
                      {isIncome ? '+' : '-'}
                      {formatINR(occ.amount)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Edit / Confirm Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0D111A] rounded-2xl border border-[rgba(212,175,55,0.3)] shadow-[0_10px_40px_rgba(0,0,0,0.8),0_0_25px_rgba(212,175,55,0.15)] w-full max-w-md p-6 space-y-4 animate-in fade-in zoom-in-95 text-[#F3F4F6]">
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <h3 className="text-base font-bold text-[#F3F4F6] tracking-tight">
                {editingItem.status === 'detected' ? 'Confirm Recurring Item' : 'Edit Recurring Item'}
              </h3>
              <button
                onClick={() => setEditingItem(null)}
                className="p-1 rounded-lg text-[#9CA3AF] hover:text-white hover:bg-white/[0.06] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="p-2.5 rounded-lg bg-[#F43F5E]/15 border border-[#F43F5E]/30 text-xs text-[#F43F5E]">
                {formError}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-[#D1D5DB] mb-1">Title / Description</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors"
                  placeholder="e.g. Netflix Subscription"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#D1D5DB] mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    value={formAmount}
                    onChange={(e) => setFormAmount(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors font-mono"
                    placeholder="e.g. 649"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#D1D5DB] mb-1">Frequency</label>
                  <select
                    value={formFrequency}
                    onChange={(e: any) => setFormFrequency(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors"
                  >
                    <option value="weekly" className="bg-[#141A26] text-white">Weekly</option>
                    <option value="fortnightly" className="bg-[#141A26] text-white">Fortnightly</option>
                    <option value="monthly" className="bg-[#141A26] text-white">Monthly</option>
                    <option value="quarterly" className="bg-[#141A26] text-white">Quarterly</option>
                    <option value="yearly" className="bg-[#141A26] text-white">Yearly</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#D1D5DB] mb-1">Category</label>
                  <input
                    type="text"
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors"
                    placeholder="e.g. Entertainment"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#D1D5DB] mb-1">Next Expected Date</label>
                  <input
                    type="date"
                    value={formNextDate}
                    onChange={(e) => setFormNextDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#D1D5DB] mb-1">Personal Notes (Optional)</label>
                <textarea
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 resize-none transition-colors"
                  rows={2}
                  placeholder="e.g. Shared with roommates, splits 50%"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <Button variant="secondary" onClick={() => setEditingItem(null)} className="text-xs">
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSaveEdit} className="text-xs">
                {editingItem.status === 'detected' ? 'Save & Confirm' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Dismiss Dialog */}
      {dismissingItem && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0D111A] rounded-2xl border border-[rgba(212,175,55,0.3)] shadow-[0_10px_40px_rgba(0,0,0,0.8),0_0_25px_rgba(212,175,55,0.15)] w-full max-w-sm p-6 space-y-4 text-[#F3F4F6]">
            <h3 className="text-base font-bold text-[#F3F4F6] tracking-tight">Dismiss Recurring Detection</h3>
            <p className="text-xs text-[#9CA3AF]">
              Dismissing <strong className="text-[#F5DE88]">{dismissingItem.name}</strong> removes it from your review queue. Source transactions will not be modified.
            </p>

            <div className="space-y-2 text-xs">
              <label className="block font-semibold text-[#D1D5DB]">Reason for dismissal:</label>
              {[
                'Not a recurring transaction',
                'One-off purchase or service',
                'Subscription already cancelled',
                'Wrong amount or merchant',
              ].map((reason) => (
                <label key={reason} className="flex items-center gap-2.5 text-[#D1D5DB] cursor-pointer hover:text-white p-2 rounded-xl hover:bg-white/[0.04] transition-colors border border-transparent hover:border-white/10">
                  <input
                    type="radio"
                    name="dismissReason"
                    checked={dismissReason === reason}
                    onChange={() => setDismissReason(reason)}
                    className="accent-[#D4AF37] w-3.5 h-3.5"
                  />
                  <span>{reason}</span>
                </label>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <Button variant="secondary" onClick={() => setDismissingItem(null)} className="text-xs">
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleDismiss}
                className="text-xs bg-[#F43F5E] hover:bg-[#E11D48] text-white"
              >
                Confirm Dismissal
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0D111A] rounded-2xl border border-[rgba(212,175,55,0.3)] shadow-[0_10px_40px_rgba(0,0,0,0.8),0_0_25px_rgba(212,175,55,0.15)] w-full max-w-md p-6 space-y-4 animate-in fade-in zoom-in-95 text-[#F3F4F6]">
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <h3 className="text-base font-bold text-[#F3F4F6] tracking-tight">Add Recurring Item</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 rounded-lg text-[#9CA3AF] hover:text-white hover:bg-white/[0.06] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="p-2.5 rounded-lg bg-[#F43F5E]/15 border border-[#F43F5E]/30 text-xs text-[#F43F5E]">
                {formError}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-[#D1D5DB] mb-1">Item Title</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors"
                  placeholder="e.g. WiFi Broadband Connection"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#D1D5DB] mb-1">Type</label>
                  <select
                    value={formType}
                    onChange={(e: any) => setFormType(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors"
                  >
                    <option value="expense" className="bg-[#141A26] text-white">Expense (Outflow)</option>
                    <option value="income" className="bg-[#141A26] text-white">Income (Inflow)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-[#D1D5DB] mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    value={formAmount}
                    onChange={(e) => setFormAmount(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors font-mono"
                    placeholder="e.g. 1199"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#D1D5DB] mb-1">Category</label>
                  <input
                    type="text"
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors"
                    placeholder="e.g. Utilities"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#D1D5DB] mb-1">Frequency</label>
                  <select
                    value={formFrequency}
                    onChange={(e: any) => setFormFrequency(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors"
                  >
                    <option value="weekly" className="bg-[#141A26] text-white">Weekly</option>
                    <option value="fortnightly" className="bg-[#141A26] text-white">Fortnightly</option>
                    <option value="monthly" className="bg-[#141A26] text-white">Monthly</option>
                    <option value="quarterly" className="bg-[#141A26] text-white">Quarterly</option>
                    <option value="yearly" className="bg-[#141A26] text-white">Yearly</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#D1D5DB] mb-1">First / Next Occurrence Date</label>
                <input
                  type="date"
                  value={formNextDate}
                  onChange={(e) => setFormNextDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-colors font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#D1D5DB] mb-1">Notes (Optional)</label>
                <textarea
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-white/15 bg-[#141A26] text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 resize-none transition-colors"
                  rows={2}
                  placeholder="e.g. Airtel fiber postpaid plan"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <Button variant="secondary" onClick={() => setShowAddModal(false)} className="text-xs">
                Cancel
              </Button>
              <Button variant="primary" onClick={handleCreateNew} className="text-xs">
                Save Recurring Record
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
