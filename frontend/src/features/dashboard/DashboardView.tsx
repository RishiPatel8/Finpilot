import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  ShieldCheck,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  PiggyBank,
  Target,
  Sparkles
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { FinancialHealthSummary, Transaction, FinancialGoal } from '../../types';

interface DashboardViewProps {
  summary: FinancialHealthSummary | null;
  recentTxns: Transaction[];
  goals: FinancialGoal[];
  isDemoActive: boolean;
  onNavigateToTab: (tab: any) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  summary,
  recentTxns,
  goals,
  isDemoActive,
  onNavigateToTab,
}) => {
  // Chart trend data points (either derived or baseline monthly flow)
  const chartData = [
    { month: 'Nov', income: 140000, expenses: 62000, surplus: 78000 },
    { month: 'Dec', income: 142000, expenses: 74000, surplus: 68000 },
    { month: 'Jan', income: 145000, expenses: 66000, surplus: 79000 },
    { month: 'Feb', income: 145000, expenses: 64000, surplus: 81000 },
    { month: 'Mar', income: 155000, expenses: 71000, surplus: 84000 },
    { month: 'Apr', income: summary?.monthly_income || 145000, expenses: summary?.monthly_expenses || 68000, surplus: summary?.monthly_surplus || 77000 },
  ];

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const emergencyMonths = summary?.emergency_fund_months || 0;
  const isEmergencyGood = emergencyMonths >= 6;

  return (
    <div className="space-y-6">
      {/* Top Banner indicating Live vs Demo Data */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/40 border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-slate-100">Financial Command Center</h1>
            {isDemoActive ? (
              <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                Synthetic Demo Data Active
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Live Data
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time deterministic aggregation of your assets, liabilities, and monthly cash flow.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigateToTab('tax')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors"
          >
            <span>Plan FY25 Tax</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
          </button>
          <button
            onClick={() => onNavigateToTab('assistant')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-xs font-bold text-slate-950 shadow-md shadow-emerald-500/20 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask AI Assistant</span>
          </button>
        </div>
      </div>

      {/* 4 Core Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Net Worth */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Estimated Net Worth</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-100 tracking-tight">
            {formatINR(summary?.net_worth || 0)}
          </p>
          <div className="flex items-center gap-2 mt-3 text-[11px] text-slate-400">
            <span className="text-emerald-400 font-semibold">{formatINR(summary?.total_assets || 0)}</span> assets
            <span>•</span>
            <span className="text-rose-400 font-semibold">{formatINR(summary?.total_liabilities || 0)}</span> liabilities
          </div>
        </div>

        {/* Monthly Surplus & Savings Rate */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Monthly Cash Surplus</span>
            <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-100 tracking-tight">
            {formatINR(summary?.monthly_surplus || 0)}
          </p>
          <div className="flex items-center gap-2 mt-3 text-[11px] text-slate-400">
            <span className="text-teal-400 font-bold">{summary?.savings_rate || 0}%</span> savings rate
            <span>•</span>
            <span>Income {formatINR(summary?.monthly_income || 0)}</span>
          </div>
        </div>

        {/* Emergency Fund Runway */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Emergency Reserve Runway</span>
            <div className={`p-2 rounded-xl ${isEmergencyGood ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
              {isEmergencyGood ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-black text-slate-100 tracking-tight">
              {emergencyMonths} <span className="text-sm font-semibold text-slate-400">months</span>
            </p>
            <span className="text-[11px] text-slate-400">/ 6 target</span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-800 h-2 rounded-full mt-3 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${isEmergencyGood ? 'bg-emerald-500' : 'bg-amber-500'}`}
              style={{ width: `${Math.min(100, (emergencyMonths / 6) * 100)}%` }}
            />
          </div>
        </div>

        {/* Active Goals Count */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Active Goals</span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
              <Target className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-100 tracking-tight">
            {goals.length} <span className="text-sm font-semibold text-slate-400">Milestones</span>
          </p>
          <p className="text-[11px] text-slate-400 mt-3 truncate">
            {goals[0] ? `Next: ${goals[0].name} (${goals[0].progress_pct || 0}%)` : 'No active targets set'}
          </p>
        </div>
      </div>

      {/* Main Charts & Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 6-Month Cash Flow Trend Chart */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-100">Monthly Cash Flow & Surplus Trends</h2>
              <p className="text-xs text-slate-400">Income vs expenses with net disposable surplus.</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Income
              </span>
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" /> Expenses
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 12 }} />
                <YAxis
                  stroke="#64748b"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(val) => `₹${val / 1000}k`}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  formatter={(val: any) => [formatINR(Number(val)), '']}
                />
                <Area type="monotone" dataKey="income" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorIncome)" />
                <Area type="monotone" dataKey="expenses" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorExpense)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Goals Progress Card */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-bold text-slate-100">Financial Goals</h2>
              <button
                onClick={() => onNavigateToTab('goals')}
                className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold"
              >
                View All
              </button>
            </div>

            <div className="space-y-3.5">
              {goals.length > 0 ? (
                goals.slice(0, 3).map((goal) => (
                  <div key={goal.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-200">{goal.name}</span>
                      <span className="text-emerald-400 font-bold">{goal.progress_pct}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(100, goal.progress_pct || 0)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>{formatINR(goal.current_amount)}</span>
                      <span>Target: {formatINR(goal.target_amount)}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No financial goals added yet. Click &apos;Goal Planner&apos; to create one.
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => onNavigateToTab('goals')}
            className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition-colors"
          >
            + Add New Financial Goal
          </button>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-100">Recent Financial Transactions</h2>
            <p className="text-xs text-slate-400">Verified cash flow movements across your accounts.</p>
          </div>
          <button
            onClick={() => onNavigateToTab('budget')}
            className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold"
          >
            Import CSV & View All
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/50 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Date</th>
                <th className="py-2.5 px-4 font-semibold">Description</th>
                <th className="py-2.5 px-4 font-semibold">Category</th>
                <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {recentTxns.length > 0 ? (
                recentTxns.slice(0, 5).map((txn) => (
                  <tr key={txn.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 text-slate-400">{txn.date}</td>
                    <td className="py-3 px-4 text-slate-200 font-semibold">{txn.description}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">
                        {txn.category}
                      </span>
                    </td>
                    <td className={`py-3 px-4 text-right font-bold ${txn.type === 'income' ? 'text-emerald-400' : 'text-slate-200'}`}>
                      {txn.type === 'income' ? '+' : '-'} {formatINR(txn.amount)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-500">
                    No transactions recorded yet. Click &apos;Load Demo Profile&apos; above or import bank statement CSV.
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
