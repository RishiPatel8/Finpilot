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
import { BankAccountsView } from './features/bank/BankAccountsView';
import { FirePlanningView } from './features/fire/FirePlanningView';
import { SettingsView } from './features/settings/SettingsView';
import { BankConsentCallbackView } from './features/bank/BankConsentCallbackView';
import { RecurringTransactionsView } from './features/recurring/RecurringTransactionsView';
import { GlobalAICFO } from './features/assistant/GlobalAICFO';
import { StatementUploadModal } from './features/statement/StatementUploadModal';
import { LandingPage } from './features/landing/LandingPage';
import { apiRequest, getAuthToken, clearAuthToken } from './services/api';
import { User, FinancialHealthSummary, Transaction, FinancialGoal } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [user, setUser] = useState<User | null>(null);
  const [viewMode, setViewMode] = useState<'landing' | 'app'>(() => {
    const token = getAuthToken();
    const pathname = window.location.pathname;
    const search = window.location.search;
    const hash = window.location.hash;
    if (
      token ||
      pathname.includes('/bank/consent') ||
      pathname.includes('/sandbox') ||
      search.includes('consentHandle') ||
      search.includes('view=app') ||
      hash === '#app'
    ) {
      return 'app';
    }
    return 'landing';
  });
  const [authInitialMode, setAuthInitialMode] = useState<'login' | 'register'>('login');
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isStatementModalOpen, setIsStatementModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isConsentCallback, setIsConsentCallback] = useState<boolean>(() => {
    const pathname = window.location.pathname;
    const search = window.location.search;
    return (
      pathname.includes('/bank/consent/callback') ||
      pathname.includes('/bank/consent-callback') ||
      pathname.includes('/sandbox/aa-consent') ||
      new URLSearchParams(search).has('consentHandle')
    );
  });

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

  // Fetch financial dashboard data (Strictly data-driven with ZERO MOCK DATA)
  const fetchData = async () => {
    const token = getAuthToken();
    if (!token) {
      setSummary(null);
      setRecentTxns([]);
      setGoals([]);
      return;
    }

    try {
      const dashData = await apiRequest<any>('/dashboard/summary');
      setSummary({
        net_worth: Number(dashData.net_worth || 0),
        total_assets: Number(dashData.total_assets || 0),
        total_liabilities: Number(dashData.total_liabilities || 0),
        monthly_income: Number(dashData.monthly_income || 0),
        monthly_expenses: Number(dashData.monthly_expenses || 0),
        monthly_surplus: Number(dashData.monthly_surplus || 0),
        savings_rate: Number(dashData.savings_rate_pct || 0),
        emergency_fund_current: Number(dashData.emergency_fund_current || 0),
        emergency_fund_target: Number(dashData.emergency_fund_target || 0),
        emergency_fund_months: Number(dashData.emergency_fund_months_covered || 0),
        monthly_history: dashData.monthly_history || [],
        statement_coverage: dashData.statement_coverage || null,
        is_empty: Boolean(dashData.is_empty),
        data_quality: dashData.data_quality || {},
      });
      setRecentTxns(dashData.recent_transactions || []);
      setGoals(dashData.goals || []);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  };

  useEffect(() => {
    fetchData();

    const handleDataUpdate = () => {
      fetchData();
    };
    window.addEventListener('finpilot:financial-data-updated', handleDataUpdate);
    return () => {
      window.removeEventListener('finpilot:financial-data-updated', handleDataUpdate);
    };
  }, [user]);

  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
    setSummary(null);
    setRecentTxns([]);
    setGoals([]);
    setActiveTab('overview');
    setViewMode('landing');
  };

  return (
    <div className="min-h-screen bg-[#07090E] text-[#F3F4F6] flex flex-col font-['Plus_Jakarta_Sans',sans-serif] relative">
      {/* Floating Public Landing Page with Smooth Glass & Levitation Transitions */}
      <div
        className={`fixed inset-0 z-50 overflow-y-auto transition-all duration-500 ease-out bg-[#07090E]/95 backdrop-blur-2xl ${
          viewMode === 'landing'
            ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto'
            : 'opacity-0 scale-95 translate-y-8 pointer-events-none'
        }`}
        aria-hidden={viewMode !== 'landing'}
      >
        <LandingPage
          onGetStarted={() => {
            setAuthInitialMode('register');
            setIsAuthOpen(true);
          }}
          onLogin={() => {
            setAuthInitialMode('login');
            setIsAuthOpen(true);
          }}
          onOpenDashboard={() => {
            setViewMode('app');
          }}
          isAuthenticated={Boolean(user || getAuthToken())}
        />
      </div>

      {/* Top Navbar */}
      <Navbar
        user={user}
        onOpenAuth={() => {
          setAuthInitialMode('login');
          setIsAuthOpen(true);
        }}
        onLogout={handleLogout}
        onOpenStatementModal={() => setIsStatementModalOpen(true)}
        activeTab={activeTab}
        onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        isMobileMenuOpen={isMobileMenuOpen}
        onSelectTab={(tab) => setActiveTab(tab)}
        onOpenLanding={() => setViewMode('landing')}
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
            {isConsentCallback ? (
              <BankConsentCallbackView
                onComplete={(targetTab) => {
                  window.history.replaceState({}, '', '/');
                  setIsConsentCallback(false);
                  setActiveTab(targetTab || 'bank');
                  fetchData();
                }}
              />
            ) : (
              <>
                {activeTab === 'overview' && (
                  <DashboardView
                    summary={summary}
                    recentTxns={recentTxns}
                    goals={goals}
                    onNavigateToTab={(tab) => setActiveTab(tab)}
                    onOpenStatementModal={() => setIsStatementModalOpen(true)}
                  />
                )}
                {activeTab === 'fire' && <FirePlanningView />}
                {activeTab === 'bank' && (
                  <BankAccountsView onNavigateToCsv={() => setActiveTab('budget')} />
                )}
                {activeTab === 'scenarios' && <ScenarioSimulatorView />}
                {activeTab === 'assistant' && <AssistantView />}
                {activeTab === 'budget' && (
                  <BudgetView
                    transactions={recentTxns}
                    onRefresh={fetchData}
                    monthlyIncome={summary?.monthly_income || 0}
                    monthlyExpenses={summary?.monthly_expenses || 0}
                  />
                )}
                {activeTab === 'recurring' && (
                  <RecurringTransactionsView
                    onRefresh={fetchData}
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
              </>
            )}
          </div>
        </main>
      </div>

      {/* Bank Statement Upload Modal (CSV, XLSX, PDF) */}
      <StatementUploadModal
        isOpen={isStatementModalOpen}
        onClose={() => setIsStatementModalOpen(false)}
        onSuccess={fetchData}
      />

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        initialMode={authInitialMode}
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

      {/* Global Floating AI CFO 2.0 Assistant */}
      {activeTab !== 'assistant' && (
        <GlobalAICFO
          activePage={activeTab}
          user={user}
          onNavigateToTab={(tab) => setActiveTab(tab as TabType)}
        />
      )}
    </div>
  );
};

export default App;
