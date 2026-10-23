import React from 'react';
import {
  LayoutDashboard,
  ReceiptIndianRupee,
  Wallet,
  TrendingUp,
  Target,
  BotMessageSquare,
  ShieldCheck,
  SlidersHorizontal,
  CreditCard,
  Settings,
} from 'lucide-react';
import { Badge } from './ui';

export type TabType = 'overview' | 'tax' | 'budget' | 'debts' | 'investments' | 'goals' | 'scenarios' | 'assistant' | 'settings';

interface SidebarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const navItems = [
    { id: 'overview' as TabType, label: 'Financial Overview', icon: LayoutDashboard, badge: null },
    { id: 'scenarios' as TabType, label: 'Decision Simulator', icon: SlidersHorizontal, badge: 'Flagship' },
    { id: 'assistant' as TabType, label: 'AI CFO Assistant', icon: BotMessageSquare, badge: 'RAG' },
    { id: 'budget' as TabType, label: 'Budget & CSV', icon: Wallet, badge: null },
    { id: 'debts' as TabType, label: 'Debt Payoff', icon: CreditCard, badge: 'Avalanche' },
    { id: 'tax' as TabType, label: 'Tax Planning', icon: ReceiptIndianRupee, badge: 'AY 25-26' },
    { id: 'investments' as TabType, label: 'Investments', icon: TrendingUp, badge: 'Liquid vs Bonds' },
    { id: 'goals' as TabType, label: 'Financial Goals', icon: Target, badge: null },
    { id: 'settings' as TabType, label: 'Settings & Privacy', icon: Settings, badge: null },
  ];

  const handleNavClick = (tab: TabType) => {
    onSelectTab(tab);
    if (onCloseMobile) onCloseMobile();
  };

  const sidebarContent = (
    <div className="flex flex-col justify-between h-full p-4">
      <div className="space-y-1.5">
        <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-[#697386]">
          Planning & Intelligence
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all select-none ${
                isActive
                  ? 'bg-[#EEF0FF] text-[#6478E8] font-bold shadow-sm shadow-[#6478E8]/5'
                  : 'text-[#697386] hover:text-[#172033] hover:bg-[#F6F8FC]'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 shrink-0 transition-colors ${isActive ? 'text-[#6478E8]' : 'text-[#697386]'}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge && (
                <Badge
                  variant={isActive ? 'lavender' : 'neutral'}
                  size="sm"
                  className={isActive ? 'bg-white/80 text-[#6478E8] font-semibold' : ''}
                >
                  {item.badge}
                </Badge>
              )}
            </button>
          );
        })}
      </div>

      {/* Compliance & Security Card */}
      <div className="p-3.5 rounded-2xl bg-[#F6F8FC] border border-[#E6EAF0] text-xs space-y-2 mt-4">
        <div className="flex items-center gap-2 text-[#16865C] font-bold text-xs">
          <ShieldCheck className="w-4 h-4 text-[#16865C] shrink-0" />
          <span>Statutory Compliance</span>
        </div>
        <p className="text-[11px] text-[#697386] leading-relaxed">
          Deterministic Income Tax Act formulas (Sec 288B) & SEBI Mutual Fund norms. Zero hallucinated numbers.
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="w-64 border-r border-[#E6EAF0] bg-white shrink-0 hidden md:block">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/30 backdrop-blur-sm transition-opacity"
            onClick={onCloseMobile}
          />
          {/* Drawer panel */}
          <aside className="relative w-72 max-w-[85vw] bg-white h-full shadow-2xl z-10 flex flex-col animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};
