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
        icon={<CalendarClock className="w-5 h-5 text-[#6478E8]" />}
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
          icon={<TrendingDown className="w-4 h-4 text-[#D9485F]" />}
          iconTone="peach"
          subtext={
            <span className="text-xs text-[#697386]">
              {summary?.active_count || 0} active confirmed bills
            </span>
          }
        />
        <MetricCard
          label="Monthly Fixed Income"
          value={formatINR(summary?.monthly_recurring_income || 0)}
          icon={<TrendingUp className="w-4 h-4 text-[#16865C]" />}
          iconTone="mint"
          subtext={
            <span className="text-xs text-[#697386]">
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
          icon={<CheckCircle2 className="w-4 h-4 text-[#6478E8]" />}
          iconTone="lavender"
          subtext={
            <span className="text-xs text-[#16865C] font-semibold">
              Retained monthly surplus
            </span>
          }
        />
        <MetricCard
          label="Review Queue"
          value={`${detections.length} Detected`}
          icon={<Sparkles className="w-4 h-4 text-[#B7791F]" />}
          iconTone="blue"
          subtext={
            <span className="text-xs text-[#B7791F] font-medium">
              {detections.length > 0 ? 'Action required' : 'All patterns reviewed'}
            </span>
          }
        />
      </div>

      {/* Review Queue: Unreviewed Detections */}
      {detections.length > 0 && (
        <Card className="border border-[#E6EAF0] shadow-sm p-5 space-y-4 bg-white">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#F0F3F8]">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-[#6478E8]/10 text-[#6478E8]">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-[#172033]">
                    Review Detected Recurring Payments
                  </h2>
                  <Badge variant="blue" className="text-[10px] py-0.5">
                    {detections.length} New
                  </Badge>
                </div>
                <p className="text-xs text-[#697386]">
                  The Intelligence Engine identified these patterns from your transaction history. Confirm them to ground forecasts.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {detections.map((det) => (
              <div
                key={det.id}
                className="p-4 rounded-xl border border-[#E6EAF0] bg-[#FAFBFD] hover:bg-white transition-all space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-[#172033]">{det.name}</h3>
                    <p className="text-xs text-[#697386]">
                      {det.category} • <span className="capitalize">{det.frequency}</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-[#172033]">
                      {formatINR(det.amount)}
                    </div>
                    <Badge
                      variant={det.confidence === 'high' ? 'mint' : 'blue'}
                      className="text-[9px] py-0 px-1.5 mt-0.5"
                    >
                      {det.confidence} confidence
                    </Badge>
                  </div>
                </div>

                {det.explanation && (
                  <p className="text-[11px] text-[#4A5568] bg-white p-2 rounded-lg border border-[#E6EAF0]/60">
                    {det.explanation}
                  </p>
                )}

                <div className="flex items-center justify-between pt-2 border-t border-[#F0F3F8]">
                  <span className="text-[11px] text-[#697386]">
                    Next: <strong className="text-[#172033]">{det.next_expected_date || 'Expected soon'}</strong>
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setDismissingItem(det)}
                      disabled={actionLoading === det.id}
                      className="px-2.5 py-1 text-xs text-[#697386] hover:text-[#D9485F] hover:bg-red-50 rounded-lg transition-colors"
                    >
                      Dismiss
                    </button>
                    <button
                      onClick={() => openEditModal(det)}
                      disabled={actionLoading === det.id}
                      className="px-2.5 py-1 text-xs text-[#6478E8] hover:bg-indigo-50 rounded-lg transition-colors font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleConfirm(det)}
                      disabled={actionLoading === det.id}
                      className="px-3 py-1 text-xs bg-[#6478E8] hover:bg-[#5063D8] text-white rounded-lg transition-colors font-medium flex items-center gap-1"
                    >
                      <Check className="w-3 h-3" />
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
      <Card className="border border-[#E6EAF0] shadow-sm p-5 space-y-4 bg-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#F0F3F8]">
          <div>
            <h2 className="text-base font-bold text-[#172033]">
              Confirmed Recurring Records
            </h2>
            <p className="text-xs text-[#697386]">
              Active financial commitments that automatically feed into 30/90-day cash flow projections.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Status Filter */}
            <div className="flex rounded-lg border border-[#E6EAF0] p-0.5 bg-[#F6F8FC] text-xs">
              {(['all', 'confirmed', 'paused', 'cancelled'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-md capitalize font-medium transition-colors ${
                    statusFilter === st
                      ? 'bg-white text-[#172033] shadow-xs'
                      : 'text-[#697386] hover:text-[#172033]'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            {/* Type Filter */}
            <div className="flex rounded-lg border border-[#E6EAF0] p-0.5 bg-[#F6F8FC] text-xs">
              {(['all', 'expense', 'income'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTypeFilter(t)}
                  className={`px-2.5 py-1 rounded-md capitalize font-medium transition-colors ${
                    typeFilter === t
                      ? 'bg-white text-[#172033] shadow-xs'
                      : 'text-[#697386] hover:text-[#172033]'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-[#697386] animate-pulse">
            Loading recurring financial commitments...
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="py-10 text-center rounded-xl bg-[#F6F8FC] border border-[#E6EAF0]">
            <p className="text-sm font-semibold text-[#172033]">No recurring records found</p>
            <p className="text-xs text-[#697386] mt-1">
              Add custom recurring payments or import statement transactions to trigger detection.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#E6EAF0] text-[#697386] font-semibold">
                  <th className="py-3 px-3">Title & Merchant</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Frequency</th>
                  <th className="py-3 px-3">Amount</th>
                  <th className="py-3 px-3">Next Due</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F0F3F8]">
                {filteredItems.map((item) => {
                  const isIncome = item.transaction_type === 'income';
                  return (
                    <tr key={item.id} className="hover:bg-[#FAFBFD] transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-bold text-[#172033]">{item.name}</div>
                        {item.merchant && item.merchant !== item.name && (
                          <div className="text-[11px] text-[#697386]">{item.merchant}</div>
                        )}
                      </td>
                      <td className="py-3 px-3 text-[#4A5568]">{item.category}</td>
                      <td className="py-3 px-3 capitalize text-[#4A5568]">{item.frequency}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`font-bold ${
                            isIncome ? 'text-[#16865C]' : 'text-[#172033]'
                          }`}
                        >
                          {isIncome ? '+' : '-'}
                          {formatINR(item.amount)}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-[#172033]">
                        {item.next_expected_date || '—'}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            item.status === 'confirmed'
                              ? 'bg-emerald-50 text-[#16865C] border border-emerald-200'
                              : item.status === 'paused'
                              ? 'bg-amber-50 text-[#B7791F] border border-amber-200'
                              : 'bg-slate-100 text-slate-600 border border-slate-200'
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
                            className="p-1 rounded-md text-[#697386] hover:text-[#172033] hover:bg-slate-100"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          {item.status === 'confirmed' && (
                            <button
                              onClick={() => handlePause(item.id)}
                              disabled={actionLoading === item.id}
                              title="Pause Subscription"
                              className="p-1 rounded-md text-[#B7791F] hover:bg-amber-50"
                            >
                              <Pause className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {item.status === 'paused' && (
                            <button
                              onClick={() => handleReactivate(item.id)}
                              disabled={actionLoading === item.id}
                              title="Reactivate"
                              className="p-1 rounded-md text-[#16865C] hover:bg-emerald-50"
                            >
                              <Play className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {item.status !== 'cancelled' && (
                            <button
                              onClick={() => handleCancel(item.id)}
                              disabled={actionLoading === item.id}
                              title="Cancel Permanently"
                              className="p-1 rounded-md text-[#D9485F] hover:bg-red-50"
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
      <Card className="border border-[#E6EAF0] shadow-sm p-5 space-y-4 bg-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#F0F3F8]">
          <div>
            <h2 className="text-base font-bold text-[#172033]">
              Upcoming Payments & Inflows (Next 30 Days)
            </h2>
            <p className="text-xs text-[#697386]">
              Chronological schedule of confirmed obligations. Overdue items remain flagged until reconciled.
            </p>
          </div>
          <div className="text-xs text-[#697386]">
            Total Projected Outflow:{' '}
            <strong className="text-[#D9485F]">
              {formatINR(upcoming.filter((u) => u.transaction_type === 'expense').reduce((acc, curr) => acc + curr.amount, 0))}
            </strong>
          </div>
        </div>

        {upcoming.length === 0 ? (
          <div className="py-6 text-center text-xs text-[#697386] rounded-xl bg-[#F6F8FC]">
            No upcoming recurring commitments in the next 30 days.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {upcoming.map((occ, idx) => {
              const isIncome = occ.transaction_type === 'income';
              return (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border ${
                    occ.is_overdue
                      ? 'border-red-200 bg-red-50/40'
                      : isIncome
                      ? 'border-emerald-200 bg-emerald-50/30'
                      : 'border-[#E6EAF0] bg-white'
                  } space-y-2`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-[#697386] uppercase">
                      {new Date(occ.expected_date).toLocaleDateString('en-IN', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        occ.is_overdue
                          ? 'bg-red-100 text-[#D9485F]'
                          : occ.days_until <= 3
                          ? 'bg-amber-100 text-[#B7791F]'
                          : 'bg-slate-100 text-slate-600'
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
                    <h4 className="text-xs font-bold text-[#172033] truncate">{occ.name}</h4>
                    <p className="text-[11px] text-[#697386] truncate">{occ.category}</p>
                  </div>

                  <div className="pt-2 border-t border-black/5 flex items-center justify-between">
                    <span className="text-[10px] text-[#697386] capitalize">{occ.frequency}</span>
                    <span
                      className={`text-xs font-bold ${
                        isIncome ? 'text-[#16865C]' : 'text-[#172033]'
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
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-[#E6EAF0] shadow-xl w-full max-w-md p-6 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-2 border-b border-[#F0F3F8]">
              <h3 className="text-base font-bold text-[#172033]">
                {editingItem.status === 'detected' ? 'Confirm Recurring Item' : 'Edit Recurring Item'}
              </h3>
              <button
                onClick={() => setEditingItem(null)}
                className="p-1 rounded-lg text-[#697386] hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-[#D9485F]">
                {formError}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-[#172033] mb-1">Title / Description</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                  placeholder="e.g. Netflix Subscription"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#172033] mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    value={formAmount}
                    onChange={(e) => setFormAmount(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                    placeholder="e.g. 649"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#172033] mb-1">Frequency</label>
                  <select
                    value={formFrequency}
                    onChange={(e: any) => setFormFrequency(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                  >
                    <option value="weekly">Weekly</option>
                    <option value="fortnightly">Fortnightly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#172033] mb-1">Category</label>
                  <input
                    type="text"
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                    placeholder="e.g. Entertainment"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#172033] mb-1">Next Expected Date</label>
                  <input
                    type="date"
                    value={formNextDate}
                    onChange={(e) => setFormNextDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Personal Notes (Optional)</label>
                <textarea
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8] resize-none"
                  rows={2}
                  placeholder="e.g. Shared with roommates, splits 50%"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F3F8]">
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
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-[#E6EAF0] shadow-xl w-full max-w-sm p-6 space-y-4">
            <h3 className="text-base font-bold text-[#172033]">Dismiss Recurring Detection</h3>
            <p className="text-xs text-[#697386]">
              Dismissing <strong>{dismissingItem.name}</strong> removes it from your review queue. Source transactions will not be modified.
            </p>

            <div className="space-y-2 text-xs">
              <label className="block font-semibold text-[#172033]">Reason for dismissal:</label>
              {[
                'Not a recurring transaction',
                'One-off purchase or service',
                'Subscription already cancelled',
                'Wrong amount or merchant',
              ].map((reason) => (
                <label key={reason} className="flex items-center gap-2 text-[#4A5568] cursor-pointer">
                  <input
                    type="radio"
                    name="dismissReason"
                    checked={dismissReason === reason}
                    onChange={() => setDismissReason(reason)}
                    className="text-[#6478E8] focus:ring-[#6478E8]"
                  />
                  <span>{reason}</span>
                </label>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F3F8]">
              <Button variant="secondary" onClick={() => setDismissingItem(null)} className="text-xs">
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleDismiss}
                className="text-xs bg-[#D9485F] hover:bg-[#C0374E] text-white"
              >
                Confirm Dismissal
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-[#E6EAF0] shadow-xl w-full max-w-md p-6 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-2 border-b border-[#F0F3F8]">
              <h3 className="text-base font-bold text-[#172033]">Add Recurring Item</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 rounded-lg text-[#697386] hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-[#D9485F]">
                {formError}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-[#172033] mb-1">Item Title</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                  placeholder="e.g. WiFi Broadband Connection"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#172033] mb-1">Type</label>
                  <select
                    value={formType}
                    onChange={(e: any) => setFormType(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                  >
                    <option value="expense">Expense (Outflow)</option>
                    <option value="income">Income (Inflow)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-[#172033] mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    value={formAmount}
                    onChange={(e) => setFormAmount(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                    placeholder="e.g. 1199"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#172033] mb-1">Category</label>
                  <input
                    type="text"
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                    placeholder="e.g. Utilities"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#172033] mb-1">Frequency</label>
                  <select
                    value={formFrequency}
                    onChange={(e: any) => setFormFrequency(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                  >
                    <option value="weekly">Weekly</option>
                    <option value="fortnightly">Fortnightly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">First / Next Occurrence Date</label>
                <input
                  type="date"
                  value={formNextDate}
                  onChange={(e) => setFormNextDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172033] mb-1">Notes (Optional)</label>
                <textarea
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-[#E6EAF0] focus:outline-none focus:border-[#6478E8] resize-none"
                  rows={2}
                  placeholder="e.g. Airtel fiber postpaid plan"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F3F8]">
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
