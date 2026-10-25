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
  Landmark,
  Flame,
  CalendarClock,
  Send,
} from 'lucide-react';

export type TabType = 'overview' | 'bank' | 'fire' | 'tax' | 'budget' | 'recurring' | 'debts' | 'investments' | 'goals' | 'scenarios' | 'assistant' | 'settings';

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
    { id: 'overview' as TabType, label: 'Financial Overview', icon: LayoutDashboard },
    { id: 'fire' as TabType, label: 'Retirement & Freedom', icon: Flame },
    { id: 'bank' as TabType, label: 'Bank Accounts', icon: Landmark },
    { id: 'scenarios' as TabType, label: 'Decision Simulator', icon: SlidersHorizontal },
    { id: 'assistant' as TabType, label: 'AI CFO Assistant', icon: BotMessageSquare },
    { id: 'budget' as TabType, label: 'Budget & Spending', icon: Wallet },
    { id: 'recurring' as TabType, label: 'Recurring Payments', icon: CalendarClock },
    { id: 'debts' as TabType, label: 'Debt Payoff Plan', icon: CreditCard },
    { id: 'tax' as TabType, label: 'Tax Planning', icon: ReceiptIndianRupee },
    { id: 'investments' as TabType, label: 'Investments', icon: TrendingUp },
    { id: 'goals' as TabType, label: 'Financial Goals', icon: Target },
    { id: 'settings' as TabType, label: 'Settings & Privacy', icon: Settings },
  ];

  const handleNavClick = (tab: TabType) => {
    onSelectTab(tab);
    if (onCloseMobile) onCloseMobile();
  };

  const sidebarContent = (
    <div className="flex flex-col justify-between h-full p-4">
      <div className="space-y-1.5">
        <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-[#D4AF37]/80">
          Planning & Intelligence
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all select-none text-left ${
                isActive
                  ? 'bg-gradient-to-r from-[#D4AF37]/20 via-[#D4AF37]/10 to-transparent text-[#F5DE88] font-bold border-l-2 border-[#D4AF37] shadow-sm shadow-[#D4AF37]/10'
                  : 'text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-white/[0.04]'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 transition-colors ${isActive ? 'text-[#F5DE88]' : 'text-[#9CA3AF]'}`} />
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Telegram Mobile Assistant Quick Card */}
      <div className="pt-2">
        <a
          href="https://t.me/my_finpilotcfo_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between p-2.5 rounded-xl bg-gradient-to-r from-[#229ED9]/15 to-[#229ED9]/5 border border-[#229ED9]/30 hover:border-[#38BDF8]/60 text-xs text-[#38BDF8] font-semibold transition-all group shadow-sm"
          title="Open Telegram Bot (@my_finpilotcfo_bot)"
        >
          <div className="flex items-center gap-2">
            <Send className="w-3.5 h-3.5 text-[#38BDF8] group-hover:scale-110 transition-transform" />
            <span className="text-[11px] font-bold">Telegram AI CFO</span>
          </div>
          <span className="text-[9px] bg-[#229ED9]/30 text-white px-1.5 py-0.5 rounded font-mono">
            @my_finpilotcfo_bot
          </span>
        </a>
      </div>

      {/* Compliance & Security Card */}
      <div className="p-3.5 rounded-2xl bg-[#111622]/80 border border-[rgba(212,175,55,0.18)] text-xs space-y-2 mt-2 shadow-sm">
        <div className="flex items-center gap-2 text-[#10B981] font-bold text-xs">
          <ShieldCheck className="w-4 h-4 text-[#10B981] shrink-0" />
          <span>Statutory Compliance</span>
        </div>
        <p className="text-[11px] text-[#9CA3AF] leading-relaxed">
          Deterministic Income Tax Act formulas (Sec 288B) & SEBI Mutual Fund norms. Zero hallucinated numbers.
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="w-72 border-r border-[rgba(212,175,55,0.15)] bg-[#0A0D14] shrink-0 hidden md:block">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={onCloseMobile}
          />
          {/* Drawer panel */}
          <aside className="relative w-72 max-w-[85vw] bg-[#0A0D14] border-r border-[rgba(212,175,55,0.2)] h-full shadow-2xl z-10 flex flex-col animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};
