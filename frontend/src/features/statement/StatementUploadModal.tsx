import React, { useState, useRef, useMemo } from 'react';
import {
  Upload,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  AlertTriangle,
  X,
  Search,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Building2,
  Calendar,
  Layers,
  ShieldCheck,
  RefreshCw,
  Info,
  Filter,
  ArrowUpDown,
  RotateCcw
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { StatementPreviewResponse, StatementPreviewRow } from '../../types';
import { Card, Badge, Button } from '../../components/ui';

interface StatementUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const StatementUploadModal: React.FC<StatementUploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<StatementPreviewResponse | null>(null);

  // Filter & Sort States
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'income' | 'expense' | 'transfer'>('all');
  const [filterStatus, setFilterStatus] = useState<'all' | 'new' | 'duplicate'>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'amount_desc' | 'amount_asc'>('date_desc');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      selectFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      selectFile(e.target.files[0]);
    }
  };

  const selectFile = (selected: File) => {
    const ext = selected.name.toLowerCase();
    if (!ext.endsWith('.csv') && !ext.endsWith('.xlsx') && !ext.endsWith('.xls') && !ext.endsWith('.pdf')) {
      setError('Please select a valid bank statement in CSV, XLSX, or PDF format.');
      return;
    }
    setFile(selected);
    setError(null);
    setPreviewData(null);
  };

  const handleUploadAndAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiRequest<StatementPreviewResponse>('/statement/preview', {
        method: 'POST',
        headers: {}, // Do NOT set Content-Type; browser handles multipart boundary
        body: formData,
      });

      if (!res.success) {
        setError(res.error || 'Failed to parse statement. Please ensure it is not password-protected.');
      } else {
        setPreviewData(res);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze statement. Check network or file integrity.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!previewData || !previewData.preview) return;
    setConfirming(true);
    setError(null);

    try {
      const validTxns = previewData.preview.filter((r) => r.is_valid && !r.is_duplicate);

      await apiRequest('/statement/confirm', {
        method: 'POST',
        body: JSON.stringify({
          filename: previewData.filename,
          file_format: previewData.format,
          metadata: previewData.metadata || {},
          transactions: validTxns.map((t) => ({
            date: t.date,
            value_date: t.value_date,
            description: t.description,
            amount: t.amount,
            type: t.type,
            category: t.category,
            raw_type: t.raw_type,
            is_internal_transfer: t.is_internal_transfer,
            reference_number: t.reference_number,
            balance_after: t.balance_after,
            source_row: t.source_row,
            is_duplicate: t.is_duplicate,
          })),
        }),
      });

      // Dispatch real-time refresh event across application
      window.dispatchEvent(new CustomEvent('finpilot:financial-data-updated'));
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to confirm statement import.');
    } finally {
      setConfirming(false);
    }
  };

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  // Extract unique categories available in the statement
  const availableCategories = useMemo(() => {
    if (!previewData?.preview) return [];
    const set = new Set<string>();
    previewData.preview.forEach((r) => {
      if (r.category) set.add(r.category);
    });
    return Array.from(set).sort();
  }, [previewData]);

  // Comprehensive multi-criteria filtering and sorting
  const filteredRows = useMemo(() => {
    if (!previewData?.preview) return [];

    let rows = previewData.preview.filter((r) => {
      const q = searchTerm.trim().toLowerCase();
      const matchesSearch =
        !q ||
        r.description.toLowerCase().includes(q) ||
        r.category.toLowerCase().includes(q) ||
        (r.reference_number && r.reference_number.toLowerCase().includes(q));

      const matchesType = filterType === 'all' || r.type === filterType;

      const matchesStatus =
        filterStatus === 'all' ||
        (filterStatus === 'new' && !r.is_duplicate) ||
        (filterStatus === 'duplicate' && r.is_duplicate);

      const matchesCategory =
        filterCategory === 'all' || r.category === filterCategory;

      return matchesSearch && matchesType && matchesStatus && matchesCategory;
    });

    // Sort order
    rows = [...rows].sort((a, b) => {
      if (sortBy === 'date_desc') return b.date.localeCompare(a.date);
      if (sortBy === 'date_asc') return a.date.localeCompare(b.date);
      if (sortBy === 'amount_desc') return b.amount - a.amount;
      if (sortBy === 'amount_asc') return a.amount - b.amount;
      return 0;
    });

    return rows;
  }, [previewData, searchTerm, filterType, filterStatus, filterCategory, sortBy]);

  const hasActiveFilters = searchTerm !== '' || filterType !== 'all' || filterStatus !== 'all' || filterCategory !== 'all' || sortBy !== 'date_desc';

  const resetFilters = () => {
    setSearchTerm('');
    setFilterType('all');
    setFilterStatus('all');
    setFilterCategory('all');
    setSortBy('date_desc');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#172033]/50 backdrop-blur-sm transition-opacity"
        onClick={() => !loading && !confirming && onClose()}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-white border border-[#E6EAF0] rounded-2xl shadow-[0_25px_50px_-12px_rgba(23,32,51,0.25)] flex flex-col z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#E6EAF0] flex items-center justify-between bg-white shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#EEF0FF] text-[#6478E8] flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#172033]">
                {previewData ? 'Review Statement Transactions' : 'Import Bank Statement'}
              </h2>
              <p className="text-xs text-[#697386]">
                {previewData
                  ? `Extracted ${previewData.total_rows} rows from ${previewData.filename} (${previewData.coverage?.coverage_months ?? 0} months analyzed)`
                  : 'Upload your genuine bank statement (CSV, XLSX, or PDF) for deterministic financial analysis.'}
              </p>
            </div>
          </div>

          <button
            onClick={() => !loading && !confirming && onClose()}
            className="p-1.5 rounded-xl text-[#697386] hover:text-[#172033] hover:bg-[#F6F8FC] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {error && (
            <div className="p-4 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 flex items-start gap-3 text-xs text-[#D9485F]">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Extraction Issue</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {!previewData ? (
            /* Upload Zone */
            <div className="space-y-6">
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 ${
                  isDragging
                    ? 'border-[#6478E8] bg-[#EEF0FF]/40'
                    : 'border-[#D1D9E6] hover:border-[#6478E8] hover:bg-[#F6F8FC]'
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileInput}
                  accept=".csv,.xlsx,.xls,.pdf"
                  className="hidden"
                />

                <div className="w-14 h-14 rounded-2xl bg-[#EEF0FF] text-[#6478E8] flex items-center justify-center">
                  <Upload className="w-7 h-7" />
                </div>

                {file ? (
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-[#172033]">{file.name}</p>
                    <p className="text-xs text-[#697386]">
                      {(file.size / 1024).toFixed(1)} KB · Ready to analyze
                    </p>
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <p className="text-sm font-bold text-[#172033]">
                      Drag & drop your statement here, or <span className="text-[#6478E8]">browse files</span>
                    </p>
                    <p className="text-xs text-[#697386]">
                      Compatible with CSV, Excel (.xlsx/.xls), and PDF statements from HDFC, SBI, ICICI, Axis, Kotak, and more.
                    </p>
                  </div>
                )}

                <div className="flex flex-wrap items-center justify-center gap-2 mt-2">
                  <Badge variant="blue" size="sm">CSV Format</Badge>
                  <Badge variant="blue" size="sm">Excel (XLSX / XLS)</Badge>
                  <Badge variant="blue" size="sm">PDF Statements</Badge>
                  <Badge variant="mint" size="sm">3 Months Recommended</Badge>
                </div>
              </div>

              {/* Security & Truth Disclaimer */}
              <div className="p-4 rounded-xl bg-[#F6F8FC] border border-[#E6EAF0] flex items-start gap-3 text-xs text-[#697386]">
                <ShieldCheck className="w-4 h-4 text-[#16865C] shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="font-bold text-[#172033]">Data Protection & Strict Determinism</p>
                  <p>
                    Your bank statement is processed securely on your authenticated account. Original statement files are never logged or stored. Calculations are 100% deterministic with zero mock or synthetic estimates.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <Button variant="ghost" size="md" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleUploadAndAnalyze}
                  disabled={!file || loading}
                  loading={loading}
                  icon={<ArrowRight className="w-4 h-4" />}
                >
                  {loading ? 'Extracting & Validating...' : 'Upload & Analyze'}
                </Button>
              </div>
            </div>
          ) : (
            /* Review & Preview Zone */
            <div className="space-y-5">
              {/* Coverage & KPI Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E6EAF0]">
                  <p className="text-[11px] font-semibold text-[#697386]">Analysis Period</p>
                  <p className="text-sm font-bold text-[#172033] mt-0.5">
                    {previewData.coverage?.coverage_months ?? 0} Months
                  </p>
                  <p className="text-[10px] text-[#697386]">
                    {previewData.coverage?.start_date || '—'} to {previewData.coverage?.end_date || '—'}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E6EAF0]">
                  <p className="text-[11px] font-semibold text-[#697386]">Verified Inflow (Credits)</p>
                  <p className="text-sm font-bold text-[#16865C] mt-0.5">
                    {formatINR(previewData.financial_summary.total_credits)}
                  </p>
                  <p className="text-[10px] text-[#697386]">Excluding transfers</p>
                </div>

                <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E6EAF0]">
                  <p className="text-[11px] font-semibold text-[#697386]">Verified Outflow (Debits)</p>
                  <p className="text-sm font-bold text-[#D9485F] mt-0.5">
                    {formatINR(previewData.financial_summary.total_debits)}
                  </p>
                  <p className="text-[10px] text-[#697386]">Expenses & commitments</p>
                </div>

                <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E6EAF0]">
                  <p className="text-[11px] font-semibold text-[#697386]">Ending Balance</p>
                  <p className="text-sm font-bold text-[#6478E8] mt-0.5">
                    {previewData.metadata?.closing_balance !== null && previewData.metadata?.closing_balance !== undefined
                      ? formatINR(previewData.metadata.closing_balance)
                      : 'Not in statement'}
                  </p>
                  <p className="text-[10px] text-[#697386] truncate">
                    {previewData.metadata?.bank_name || 'Bank Statement'} ({previewData.metadata?.account_number_masked || 'Verified'})
                  </p>
                </div>
              </div>

              {/* Warnings Box */}
              {previewData.warnings && previewData.warnings.length > 0 && (
                <div className="p-3 rounded-xl bg-[#FFF9EB] border border-[#B7791F]/30 text-xs text-[#7A4D05] space-y-1">
                  <div className="flex items-center gap-1.5 font-bold">
                    <Info className="w-3.5 h-3.5 text-[#B7791F]" />
                    <span>Statement Observations</span>
                  </div>
                  <ul className="list-disc pl-5 space-y-0.5 text-[11px]">
                    {previewData.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Enhanced Filter Bar: Search, Type, Status, Category, Sort */}
              <div className="space-y-2.5 p-3 rounded-xl bg-[#F8FAFC] border border-[#E6EAF0]">
                {/* Top Row: Search and Type Pills */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="relative w-full sm:w-80">
                    <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-[#697386]" />
                    <input
                      type="text"
                      placeholder="Search description, merchant, ref..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full bg-white border border-[#E6EAF0] rounded-xl pl-9 pr-8 py-1.5 text-xs text-[#172033] placeholder:text-[#8896A6] focus:outline-none focus:border-[#6478E8]"
                    />
                    {searchTerm && (
                      <button
                        onClick={() => setSearchTerm('')}
                        className="absolute right-2.5 top-2.5 text-[#8896A6] hover:text-[#172033]"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  {/* Type Filter Pills */}
                  <div className="flex items-center gap-1 self-start sm:self-auto bg-white p-1 rounded-xl border border-[#E6EAF0]">
                    {(['all', 'income', 'expense', 'transfer'] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => setFilterType(t)}
                        className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                          filterType === t
                            ? 'bg-[#172033] text-white shadow-sm'
                            : 'text-[#697386] hover:text-[#172033] hover:bg-[#F6F8FC]'
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Bottom Row: Status Filter, Category Dropdown, Sort Dropdown & Reset */}
                <div className="flex flex-wrap items-center justify-between gap-2.5 pt-1 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Status Filter */}
                    <div className="flex items-center gap-1 bg-white p-0.5 rounded-lg border border-[#E6EAF0]">
                      <button
                        onClick={() => setFilterStatus('all')}
                        className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                          filterStatus === 'all'
                            ? 'bg-[#172033] text-white'
                            : 'text-[#697386] hover:text-[#172033]'
                        }`}
                      >
                        All Status ({previewData.total_rows})
                      </button>
                      <button
                        onClick={() => setFilterStatus('new')}
                        className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                          filterStatus === 'new'
                            ? 'bg-[#16865C] text-white'
                            : 'text-[#16865C] hover:bg-[#EBF7F2]'
                        }`}
                      >
                        New ({previewData.valid_rows})
                      </button>
                      <button
                        onClick={() => setFilterStatus('duplicate')}
                        className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                          filterStatus === 'duplicate'
                            ? 'bg-[#697386] text-white'
                            : 'text-[#697386] hover:bg-[#F6F8FC]'
                        }`}
                      >
                        Duplicates ({previewData.duplicate_rows})
                      </button>
                    </div>

                    {/* Category Dropdown */}
                    <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-[#E6EAF0]">
                      <Filter className="w-3 h-3 text-[#697386]" />
                      <select
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                        className="bg-transparent text-xs text-[#172033] font-medium focus:outline-none cursor-pointer"
                      >
                        <option value="all">All Categories ({availableCategories.length})</option>
                        {availableCategories.map((cat) => (
                          <option key={cat} value={cat}>
                            {cat}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Sort Dropdown */}
                    <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-[#E6EAF0]">
                      <ArrowUpDown className="w-3 h-3 text-[#697386]" />
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as any)}
                        className="bg-transparent text-xs text-[#172033] font-medium focus:outline-none cursor-pointer"
                      >
                        <option value="date_desc">Date: Newest First</option>
                        <option value="date_asc">Date: Oldest First</option>
                        <option value="amount_desc">Amount: High to Low</option>
                        <option value="amount_asc">Amount: Low to High</option>
                      </select>
                    </div>
                  </div>

                  {/* Results Count & Reset Button */}
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-[#697386]">
                      Showing <strong className="text-[#172033]">{filteredRows.length}</strong> of {previewData.total_rows}
                    </span>
                    {hasActiveFilters && (
                      <button
                        onClick={resetFilters}
                        className="flex items-center gap-1 text-[11px] text-[#6478E8] hover:underline font-medium"
                      >
                        <RotateCcw className="w-3 h-3" />
                        Reset
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Transactions Preview Table */}
              <div className="border border-[#E6EAF0] rounded-xl overflow-hidden max-h-[300px] overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F6F8FC] border-b border-[#E6EAF0] sticky top-0 text-[11px] font-bold text-[#697386]">
                    <tr>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Description / Merchant</th>
                      <th className="py-2.5 px-3">Category</th>
                      <th className="py-2.5 px-3 text-right">Amount</th>
                      <th className="py-2.5 px-3 text-right">Balance</th>
                      <th className="py-2.5 px-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E6EAF0]">
                    {filteredRows.length > 0 ? (
                      filteredRows.map((row, idx) => (
                        <tr
                          key={idx}
                          className={`hover:bg-[#F9FAFC] transition-colors ${row.is_duplicate ? 'opacity-50 bg-[#F6F8FC]/50' : ''}`}
                        >
                          <td className="py-2 px-3 font-mono text-[11px] text-[#424E61] whitespace-nowrap">
                            {row.date}
                          </td>
                          <td className="py-2 px-3 max-w-[260px] truncate text-[#172033]" title={row.description}>
                            <p className="font-medium truncate">{row.description}</p>
                            {row.reference_number && (
                              <p className="text-[10px] text-[#8896A6] font-mono truncate">
                                Ref: {row.reference_number}
                              </p>
                            )}
                          </td>
                          <td className="py-2 px-3 whitespace-nowrap">
                            <Badge variant={row.category === 'Uncategorized' ? 'peach' : 'lavender'} size="sm">
                              {row.category}
                            </Badge>
                          </td>
                          <td
                            className={`py-2 px-3 font-mono font-bold text-right tabular-nums whitespace-nowrap ${
                              row.type === 'income'
                                ? 'text-[#16865C]'
                                : row.type === 'transfer'
                                ? 'text-[#6478E8]'
                                : 'text-[#172033]'
                            }`}
                          >
                            {row.type === 'income' ? '+' : row.type === 'expense' ? '-' : ''}
                            {formatINR(row.amount)}
                          </td>
                          <td className="py-2 px-3 font-mono text-right text-[11px] text-[#697386] tabular-nums whitespace-nowrap">
                            {row.balance_after !== null && row.balance_after !== undefined
                              ? formatINR(row.balance_after)
                              : '—'}
                          </td>
                          <td className="py-2 px-3 text-center whitespace-nowrap">
                            {row.is_duplicate ? (
                              <Badge variant="neutral" size="sm">
                                Duplicate
                              </Badge>
                            ) : (
                              <Badge variant="mint" size="sm">
                                New
                              </Badge>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-10 text-center text-[#697386]">
                          <p className="font-semibold text-sm">No transactions match current filters</p>
                          <p className="text-xs text-[#8896A6] mt-1">Try resetting search or selecting "All Status".</p>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-2 border-t border-[#E6EAF0]">
                <Button
                  variant="ghost"
                  size="md"
                  onClick={() => setPreviewData(null)}
                  disabled={confirming}
                >
                  Upload Different File
                </Button>

                <div className="flex items-center gap-3">
                  <Button variant="ghost" size="md" onClick={onClose} disabled={confirming}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleConfirmImport}
                    disabled={confirming || previewData.valid_rows === 0}
                    icon={confirming ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  >
                    {confirming
                      ? 'Persisting & Recalculating...'
                      : `Confirm & Import ${previewData.valid_rows} Transactions`}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
