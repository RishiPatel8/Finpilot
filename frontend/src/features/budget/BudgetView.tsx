import React, { useState } from 'react';
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
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { Transaction } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';

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
      />

      {/* 50/30/20 Rule Analysis Widget */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#6478E8]" />
              <span>50 / 30 / 20 Cash Flow Allocation Framework</span>
            </h2>
            <p className="text-xs text-[#697386]">
              Standard recommended allocation benchmarked against your net monthly income of {formatINR(monthlyIncome)}.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Needs */}
          <div className="p-4 rounded-2xl bg-[#E8F2FF]/60 border border-[#E8F2FF] space-y-1">
            <span className="text-xs font-semibold text-[#2B6CB0]">Needs (50% Target)</span>
            <p className="text-xl font-extrabold text-[#172033] font-mono tabular-nums">
              {formatINR(monthlyIncome * 0.50)}
            </p>
            <p className="text-[11px] text-[#697386]">
              Rent, Groceries, EMIs, Utilities & Healthcare
            </p>
          </div>

          {/* Wants */}
          <div className="p-4 rounded-2xl bg-[#FFF0E5]/60 border border-[#FFF0E5] space-y-1">
            <span className="text-xs font-semibold text-[#B7791F]">Wants (30% Target)</span>
            <p className="text-xl font-extrabold text-[#172033] font-mono tabular-nums">
              {formatINR(monthlyIncome * 0.30)}
            </p>
            <p className="text-[11px] text-[#697386]">
              Dining out, Travel, Subscriptions & Hobbies
            </p>
          </div>

          {/* Savings */}
          <div className="p-4 rounded-2xl bg-[#E5F7EF]/60 border border-[#E5F7EF] space-y-1">
            <span className="text-xs font-semibold text-[#16865C]">Savings & Investments (20% Target)</span>
            <p className="text-xl font-extrabold text-[#16865C] font-mono tabular-nums">
              {formatINR(monthlyIncome * 0.20)}
            </p>
            <p className="text-[11px] text-[#697386]">
              Liquid funds, SIPs, PPF, Pre-payments
            </p>
          </div>
        </div>
      </Card>

      {/* CSV Bank Statement Import Card */}
      <Card className="space-y-4">
        <div>
          <h2 className="text-base font-bold text-[#172033] flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-[#6478E8]" />
            <span>Import Bank Statement (CSV)</span>
          </h2>
          <p className="text-xs text-[#697386] mt-0.5">
            Compatible with HDFC, ICICI, SBI, Axis, Kotak, and standard bank exports with automatic duplicate suppression.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="w-full text-xs text-[#697386] file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border file:border-[#E6EAF0] file:text-xs file:font-semibold file:bg-[#F6F8FC] file:text-[#172033] hover:file:bg-slate-100 cursor-pointer"
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
            {isUploading ? 'Validating CSV...' : 'Upload & Validate'}
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
                  Valid New: <strong>{previewData.valid_rows}</strong>
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
                disabled={previewData.valid_rows === 0 || isConfirming}
                loading={isConfirming}
              >
                {isConfirming
                  ? 'Importing...'
                  : `Confirm Import (${previewData.valid_rows} txns)`}
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
                  {previewData.preview.map((row: any, idx: number) => (
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
    </div>
  );
};
