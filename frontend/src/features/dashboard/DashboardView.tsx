import React from 'react';
import {
  TrendingUp,
  Wallet,
  ShieldCheck,
  ShieldAlert,
  Target,
  ArrowUpRight,
  Sparkles,
  Calendar,
  Layers,
  ArrowRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { FinancialHealthSummary, Transaction, FinancialGoal } from '../../types';
import { Card, Badge, MetricCard, Button, PageHeader } from '../../components/ui';

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
  // Cash flow trend data points
  const chartData = [
    { month: 'Nov', income: 140000, expenses: 62000, surplus: 78000 },
    { month: 'Dec', income: 142000, expenses: 74000, surplus: 68000 },
    { month: 'Jan', income: 145000, expenses: 66000, surplus: 79000 },
    { month: 'Feb', income: 145000, expenses: 64000, surplus: 81000 },
    { month: 'Mar', income: 155000, expenses: 71000, surplus: 84000 },
    {
      month: 'Apr',
      income: summary?.monthly_income || 145000,
      expenses: summary?.monthly_expenses || 68000,
      surplus: summary?.monthly_surplus || 77000,
    },
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
      {/* Page Header */}
      <PageHeader
        title="Financial Overview"
        description="Real-time deterministic aggregation of your net worth, cash flow runway, and milestone trajectories."
        icon={<TrendingUp className="w-4 h-4 text-[#6478E8]" />}
        badge={
          isDemoActive ? (
            <Badge variant="peach" size="sm">
              Demo Profile Active
            </Badge>
          ) : (
            <Badge variant="mint" size="sm">
              Live Profile
            </Badge>
          )
        }
        actions={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onNavigateToTab('tax')}
              icon={<ArrowUpRight className="w-3.5 h-3.5 text-[#6478E8]" />}
              iconPosition="right"
            >
              Plan FY25 Tax
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => onNavigateToTab('scenarios')}
              icon={<Sparkles className="w-3.5 h-3.5" />}
            >
              Simulate Decision
            </Button>
          </>
        }
      />

      {/* 4 Core Financial Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Estimated Net Worth */}
        <MetricCard
          label="Estimated Net Worth"
          value={formatINR(summary?.net_worth || 0)}
          icon={<TrendingUp className="w-4 h-4" />}
          iconTone="lavender"
          subtext={
            <div className="flex items-center justify-between w-full text-[11px]">
              <span className="text-[#16865C] font-semibold">
                {formatINR(summary?.total_assets || 0)} Assets
              </span>
              <span className="text-[#E6EAF0]">•</span>
              <span className="text-[#D9485F] font-semibold">
                {formatINR(summary?.total_liabilities || 0)} Debt
              </span>
            </div>
          }
        />

        {/* Monthly Cash Surplus & Savings Rate */}
        <MetricCard
          label="Monthly Cash Surplus"
          value={formatINR(summary?.monthly_surplus || 0)}
          icon={<Wallet className="w-4 h-4" />}
          iconTone="mint"
          subtext={
            <div className="flex items-center justify-between w-full text-[11px]">
              <span className="text-[#16865C] font-bold">
                {summary?.savings_rate || 0}% Savings Rate
              </span>
              <span className="text-[#697386]">
                Income {formatINR(summary?.monthly_income || 0)}
              </span>
            </div>
          }
        />

        {/* Emergency Reserve Runway */}
        <MetricCard
          label="Emergency Reserve Runway"
          value={`${emergencyMonths} Months`}
          icon={isEmergencyGood ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
          iconTone={isEmergencyGood ? 'mint' : 'peach'}
          progress={{
            current: emergencyMonths,
            target: 6,
            color: isEmergencyGood ? 'bg-[#16865C]' : 'bg-[#B7791F]',
          }}
          subtext={
            <div className="flex items-center justify-between w-full text-[11px]">
              <span className={isEmergencyGood ? 'text-[#16865C] font-semibold' : 'text-[#B7791F] font-semibold'}>
                {isEmergencyGood ? 'Target Met (6 mo)' : 'Target: 6 months'}
              </span>
              <span className="text-[#697386]">
                {formatINR(summary?.emergency_fund_current || 0)}
              </span>
            </div>
          }
        />

        {/* Active Milestones */}
        <MetricCard
          label="Active Milestones"
          value={`${goals.length} Goals`}
          icon={<Target className="w-4 h-4" />}
          iconTone="blue"
          subtext={
            <div className="flex items-center justify-between w-full text-[11px] truncate">
              <span className="text-[#697386] truncate">
                {goals[0] ? `Next: ${goals[0].name}` : 'No active targets'}
              </span>
              {goals[0] && (
                <span className="text-[#6478E8] font-bold shrink-0 ml-1">
                  {goals[0].progress_pct || 0}%
                </span>
              )}
            </div>
          }
        />
      </div>

      {/* Main Charts & Goals Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cash Flow Trends Chart */}
        <Card className="lg:col-span-2 min-w-0 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-bold text-[#172033]">
                Monthly Cash Flow & Surplus Trends
              </h2>
              <p className="text-xs text-[#697386]">
                Income vs living expenses with net retained surplus across recent months.
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs font-semibold">
              <span className="flex items-center gap-1.5 text-[#172033]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#16865C] inline-block" /> Income
              </span>
              <span className="flex items-center gap-1.5 text-[#172033]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#D9485F] inline-block" /> Expenses
              </span>
              <span className="flex items-center gap-1.5 text-[#172033]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#6478E8] inline-block" /> Surplus
              </span>
            </div>
          </div>

          <div className="h-64 sm:h-72 w-full min-w-0 pt-2">
            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="incomeFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#16865C" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#16865C" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="expenseFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#D9485F" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#D9485F" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E6EAF0" vertical={false} />
                <XAxis
                  dataKey="month"
                  stroke="#697386"
                  tick={{ fontSize: 12, fill: '#697386' }}
                  tickLine={false}
                  axisLine={{ stroke: '#E6EAF0' }}
                />
                <YAxis
                  stroke="#697386"
                  tick={{ fontSize: 11, fill: '#697386' }}
                  tickLine={false}
                  axisLine={{ stroke: '#E6EAF0' }}
                  tickFormatter={(val) => `₹${val / 1000}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E6EAF0',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(23, 32, 51, 0.08)',
                    fontSize: '12px',
                    color: '#172033',
                  }}
                  formatter={(val: any) => [formatINR(Number(val)), '']}
                />
                <Area
                  type="monotone"
                  dataKey="income"
                  stroke="#16865C"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#incomeFill)"
                />
                <Area
                  type="monotone"
                  dataKey="expenses"
                  stroke="#D9485F"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#expenseFill)"
                />
                <Line
                  type="monotone"
                  dataKey="surplus"
                  stroke="#6478E8"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#6478E8' }}
                  activeDot={{ r: 5 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>


        {/* Goals Progress Card */}
        <Card className="flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-base font-bold text-[#172033]">Target Milestones</h2>
                <p className="text-xs text-[#697386]">Priority goal horizons</p>
              </div>
              <button
                onClick={() => onNavigateToTab('goals')}
                className="text-xs text-[#6478E8] hover:underline font-semibold"
              >
                View All
              </button>
            </div>

            <div className="space-y-3">
              {goals.length > 0 ? (
                goals.slice(0, 3).map((goal) => (
                  <div
                    key={goal.id}
                    className="p-3.5 rounded-xl bg-[#F6F8FC] border border-[#E6EAF0] space-y-2 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-[#172033]">{goal.name}</span>
                      <span className="text-[#16865C] font-bold tabular-nums">
                        {goal.progress_pct}%
                      </span>
                    </div>
                    <div className="w-full bg-[#E6EAF0] h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-[#16865C] h-full rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(100, goal.progress_pct || 0)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-[#697386] tabular-nums">
                      <span>{formatINR(goal.current_amount)}</span>
                      <span>Target: {formatINR(goal.target_amount)}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-[#697386] text-xs">
                  No financial goals created yet. Click below to add your first milestone.
                </div>
              )}
            </div>
          </div>

          <Button
            variant="soft"
            size="sm"
            onClick={() => onNavigateToTab('goals')}
            className="w-full mt-4"
          >
            + Add New Financial Goal
          </Button>
        </Card>
      </div>

      {/* Recent Activity Table */}
      <Card className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-[#172033]">
              Recent Financial Transactions
            </h2>
            <p className="text-xs text-[#697386]">
              Verified cash flow movements across your linked Indian bank accounts.
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigateToTab('budget')}
            icon={<ArrowRight className="w-3.5 h-3.5 text-[#6478E8]" />}
            iconPosition="right"
          >
            Manage Transactions & CSV
          </Button>
        </div>

        <div className="overflow-x-auto -mx-5 sm:mx-0">
          <table className="w-full text-left text-xs text-[#172033]">
            <thead className="bg-[#F6F8FC] text-[#697386] uppercase text-[10px] tracking-wider border-y border-[#E6EAF0]">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Date</th>
                <th className="py-2.5 px-4 font-semibold">Description</th>
                <th className="py-2.5 px-4 font-semibold">Category</th>
                <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E6EAF0] font-medium">
              {recentTxns.length > 0 ? (
                recentTxns.slice(0, 5).map((txn) => (
                  <tr key={txn.id} className="hover:bg-[#F6F8FC] transition-colors">
                    <td className="py-3 px-4 text-[#697386] tabular-nums font-mono">{txn.date}</td>
                    <td className="py-3 px-4 text-[#172033] font-semibold">{txn.description}</td>
                    <td className="py-3 px-4">
                      <Badge variant="neutral" size="sm">
                        {txn.category}
                      </Badge>
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-bold tabular-nums ${
                        txn.type === 'income' ? 'text-[#16865C]' : 'text-[#172033]'
                      }`}
                    >
                      {txn.type === 'income' ? '+' : '-'} {formatINR(txn.amount)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-[#697386]">
                    No transactions recorded yet. Click &apos;Load Demo Profile&apos; above or import bank statement CSV.
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
