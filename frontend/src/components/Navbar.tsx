import React from 'react';
import { ShieldCheck, User as UserIcon, LogOut, Database, Sparkles } from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  user: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  onSeedDemo: () => void;
  isDemoActive: boolean;
  activeTab: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onOpenAuth,
  onLogout,
  onSeedDemo,
  isDemoActive,
  activeTab,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
          <Sparkles className="w-5 h-5 text-slate-950 font-bold" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-emerald-400 bg-clip-text text-transparent">
              FinPilot AI
            </span>
            <span className="px-1.5 py-0.5 text-[10px] uppercase font-bold tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
              India
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">Explainable Personal Finance Intelligence</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Synthetic Demo Data Trigger Button */}
        <button
          onClick={onSeedDemo}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            isDemoActive
              ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20'
              : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 border border-slate-700'
          }`}
          title="Load realistic Indian financial profile, transactions, assets & liabilities"
        >
          <Database className="w-3.5 h-3.5 text-amber-400" />
          <span>{isDemoActive ? 'Demo Data Loaded' : 'Load Demo Profile'}</span>
        </button>

        {user ? (
          <div className="flex items-center gap-3 pl-2 border-l border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-semibold text-xs">
                {user.full_name.charAt(0)}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-semibold text-slate-200 leading-tight">{user.full_name}</p>
                <p className="text-[10px] text-slate-400 capitalize">{user.role}</p>
              </div>
            </div>
            <button
              onClick={onLogout}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs transition-all shadow-md shadow-emerald-500/20"
          >
            <UserIcon className="w-3.5 h-3.5" />
            <span>Sign In / Register</span>
          </button>
        )}
      </div>
    </header>
  );
};
