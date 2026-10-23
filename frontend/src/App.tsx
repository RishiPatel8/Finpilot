import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, TabType } from './components/Sidebar';
import { AuthModal } from './components/AuthModal';
import { OnboardingModal } from './components/OnboardingModal';
import { DashboardView } from './features/dashboard/DashboardView';
import { TaxPlannerView } from './features/tax/TaxPlannerView';
import { BudgetView } from './features/budget/BudgetView';
import { DebtManagementView } from './features/debts/DebtManagementView';
import { InvestmentsView } from './features/investments/InvestmentsView';
import { GoalsView } from './features/goals/GoalsView';
import { ScenarioSimulatorView } from './features/scenarios/ScenarioSimulatorView';
import { AssistantView } from './features/assistant/AssistantView';
import { SettingsView } from './features/settings/SettingsView';
import { apiRequest, getAuthToken, clearAuthToken } from './services/api';
import { User, FinancialHealthSummary, Transaction, FinancialGoal } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [user, setUser] = useState<User | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isDemoActive, setIsDemoActive] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const [summary, setSummary] = useState<FinancialHealthSummary | null>(null);
  const [recentTxns, setRecentTxns] = useState<Transaction[]>([]);
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [loading, setLoading] = useState(true);

  // Initialize user session
  useEffect(() => {
    const initSession = async () => {
      const token = getAuthToken();
      if (token) {
        try {
          const userData = await apiRequest<User>('/auth/me');
          setUser(userData);
        } catch {
          clearAuthToken();
          setUser(null);
        }
      }
      setLoading(false);
    };
    initSession();
  }, []);

  // Fetch financial dashboard data
  const fetchData = async () => {
    const token = getAuthToken();
    if (!token) {
      // Guest baseline numbers
      setSummary({
        net_worth: 1845000,
        total_assets: 2095000,
        total_liabilities: 250000,
        monthly_income: 145000,
        monthly_expenses: 68000,
        monthly_surplus: 77000,
        savings_rate: 53.1,
        emergency_fund_current: 318500,
        emergency_fund_target: 408000,
        emergency_fund_months: 4.7,
      });
      return;
    }

    try {
      const dashData = await apiRequest<any>('/dashboard/summary');
      setSummary({
        net_worth: Number(dashData.net_worth),
        total_assets: Number(dashData.total_assets),
        total_liabilities: Number(dashData.total_liabilities),
        monthly_income: Number(dashData.monthly_income),
        monthly_expenses: Number(dashData.monthly_expenses),
        monthly_surplus: Number(dashData.monthly_surplus),
        savings_rate: Number(dashData.savings_rate_pct),
        emergency_fund_current: Number(dashData.emergency_fund_current),
        emergency_fund_target: Number(dashData.emergency_fund_target),
        emergency_fund_months: Number(dashData.emergency_fund_months_covered),
      });
      setRecentTxns(dashData.recent_transactions || []);
      setGoals(dashData.goals || []);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [user, isDemoActive]);

  const handleSeedDemo = async () => {
    if (!user) {
      // Isolated guest demo preview without creating real accounts in database
      setIsDemoActive(true);
      setSummary({
        net_worth: 1845000,
        total_assets: 2095000,
        total_liabilities: 250000,
        monthly_income: 145000,
        monthly_expenses: 68000,
        monthly_surplus: 77000,
        savings_rate: 53.1,
        emergency_fund_current: 318500,
        emergency_fund_target: 408000,
        emergency_fund_months: 4.7,
      });
      setRecentTxns([
        {
          id: 'demo-1',
          date: new Date().toISOString().slice(0, 10),
          amount: 145000,
          type: 'income',
          category: 'Income',
          description: 'Monthly Tech Salary Credit',
          source: 'manual',
          is_recurring: true,
        },
        {
          id: 'demo-2',
          date: new Date(Date.now() - 86400000 * 2).toISOString().slice(0, 10),
          amount: 32000,
          type: 'expense',
          category: 'Housing',
          description: 'HDFC Home Loan EMI',
          source: 'manual',
          is_recurring: true,
        },
        {
          id: 'demo-3',
          date: new Date(Date.now() - 86400000 * 4).toISOString().slice(0, 10),
          amount: 8500,
          type: 'expense',
          category: 'Food & Dining',
          description: 'Supermarket & Groceries',
          source: 'manual',
          is_recurring: false,
        },
      ]);
      setGoals([
        {
          id: 'demo-g1',
          name: 'Emergency Reserve',
          category: 'emergency_fund',
          target_amount: 408000,
          current_amount: 318500,
          target_date: '2026-12-31',
          progress_pct: 78.1,
          monthly_required: 12500,
        },
        {
          id: 'demo-g2',
          name: 'EV Car Purchase',
          category: 'custom',
          target_amount: 800000,
          current_amount: 350000,
          target_date: '2027-06-30',
          progress_pct: 43.8,
          monthly_required: 22000,
        },
      ]);
      return;
    }

    try {
      await apiRequest('/demo/seed', { method: 'POST' });
      setIsDemoActive(true);
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to seed demo data');
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
    setIsDemoActive(false);
    setActiveTab('overview');
    fetchData();
  };

  return (
    <div className="min-h-screen bg-[#F6F8FC] text-[#172033] flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Top Navbar */}
      <Navbar
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onLogout={handleLogout}
        onSeedDemo={handleSeedDemo}
        isDemoActive={isDemoActive}
        activeTab={activeTab}
        onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        isMobileMenuOpen={isMobileMenuOpen}
        onSelectTab={(tab) => setActiveTab(tab)}
      />

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar (Desktop + Mobile Drawer) */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tab) => setActiveTab(tab)}
          isMobileOpen={isMobileMenuOpen}
          onCloseMobile={() => setIsMobileMenuOpen(false)}
        />

        {/* Dynamic Content View Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {activeTab === 'overview' && (
              <DashboardView
                summary={summary}
                recentTxns={recentTxns}
                goals={goals}
                isDemoActive={isDemoActive}
                onNavigateToTab={(tab) => setActiveTab(tab)}
              />
            )}
            {activeTab === 'scenarios' && <ScenarioSimulatorView />}
            {activeTab === 'assistant' && <AssistantView />}
            {activeTab === 'budget' && (
              <BudgetView
                transactions={recentTxns}
                onRefresh={fetchData}
                monthlyIncome={summary?.monthly_income || 145000}
                monthlyExpenses={summary?.monthly_expenses || 68000}
              />
            )}
            {activeTab === 'debts' && <DebtManagementView />}
            {activeTab === 'tax' && <TaxPlannerView />}
            {activeTab === 'investments' && <InvestmentsView />}
            {activeTab === 'goals' && (
              <GoalsView goals={goals} onRefresh={fetchData} />
            )}
            {activeTab === 'settings' && (
              <SettingsView
                user={user}
                onProfileUpdated={fetchData}
                onLogout={handleLogout}
              />
            )}
          </div>
        </main>
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={(u) => {
          setUser(u);
          setIsAuthOpen(false);
          setIsOnboardingOpen(true);
          fetchData();
        }}
      />

      {/* Onboarding Setup Modal for New Users */}
      <OnboardingModal
        isOpen={isOnboardingOpen}
        user={user}
        onClose={() => setIsOnboardingOpen(false)}
        onComplete={() => {
          setIsOnboardingOpen(false);
          fetchData();
        }}
      />
    </div>
  );
};

export default App;
