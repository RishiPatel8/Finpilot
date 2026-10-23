import React, { useState } from 'react';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  Search,
  Filter,
  DollarSign,
  Layers,
  ArrowDownUp
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { Transaction } from '../../types';

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
      const res = await apiRequest<any>('/transactions/import-csv/preview', {
        method: 'POST',
        headers: {}, // let browser set multipart boundary
        body: formData,
      });
      setPreviewData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to parse CSV file. Ensure valid columns.');
    } finally {
      setIsUploading(false);
    }
  };

  const confirmImport = async () => {
    if (!previewData || !previewData.preview) return;
    setIsConfirming(true);
    setError(null);

    const validTxns = previewData.preview
      .filter((p: any) => p.is_valid && !p.is_duplicate)
      .map((p: any) => ({
        date: p.date,
        amount: p.amount,
        type: p.type,
        category: p.category,
        description: p.description,
        is_recurring: false,
      }));

    try {
      await apiRequest('/transactions/import-csv/confirm', {
        method: 'POST',
        body: JSON.stringify({ transactions: validTxns }),
      });
      setPreviewData(null);
      setFile(null);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to save transactions.');
    } finally {
      setIsConfirming(false);
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
    const matchesSearch = t.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          t.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || t.type === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/40 border border-slate-800">
        <h1 className="text-xl font-extrabold text-slate-100">Budgeting & Transaction Management</h1>
        <p className="text-xs text-slate-400 mt-1">
          Import CSV statements, analyze 50-30-20 cash flows, and manage transactions with duplicate detection.
        </p>
      </div>

      {/* 50/30/20 Rule Analysis Widget */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          <span>50 / 30 / 20 Cash Flow Allocation Framework</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-xs text-slate-400">Needs (50% Ideal)</span>
            <p className="text-lg font-black text-slate-200 mt-1 font-mono">
              {formatINR(monthlyIncome * 0.50)}
            </p>
            <p className="text-[11px] text-slate-500 mt-1">Housing, Groceries, EMIs & Bills</p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-xs text-slate-400">Wants (30% Ideal)</span>
            <p className="text-lg font-black text-slate-200 mt-1 font-mono">
              {formatINR(monthlyIncome * 0.30)}
            </p>
            <p className="text-[11px] text-slate-500 mt-1">Dining, Travel, Subscriptions & Leisure</p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-xs text-slate-400">Savings & Investments (20% Target)</span>
            <p className="text-lg font-black text-emerald-400 mt-1 font-mono">
              {formatINR(monthlyIncome * 0.20)}
            </p>
            <p className="text-[11px] text-slate-500 mt-1">Liquid reserve, SIPs, Debt pre-payments</p>
          </div>
        </div>
      </div>

      {/* CSV Bank Statement Import Card */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              <span>Import Bank Statement (CSV)</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Supports HDFC, ICICI, SBI, Axis, Zerodha, and standard CSV statements with duplicate detection.
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
          />
          <button
            onClick={uploadAndPreview}
            disabled={!file || isUploading}
            className="w-full sm:w-auto px-4 py-2 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-xl shrink-0 transition-all shadow-md shadow-emerald-500/20"
          >
            {isUploading ? 'Validating...' : 'Upload & Preview'}
          </button>
        </div>

        {error && (
          <p className="text-xs text-rose-400 bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20">
            {error}
          </p>
        )}

        {/* CSV Preview Results Table */}
        {previewData && (
          <div className="mt-4 p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-4 animate-in fade-in duration-200">
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-4">
                <span className="text-slate-300">Total: <strong>{previewData.total_rows}</strong></span>
                <span className="text-emerald-400 font-semibold">Valid New: <strong>{previewData.valid_rows}</strong></span>
                <span className="text-amber-400 font-semibold">Duplicates: <strong>{previewData.duplicate_rows}</strong></span>
                <span className="text-rose-400 font-semibold">Invalid: <strong>{previewData.invalid_rows}</strong></span>
              </div>
              <button
                onClick={confirmImport}
                disabled={previewData.valid_rows === 0 || isConfirming}
                className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-xl shadow-md shadow-emerald-500/20"
              >
                {isConfirming ? 'Importing...' : `Confirm Import (${previewData.valid_rows} txns)`}
              </button>
            </div>

            <div className="max-h-56 overflow-y-auto border border-slate-800/80 rounded-lg">
              <table className="w-full text-left text-[11px] text-slate-300">
                <thead className="bg-slate-900 sticky top-0 text-slate-400 uppercase text-[9px] tracking-wider">
                  <tr>
                    <th className="py-2 px-3">Date</th>
                    <th className="py-2 px-3">Description</th>
                    <th className="py-2 px-3">Category</th>
                    <th className="py-2 px-3 text-right">Amount</th>
                    <th className="py-2 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {previewData.preview.map((row: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/20">
                      <td className="py-2 px-3 font-mono text-slate-400">{row.date}</td>
                      <td className="py-2 px-3 text-slate-200 truncate max-w-xs">{row.description}</td>
                      <td className="py-2 px-3 text-slate-400">{row.category}</td>
                      <td className="py-2 px-3 text-right font-mono font-bold text-slate-200">
                        {row.type === 'income' ? '+' : '-'} ₹{row.amount}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {row.is_duplicate ? (
                          <span className="px-1.5 py-0.5 rounded text-[9px] bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            Duplicate
                          </span>
                        ) : row.is_valid ? (
                          <span className="px-1.5 py-0.5 rounded text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Ready
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded text-[9px] bg-rose-500/10 text-rose-400 border border-rose-500/20" title={row.validation_error}>
                            Invalid
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Transaction History Filter & Table */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <h2 className="text-sm font-bold text-slate-100">Transaction History ({filteredTxns.length})</h2>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-60">
              <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search transactions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as any)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Types</option>
              <option value="income">Income Only</option>
              <option value="expense">Expenses Only</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Date</th>
                <th className="py-2.5 px-4 font-semibold">Description</th>
                <th className="py-2.5 px-4 font-semibold">Category</th>
                <th className="py-2.5 px-4 font-semibold">Source</th>
                <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                <th className="py-2.5 px-4 font-semibold text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {filteredTxns.length > 0 ? (
                filteredTxns.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-400">{t.date}</td>
                    <td className="py-3 px-4 text-slate-200 font-semibold">{t.description}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">
                        {t.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-400 capitalize">{t.source.replace('_', ' ')}</td>
                    <td className={`py-3 px-4 text-right font-mono font-bold ${t.type === 'income' ? 'text-emerald-400' : 'text-slate-200'}`}>
                      {t.type === 'income' ? '+' : '-'} {formatINR(t.amount)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleDelete(t.id)}
                        className="text-slate-500 hover:text-rose-400 p-1 rounded transition-colors"
                        title="Delete transaction"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No matching transactions found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
