import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, TabType } from './components/Sidebar';
import { AuthModal } from './components/AuthModal';
import { DashboardView } from './features/dashboard/DashboardView';
import { TaxPlannerView } from './features/tax/TaxPlannerView';
import { BudgetView } from './features/budget/BudgetView';
import { InvestmentsView } from './features/investments/InvestmentsView';
import { GoalsView } from './features/goals/GoalsView';
import { ScenarioSimulatorView } from './features/scenarios/ScenarioSimulatorView';
import { AssistantView } from './features/assistant/AssistantView';
import { apiRequest, getAuthToken, clearAuthToken, setAuthToken } from './services/api';
import { User, FinancialHealthSummary, Transaction, FinancialGoal } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [user, setUser] = useState<User | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
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
      try {
        const email = `demo_${Date.now()}@finpilot.local`;
        const res = await apiRequest<{ access_token: string; user: User }>('/auth/register', {
          method: 'POST',
          body: JSON.stringify({
            email,
            password: 'DemoPassword123!',
            full_name: 'Aditya Verma (Demo Profile)',
            role: 'salaried',
          }),
        });
        setAuthToken(res.access_token);
        setUser(res.user);
      } catch (e) {
        console.error('Demo registration fallback:', e);
      }
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
            {activeTab === 'tax' && <TaxPlannerView />}
            {activeTab === 'investments' && <InvestmentsView />}
            {activeTab === 'goals' && (
              <GoalsView goals={goals} onRefresh={fetchData} />
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
          fetchData();
        }}
      />
    </div>
  );
};

export default App;
