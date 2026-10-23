import React, { useState } from 'react';
import {
  Target,
  Plus,
  Trash2,
  Calendar,
  PiggyBank,
  CheckCircle2,
  TrendingUp,
  Percent,
  X,
  Sparkles,
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { FinancialGoal } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';

interface GoalsViewProps {
  goals: FinancialGoal[];
  onRefresh: () => void;
}

export const GoalsView: React.FC<GoalsViewProps> = ({ goals, onRefresh }) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState('');
  const [category, setCategory] = useState<
    'emergency_fund' | 'home' | 'education' | 'retirement' | 'custom'
  >('custom');
  const [targetAmount, setTargetAmount] = useState<number>(1000000);
  const [currentAmount, setCurrentAmount] = useState<number>(100000);
  const [targetDate, setTargetDate] = useState('2026-12-31');
  const [priority, setPriority] = useState('high');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await apiRequest('/goals', {
        method: 'POST',
        body: JSON.stringify({
          name,
          category,
          target_amount: targetAmount,
          current_amount: currentAmount,
          target_date: targetDate,
          priority,
        }),
      });
      setShowAddModal(false);
      setName('');
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to create goal.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteGoal = async (id: string) => {
    try {
      await apiRequest(`/goals/${id}`, { method: 'DELETE' });
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to delete goal.');
    }
  };

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Financial Goal Planning & Projections"
        description="Compute exact required monthly SIPs, track asset milestones, and project target timelines adjusted for Indian inflation."
        icon={<Target className="w-4 h-4 text-[#6478E8]" />}
        badge={
          <Badge variant="mint" size="sm">
            {goals.length} Active Targets
          </Badge>
        }
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowAddModal(true)}
            icon={<Plus className="w-3.5 h-3.5" />}
          >
            Add New Milestone
          </Button>
        }
      />

      {/* Goals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {goals.length > 0 ? (
          goals.map((goal) => {
            const isCompleted = (goal.progress_pct || 0) >= 100;
            return (
              <Card
                key={goal.id}
                className="space-y-4 flex flex-col justify-between hover:border-[#D1D9E6] transition-all"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-[#172033]">{goal.name}</h3>
                        {(goal as any).priority && (
                          <Badge
                            variant={
                              (goal as any).priority === 'high'
                                ? 'peach'
                                : (goal as any).priority === 'critical'
                                ? 'danger'
                                : 'neutral'
                            }
                            size="sm"
                            className="capitalize"
                          >
                            {(goal as any).priority}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-[#697386] capitalize mt-0.5">
                        {goal.category.replace('_', ' ')}
                      </p>
                    </div>

                    <button
                      onClick={() => handleDeleteGoal(goal.id)}
                      className="text-[#697386] hover:text-[#D9485F] hover:bg-[#FDF2F4] p-1.5 rounded-lg transition-colors"
                      title="Delete goal"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Progress Bar & Amounts */}
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-[#697386]">Milestone Progress</span>
                      <span className="text-[#16865C] font-bold tabular-nums">
                        {goal.progress_pct || 0}%
                      </span>
                    </div>
                    <div className="w-full bg-[#F1F4F9] h-2.5 rounded-full overflow-hidden">
                      <div
                        className="bg-[#16865C] h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, goal.progress_pct || 0)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs font-bold text-[#172033] tabular-nums pt-1">
                      <span>{formatINR(goal.current_amount)}</span>
                      <span className="text-[#697386] font-normal">
                        Target: {formatINR(goal.target_amount)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Contribution projections */}
                <div className="pt-3 border-t border-[#F1F4F9] space-y-2 text-xs">
                  <div className="flex items-center justify-between text-[#697386]">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-[#6478E8]" /> Target Date:
                    </span>
                    <span className="font-semibold text-[#172033] tabular-nums">
                      {goal.target_date}
                    </span>
                  </div>

                  {goal.monthly_required && (
                    <div className="p-3 rounded-xl bg-[#EEF0FF]/60 border border-[#EEF0FF] flex items-center justify-between">
                      <span className="text-[#6478E8] font-medium text-[11px]">
                        Required Monthly SIP:
                      </span>
                      <span className="font-extrabold text-[#6478E8] tabular-nums">
                        {formatINR(goal.monthly_required)}
                      </span>
                    </div>
                  )}
                </div>
              </Card>
            );
          })
        ) : (
          <Card className="col-span-full py-16 text-center space-y-3 flex flex-col items-center justify-center">
            <div className="w-12 h-12 rounded-2xl bg-[#EEF0FF] text-[#6478E8] flex items-center justify-center shadow-sm">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-[#172033]">
              No Financial Milestones Defined Yet
            </h3>
            <p className="text-xs sm:text-sm text-[#697386] max-w-md leading-relaxed">
              Create your financial goals (such as home down payment, emergency fund, or retirement corpus) to compute exact required monthly SIPs.
            </p>
            <Button
              variant="primary"
              size="md"
              onClick={() => setShowAddModal(true)}
              icon={<Plus className="w-3.5 h-3.5" />}
              className="mt-2"
            >
              Add First Milestone
            </Button>
          </Card>
        )}
      </div>

      {/* Add Goal Modal Dialog */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-[#172033]/40 backdrop-blur-sm transition-opacity"
            onClick={() => setShowAddModal(false)}
          />

          <div className="relative w-full max-w-lg bg-white border border-[#E6EAF0] rounded-2xl shadow-[0_20px_25px_-5px_rgba(23,32,51,0.1),0_8px_10px_-6px_rgba(23,32,51,0.05)] p-6 sm:p-7 z-10 animate-in fade-in zoom-in-95 duration-200">
            <button
              onClick={() => setShowAddModal(false)}
              className="absolute top-5 right-5 p-1.5 rounded-xl text-[#697386] hover:text-[#172033] hover:bg-[#F6F8FC] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="mb-5">
              <h2 className="text-lg font-bold text-[#172033]">Create New Financial Milestone</h2>
              <p className="text-xs text-[#697386] mt-0.5">
                Calculate required monthly investments and monitor milestone progress.
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-xl bg-[#FDF2F4] border border-[#D9485F]/20 text-xs text-[#D9485F]">
                {error}
              </div>
            )}

            <form onSubmit={handleAddGoal} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">
                  Goal Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Home Down Payment, Child Education, Car"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#172033] mb-1">
                    Goal Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                  >
                    <option value="custom">Custom Milestone</option>
                    <option value="emergency_fund">Emergency Fund</option>
                    <option value="home">Home Purchase / Down Payment</option>
                    <option value="education">Education / Higher Studies</option>
                    <option value="retirement">Retirement Corpus</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#172033] mb-1">
                    Priority
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                  >
                    <option value="low">Low Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="high">High Priority</option>
                    <option value="critical">Critical (Essential)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#172033] mb-1">
                    Target Amount (₹)
                  </label>
                  <input
                    type="number"
                    required
                    value={targetAmount || ''}
                    onChange={(e) => setTargetAmount(Number(e.target.value))}
                    className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#172033] mb-1">
                    Current Amount (₹)
                  </label>
                  <input
                    type="number"
                    value={currentAmount || ''}
                    onChange={(e) => setCurrentAmount(Number(e.target.value))}
                    className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs font-mono tabular-nums text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">
                  Target Date
                </label>
                <input
                  type="date"
                  required
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="w-full bg-white border border-[#E6EAF0] rounded-xl px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#6478E8] transition-all"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="md"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  loading={loading}
                  className="flex-1"
                >
                  Create Milestone
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
