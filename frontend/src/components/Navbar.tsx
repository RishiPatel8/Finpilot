import { User as UserIcon, LogOut, Database, Sparkles, Menu, X, ShieldCheck, Settings } from 'lucide-react';
import { User } from '../types';
import { Badge, Button } from './ui';

interface NavbarProps {
  user: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  onSeedDemo: () => void;
  isDemoActive: boolean;
  activeTab: string;
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
  onSelectTab?: (tab: any) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onOpenAuth,
  onLogout,
  onSeedDemo,
  isDemoActive,
  activeTab,
  onToggleMobileMenu,
  isMobileMenuOpen = false,
  onSelectTab,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#E6EAF0] bg-white/95 backdrop-blur-md px-4 sm:px-6 py-3 flex items-center justify-between transition-colors">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        <button
          onClick={onToggleMobileMenu}
          className="p-1.5 rounded-xl text-[#697386] hover:text-[#172033] hover:bg-[#F6F8FC] md:hidden transition-colors"
          aria-label="Toggle navigation menu"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Brand Mark */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-[#EEF0FF] border border-[#6478E8]/20 flex items-center justify-center text-[#6478E8] shadow-sm">
            <Sparkles className="w-4 h-4 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base sm:text-lg tracking-tight text-[#172033] whitespace-nowrap">
                FinPilot AI
              </span>
              <Badge variant="lavender" size="sm" className="hidden xs:inline-flex">
                India
              </Badge>
            </div>

            <p className="text-[11px] text-[#697386] hidden sm:block font-normal">
              Explainable Personal Finance Intelligence
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* Demo Profile Trigger Button */}
        <button
          onClick={onSeedDemo}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border ${
            isDemoActive
              ? 'bg-[#FFF0E5] text-[#B7791F] border-[#B7791F]/30 hover:bg-[#FFE6D4]'
              : 'bg-[#F6F8FC] text-[#697386] hover:text-[#172033] border-[#E6EAF0] hover:bg-slate-100'
          }`}
          title="Load realistic Indian financial profile, transactions, assets & liabilities"
        >
          <Database className="w-3.5 h-3.5 text-[#B7791F]" />
          <span className="hidden sm:inline">
            {isDemoActive ? 'Demo Profile Loaded' : 'Load Demo Profile'}
          </span>
          <span className="sm:hidden">
            {isDemoActive ? 'Demo' : 'Load Demo'}
          </span>
        </button>

        {user ? (
          <div className="flex items-center gap-2.5 pl-2 border-l border-[#E6EAF0]">
            <button
              onClick={() => onSelectTab && onSelectTab('settings')}
              className="flex items-center gap-2 hover:opacity-85 transition-opacity text-left"
              title="View Account Settings & Financial Profile"
            >
              <div className="w-8 h-8 rounded-full bg-[#EEF0FF] border border-[#6478E8]/30 flex items-center justify-center text-[#6478E8] font-bold text-xs">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="hidden lg:block text-left">
                <p className="text-xs font-semibold text-[#172033] leading-tight truncate max-w-[130px]">
                  {user.full_name}
                </p>
                <p className="text-[10px] text-[#697386] capitalize font-medium">
                  {user.role}
                </p>
              </div>
            </button>
            <button
              onClick={() => onSelectTab && onSelectTab('settings')}
              className={`p-1.5 rounded-xl transition-colors ${
                activeTab === 'settings'
                  ? 'text-[#6478E8] bg-[#EEF0FF]'
                  : 'text-[#697386] hover:text-[#172033] hover:bg-[#F6F8FC]'
              }`}
              title="Account Settings & Privacy"
            >
              <Settings className="w-4 h-4" />
            </button>
            <button
              onClick={onLogout}
              className="p-1.5 text-[#697386] hover:text-[#D9485F] hover:bg-[#FDF2F4] rounded-xl transition-colors"
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
