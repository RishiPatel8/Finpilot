import React from 'react';
import {
  LayoutDashboard,
  ReceiptIndianRupee,
  Wallet,
  TrendingUp,
  Target,
  BotMessageSquare,
  ShieldCheck,
  FileSpreadsheet
} from 'lucide-react';

export type TabType = 'overview' | 'tax' | 'budget' | 'investments' | 'goals' | 'assistant';

interface SidebarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const navItems = [
    { id: 'overview' as TabType, label: 'Dashboard', icon: LayoutDashboard, badge: null },
    { id: 'tax' as TabType, label: 'Tax Planner', icon: ReceiptIndianRupee, badge: 'AY 25-26' },
    { id: 'budget' as TabType, label: 'Budget & CSV', icon: Wallet, badge: null },
    { id: 'investments' as TabType, label: 'Investments', icon: TrendingUp, badge: 'Liquid vs Bonds' },
    { id: 'goals' as TabType, label: 'Goal Planner', icon: Target, badge: null },
    { id: 'assistant' as TabType, label: 'AI Assistant', icon: BotMessageSquare, badge: 'RAG' },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between shrink-0 hidden md:flex">
      <div className="space-y-1">
        <p className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Financial Intelligence
        </p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm shadow-emerald-500/5 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-semibold ${
                  isActive ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs space-y-2">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold">
          <ShieldCheck className="w-4 h-4" />
          <span>Section 288B Tested</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Deterministic arithmetic & verified Income Tax Act formulas. Zero hallucination.
        </p>
      </div>
    </aside>
  );
};
