import React, { useMemo, useState, useEffect } from 'react';
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
  Zap,
  AlertCircle,
  Lightbulb,
  FileSpreadsheet,
  Upload,
  CheckCircle2,
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
import { apiRequest, getAuthToken } from '../../services/api';
import { FinancialHealthSummary, Transaction, FinancialGoal, FinancialInsight } from '../../types';
import { Card, Badge, MetricCard, Button, PageHeader } from '../../components/ui';
import { KnowMore } from '../../components/KnowMore';

interface DashboardViewProps {
  summary: FinancialHealthSummary | null;
  recentTxns: Transaction[];
  goals: FinancialGoal[];
  onNavigateToTab: (tab: any) => void;
  onOpenStatementModal?: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  summary,
  recentTxns,
  goals,
  onNavigateToTab,
  onOpenStatementModal,
}) => {
  const [insights, setInsights] = useState<FinancialInsight[]>([]);
  const [loadingInsights, setLoadingInsights] = useState(false);

  useEffect(() => {
    if (getAuthToken()) {
      setLoadingInsights(true);
      apiRequest<any>('/intelligence/feed')
        .then((res) => {
          if (res && res.insights) {
            setInsights(res.insights);
          } else {
            setInsights([]);
          }
        })
        .catch((err) => {
          console.warn('Could not load intelligence feed:', err);
          setInsights([]);
        })
        .finally(() => setLoadingInsights(false));
    } else {
      setInsights([]);
    }
  }, []);

  // Cash flow trend data points: strictly computed from verified monthly history
  const chartData = useMemo(() => {
    if (summary?.monthly_history && summary.monthly_history.length > 0) {
      return summary.monthly_history.map((m) => ({
        month: m.month,
        income: m.income,
        expenses: m.expenses,
        surplus: m.surplus,
      }));
    }
    return [];
  }, [summary]);

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
        icon={<TrendingUp className="w-4 h-4 text-[#F5DE88]" />}
        badge={
          summary?.statement_coverage ? (
            <Badge variant="mint" size="sm" className="bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30">
              {summary.statement_coverage?.coverage_months ?? 0} Mo Statement Verified ({summary.statement_coverage?.total_transactions ?? 0} txns)
            </Badge>
          ) : summary?.is_empty || !summary ? (
            <Badge variant="peach" size="sm" className="bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30">
              Awaiting Bank Statement
            </Badge>
          ) : (
            <Badge variant="lavender" size="sm" className="bg-[#D4AF37]/15 text-[#F5DE88] border-[#D4AF37]/30">
              Live Profile
            </Badge>
          )
        }
        actions={
          <>
            {onOpenStatementModal && (
              <Button
                variant="primary"
                size="sm"
                onClick={onOpenStatementModal}
                icon={<FileSpreadsheet className="w-3.5 h-3.5" />}
              >
                Upload Statement
              </Button>
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onNavigateToTab('tax')}
              icon={<ArrowUpRight className="w-3.5 h-3.5 text-[#F5DE88]" />}
              iconPosition="right"
            >
              Plan FY25 Tax
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onNavigateToTab('scenarios')}
              icon={<Sparkles className="w-3.5 h-3.5 text-[#F5DE88]" />}
            >
              Simulate Decision
            </Button>
          </>
        }
      />

      {/* Zero Mock Data Onboarding Card */}
      {(!summary || summary.is_empty || recentTxns.length === 0) && (
        <Card className="bg-gradient-to-r from-[#121622] via-[#0E121B] to-[#121622] border-[rgba(212,175,55,0.25)] p-5 sm:p-6 space-y-3 shadow-lg">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-[#F5DE88]" />
                <h2 className="text-base font-bold text-[#F3F4F6]">
                  Connect Real Financial Data: Upload 3-Month Bank Statements
                </h2>
              </div>
              <p className="text-xs text-[#9CA3AF] max-w-2xl leading-relaxed">
                FinPilot operates under a strict <strong>Zero Mock Data</strong> policy. Upload your genuine bank statement (CSV, XLSX, or PDF) to populate your dashboard with deterministic net worth, verified monthly spending, detected subscriptions, and AI CFO intelligence.
              </p>
            </div>
            {onOpenStatementModal && (
              <Button
                variant="primary"
                size="md"
                onClick={onOpenStatementModal}
                icon={<Upload className="w-4 h-4" />}
                className="shrink-0"
              >
                Upload Bank Statement
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* 4 Core Financial Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Estimated Net Worth */}
        <MetricCard
          label={
            <span className="inline-flex items-center gap-1.5">
              <span>Estimated Net Worth</span>
              <KnowMore
                termId="net_worth"
                contextualValue={{
                  label: 'Estimated Net Worth',
                  value: formatINR(summary?.net_worth || 0),
                  isEstimate: false,
                }}
              />
            </span>
          }
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
          label={
            <span className="inline-flex items-center gap-1.5">
              <span>Monthly Cash Surplus</span>
              <KnowMore
                termId="cash_flow"
                contextualValue={{
                  label: 'Monthly Cash Surplus',
                  value: formatINR(summary?.monthly_surplus || 0),
                  isEstimate: false,
                }}
              />
            </span>
          }
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
          label={
            <span className="inline-flex items-center gap-1.5">
              <span>Emergency Reserve Runway</span>
              <KnowMore
                termId="emergency_fund"
                contextualValue={{
                  label: 'Emergency Reserve Runway',
                  value: `${emergencyMonths} Months`,
                  isEstimate: false,
                }}
              />
            </span>
          }
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
          label={
            <span className="inline-flex items-center gap-1.5">
              <span>Active Goals</span>
              <KnowMore termId="financial_independence" />
            </span>
          }
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

      {/* FinPilot Intelligence Feed */}
      <Card className="border border-[rgba(212,175,55,0.2)] shadow-md p-5 space-y-4 bg-[#111622]/90">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/[0.08]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#D4AF37]/15 text-[#F5DE88] border border-[#D4AF37]/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[#F3F4F6]">
                  FinPilot Intelligence Feed
                </h2>
                <Badge variant="lavender" className="text-[10px] py-0.5 px-2 font-medium bg-[#D4AF37]/15 text-[#F5DE88] border-[#D4AF37]/30">
                  v1 Deterministic
                </Badge>
              </div>
              <p className="text-xs text-[#9CA3AF]">
                Proactive spending anomaly detection, cash-flow forecasting alerts, and actionable goal calibrations.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#9CA3AF]">
            <span>{insights.length} active insight{insights.length === 1 ? '' : 's'}</span>
          </div>
        </div>

        {loadingInsights ? (
          <div className="py-8 text-center text-xs text-[#9CA3AF] animate-pulse">
            Analyzing transaction patterns, recurring obligations, and cash-flow trajectories...
          </div>
        ) : insights.length === 0 ? (
          <div className="py-6 px-4 text-center rounded-xl bg-white/[0.03] border border-white/10">
            <p className="text-sm font-semibold text-[#F3F4F6]">All systems optimal</p>
            <p className="text-xs text-[#9CA3AF] mt-1">
              No anomalies or critical budget risks detected for the active statement period.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {insights.map((insight) => {
              const severityStyles = {
                critical: 'border-l-4 border-l-[#F43F5E] bg-[#F43F5E]/5',
                warning: 'border-l-4 border-l-[#F59E0B] bg-[#F59E0B]/5',
                info: 'border-l-4 border-l-[#38BDF8] bg-[#38BDF8]/5',
                success: 'border-l-4 border-l-[#10B981] bg-[#10B981]/5',
              }[insight.severity] || 'border-l-4 border-l-[#D4AF37] bg-[#D4AF37]/5';

              const badgeColor = {
                critical: 'bg-[#F43F5E]/15 text-[#F43F5E] border border-[#F43F5E]/30',
                warning: 'bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30',
                info: 'bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30',
                success: 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30',
              }[insight.severity] || 'bg-[#D4AF37]/15 text-[#F5DE88] border border-[#D4AF37]/30';

              return (
                <div
                  key={insight.id}
                  className={`p-4 rounded-xl border border-white/10 ${severityStyles} flex flex-col justify-between transition-all hover:border-[#D4AF37]/40 hover:shadow-md`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md ${badgeColor}`}>
                        {insight.category.replace('_', ' ')}
                      </span>
                      {insight.metric_value && (
                        <span className="text-xs font-bold text-[#F3F4F6] bg-white/10 px-2 py-0.5 rounded border border-white/10">
                          {insight.metric_value}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-[#F3F4F6] leading-snug">
                      {insight.title}
                    </h3>
                    <p className="text-xs text-[#9CA3AF] leading-relaxed">
                      {insight.summary}
                    </p>
                    {insight.detail && (
                      <p className="text-[11px] text-[#9CA3AF] border-t border-white/10 pt-1.5 mt-1">
                        {insight.detail}
                      </p>
                    )}
                  </div>

                  <div className="pt-3 mt-3 flex items-center justify-between border-t border-white/10">
                    <div className="text-[10px] text-[#9CA3AF]">
                      Confidence: <span className="font-semibold capitalize text-[#F3F4F6]">{insight.confidence}</span>
                    </div>
                    {insight.action_label && (
                      <button
                        onClick={() => {
                          if (insight.action_tab) {
                            onNavigateToTab(insight.action_tab);
                          }
                        }}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-[#F5DE88] hover:text-[#D4AF37] hover:underline"
                      >
                        <span>{insight.action_label}</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Main Charts & Goals Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cash Flow Trends Chart */}
        <Card className="lg:col-span-2 min-w-0 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[#F3F4F6]">
                  Monthly Cash Flow & Surplus Trends
                </h2>
                <KnowMore termId="cash_flow" variant="button" label="About Cash Flow" />
              </div>
              <p className="text-xs text-[#9CA3AF]">
                Income vs living expenses with net retained surplus across recent months.
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs font-semibold">
              <span className="flex items-center gap-1.5 text-[#F3F4F6]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#10B981] inline-block shadow-sm shadow-[#10B981]/50" /> Income
              </span>
              <span className="flex items-center gap-1.5 text-[#F3F4F6]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#F43F5E] inline-block shadow-sm shadow-[#F43F5E]/50" /> Expenses
              </span>
              <span className="flex items-center gap-1.5 text-[#F3F4F6]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#D4AF37] inline-block shadow-sm shadow-[#D4AF37]/50" /> Surplus
              </span>
            </div>
          </div>

          <div className="h-64 sm:h-72 w-full min-w-0 pt-2">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="incomeFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="expenseFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#F43F5E" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                  <XAxis
                    dataKey="month"
                    stroke="#9CA3AF"
                    tick={{ fontSize: 12, fill: '#9CA3AF' }}
                    tickLine={false}
                    axisLine={{ stroke: 'rgba(212,175,55,0.2)' }}
                  />
                  <YAxis
                    stroke="#9CA3AF"
                    tick={{ fontSize: 11, fill: '#9CA3AF' }}
                    tickLine={false}
                    axisLine={{ stroke: 'rgba(212,175,55,0.2)' }}
                    tickFormatter={(val) => `₹${val / 1000}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0D111A',
                      border: '1px solid rgba(212, 175, 55, 0.35)',
                      borderRadius: '12px',
                      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.7)',
                      fontSize: '12px',
                      color: '#F3F4F6',
                    }}
                    formatter={(val: any) => [formatINR(Number(val)), '']}
                  />
                  <Area
                    type="monotone"
                    dataKey="income"
                    stroke="#10B981"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#incomeFill)"
                  />
                  <Area
                    type="monotone"
                    dataKey="expenses"
                    stroke="#F43F5E"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#expenseFill)"
                  />
                  <Line
                    type="monotone"
                    dataKey="surplus"
                    stroke="#D4AF37"
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: '#D4AF37' }}
                    activeDot={{ r: 5 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full w-full flex flex-col items-center justify-center p-6 text-center border border-dashed border-[rgba(212,175,55,0.25)] rounded-xl bg-white/[0.02]">
                <TrendingUp className="w-8 h-8 text-[#D4AF37] mb-2" />
                <p className="text-sm font-bold text-[#F3F4F6]">No Historical Cash Flow Data</p>
                <p className="text-xs text-[#9CA3AF] max-w-sm mt-1">
                  Upload 3 months of bank statements to visualize verified monthly income, living expenses, and cash surplus.
                </p>
                {onOpenStatementModal && (
                  <Button variant="primary" size="sm" onClick={onOpenStatementModal} className="mt-3">
                    Upload Bank Statement
                  </Button>
                )}
              </div>
            )}
          </div>
        </Card>


        {/* Goals Progress Card */}
        <Card className="flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-base font-bold text-[#F3F4F6]">Target Milestones</h2>
                <p className="text-xs text-[#9CA3AF]">Priority goal horizons</p>
              </div>
              <button
                onClick={() => onNavigateToTab('goals')}
                className="text-xs text-[#D4AF37] hover:text-[#ECC856] hover:underline font-semibold transition-colors"
              >
                View All
              </button>
            </div>

            <div className="space-y-3">
              {goals.length > 0 ? (
                goals.slice(0, 3).map((goal) => (
                  <div
                    key={goal.id}
                    className="p-3.5 rounded-xl bg-white/[0.02] border border-[rgba(212,175,55,0.15)] space-y-2 hover:bg-white/[0.04] hover:border-[rgba(212,175,55,0.3)] transition-all"
                  >
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-[#F3F4F6]">{goal.name}</span>
                      <span className="text-[#D4AF37] font-bold tabular-nums">
                        {goal.progress_pct}%
                      </span>
                    </div>
                    <div className="w-full bg-charcoal-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-[#D4AF37] to-[#ECC856] h-full rounded-full transition-all duration-300 shadow-[0_0_8px_rgba(212,175,55,0.4)]"
                        style={{ width: `${Math.min(100, goal.progress_pct || 0)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-[#9CA3AF] tabular-nums">
                      <span>{formatINR(goal.current_amount)}</span>
                      <span>Target: {formatINR(goal.target_amount)}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-[#9CA3AF] text-xs">
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
            <h2 className="text-base font-bold text-[#F3F4F6]">
              Recent Financial Transactions
            </h2>
            <p className="text-xs text-[#9CA3AF]">
              Verified cash flow movements across your linked Indian bank accounts.
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigateToTab('budget')}
            icon={<ArrowRight className="w-3.5 h-3.5 text-[#D4AF37]" />}
            iconPosition="right"
          >
            Manage Transactions & CSV
          </Button>
        </div>

        <div className="overflow-x-auto -mx-5 sm:mx-0">
          <table className="w-full text-left text-xs text-[#F3F4F6]">
            <thead className="bg-white/[0.02] text-[#9CA3AF] uppercase text-[10px] tracking-wider border-y border-white/10">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Date</th>
                <th className="py-2.5 px-4 font-semibold">Description</th>
                <th className="py-2.5 px-4 font-semibold">Category</th>
                <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-medium">
              {recentTxns.length > 0 ? (
                recentTxns.slice(0, 5).map((txn) => (
                  <tr key={txn.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-[#9CA3AF] tabular-nums font-mono">{txn.date}</td>
                    <td className="py-3 px-4 text-[#F3F4F6] font-semibold">{txn.description}</td>
                    <td className="py-3 px-4">
                      <Badge variant="neutral" size="sm">
                        {txn.category}
                      </Badge>
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-bold tabular-nums ${
                        txn.type === 'income' ? 'text-emerald-400' : 'text-[#F3F4F6]'
                      }`}
                    >
                      {txn.type === 'income' ? '+' : '-'} {formatINR(txn.amount)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-[#9CA3AF]">
                    No verified transactions recorded yet. Click &apos;Upload Statement&apos; above to import your bank statement (CSV, XLSX, or PDF).
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
