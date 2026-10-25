import { User as UserIcon, LogOut, FileSpreadsheet, Sparkles, Menu, X, ShieldCheck, Settings, Home, Send } from 'lucide-react';
import { User } from '../types';
import { Badge, Button } from './ui';

interface NavbarProps {
  user: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  onOpenStatementModal: () => void;
  activeTab: string;
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
  onSelectTab?: (tab: any) => void;
  onOpenLanding?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onOpenAuth,
  onLogout,
  onOpenStatementModal,
  activeTab,
  onToggleMobileMenu,
  isMobileMenuOpen = false,
  onSelectTab,
  onOpenLanding,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-[rgba(212,175,55,0.18)] bg-[#0A0D14]/95 backdrop-blur-md px-4 sm:px-6 py-3 flex items-center justify-between transition-colors shadow-[0_4px_25px_rgba(0,0,0,0.6)]">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        <button
          onClick={onToggleMobileMenu}
          className="p-1.5 rounded-xl text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-white/5 md:hidden transition-colors border border-transparent hover:border-[#D4AF37]/20"
          aria-label="Toggle navigation menu"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5 text-[#F5DE88]" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Brand Mark */}
        <div
          onClick={onOpenLanding || (() => onSelectTab && onSelectTab('overview'))}
          className="flex items-center gap-2.5 cursor-pointer group select-none"
          title="FinPilot AI Homepage"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#ECC856]/20 via-[#D4AF37]/15 to-transparent border border-[#D4AF37]/40 flex items-center justify-center text-[#F5DE88] shadow-[0_0_15px_rgba(212,175,55,0.2)] group-hover:scale-105 group-hover:border-[#D4AF37] transition-all">
            <Sparkles className="w-4 h-4 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base sm:text-lg tracking-tight bg-gradient-to-r from-[#FFF0BE] via-[#D4AF37] to-[#C5A059] bg-clip-text text-transparent whitespace-nowrap">
                FinPilot AI
              </span>
              <Badge variant="lavender" size="sm" className="hidden xs:inline-flex bg-[#D4AF37]/15 text-[#F5DE88] border-[#D4AF37]/30">
                India
              </Badge>
            </div>

            <p className="text-[11px] text-[#9CA3AF] hidden sm:block font-normal">
              Explainable Personal Finance Intelligence
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* Home Overview Trigger */}
        {onOpenLanding && (
          <button
            onClick={onOpenLanding}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-[#F5DE88] hover:text-[#FFF0BE] bg-[#D4AF37]/10 hover:bg-[#D4AF37]/20 border border-[#D4AF37]/35 hover:border-[#D4AF37]/60 transition-all shadow-[0_0_12px_rgba(212,175,55,0.15)]"
            title="Open FinPilot Home Overview"
          >
            <Home className="w-3.5 h-3.5 text-[#D4AF37]" />
            <span>Home</span>
          </button>
        )}

        {/* Telegram Bot Direct Connection */}
        <a
          href="https://t.me/my_finpilotcfo_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#229ED9]/15 hover:bg-[#229ED9]/25 text-[#38BDF8] border border-[#229ED9]/35 hover:border-[#38BDF8]/60 transition-all shadow-sm group"
          title="Connect to FinPilot Global AI CFO on Telegram (@my_finpilotcfo_bot)"
        >
          <Send className="w-3.5 h-3.5 text-[#38BDF8] group-hover:scale-110 transition-transform" />
          <span className="hidden sm:inline">Telegram Bot</span>
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#38BDF8] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#229ED9]"></span>
          </span>
        </a>

        {/* Genuine Bank Statement Import Trigger */}
        <button
          onClick={onOpenStatementModal}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border bg-[#131824] text-[#F5DE88] border-[#D4AF37]/30 hover:bg-[#D4AF37]/15 hover:border-[#D4AF37]/60 shadow-sm"
          title="Upload authentic bank statement (CSV, XLSX, or PDF) for deterministic financial calculations"
        >
          <FileSpreadsheet className="w-3.5 h-3.5 text-[#D4AF37]" />
          <span className="hidden sm:inline">Import Statement</span>
          <span className="sm:hidden">Import</span>
        </button>

        {user ? (
          <div className="flex items-center gap-2.5 pl-2 border-l border-white/10">
            <button
              onClick={() => onSelectTab && onSelectTab('settings')}
              className="flex items-center gap-2 hover:opacity-85 transition-opacity text-left"
              title="View Account Settings & Financial Profile"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/15 border border-[#D4AF37]/40 flex items-center justify-center text-[#F5DE88] font-bold text-xs shadow-sm shadow-[#D4AF37]/10">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="hidden lg:block text-left">
                <p className="text-xs font-semibold text-[#F3F4F6] leading-tight truncate max-w-[130px]">
                  {user.full_name}
                </p>
                <p className="text-[10px] text-[#9CA3AF] capitalize font-medium">
                  {user.role}
                </p>
              </div>
            </button>
            <button
              onClick={() => onSelectTab && onSelectTab('settings')}
              className={`p-1.5 rounded-xl transition-colors ${
                activeTab === 'settings'
                  ? 'text-[#F5DE88] bg-[#D4AF37]/20 border border-[#D4AF37]/30'
                  : 'text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-white/5'
              }`}
              title="Account Settings & Privacy"
            >
              <Settings className="w-4 h-4" />
            </button>
            <button
              onClick={onLogout}
              className="p-1.5 text-[#9CA3AF] hover:text-[#F43F5E] hover:bg-[#F43F5E]/10 rounded-xl transition-colors border border-transparent hover:border-[#F43F5E]/20"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

        ) : (
          <Button
            variant="primary"
            size="sm"
            onClick={onOpenAuth}
            icon={<UserIcon className="w-3.5 h-3.5" />}
          >
            Sign In / Register
          </Button>
        )}
      </div>
    </header>
  );
};
