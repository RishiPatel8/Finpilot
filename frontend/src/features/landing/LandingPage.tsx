import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  BotMessageSquare,
  LayoutDashboard,
  Landmark,
  Wallet,
  TrendingUp,
  Target,
  ReceiptIndianRupee,
  Flame,
  LineChart,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Lock,
  Zap,
  SlidersHorizontal,
  FileSpreadsheet,
  CalendarClock,
  Menu,
  X,
  CreditCard,
  ChevronRight,
  Eye,
  Layers,
  Send,
  Home,
  Activity,
  ArrowUpRight,
  Percent,
} from 'lucide-react';
import { Button, Badge, Card } from '../../components/ui';

interface LandingPageProps {
  onGetStarted: () => void;
  onLogin: () => void;
  onOpenDashboard?: () => void;
  isAuthenticated?: boolean;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onGetStarted,
  onLogin,
  onOpenDashboard,
  isAuthenticated = false,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activePreviewTab, setActivePreviewTab] = useState<'overview' | 'cfo' | 'tax' | 'fire'>('overview');
  
  // Interactive Chart State
  const [chartMode, setChartMode] = useState<'wealth' | 'cashflow' | 'fire'>('wealth');
  const [hoveredPointIndex, setHoveredPointIndex] = useState<number | null>(null);

  // Parallax & Scroll-driven Animation State
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollY, setScrollY] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          // Check scroll position from parent floating container or window
          const parent = containerRef.current?.parentElement;
          const currentY = parent && parent.scrollTop > 0 ? parent.scrollTop : window.scrollY;
          const maxScroll = parent && parent.scrollHeight - parent.clientHeight > 0
            ? parent.scrollHeight - parent.clientHeight
            : Math.max(1, document.documentElement.scrollHeight - window.innerHeight);

          setScrollY(currentY);
          setScrollProgress(Math.min(100, Math.max(0, (currentY / maxScroll) * 100)));
          ticking = false;
        });
        ticking = true;
      }
    };

    const parent = containerRef.current?.parentElement;
    if (parent) {
      parent.addEventListener('scroll', handleScroll, { passive: true });
    }
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      if (parent) parent.removeEventListener('scroll', handleScroll);
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Sample data points for interactive chart
  const wealthData = [
    { label: 'Jan', netWorth: '₹38.2L', val: 38.2, target: 36.0, note: 'Baseline Verified' },
    { label: 'Mar', netWorth: '₹40.5L', val: 40.5, target: 37.8, note: '₹28,600 Tax Saved' },
    { label: 'May', netWorth: '₹42.4L', val: 42.4, target: 39.5, note: 'Emergency Fund 100%' },
    { label: 'Jul', netWorth: '₹44.8L', val: 44.8, target: 41.2, note: 'SIP Compounding' },
    { label: 'Sep', netWorth: '₹46.7L', val: 46.7, target: 43.0, note: 'Car Loan Accelerated' },
    { label: 'Oct', netWorth: '₹48.25L', val: 48.25, target: 44.0, note: '+14.2% YoY Milestone' },
    { label: 'Dec (Proj)', netWorth: '₹51.0L', val: 51.0, target: 45.8, note: 'First ₹50L Horizon' },
  ];

  const cashflowData = [
    { label: 'May', income: '₹1,25,000', expenses: '₹82,500', surplus: '₹42,500', inVal: 80, outVal: 52 },
    { label: 'Jun', income: '₹1,25,000', expenses: '₹84,100', surplus: '₹40,900', inVal: 80, outVal: 54 },
    { label: 'Jul', income: '₹1,28,000', expenses: '₹81,200', surplus: '₹46,800', inVal: 82, outVal: 50 },
    { label: 'Aug', income: '₹1,45,000', expenses: '₹88,000', surplus: '₹57,000', inVal: 95, outVal: 56 },
    { label: 'Sep', income: '₹1,25,000', expenses: '₹80,500', surplus: '₹44,500', inVal: 80, outVal: 48 },
    { label: 'Oct', income: '₹1,25,000', expenses: '₹82,500', surplus: '₹42,500', inVal: 80, outVal: 52 },
  ];

  const fireData = [
    { age: 'Age 28', corpus: '₹48.25L', stage: 'Current Portfolio', pct: '38.4%' },
    { age: 'Age 32', corpus: '₹1.15 Cr', stage: 'Emergency & Debt-Free', pct: '52.0%' },
    { age: 'Age 36', corpus: '₹1.95 Cr', stage: 'Coast FIRE Achieved', pct: '70.8%' },
    { age: 'Age 40', corpus: '₹2.85 Cr', stage: 'Lean FIRE Milestone', pct: '88.2%' },
    { age: 'Age 43', corpus: '₹3.42 Cr', stage: 'Full Financial Freedom', pct: '100%' },
  ];

  const activeHover = hoveredPointIndex !== null ? wealthData[hoveredPointIndex] : wealthData[5];

  return (
    <div
      ref={containerRef}
      className="min-h-screen bg-[#07090E] text-[#F3F4F6] font-['Plus_Jakarta_Sans',sans-serif] selection:bg-[#D4AF37]/30 selection:text-[#FFF0BE] relative overflow-x-hidden"
    >
      {/* Scroll-Driven Top Neon Progress Indicator */}
      <div className="fixed top-0 left-0 right-0 h-[2.5px] z-[60] bg-white/[0.04]">
        <div
          className="h-full bg-gradient-to-r from-[#D4AF37] via-[#ECC856] to-[#38BDF8] shadow-[0_0_12px_rgba(212,175,55,0.8)] transition-all duration-100 ease-out"
          style={{ width: `${scrollProgress}%` }}
        />
      </div>

      {/* Parallax Ambient Background Glow Orbs */}
      <div
        className="fixed top-0 left-1/2 w-[850px] h-[380px] bg-gradient-to-b from-[#D4AF37]/15 via-[#B89327]/8 to-transparent blur-3xl pointer-events-none -z-10 transition-transform duration-75 ease-out will-change-transform"
        style={{
          transform: `translate3d(-50%, ${scrollY * 0.16}px, 0)`,
        }}
      />
      <div
        className="fixed top-28 -left-28 w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-[#D4AF37]/12 via-[#ECC856]/5 to-transparent blur-[130px] pointer-events-none -z-10 transition-transform duration-75 ease-out will-change-transform"
        style={{
          transform: `translate3d(0, ${scrollY * 0.28}px, 0) rotate(${scrollY * 0.05}deg)`,
        }}
      />
      <div
        className="fixed top-1/2 -right-24 w-[600px] h-[600px] rounded-full bg-gradient-to-bl from-[#229ED9]/10 via-[#D4AF37]/5 to-transparent blur-[140px] pointer-events-none -z-10 transition-transform duration-75 ease-out will-change-transform"
        style={{
          transform: `translate3d(0, ${-scrollY * 0.2}px, 0)`,
        }}
      />
      <div
        className="fixed bottom-16 left-1/4 w-[550px] h-[550px] rounded-full bg-gradient-to-t from-[#B89327]/10 to-transparent blur-[150px] pointer-events-none -z-10 transition-transform duration-75 ease-out will-change-transform"
        style={{
          transform: `translate3d(0, ${scrollY * 0.12}px, 0)`,
        }}
      />

      {/* Floating Return to Dashboard Action (When Authenticated) */}
      {isAuthenticated && onOpenDashboard && (
        <aside aria-label="Return to Dashboard Navigation" className="fixed bottom-6 right-6 z-50 animate-float">
          <button
            onClick={onOpenDashboard}
            className="group flex items-center gap-2.5 px-5 py-3 rounded-full bg-gradient-to-r from-[#ECC856] via-[#D4AF37] to-[#B89327] text-charcoal-950 font-extrabold text-xs tracking-wide shadow-[0_10px_35px_rgba(212,175,55,0.45)] hover:shadow-[0_15px_45px_rgba(212,175,55,0.65)] hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer border border-[#FFF0BE]/60"
            title="Return to your authenticated dashboard"
          >
            <LayoutDashboard className="w-4 h-4 text-charcoal-950 font-bold" />
            <span>Return to Live Dashboard</span>
            <ArrowRight className="w-4 h-4 font-bold group-hover:translate-x-1 transition-transform" />
          </button>
        </aside>
      )}

      {/* Navigation Header */}
      <nav className="sticky top-0 z-50 w-full border-b border-[rgba(212,175,55,0.18)] bg-[#07090E]/90 backdrop-blur-md transition-all shadow-[0_4px_25px_rgba(0,0,0,0.5)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between">
          {/* Brand Logo & Home Mark */}
          <div
            className="flex items-center gap-3 cursor-pointer select-none group"
            onClick={() => {
              const parent = containerRef.current?.parentElement;
              if (parent) parent.scrollTo({ top: 0, behavior: 'smooth' });
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            title="FinPilot AI Home"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#ECC856]/25 via-[#D4AF37]/15 to-transparent border border-[#D4AF37]/40 flex items-center justify-center text-[#F5DE88] shadow-[0_0_15px_rgba(212,175,55,0.2)] group-hover:scale-105 group-hover:border-[#D4AF37] transition-all">
              <Sparkles className="w-5 h-5 font-bold" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg sm:text-xl tracking-tight bg-gradient-to-r from-[#FFF0BE] via-[#D4AF37] to-[#C5A059] bg-clip-text text-transparent">
                  FinPilot AI
                </span>
                <span className="text-[10px] uppercase font-bold tracking-widest text-[#D4AF37] px-2 py-0.5 rounded-full border border-[#D4AF37]/35 bg-[#D4AF37]/15 shadow-sm shadow-[#D4AF37]/10 flex items-center gap-1">
                  <Home className="w-2.5 h-2.5 text-[#D4AF37]" />
                  Home
                </span>
              </div>
              <p className="text-[10px] text-[#9CA3AF] hidden sm:block">Explainable Personal Finance Intelligence</p>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-[#9CA3AF]">
            <button
              onClick={() => scrollToSection('features')}
              className="hover:text-[#F5DE88] transition-colors"
            >
              Features
            </button>
            <button
              onClick={() => scrollToSection('how-it-works')}
              className="hover:text-[#F5DE88] transition-colors"
            >
              How It Works
            </button>
            <button
              onClick={() => scrollToSection('financial-tools')}
              className="hover:text-[#F5DE88] transition-colors"
            >
              Financial Tools
            </button>
            <button
              onClick={() => scrollToSection('security')}
              className="hover:text-[#F5DE88] transition-colors"
            >
              Security
            </button>
          </div>

          {/* Action CTAs */}
          <div className="hidden sm:flex items-center gap-2.5">
            {/* Telegram Bot Direct Action */}
            <a
              href="https://t.me/my_finpilotcfo_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#229ED9]/15 hover:bg-[#229ED9]/25 text-[#38BDF8] border border-[#229ED9]/35 hover:border-[#38BDF8]/60 transition-all shadow-sm group"
              title="Connect with FinPilot Global AI CFO on Telegram (@my_finpilotcfo_bot)"
            >
              <Send className="w-3.5 h-3.5 text-[#38BDF8] group-hover:scale-110 transition-transform" />
              <span>Telegram Bot</span>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#38BDF8] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#229ED9]"></span>
              </span>
            </a>

            {isAuthenticated ? (
              <Button
                variant="primary"
                size="md"
                onClick={onOpenDashboard}
                icon={<LayoutDashboard className="w-4 h-4" />}
              >
                Go to Dashboard
              </Button>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="md"
                  onClick={onLogin}
                  className="text-[#D1D5DB] hover:text-[#F5DE88]"
                >
                  Login
                </Button>
                <Button
                  variant="primary"
                  size="md"
                  onClick={onGetStarted}
                  icon={<ArrowRight className="w-4 h-4" />}
                  iconPosition="right"
                >
                  Get Started
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl text-[#9CA3AF] hover:text-white md:hidden hover:bg-white/5 transition-colors border border-transparent hover:border-[#D4AF37]/20"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6 text-[#F5DE88]" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-[rgba(212,175,55,0.18)] bg-[#0A0D14]/95 backdrop-blur-xl px-4 py-6 space-y-4 animate-in slide-in-from-top-4 duration-200">
            <div className="flex flex-col space-y-3 text-sm font-semibold text-[#9CA3AF]">
              <button
                onClick={() => scrollToSection('features')}
                className="text-left py-2 hover:text-[#F5DE88] border-b border-white/5"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection('how-it-works')}
                className="text-left py-2 hover:text-[#F5DE88] border-b border-white/5"
              >
                How It Works
              </button>
              <button
                onClick={() => scrollToSection('financial-tools')}
                className="text-left py-2 hover:text-[#F5DE88] border-b border-white/5"
              >
                Financial Tools
              </button>
              <button
                onClick={() => scrollToSection('security')}
                className="text-left py-2 hover:text-[#F5DE88] border-b border-white/5"
              >
                Security & DPDP
              </button>
            </div>

            {/* Mobile Telegram Link */}
            <a
              href="https://t.me/my_finpilotcfo_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold bg-[#229ED9]/15 text-[#38BDF8] border border-[#229ED9]/35"
            >
              <Send className="w-3.5 h-3.5 text-[#38BDF8]" />
              <span>Talk on Telegram (@my_finpilotcfo_bot)</span>
            </a>

            <div className="pt-2 flex flex-col gap-2.5">
              {isAuthenticated ? (
                <Button
                  variant="primary"
                  size="md"
                  onClick={onOpenDashboard}
                  className="w-full"
                  icon={<LayoutDashboard className="w-4 h-4" />}
                >
                  Go to Dashboard
                </Button>
              ) : (
                <>
                  <Button
                    variant="primary"
                    size="md"
                    onClick={onGetStarted}
                    className="w-full"
                    icon={<ArrowRight className="w-4 h-4" />}
                    iconPosition="right"
                  >
                    Get Started Free
                  </Button>
                  <Button
                    variant="ghost"
                    size="md"
                    onClick={onLogin}
                    className="w-full border border-white/10"
                  >
                    Login
                  </Button>
                </>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section with Parallax Floating Badges */}
      <section className="relative pt-12 sm:pt-20 pb-16 sm:pb-24 overflow-hidden">
        {/* Parallax Floating Metric Badge: Left */}
        <div
          className="hidden xl:flex items-center gap-3 absolute top-28 left-8 p-3 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.3)] shadow-[0_15px_35px_rgba(0,0,0,0.8)] backdrop-blur-md pointer-events-none transition-transform duration-100 ease-out z-20"
          style={{
            transform: `translate3d(0, ${-scrollY * 0.16}px, 0)`,
          }}
        >
          <div className="w-9 h-9 rounded-xl bg-[#D4AF37]/20 border border-[#D4AF37]/40 flex items-center justify-center text-[#F5DE88]">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-[#F3F4F6]">Coast FIRE On Track</span>
              <span className="text-[10px] text-[#10B981] font-semibold">38.4%</span>
            </div>
            <p className="text-[10px] text-[#9CA3AF]">Target: ₹3.42 Cr • Age 43</p>
          </div>
        </div>

        {/* Parallax Floating Metric Badge: Right */}
        <div
          className="hidden xl:flex items-center gap-3 absolute top-36 right-8 p-3 rounded-2xl bg-[#111622]/90 border border-[rgba(56,189,248,0.3)] shadow-[0_15px_35px_rgba(0,0,0,0.8)] backdrop-blur-md pointer-events-none transition-transform duration-100 ease-out z-20"
          style={{
            transform: `translate3d(0, ${-scrollY * 0.26}px, 0)`,
          }}
        >
          <div className="w-9 h-9 rounded-xl bg-[#229ED9]/20 border border-[#229ED9]/40 flex items-center justify-center text-[#38BDF8]">
            <Send className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-[#F3F4F6]">Telegram AI CFO</span>
              <span className="w-2 h-2 rounded-full bg-[#10B981] animate-ping" />
            </div>
            <p className="text-[10px] text-[#38BDF8] font-mono">@my_finpilotcfo_bot active</p>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          {/* Badge Tag */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#D4AF37]/10 border border-[#D4AF37]/35 text-xs text-[#F5DE88] mb-6 shadow-sm shadow-[#D4AF37]/15">
            <Sparkles className="w-3.5 h-3.5 text-[#ECC856]" />
            <span className="font-semibold tracking-wide">Next-Gen Explainable Indian FinTech</span>
          </div>

          {/* EXACT Hero Title */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-[#F3F4F6] leading-[1.12]">
            Smarter Finances. <br />
            <span className="bg-gradient-to-r from-[#FFF0BE] via-[#D4AF37] to-[#C5A059] bg-clip-text text-transparent">
              A Brighter Future.
            </span>
          </h1>

          {/* EXACT Hero Subtitle */}
          <p className="mt-6 text-base sm:text-lg lg:text-xl text-[#9CA3AF] max-w-3xl mx-auto leading-relaxed">
            Your AI-powered financial companion tailored for Indian professionals.
            Explainable wealth intelligence, real bank statement ingestion, deterministic tax planning,
            and automated FIRE roadmaps with zero hallucinated calculations.
          </p>

          {/* Hero CTAs: Get Started, Explore Features, Telegram Bot */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3.5 sm:gap-4">
            <Button
              variant="primary"
              size="lg"
              onClick={onGetStarted}
              className="w-full sm:w-auto px-8 py-3.5 text-base shadow-[0_4px_25px_rgba(212,175,55,0.3)] hover:scale-105 transition-all"
              icon={<ArrowRight className="w-5 h-5" />}
              iconPosition="right"
            >
              Get Started Free
            </Button>

            <a
              href="https://t.me/my_finpilotcfo_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-base font-bold bg-[#229ED9]/15 hover:bg-[#229ED9]/25 text-[#38BDF8] border border-[#229ED9]/40 hover:border-[#38BDF8] transition-all shadow-[0_0_20px_rgba(34,158,217,0.2)] hover:scale-105 group"
            >
              <Send className="w-4 h-4 text-[#38BDF8] group-hover:scale-110 transition-transform" />
              <span>Connect on Telegram</span>
              <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-[#229ED9]/30 text-white">
                @my_finpilotcfo_bot
              </span>
            </a>

            <Button
              variant="secondary"
              size="lg"
              onClick={() => scrollToSection('features')}
              className="w-full sm:w-auto px-6 py-3.5 text-base border-[rgba(212,175,55,0.3)] hover:border-[#D4AF37]/60"
            >
              Explore Features
            </Button>
          </div>

          {/* Trust Guarantees */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-xs text-[#9CA3AF]">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#10B981]" />
              <span>Section 115BAC & Indian Tax Norms</span>
            </div>
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-[#D4AF37]" />
              <span>Private Bank Statement Intelligence</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#38BDF8]" />
              <span>Zero Hallucinated Financial Calculations</span>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Product Preview Section with New High-End Vector Fintech Graph */}
      <section className="py-10 sm:py-16 relative">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* 3D Perspective Tilt Parallax Container */}
          <div
            className="relative rounded-3xl p-1 sm:p-2 bg-gradient-to-b from-[#D4AF37]/35 via-[#D4AF37]/15 to-transparent shadow-[0_25px_60px_-15px_rgba(0,0,0,0.95),0_0_40px_rgba(212,175,55,0.2)] transition-transform duration-100 ease-out will-change-transform"
            style={{
              transform: `perspective(1200px) rotateX(${Math.min(6, Math.max(0, scrollY * 0.012))}deg) translate3d(0, ${scrollY * 0.04}px, 0)`,
            }}
          >
            {/* Top Toolbar / Tab Switcher */}
            <div className="bg-[#0D111A] rounded-[22px] border border-[rgba(212,175,55,0.2)] p-4 sm:p-6 lg:p-8">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-white/[0.08] gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-[#F43F5E]/80" />
                  <div className="w-3 h-3 rounded-full bg-[#F59E0B]/80" />
                  <div className="w-3 h-3 rounded-full bg-[#10B981]/80" />
                  <span className="text-xs font-semibold text-[#D4AF37] ml-2 tracking-wide uppercase">
                    FinPilot Interactive Dashboard Preview
                  </span>
                </div>
                {/* Sample Data Disclaimer Tag */}
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-[11px] text-[#9CA3AF]">
                  <Eye className="w-3.5 h-3.5 text-[#D4AF37]" />
                  <span>Illustrative Sample Data (Never writes to user account)</span>
                </div>
              </div>

              {/* Preview Feature Tabs */}
              <div className="flex flex-wrap items-center gap-2 mt-5">
                {[
                  { id: 'overview', label: 'Financial Overview', icon: LayoutDashboard },
                  { id: 'cfo', label: 'AI CFO Assistant', icon: BotMessageSquare },
                  { id: 'tax', label: 'Tax Optimization', icon: ReceiptIndianRupee },
                  { id: 'fire', label: 'FIRE Freedom Planner', icon: Flame },
                ].map((t) => {
                  const Icon = t.icon;
                  const isActive = activePreviewTab === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setActivePreviewTab(t.id as any)}
                      className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                        isActive
                          ? 'bg-gradient-to-r from-[#D4AF37]/25 to-[#B89327]/15 text-[#F5DE88] border border-[#D4AF37]/40 shadow-sm shadow-[#D4AF37]/15'
                          : 'text-[#9CA3AF] hover:text-white bg-white/[0.03] hover:bg-white/[0.06] border border-transparent'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span>{t.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Dynamic Preview Canvas */}
              <div className="mt-6">
                {activePreviewTab === 'overview' && (
                  <div className="space-y-6">
                    {/* KPI Cards Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="p-4 rounded-xl bg-[#121622]/90 border border-[rgba(212,175,55,0.2)] shadow-sm">
                        <span className="text-xs text-[#9CA3AF]">Net Worth (Sample)</span>
                        <p className="text-2xl font-extrabold text-[#F3F4F6] mt-1 tabular-nums">₹48,25,000</p>
                        <span className="text-[11px] text-[#10B981] font-semibold mt-1 inline-block">+14.2% YoY Growth</span>
                      </div>
                      <div className="p-4 rounded-xl bg-[#121622]/90 border border-[rgba(212,175,55,0.2)] shadow-sm">
                        <span className="text-xs text-[#9CA3AF]">Monthly Surplus</span>
                        <p className="text-2xl font-extrabold text-[#F3F4F6] mt-1 tabular-nums">₹42,500</p>
                        <span className="text-[11px] text-[#38BDF8] font-semibold mt-1 inline-block">32% Savings Rate</span>
                      </div>
                      <div className="p-4 rounded-xl bg-[#121622]/90 border border-[rgba(212,175,55,0.2)] shadow-sm">
                        <span className="text-xs text-[#9CA3AF]">Emergency Runway</span>
                        <p className="text-2xl font-extrabold text-[#F5DE88] mt-1 tabular-nums">8.4 Months</p>
                        <span className="text-[11px] text-[#10B981] font-semibold mt-1 inline-block">Safe Reserve (&gt;6 Mo)</span>
                      </div>
                      <div className="p-4 rounded-xl bg-[#121622]/90 border border-[rgba(212,175,55,0.2)] shadow-sm">
                        <span className="text-xs text-[#9CA3AF]">Active Debts</span>
                        <p className="text-2xl font-extrabold text-[#F3F4F6] mt-1 tabular-nums">₹12,40,000</p>
                        <span className="text-[11px] text-[#F59E0B] font-semibold mt-1 inline-block">₹24,675/mo EMI</span>
                      </div>
                    </div>

                    {/* NEW HIGH-END FINTECH VECTOR GRAPH */}
                    <div className="p-5 sm:p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.22)] shadow-lg">
                      {/* Graph Mode Switcher & Title */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/[0.08] gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-[#F3F4F6]">
                              Institutional Wealth & Cash Flow Projection
                            </span>
                            <Badge variant="lavender" size="sm" className="bg-[#D4AF37]/15 text-[#F5DE88] border-[#D4AF37]/30">
                              Deterministic Model
                            </Badge>
                          </div>
                          <p className="text-xs text-[#9CA3AF] mt-0.5">
                            Interactive curve tracking compounding returns, debt reduction, and disposable cash reserves.
                          </p>
                        </div>

                        {/* Chart View Mode Controls */}
                        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-black/40 border border-white/10 self-start sm:self-auto">
                          <button
                            onClick={() => setChartMode('wealth')}
                            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                              chartMode === 'wealth'
                                ? 'bg-[#D4AF37] text-charcoal-950 shadow-sm'
                                : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
                            }`}
                          >
                            Net Worth
                          </button>
                          <button
                            onClick={() => setChartMode('cashflow')}
                            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                              chartMode === 'cashflow'
                                ? 'bg-[#D4AF37] text-charcoal-950 shadow-sm'
                                : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
                            }`}
                          >
                            Cash Flow
                          </button>
                          <button
                            onClick={() => setChartMode('fire')}
                            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                              chartMode === 'fire'
                                ? 'bg-[#D4AF37] text-charcoal-950 shadow-sm'
                                : 'text-[#9CA3AF] hover:text-[#F3F4F6]'
                            }`}
                          >
                            FIRE Horizon
                          </button>
                        </div>
                      </div>

                      {/* Interactive SVG Graph Canvas */}
                      <div className="relative pt-6 pb-2">
                        {/* MODE 1: WEALTH GROWTH CURVE */}
                        {chartMode === 'wealth' && (
                          <div className="space-y-4">
                            {/* Live Tooltip / Inspector Header */}
                            <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/10 text-xs">
                              <div className="flex items-center gap-3">
                                <span className="text-[#9CA3AF]">Selected Period:</span>
                                <span className="font-bold text-[#F5DE88]">{activeHover.label} 2024</span>
                                <span className="text-[#9CA3AF]">•</span>
                                <span className="text-[#9CA3AF]">Net Worth:</span>
                                <span className="font-extrabold text-[#F3F4F6] text-sm tabular-nums">{activeHover.netWorth}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="px-2 py-0.5 rounded bg-[#10B981]/15 text-[#10B981] font-semibold border border-[#10B981]/25">
                                  {activeHover.note}
                                </span>
                              </div>
                            </div>

                            {/* SVG Curved Vector Chart */}
                            <div className="relative w-full h-56 sm:h-64">
                              <svg className="w-full h-full overflow-visible" viewBox="0 0 700 240">
                                <defs>
                                  {/* Golden Area Gradient */}
                                  <linearGradient id="wealthGoldArea" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.45" />
                                    <stop offset="50%" stopColor="#B89327" stopOpacity="0.15" />
                                    <stop offset="100%" stopColor="#07090E" stopOpacity="0.0" />
                                  </linearGradient>
                                  {/* Cyan Target Area Gradient */}
                                  <linearGradient id="cyanLine" x1="0" y1="0" x2="1" y2="0">
                                    <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.7" />
                                    <stop offset="100%" stopColor="#10B981" stopOpacity="0.9" />
                                  </linearGradient>
                                  {/* Neon Glow Filter */}
                                  <filter id="goldNeonGlow" x="-20%" y="-20%" width="140%" height="140%">
                                    <feGaussianBlur stdDeviation="3.5" result="coloredBlur" />
                                    <feMerge>
                                      <feMergeNode in="coloredBlur" />
                                      <feMergeNode in="SourceGraphic" />
                                    </feMerge>
                                  </filter>
                                </defs>

                                {/* Horizontal Grid Lines */}
                                <line x1="0" y1="40" x2="700" y2="40" stroke="rgba(255,255,255,0.06)" strokeDasharray="4 4" />
                                <text x="10" y="36" fill="#9CA3AF" fontSize="10">₹50,00,000</text>

                                <line x1="0" y1="100" x2="700" y2="100" stroke="rgba(255,255,255,0.06)" strokeDasharray="4 4" />
                                <text x="10" y="96" fill="#9CA3AF" fontSize="10">₹45,00,000</text>

                                <line x1="0" y1="160" x2="700" y2="160" stroke="rgba(255,255,255,0.06)" strokeDasharray="4 4" />
                                <text x="10" y="156" fill="#9CA3AF" fontSize="10">₹40,00,000</text>

                                <line x1="0" y1="220" x2="700" y2="220" stroke="rgba(255,255,255,0.06)" />
                                <text x="10" y="216" fill="#9CA3AF" fontSize="10">₹35,00,000</text>

                                {/* Target Trajectory Line (Cyan Dotted) */}
                                <path
                                  d="M 50 205 C 150 185, 270 160, 390 145 C 500 130, 600 105, 660 90"
                                  fill="none"
                                  stroke="url(#cyanLine)"
                                  strokeWidth="2"
                                  strokeDasharray="5 5"
                                  opacity="0.8"
                                />

                                {/* Area Under Wealth Curve */}
                                <path
                                  d="M 50 185 C 150 160, 270 135, 390 115 C 500 95, 590 65, 660 38 L 660 220 L 50 220 Z"
                                  fill="url(#wealthGoldArea)"
                                />

                                {/* Main Wealth Curve (Glow Golden Bezier) */}
                                <path
                                  d="M 50 185 C 150 160, 270 135, 390 115 C 500 95, 590 65, 660 38"
                                  fill="none"
                                  stroke="#ECC856"
                                  strokeWidth="3.5"
                                  filter="url(#goldNeonGlow)"
                                />

                                {/* Interactive Data Nodes */}
                                {[
                                  { cx: 50, cy: 185, idx: 0 },
                                  { cx: 152, cy: 160, idx: 1 },
                                  { cx: 254, cy: 139, idx: 2 },
                                  { cx: 356, cy: 118, idx: 3 },
                                  { cx: 458, cy: 98, idx: 4 },
                                  { cx: 560, cy: 74, idx: 5 },
                                  { cx: 660, cy: 38, idx: 6 },
                                ].map((pt) => {
                                  const isSelected = hoveredPointIndex === pt.idx || (hoveredPointIndex === null && pt.idx === 5);
                                  return (
                                    <g
                                      key={pt.idx}
                                      className="cursor-pointer group"
                                      onMouseEnter={() => setHoveredPointIndex(pt.idx)}
                                    >
                                      {/* Laser vertical tracking line */}
                                      {isSelected && (
                                        <line
                                          x1={pt.cx}
                                          y1="20"
                                          x2={pt.cx}
                                          y2="220"
                                          stroke="#D4AF37"
                                          strokeWidth="1.5"
                                          strokeDasharray="3 3"
                                          opacity="0.75"
                                        />
                                      )}
                                      {/* Outer Pulse Ring */}
                                      <circle
                                        cx={pt.cx}
                                        cy={pt.cy}
                                        r={isSelected ? 10 : 6}
                                        fill="#D4AF37"
                                        fillOpacity={isSelected ? 0.35 : 0.15}
                                        className="transition-all duration-200"
                                      />
                                      {/* Center Solid Node */}
                                      <circle
                                        cx={pt.cx}
                                        cy={pt.cy}
                                        r={isSelected ? 5 : 3.5}
                                        fill={isSelected ? '#FFF0BE' : '#D4AF37'}
                                        stroke="#07090E"
                                        strokeWidth="2"
                                        className="transition-all duration-200"
                                      />
                                    </g>
                                  );
                                })}

                                {/* X-Axis Month Markers */}
                                {wealthData.map((d, i) => {
                                  const xPos = 50 + i * 101.6;
                                  return (
                                    <text
                                      key={i}
                                      x={xPos}
                                      y="238"
                                      fill={hoveredPointIndex === i ? '#F5DE88' : '#9CA3AF'}
                                      fontSize="11"
                                      fontWeight={hoveredPointIndex === i ? 'bold' : 'normal'}
                                      textAnchor="middle"
                                    >
                                      {d.label}
                                    </text>
                                  );
                                })}
                              </svg>
                            </div>

                            {/* Legend and Key Milestones */}
                            <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-white/[0.08] text-xs">
                              <div className="flex items-center gap-5">
                                <div className="flex items-center gap-2">
                                  <div className="w-3 h-1 rounded-full bg-[#ECC856]" />
                                  <span className="text-[#F3F4F6] font-medium">Actual Wealth Growth</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <div className="w-3 h-1 rounded-full bg-[#38BDF8] border-b border-dashed border-[#38BDF8]" />
                                  <span className="text-[#9CA3AF]">FIRE Milestone Baseline</span>
                                </div>
                              </div>
                              <div className="flex items-center gap-2 text-[11px] text-[#D4AF37]">
                                <Sparkles className="w-3.5 h-3.5" />
                                <span>Ahead of Target FIRE Curve by 1.8 Years</span>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* MODE 2: CASH FLOW SURPLUS DYNAMICS */}
                        {chartMode === 'cashflow' && (
                          <div className="space-y-4">
                            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/10 flex flex-wrap items-center justify-between gap-3 text-xs">
                              <div className="flex items-center gap-4">
                                <div>
                                  <span className="text-[#9CA3AF] block text-[10px]">Monthly Inflow</span>
                                  <span className="font-extrabold text-[#10B981] text-sm">₹1,25,000</span>
                                </div>
                                <div className="h-6 w-px bg-white/10" />
                                <div>
                                  <span className="text-[#9CA3AF] block text-[10px]">Living & EMI Outflow</span>
                                  <span className="font-extrabold text-[#F43F5E] text-sm">₹82,500</span>
                                </div>
                                <div className="h-6 w-px bg-white/10" />
                                <div>
                                  <span className="text-[#9CA3AF] block text-[10px]">Net Investable Surplus</span>
                                  <span className="font-extrabold text-[#F5DE88] text-sm">+₹42,500</span>
                                </div>
                              </div>
                              <span className="px-2.5 py-1 rounded-lg bg-[#D4AF37]/15 text-[#F5DE88] font-semibold border border-[#D4AF37]/30 text-xs">
                                34% Savings Rate
                              </span>
                            </div>

                            {/* Dual Bar Dynamics */}
                            <div className="h-44 w-full flex items-end gap-3 pt-4 border-b border-white/10">
                              {cashflowData.map((col, idx) => (
                                <div key={idx} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                                  <div className="w-full max-w-[36px] flex items-end justify-center gap-1.5 h-full">
                                    <div
                                      className="w-1/2 rounded-t-md bg-gradient-to-t from-[#059669] to-[#10B981] group-hover:brightness-125 transition-all"
                                      style={{ height: `${col.inVal}%` }}
                                      title={`Income: ${col.income}`}
                                    />
                                    <div
                                      className="w-1/2 rounded-t-md bg-gradient-to-t from-[#BE123C] to-[#F43F5E] group-hover:brightness-125 transition-all"
                                      style={{ height: `${col.outVal}%` }}
                                      title={`Expenses: ${col.expenses}`}
                                    />
                                  </div>
                                  <span className="text-[11px] text-[#9CA3AF] group-hover:text-white font-medium">{col.label}</span>
                                </div>
                              ))}
                            </div>

                            <div className="flex items-center justify-between text-xs text-[#9CA3AF] pt-2">
                              <div className="flex items-center gap-4">
                                <div className="flex items-center gap-1.5">
                                  <div className="w-2.5 h-2.5 rounded bg-[#10B981]" />
                                  <span>Income Inflow</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <div className="w-2.5 h-2.5 rounded bg-[#F43F5E]" />
                                  <span>Living Outflow</span>
                                </div>
                              </div>
                              <span className="text-[#10B981] font-semibold">Zero Unverified Deficit</span>
                            </div>
                          </div>
                        )}

                        {/* MODE 3: FIRE FREEDOM COMPOUNDING HORIZON */}
                        {chartMode === 'fire' && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                              <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10">
                                <span className="text-[11px] text-[#9CA3AF]">Target FIRE Corpus</span>
                                <p className="text-xl font-extrabold text-[#F5DE88] mt-1">₹3.42 Crore</p>
                                <span className="text-[10px] text-[#9CA3AF]">Adjusted for 6% Indian inflation</span>
                              </div>
                              <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10">
                                <span className="text-[11px] text-[#9CA3AF]">Current Progress</span>
                                <p className="text-xl font-extrabold text-[#10B981] mt-1">38.4%</p>
                                <span className="text-[10px] text-[#9CA3AF]">₹1.31 Crore accumulated</span>
                              </div>
                              <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10">
                                <span className="text-[11px] text-[#9CA3AF]">Coast FIRE Horizon</span>
                                <p className="text-xl font-extrabold text-[#38BDF8] mt-1">Age 36</p>
                                <span className="text-[10px] text-[#9CA3AF]">Zero additional SIP required</span>
                              </div>
                            </div>

                            {/* Milestone Timeline Progress Bars */}
                            <div className="space-y-3 pt-2">
                              {fireData.map((stage, idx) => (
                                <div key={idx} className="p-3 rounded-xl bg-[#0B0F17] border border-white/[0.08] flex items-center justify-between gap-4">
                                  <div className="flex items-center gap-3">
                                    <div className="w-7 h-7 rounded-lg bg-[#D4AF37]/20 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] font-bold text-xs">
                                      {idx + 1}
                                    </div>
                                    <div>
                                      <span className="text-xs font-bold text-[#F3F4F6]">{stage.age} • {stage.stage}</span>
                                      <p className="text-[11px] text-[#9CA3AF]">Target: {stage.corpus}</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <div className="w-24 sm:w-32 h-2 rounded-full bg-white/10 overflow-hidden">
                                      <div
                                        className="h-full bg-gradient-to-r from-[#D4AF37] to-[#10B981] rounded-full"
                                        style={{ width: stage.pct }}
                                      />
                                    </div>
                                    <span className="text-xs font-bold text-[#F5DE88] w-12 text-right">{stage.pct}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {activePreviewTab === 'cfo' && (
                  <div className="p-5 rounded-xl bg-[#121622]/90 border border-[rgba(212,175,55,0.2)] space-y-4">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-[#D4AF37]/20 border border-[#D4AF37]/30 flex items-center justify-center text-[#F5DE88] text-xs font-bold shrink-0">
                        CFO
                      </div>
                      <div className="p-4 rounded-2xl bg-white/[0.04] border border-white/10 text-xs sm:text-sm leading-relaxed max-w-2xl text-[#E5E7EB]">
                        <p className="font-semibold text-[#F5DE88] mb-1">FinPilot AI CFO Analysis:</p>
                        "Based on your actual net income of ₹1,25,000 and current ₹24,675 car EMI, taking an additional ₹15,000 personal loan would increase your Debt-to-Income (DTI) ratio to 31.7%. Your 8.4-month emergency runway remains fully intact."
                        <div className="mt-3 flex flex-wrap gap-2">
                          <span className="px-2 py-0.5 rounded bg-[#D4AF37]/15 text-[#F5DE88] text-[11px] font-semibold border border-[#D4AF37]/25">
                            Deterministic Calculation
                          </span>
                          <span className="px-2 py-0.5 rounded bg-white/5 text-[#9CA3AF] text-[11px] border border-white/10">
                            Sec 288B Compliant
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activePreviewTab === 'tax' && (
                  <div className="p-5 rounded-xl bg-[#121622]/90 border border-[rgba(212,175,55,0.2)] grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-white/[0.03] border border-[#10B981]/30">
                      <span className="text-xs font-semibold text-[#10B981]">Section 115BAC (New Regime)</span>
                      <p className="text-2xl font-extrabold text-[#F3F4F6] mt-1 tabular-nums">₹1,14,400</p>
                      <p className="text-xs text-[#9CA3AF] mt-1">₹75,000 Standard Deduction Applied. Saves ₹28,600 over Old Regime.</p>
                      <Badge variant="mint" size="sm" className="mt-3 bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30">
                        Recommended Regime
                      </Badge>
                    </div>
                    <div className="p-4 rounded-xl bg-white/[0.03] border border-white/10 opacity-70">
                      <span className="text-xs font-semibold text-[#9CA3AF]">Old Tax Regime</span>
                      <p className="text-2xl font-extrabold text-[#F3F4F6] mt-1 tabular-nums">₹1,43,000</p>
                      <p className="text-xs text-[#9CA3AF] mt-1">With 80C (₹1.5L), 80D (₹25k) and standard deductions.</p>
                      <Badge variant="neutral" size="sm" className="mt-3">
                        Alternate Regime
                      </Badge>
                    </div>
                  </div>
                )}

                {activePreviewTab === 'fire' && (
                  <div className="p-5 rounded-xl bg-[#121622]/90 border border-[rgba(212,175,55,0.2)] space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div className="p-3.5 rounded-lg bg-white/[0.03] border border-white/10">
                        <span className="text-[11px] text-[#9CA3AF]">Target FIRE Corpus</span>
                        <p className="text-xl font-extrabold text-[#F5DE88] mt-1">₹3.42 Crore</p>
                        <span className="text-[10px] text-[#9CA3AF]">Adjusted for 6% Indian inflation</span>
                      </div>
                      <div className="p-3.5 rounded-lg bg-white/[0.03] border border-white/10">
                        <span className="text-[11px] text-[#9CA3AF]">Current Progress</span>
                        <p className="text-xl font-extrabold text-[#10B981] mt-1">38.4%</p>
                        <span className="text-[10px] text-[#9CA3AF]">₹1.31 Crore accumulated</span>
                      </div>
                      <div className="p-3.5 rounded-lg bg-white/[0.03] border border-white/10">
                        <span className="text-[11px] text-[#9CA3AF]">Coast FIRE Horizon</span>
                        <p className="text-xl font-extrabold text-[#38BDF8] mt-1">Age 44</p>
                        <span className="text-[10px] text-[#9CA3AF]">Zero additional SIP required</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Features Grid Section */}
      <section id="features" className="py-20 sm:py-28 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 sm:mb-20">
            <h2 className="text-xs uppercase font-bold tracking-widest text-[#D4AF37] mb-3">
              Full-Spectrum Intelligence
            </h2>
            <p className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-[#F3F4F6]">
              Every Financial Module. <br />
              <span className="text-gold-gradient">Built for Real Life in India.</span>
            </p>
            <p className="mt-4 text-base text-[#9CA3AF] leading-relaxed">
              Explore the dedicated engines running inside FinPilot AI. All grounded with zero mock data and statutory precision.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 1. Global AI CFO */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <BotMessageSquare className="w-5 h-5" />
              </div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-bold text-[#F3F4F6]">Global AI CFO & Assistant</h3>
                <span className="text-[10px] bg-[#229ED9]/20 text-[#38BDF8] border border-[#229ED9]/30 px-2 py-0.5 rounded-full font-mono">
                  Telegram Bot
                </span>
              </div>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Conversational advisor analyzing verified cash flows, staging write actions, disambiguating casual loan requests, and citing Indian tax statutes.
              </p>
            </div>

            {/* 2. Financial Overview */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <LayoutDashboard className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F3F4F6] mb-2">Dashboard & Real-Time Net Worth</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Holistic view of assets, liabilities, verified liquid bank reserves, monthly surplus rate, and emergency runway months.
              </p>
            </div>

            {/* 3. Accounts & Statements */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <Landmark className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F3F4F6] mb-2">Bank Statements & Accounts</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Multi-format statement ingestion (CSV, XLSX, PDF) with Indian date normalization, internal transfer deduplication, and zero mock data.
              </p>
            </div>

            {/* 4. Budget Management */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <Wallet className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F3F4F6] mb-2">50-30-20 Budget Management</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Benchmark your lifestyle against verified income. Categorize discretionary spending, detect anomalous surges, and unlock savings surplus.
              </p>
            </div>

            {/* 5. Investment Planning */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <TrendingUp className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F3F4F6] mb-2">Investments & Asset Allocation</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Compare Liquid Funds vs Bonds vs Fixed Deposits. Model SIP compounding and evaluate Section 50AA debt fund taxation rules.
              </p>
            </div>

            {/* 6. Financial Goals */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <Target className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F3F4F6] mb-2">Financial Goals & SIP Sizing</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Define targets for home down payments, weddings, education, and vehicles with inflation-adjusted monthly SIP recommendations.
              </p>
            </div>

            {/* 7. Tax Planning */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <ReceiptIndianRupee className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F3F4F6] mb-2">Tax Planning (AY 2025-26)</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Compare Section 115BAC New Regime vs Old Regime with enhanced ₹75,000 standard deductions, 87A rebate, and marginal surcharge relief.
              </p>
            </div>

            {/* 8. Retirement & Freedom */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <Flame className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F3F4F6] mb-2">Retirement & FIRE Forecaster</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Fisher equation real compound returns across 4 strategies: Regular, Lean, Fat, and Coast FIRE with decumulation simulations.
              </p>
            </div>

            {/* 9. Decision Simulator & Reports */}
            <div className="p-6 rounded-2xl bg-[#111622]/90 border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_rgba(212,175,55,0.12)] transition-all group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#D4AF37]/25 to-[#B89327]/10 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88] mb-5 group-hover:scale-105 transition-transform">
                <SlidersHorizontal className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F3F4F6] mb-2">Decision Simulator & Stress Tests</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Test life purchases across 3 option pathways against 5 stress tests (income cuts, inflation hikes, emergency shocks) before committing.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 sm:py-28 bg-[#0A0D14] border-y border-[rgba(212,175,55,0.15)] relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-xs uppercase font-bold tracking-widest text-[#D4AF37] mb-3">
              Streamlined Financial Flow
            </h2>
            <p className="text-3xl sm:text-4xl font-extrabold text-[#F3F4F6]">
              How FinPilot Works
            </p>
            <p className="mt-3 text-sm text-[#9CA3AF]">
              Three simple steps to transition from scattered numbers to institutional wealth clarity.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl bg-[#111622] border border-white/[0.08] relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#D4AF37] to-[#B89327] text-black font-extrabold flex items-center justify-center text-sm mb-4">
                1
              </div>
              <h3 className="text-base font-bold text-[#F3F4F6] mb-2">Import or Link Your Data</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Upload authentic bank statements (CSV, XLSX, PDF) or link via RBI-regulated Account Aggregator consent. Zero mock data.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[#111622] border border-[rgba(212,175,55,0.3)] shadow-[0_4px_25px_rgba(212,175,55,0.1)] relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#D4AF37] to-[#B89327] text-black font-extrabold flex items-center justify-center text-sm mb-4">
                2
              </div>
              <h3 className="text-base font-bold text-[#F3F4F6] mb-2">Deterministic Engines Calculate</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Algorithms evaluate cash flows, detect recurring bills, compute DTI, calculate tax under Sec 115BAC, and simulate emergency runways.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[#111622] border border-white/[0.08] relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#D4AF37] to-[#B89327] text-black font-extrabold flex items-center justify-center text-sm mb-4">
                3
              </div>
              <h3 className="text-base font-bold text-[#F3F4F6] mb-2">Interact & Execute with AI CFO</h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Chat via web or connect to Telegram (<a href="https://t.me/my_finpilotcfo_bot" target="_blank" rel="noopener noreferrer" className="text-[#38BDF8] hover:underline font-semibold">@my_finpilotcfo_bot</a>). Authorize debt entries, adjust budgets, track repayments, and receive proactive alerts.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Financial Tools Section */}
      <section id="financial-tools" className="py-20 sm:py-28 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
            <div>
              <h2 className="text-xs uppercase font-bold tracking-widest text-[#D4AF37] mb-2">
                Specialized Calculators
              </h2>
              <p className="text-3xl sm:text-4xl font-extrabold text-[#F3F4F6]">
                Interactive Financial Tools
              </p>
            </div>
            <p className="text-xs sm:text-sm text-[#9CA3AF] max-w-md">
              Accessible across the platform with plain-language explanations and instant results.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-[#111622]/80 border border-white/[0.08] hover:border-[#D4AF37]/40 transition-colors">
              <ReceiptIndianRupee className="w-5 h-5 text-[#F5DE88] mb-3" />
              <h4 className="text-sm font-bold text-[#F3F4F6]">Tax Regime Estimator</h4>
              <p className="text-xs text-[#9CA3AF] mt-1.5 leading-relaxed">
                Section 115BAC vs Old Regime comparison with surcharge relief and 87A rebate.
              </p>
            </div>
            <div className="p-5 rounded-xl bg-[#111622]/80 border border-white/[0.08] hover:border-[#D4AF37]/40 transition-colors">
              <CreditCard className="w-5 h-5 text-[#F5DE88] mb-3" />
              <h4 className="text-sm font-bold text-[#F3F4F6]">Debt Avalanche vs Snowball</h4>
              <p className="text-xs text-[#9CA3AF] mt-1.5 leading-relaxed">
                Prioritize interest savings or psychological wins with prepayment simulation.
              </p>
            </div>
            <div className="p-5 rounded-xl bg-[#111622]/80 border border-white/[0.08] hover:border-[#D4AF37]/40 transition-colors">
              <TrendingUp className="w-5 h-5 text-[#F5DE88] mb-3" />
              <h4 className="text-sm font-bold text-[#F3F4F6]">Liquid Funds vs FD Analyzer</h4>
              <p className="text-xs text-[#9CA3AF] mt-1.5 leading-relaxed">
                Evaluate post-tax returns under Section 50AA with instant redemption liquidity.
              </p>
            </div>
            <div className="p-5 rounded-xl bg-[#111622]/80 border border-white/[0.08] hover:border-[#D4AF37]/40 transition-colors">
              <Send className="w-5 h-5 text-[#38BDF8] mb-3" />
              <h4 className="text-sm font-bold text-[#F3F4F6]">Telegram Mobile CFO</h4>
              <p className="text-xs text-[#9CA3AF] mt-1.5 leading-relaxed">
                Manage budgets, simulate purchases, and query net worth directly on Telegram.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Security & Statutory Section */}
      <section id="security" className="py-16 sm:py-24 bg-[#0A0D14] border-t border-[rgba(212,175,55,0.18)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-3xl p-8 sm:p-12 bg-gradient-to-br from-[#121622] to-[#0A0D14] border border-[rgba(212,175,55,0.25)] flex flex-col md:flex-row items-center justify-between gap-8 shadow-xl">
            <div className="space-y-3 max-w-xl text-left">
              <Badge variant="mint" size="sm" className="bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30">
                DPDP Act 2023 Compliant
              </Badge>
              <h3 className="text-2xl sm:text-3xl font-extrabold text-[#F3F4F6]">
                Data Isolation & Financial Sovereignty
              </h3>
              <p className="text-xs sm:text-sm text-[#9CA3AF] leading-relaxed">
                Your private financial records are strictly isolated. We do not store banking credentials, execute unauthorized broker trades, or index user data into public models. Full portability and permanent data deletion supported.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 shrink-0 w-full sm:w-auto">
              <Button
                variant="primary"
                size="lg"
                onClick={onGetStarted}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
                className="w-full sm:w-auto"
              >
                Create Free Account
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.08] bg-[#07090E] py-12 text-xs text-[#9CA3AF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#D4AF37]/20 border border-[#D4AF37]/35 flex items-center justify-center text-[#F5DE88]">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <span className="font-bold text-sm text-[#F3F4F6]">FinPilot AI</span>
            <span className="text-[#9CA3AF] ml-2">© 2026 FinPilot AI. All rights reserved.</span>
          </div>

          <div className="flex flex-wrap items-center gap-6">
            <button onClick={() => scrollToSection('features')} className="hover:text-[#F5DE88] transition-colors">
              Features
            </button>
            <button onClick={() => scrollToSection('how-it-works')} className="hover:text-[#F5DE88] transition-colors">
              How It Works
            </button>
            <button onClick={() => scrollToSection('financial-tools')} className="hover:text-[#F5DE88] transition-colors">
              Financial Tools
            </button>
            <a
              href="https://t.me/my_finpilotcfo_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#38BDF8] hover:underline font-semibold flex items-center gap-1"
            >
              <Send className="w-3 h-3 text-[#38BDF8]" />
              <span>Telegram Bot</span>
            </a>
            <button onClick={onLogin} className="hover:text-[#F5DE88] transition-colors">
              Sign In
            </button>
            <button onClick={onGetStarted} className="text-[#D4AF37] hover:underline font-semibold">
              Get Started
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
