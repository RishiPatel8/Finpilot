import React, { useState } from 'react';
import {
  Target,
  Plus,
  Trash2,
  Calendar,
  PiggyBank,
  CheckCircle2,
  TrendingUp,
  Percent
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { FinancialGoal } from '../../types';

interface GoalsViewProps {
  goals: FinancialGoal[];
  onRefresh: () => void;
}

export const GoalsView: React.FC<GoalsViewProps> = ({ goals, onRefresh }) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState('');
  const [category, setCategory] = useState<'emergency_fund' | 'home' | 'education' | 'retirement' | 'custom'>('custom');
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/40 border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-emerald-400" />
            <h1 className="text-xl font-extrabold text-slate-100">Financial Goal Planning & Projections</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Calculate exact required monthly SIPs, track milestones, and adjust for Indian inflation.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs rounded-xl shadow-md shadow-emerald-500/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Milestone</span>
        </button>
      </div>

      {/* Goals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {goals.length > 0 ? (
          goals.map((goal) => (
            <div
              key={goal.id}
              className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {goal.category.replace('_', ' ')}
                    </span>
                    <h3 className="text-base font-bold text-slate-100 mt-2">{goal.name}</h3>
                  </div>
                  <button
                    onClick={() => handleDeleteGoal(goal.id)}
                    className="text-slate-500 hover:text-rose-400 p-1 rounded transition-colors"
                    title="Delete Goal"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-400">Progress</span>
                    <span className="text-emerald-400 font-bold">{goal.progress_pct}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(100, goal.progress_pct || 0)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                    <span>{formatINR(goal.current_amount)}</span>
                    <span>Target: {formatINR(goal.target_amount)}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-slate-400">Required Monthly SIP</span>
                    <p className="text-sm font-black text-emerald-400 font-mono">
                      {formatINR(goal.monthly_required || 0)} / mo
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400">Target Date</span>
                    <p className="text-xs font-semibold text-slate-300">{goal.target_date}</p>
                  </div>
                </div>
              </div>

              <div className="pt-2 text-[11px] text-slate-500 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Deterministic SIP formula applied</span>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800/60 space-y-3">
            <PiggyBank className="w-8 h-8 text-emerald-400 mx-auto opacity-70" />
            <h3 className="text-sm font-bold text-slate-200">No Goals Created Yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Create your first financial milestone (e.g. 6-Month Emergency Fund, House Down Payment, Child Education)
              to receive calculated monthly SIP contribution requirements.
            </p>
          </div>
        )}
      </div>

      {/* Add Goal Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <h2 className="text-base font-bold text-slate-100">Create Financial Milestone</h2>

            {error && (
              <p className="text-xs text-rose-400 bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20">
                {error}
              </p>
            )}

            <form onSubmit={handleAddGoal} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Goal Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Home Down Payment"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="emergency_fund">Emergency Fund</option>
                    <option value="home">Home Purchase</option>
                    <option value="education">Education</option>
                    <option value="retirement">Retirement</option>
                    <option value="custom">Custom Goal</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="high">High Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="low">Low Priority</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Target Amount (₹)</label>
                  <input
                    type="number"
                    required
                    value={targetAmount}
                    onChange={(e) => setTargetAmount(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Current Saved (₹)</label>
                  <input
                    type="number"
                    required
                    value={currentAmount}
                    onChange={(e) => setCurrentAmount(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Target Date</label>
                <input
                  type="date"
                  required
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold rounded-xl shadow-md shadow-emerald-500/20"
                >
                  {loading ? 'Saving...' : 'Create Goal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
