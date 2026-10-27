import React, { useState, useRef, useEffect } from 'react';
import {
  BotMessageSquare,
  Sparkles,
  X,
  Maximize2,
  Minimize2,
  Trash2,
  Send,
  Copy,
  Check,
  RotateCcw,
  AlertCircle,
  TrendingUp,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Zap,
  ThumbsUp,
  ThumbsDown,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { apiRequest, getAuthToken } from '../../services/api';
import { ChatMessage, ProactiveInsightItem, User } from '../../types';
import { Badge, Button } from '../../components/ui';

interface GlobalAICFOProps {
  activePage: string;
  user: User | null;
  onNavigateToTab?: (tab: string) => void;
}

const renderFormattedInline = (text: string) => {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let lastIdx = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.slice(lastIdx, match.index));
    }
    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(<strong key={match.index} className="font-bold text-[#F3F4F6]">{token.slice(2, -2)}</strong>);
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(<em key={match.index} className="italic text-[#9CA3AF]">{token.slice(1, -1)}</em>);
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(<code key={match.index} className="bg-charcoal-800 text-[#D4AF37] px-1 py-0.5 rounded text-[11px] font-mono border border-[rgba(212,175,55,0.2)]">{token.slice(1, -1)}</code>);
    }
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < text.length) {
    parts.push(text.slice(lastIdx));
  }
  return parts.length > 0 ? parts : text;
};

const FormattedMessage: React.FC<{ content: string; isUser: boolean }> = ({ content, isUser }) => {
  if (isUser) {
    return <div className="whitespace-pre-wrap break-words">{content}</div>;
  }

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];
  let inAlert = false;
  let alertContent: string[] = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="my-1.5 space-y-1 pl-1">
          {currentList}
        </ul>
      );
      currentList = [];
    }
  };

  const flushAlert = () => {
    if (inAlert && alertContent.length > 0) {
      elements.push(
        <div
          key={`alert-${elements.length}`}
          className="my-2 p-2.5 bg-[#D4AF37]/10 border border-[#D4AF37]/30 rounded-xl text-[11px] text-[#F3F4F6] flex items-start gap-2"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-[#D4AF37] shrink-0 mt-0.5" />
          <div className="flex-1 space-y-0.5">
            {alertContent.map((l, idx) => (
              <p key={idx}>{renderFormattedInline(l)}</p>
            ))}
          </div>
        </div>
      );
      inAlert = false;
      alertContent = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const line = rawLine.trim();

    if (line.startsWith('>')) {
      flushList();
      const alertLine = line.replace(/^>\s*(\[![\w]+\])?\s*/, '').trim();
      if (!inAlert) {
        inAlert = true;
      }
      if (alertLine) alertContent.push(alertLine);
      continue;
    } else if (inAlert) {
      flushAlert();
    }

    if (!line) {
      flushList();
      continue;
    }

    if (line.startsWith('#')) {
      flushList();
      const title = line.replace(/^#+\s*/, '');
      elements.push(
        <div key={`h-${i}`} className="font-extrabold text-[12px] text-[#F5DE88] mt-2 mb-1 tracking-tight border-b border-[rgba(212,175,55,0.15)] pb-0.5">
          {renderFormattedInline(title)}
        </div>
      );
      continue;
    }

    if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ')) {
      const itemText = line.replace(/^[-*•]\s+/, '').trim();
      currentList.push(
        <li key={`li-${i}`} className="flex items-start gap-1.5 text-[11px] text-[#E5E7EB]">
          <span className="text-[#D4AF37] font-bold shrink-0">•</span>
          <span className="flex-1">{renderFormattedInline(itemText)}</span>
        </li>
      );
      continue;
    }

    flushList();
    elements.push(
      <p key={`p-${i}`} className="text-[11px] text-[#D1D5DB] leading-relaxed my-1">
        {renderFormattedInline(line)}
      </p>
    );
  }

  flushList();
  flushAlert();

  return <div className="space-y-1">{elements}</div>;
};

export const GlobalAICFO: React.FC<GlobalAICFOProps> = ({
  activePage,
  user,
  onNavigateToTab,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [proactiveInsights, setProactiveInsights] = useState<ProactiveInsightItem[]>([]);
  const [showInsightsBanner, setShowInsightsBanner] = useState(true);
  const [expandedToolIndex, setExpandedToolIndex] = useState<string | null>(null);
  const [providerStatus, setProviderStatus] = useState<{ provider: string; model: string; ready: boolean } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load chat history & provider status
  const loadHistory = async () => {
    if (getAuthToken()) {
      try {
        const data = await apiRequest<Array<{ id: string; sender: 'user' | 'assistant'; content: string; citations?: string[]; tool_invocations?: any[]; created_at: string }>>('/assistant/history');
        if (data && data.length > 0) {
          const mapped: ChatMessage[] = data.map((m) => ({
            id: m.id,
            sender: m.sender,
            content: m.content,
            timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            citations: m.citations || [],
            tool_invocations: m.tool_invocations || [],
          }));
          setMessages(mapped);
          return;
        }
      } catch (err) {
        console.warn('Failed to load chat history:', err);
      }
    }

    // Default welcome if no history
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        content: (
          "Hello! I am **FinPilot Global AI CFO 2.0**.\n\n" +
          "I have continuous access to your complete financial standing across all pages—including linked bank balances, " +
          "recurring commitments, category budgets, cash-flow projections, and tax settings.\n\n" +
          "Ask me anything, like **'Can I afford a ₹25,000 monthly EMI?'** or **'What payments are due next month?'**"
        ),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: ["FinPilot Multi-Module Financial Intelligence", "Indian Income Tax & RBI Guidelines"],
      },
    ]);
  };

  // Load proactive insights when assistant is opened
  const loadProactiveInsights = async () => {
    try {
      const data = await apiRequest<ProactiveInsightItem[]>('/assistant/proactive-insights');
      if (data && data.length > 0) {
        setProactiveInsights(data);
      }
    } catch {
      setProactiveInsights([]);
    }
  };

  useEffect(() => {
    apiRequest<{ provider: string; model: string; ready: boolean }>('/assistant/provider-status')
      .then((data) => setProviderStatus(data))
      .catch(() => setProviderStatus(null));

    loadHistory();
    loadProactiveInsights();
  }, [user]);

  useEffect(() => {
    if (isOpen) {
      loadProactiveInsights();
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Page-specific contextual prompt suggestions
  const getContextualPrompts = (): string[] => {
    switch (activePage) {
      case 'budget':
        return [
          "Why am I overspending this month?",
          "Where did my highest discretionary spending go?",
          "What if I reduce Dining Out by 15%?",
        ];
      case 'recurring':
        return [
          "What recurring payments do I have next month?",
          "How much do I spend on subscriptions each month?",
          "What happens to my cash flow if I pause a subscription?",
        ];
      case 'fire':
        return [
          "Can I retire at 45 with my current savings rate?",
          "How does a 15% market return change my FIRE date?",
          "What is my safe withdrawal rate benchmark?",
        ];
      case 'goals':
        return [
          "Am I on track for my financial goals?",
          "How much monthly SIP do I need for my down payment?",
        ];
      case 'debts':
        return [
          "Can I afford another monthly EMI?",
          "Avalanche vs Snowball: which pays my loans faster?",
        ];
      case 'tax':
        return [
          "Compare AY 2025-26 New vs Old Tax Regime for my income.",
          "How can I optimize 80C and standard deduction?",
        ];
      default:
        return [
          "Can I afford a ₹25,000 monthly EMI?",
          "What is my net worth and financial health standing?",
          "What recurring payments do I have next month?",
          "Compare tax for 15 LPA salary in new vs old regime",
        ];
    }
  };

  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const handleSend = async (textToSend?: string, clarificationId?: string, optionId?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const res = await apiRequest<{
        content: string;
        citations: string[];
        tool_invocations: Array<{ tool: string; summary: string }>;
        active_page?: string;
        pending_action?: any;
        clarification?: any;
      }>('/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: query,
          clarification_id: clarificationId,
          option_id: optionId,
          page_context: {
            page: activePage,
            url: window.location.pathname,
            timestamp: new Date().toISOString(),
          },
        }),
      });

      const asstMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        content: res.content,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: res.citations || [],
        tool_invocations: res.tool_invocations || [],
        pending_action: res.pending_action || null,
        clarification: res.clarification || null,
      };

      if (res.pending_action?.status === 'succeeded') {
        window.dispatchEvent(new CustomEvent('finpilot:financial-data-updated', { detail: res }));
      }

      setMessages((prev) => [...prev, asstMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        content: `I encountered an issue processing your request: ${err.message || 'Service temporarily unavailable'}. Please verify your network connection and retry.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAction = async (actionId: string, msgId: string) => {
    setActionLoadingId(actionId);
    try {
      const res = await apiRequest<{
        status: string;
        action_id: string;
        message: string;
        result?: any;
      }>(`/assistant/actions/${actionId}/confirm`, {
        method: 'POST',
        body: JSON.stringify({ idempotency_key: `web_${Date.now()}` }),
      });

      if (res.status === 'succeeded') {
        window.dispatchEvent(new CustomEvent('finpilot:financial-data-updated', { detail: res }));
      }

      setMessages((prev) =>
        prev.map((m) => {
          if (m.id === msgId && m.pending_action) {
            return {
              ...m,
              pending_action: {
                ...m.pending_action,
                status: res.status,
                execution_result: res.result,
              },
            };
          }
          return m;
        })
      );
    } catch (err: any) {
      alert(`Execution failed: ${err.message || 'Error occurred'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleCancelAction = async (actionId: string, msgId: string) => {
    setActionLoadingId(actionId);
    try {
      await apiRequest(`/assistant/actions/${actionId}/cancel`, { method: 'POST' });
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id === msgId && m.pending_action) {
            return {
              ...m,
              pending_action: {
                ...m.pending_action,
                status: 'cancelled',
              },
            };
          }
          return m;
        })
      );
    } catch (err: any) {
      alert(`Cancellation failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleFeedback = async (msgId: string, rating: number) => {
    try {
      await apiRequest('/assistant/feedback', {
        method: 'POST',
        body: JSON.stringify({
          event_type: 'rating_feedback',
          rating,
        }),
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, feedback: { rating, submitted: true } } : m))
      );
    } catch (err) {
      console.error('Feedback failed:', err);
    }
  };

  const handleClearHistory = async () => {
    if (confirm('Clear entire AI CFO conversation history?')) {
      try {
        if (getAuthToken()) {
          await apiRequest('/assistant/history', { method: 'DELETE' });
        }
        setMessages([
          {
            id: 'welcome-reset',
            sender: 'assistant',
            content: "Conversation history cleared. How can I assist you with your financial decisions today?",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      } catch (err) {
        console.error('Failed to clear history:', err);
      }
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Action Button (Launcher) */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-40 animate-in fade-in duration-300">
          <button
            onClick={() => setIsOpen(true)}
            className="group relative flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-[#ECC856] via-[#D4AF37] to-[#B89327] text-charcoal-950 font-bold rounded-full shadow-[0_10px_25px_-5px_rgba(212,175,55,0.4),0_8px_10px_-6px_rgba(212,175,55,0.2)] hover:shadow-[0_15px_30px_-5px_rgba(212,175,55,0.6)] hover:scale-105 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-[#D4AF37]/30"
            aria-label="Open AI CFO Assistant"
          >
            <div className="relative">
              <Sparkles className="w-5 h-5 text-charcoal-950" />
              {proactiveInsights.length > 0 && (
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full ring-2 ring-charcoal-950 animate-pulse" />
              )}
            </div>
            <span className="text-xs font-extrabold tracking-wide text-charcoal-950">AI CFO</span>

            {/* Context Tooltip Pill */}
            <span className="hidden sm:inline-block text-[10px] font-semibold bg-charcoal-950/20 text-charcoal-950 px-2 py-0.5 rounded-full capitalize">
              {activePage}
            </span>
          </button>
        </div>
      )}

      {/* Floating Assistant Panel */}
      {isOpen && (
        <div
          className={`fixed z-50 flex flex-col bg-[#0D111A] border border-[rgba(212,175,55,0.25)] shadow-[0_25px_50px_-12px_rgba(0,0,0,0.8)] backdrop-blur-xl transition-all duration-300 ease-out animate-in slide-in-from-bottom-6 fade-in ${
            isExpanded
              ? 'inset-4 sm:inset-10 max-w-4xl mx-auto rounded-3xl'
              : 'bottom-4 right-4 sm:bottom-6 sm:right-6 w-[calc(100vw-2rem)] sm:w-[440px] h-[600px] max-h-[88vh] rounded-3xl'
          }`}
        >
          {/* Panel Header */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/10 bg-[#111622] rounded-t-3xl">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-r from-[#ECC856] to-[#D4AF37] flex items-center justify-center text-charcoal-950 shrink-0 shadow-sm">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-xs font-extrabold text-[#F3F4F6] tracking-tight">
                    FinPilot AI CFO 2.0
                  </h3>
                  <Badge variant="mint" size="sm">
                    Live Context
                  </Badge>
                </div>
                <div className="flex items-center gap-1.5 text-[10px] text-[#9CA3AF] truncate">
                  <span>Viewing:</span>
                  <span className="font-semibold text-[#D4AF37] capitalize">{activePage}</span>
                  <span>•</span>
                  <span>Intelligence Engine</span>
                </div>
              </div>
            </div>

            {/* Header Action Controls */}
            <div className="flex items-center gap-1">
              <button
                onClick={handleClearHistory}
                className="p-1.5 rounded-lg text-[#9CA3AF] hover:text-rose-400 hover:bg-white/[0.04] transition-colors"
                title="Clear conversation"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="hidden sm:inline-flex p-1.5 rounded-lg text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-white/[0.04] transition-colors"
                title={isExpanded ? 'Dock panel' : 'Expand panel'}
              >
                {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-white/[0.04] transition-colors"
                title="Close AI CFO"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Proactive Insights Banner (Dismissible / Collapsible) */}
          {showInsightsBanner && proactiveInsights.length > 0 && (
            <div className="mx-4 mt-3 p-3 bg-white/[0.02] border border-[rgba(212,175,55,0.2)] rounded-2xl transition-all">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-[#D4AF37]" />
                  <span className="text-[11px] font-bold text-[#F3F4F6]">
                    Proactive Financial Insights ({proactiveInsights.length})
                  </span>
                </div>
                <button
                  onClick={() => setShowInsightsBanner(false)}
                  className="text-[10px] text-[#9CA3AF] hover:text-[#F3F4F6]"
                >
                  Dismiss
                </button>
              </div>
              <div className="space-y-1.5">
                {proactiveInsights.slice(0, 2).map((ins) => (
                  <button
                    key={ins.id}
                    onClick={() => handleSend(ins.suggested_prompt)}
                    className="w-full text-left p-2 bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 rounded-xl transition-all flex items-start justify-between gap-2 group"
                  >
                    <div>
                      <div className="text-[11px] font-semibold text-[#F3F4F6] group-hover:text-[#D4AF37]">
                        {ins.title}
                      </div>
                      <div className="text-[10px] text-[#9CA3AF] line-clamp-1">{ins.message}</div>
                    </div>
                    <span className="text-[9px] font-bold text-[#D4AF37] shrink-0 mt-0.5">Ask →</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
            {messages.map((m, mIdx) => (
              <div
                key={m.id || mIdx}
                className={`flex items-start gap-2.5 ${
                  m.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.sender === 'assistant' && (
                  <div className="w-7 h-7 rounded-xl bg-white/[0.04] border border-[rgba(212,175,55,0.25)] flex items-center justify-center text-[#D4AF37] shrink-0 mt-0.5 shadow-sm">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-3.5 sm:p-4 text-xs leading-relaxed space-y-2 shadow-sm ${
                    m.sender === 'user'
                      ? 'bg-gradient-to-r from-[#ECC856] to-[#D4AF37] text-charcoal-950 font-semibold rounded-tr-none'
                      : 'bg-[#111622] border border-white/10 text-[#F3F4F6] rounded-tl-none'
                  }`}
                >
                  {/* Tool Invocations Details Badge */}
                  {m.tool_invocations && m.tool_invocations.length > 0 && (
                    <div className="space-y-1 pb-2 border-b border-[#E6EAF0]">
                      {m.tool_invocations.map((t, tIdx) => {
                        const key = `${m.id}-${tIdx}`;
                        const isExpanded = expandedToolIndex === key;
                        return (
                          <div
                            key={tIdx}
                            className="bg-white border border-[#E6EAF0] rounded-xl p-2 text-[10px] text-[#697386]"
                          >
                            <div
                              className="flex items-center justify-between cursor-pointer"
                              onClick={() => setExpandedToolIndex(isExpanded ? null : key)}
                            >
                              <div className="flex items-center gap-1.5 font-semibold text-[#172033]">
                                <ShieldCheck className="w-3 h-3 text-[#38A169]" />
                                <span>Tool: {t.tool}</span>
                              </div>
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </div>
                            {isExpanded && (
                              <div className="mt-1.5 pt-1.5 border-t border-[#E6EAF0] text-[#172033] font-mono whitespace-pre-wrap">
                                {t.summary}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Message Markdown Body */}
                  <FormattedMessage content={m.content} isUser={m.sender === 'user'} />

                  {/* Clarification Option Chips */}
                  {m.clarification?.options && m.clarification.options.length > 0 && (
                    <div className="pt-2 border-t border-[#E6EAF0] space-y-1.5">
                      <div className="text-[10px] font-bold text-[#6478E8] flex items-center justify-between">
                        <span>Select an option:</span>
                        {m.clarification.expires_at && (
                          <span className="text-[9px] text-[#697386] font-normal flex items-center gap-1">
                            <Clock className="w-2.5 h-2.5" />
                            Valid for 15m
                          </span>
                        )}
                      </div>
                      <div className="flex flex-col gap-1.5">
                        {m.clarification.options.map((opt, oIdx) => {
                          const label = typeof opt === 'string' ? opt : opt.label;
                          const optId = typeof opt === 'string' ? `opt_${oIdx + 1}` : opt.id;
                          return (
                            <button
                              key={optId || oIdx}
                              disabled={loading}
                              onClick={() => handleSend(label, m.clarification?.id, optId)}
                              className="text-left px-3 py-2 bg-white hover:bg-[#EEF0FF] border border-[#6478E8]/30 hover:border-[#6478E8] text-[#172033] hover:text-[#6478E8] text-[11px] font-medium rounded-xl transition-all shadow-sm flex items-center justify-between group disabled:opacity-50"
                            >
                              <span>
                                <strong className="font-bold mr-1.5 text-[#6478E8]">{oIdx + 1}.</strong>
                                {label}
                              </span>
                              <ArrowRight className="w-3 h-3 text-[#6478E8] opacity-0 group-hover:opacity-100 transition-opacity" />
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Pending Action Proposal Card */}
                  {m.pending_action && (
                    <div className="pt-2.5 border-t border-[#E6EAF0]">
                      <div className="bg-white border-2 border-[#6478E8]/30 rounded-2xl p-3 space-y-2.5 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <AlertCircle className="w-4 h-4 text-[#6478E8]" />
                            <span className="text-[11px] font-bold text-[#172033]">
                              {m.pending_action.preview?.title || 'Action Proposal'}
                            </span>
                          </div>
                          <Badge
                            variant={
                              m.pending_action.status === 'succeeded'
                                ? 'mint'
                                : m.pending_action.status === 'cancelled'
                                ? 'neutral'
                                : m.pending_action.status === 'expired'
                                ? 'danger'
                                : 'blue'
                            }
                            size="sm"
                          >
                            {m.pending_action.status.replace('_', ' ').toUpperCase()}
                          </Badge>
                        </div>

                        <div className="text-[11px] text-[#697386]">
                          {m.pending_action.preview?.summary}
                        </div>

                        {/* Item fields */}
                        {m.pending_action.preview?.items && (
                          <div className="bg-charcoal-900/80 border border-white/5 rounded-xl p-2.5 space-y-1.5 text-[10px]">
                            {m.pending_action.preview.items.map((it, itIdx) => (
                              <div key={itIdx} className="flex justify-between items-center text-[#F3F4F6]">
                                <span className="text-[#9CA3AF] font-medium">{it.label}</span>
                                <span className="font-bold text-[#D4AF37]">{it.value}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Safety Disclaimer */}
                        <div className="text-[9px] text-[#9CA3AF] bg-[#D4AF37]/10 border border-[#D4AF37]/20 p-2 rounded-xl flex items-start gap-1.5">
                          <ShieldCheck className="w-3 h-3 text-[#D4AF37] shrink-0 mt-0.5" />
                          <span>{m.pending_action.preview?.disclaimer}</span>
                        </div>

                        {/* Confirm / Cancel Controls */}
                        {m.pending_action.status === 'awaiting_confirmation' && (
                          <div className="flex items-center gap-2 pt-1">
                            <button
                              onClick={() => handleConfirmAction(m.pending_action!.id, m.id)}
                              disabled={actionLoadingId === m.pending_action.id}
                              className="flex-1 py-2 px-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-charcoal-950 text-[11px] font-extrabold rounded-xl transition-all shadow-sm flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
                            >
                              {actionLoadingId === m.pending_action.id ? (
                                <>
                                  <Loader2 className="w-3.5 h-3.5 animate-spin text-charcoal-950" />
                                  <span>Verifying...</span>
                                </>
                              ) : (
                                <>
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  <span>Confirm & Execute</span>
                                </>
                              )}
                            </button>
                            <button
                              onClick={() => handleCancelAction(m.pending_action!.id, m.id)}
                              disabled={actionLoadingId === m.pending_action.id}
                              className="py-2 px-3 bg-white/[0.04] hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[11px] font-bold rounded-xl transition-all disabled:opacity-50 cursor-pointer"
                            >
                              Cancel
                            </button>
                          </div>
                        )}

                        {m.pending_action.status === 'succeeded' && (
                          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-2.5 text-[11px] text-emerald-400 font-medium flex items-center justify-between gap-2">
                            <div className="flex items-center gap-1.5">
                              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                              <span>Action Verified & Persisted to FinPilot</span>
                            </div>
                            {m.pending_action.target_entity === 'liability' && onNavigateToTab && (
                              <button
                                onClick={() => onNavigateToTab('debts')}
                                className="text-[10px] font-bold text-[#D4AF37] underline hover:text-[#ECC856]"
                              >
                                View in Debts →
                              </button>
                            )}
                            {m.pending_action.target_entity === 'recurring_transaction' && onNavigateToTab && (
                              <button
                                onClick={() => onNavigateToTab('recurring')}
                                className="text-[10px] font-bold text-[#D4AF37] underline hover:text-[#ECC856]"
                              >
                                View in Recurring →
                              </button>
                            )}
                          </div>
                        )}

                        {m.pending_action.status === 'cancelled' && (
                          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-2 text-[10px] text-[#9CA3AF] flex items-center gap-1.5">
                            <XCircle className="w-3.5 h-3.5 text-[#9CA3AF]" />
                            <span>Action safely cancelled. No changes were made to your records.</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Statutory Citations */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-2 border-t border-white/10 flex flex-wrap gap-1">
                      {m.citations.map((c, cIdx) => (
                        <span
                          key={cIdx}
                          className="inline-flex items-center gap-1 text-[9px] font-semibold bg-white/[0.04] border border-white/10 px-2 py-0.5 rounded-md text-[#9CA3AF]"
                        >
                          <ShieldCheck className="w-2.5 h-2.5 text-[#D4AF37]" />
                          {c}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Message Footer / Feedback / Copy */}
                  <div className="flex items-center justify-between pt-1 text-[10px] opacity-70 text-[#9CA3AF]">
                    <span>{m.timestamp}</span>
                    {m.sender === 'assistant' && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleFeedback(m.id, 1)}
                          className={`hover:opacity-100 p-0.5 rounded transition-colors ${
                            m.feedback?.rating === 1 ? 'text-emerald-400 font-bold opacity-100' : 'text-[#9CA3AF]'
                          }`}
                          title="Helpful response"
                        >
                          <ThumbsUp className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleFeedback(m.id, -1)}
                          className={`hover:opacity-100 p-0.5 rounded transition-colors ${
                            m.feedback?.rating === -1 ? 'text-rose-400 font-bold opacity-100' : 'text-[#9CA3AF]'
                          }`}
                          title="Needs improvement"
                        >
                          <ThumbsDown className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => copyToClipboard(m.content, m.id)}
                          className="hover:opacity-100 p-0.5"
                          title="Copy text"
                        >
                          {copiedId === m.id ? (
                            <Check className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex items-start gap-2.5">
                <div className="w-7 h-7 rounded-xl bg-white/[0.04] border border-[rgba(212,175,55,0.25)] flex items-center justify-center text-[#D4AF37] shrink-0 animate-pulse">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
                <div className="bg-[#111622] border border-white/10 rounded-2xl p-3.5 text-xs text-[#9CA3AF] flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#D4AF37] animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-[#D4AF37] animate-bounce [animation-delay:0.2s]" />
                  <div className="w-2 h-2 rounded-full bg-[#D4AF37] animate-bounce [animation-delay:0.4s]" />
                  <span className="text-[11px] font-medium ml-1">Analyzing cross-feature records...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Contextual Quick Prompts Carousel */}
          <div className="px-4 py-2 border-t border-white/10 bg-[#0A0D14] overflow-x-auto no-scrollbar flex items-center gap-1.5">
            {getContextualPrompts().map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                disabled={loading}
                className="whitespace-nowrap px-2.5 py-1 text-[10px] font-semibold text-[#F3F4F6] bg-white/[0.04] hover:bg-white/[0.08] hover:text-[#D4AF37] border border-white/10 hover:border-[rgba(212,175,55,0.4)] rounded-lg transition-all shrink-0 shadow-[0_1px_2px_rgba(0,0,0,0.2)]"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Form Bar */}
          <div className="p-3.5 border-t border-white/10 bg-[#111622] rounded-b-3xl">
            <div className="relative flex items-center bg-charcoal-900/90 border border-white/10 focus-within:border-[rgba(212,175,55,0.5)] focus-within:ring-2 focus-within:ring-[#D4AF37]/20 rounded-2xl p-1.5 transition-all">
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your financial decisions..."
                className="flex-1 bg-transparent border-none text-xs text-[#F3F4F6] placeholder-[#9CA3AF]/60 px-3 py-1.5 focus:outline-none resize-none max-h-24"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="w-8 h-8 rounded-xl bg-gradient-to-r from-[#ECC856] to-[#D4AF37] hover:brightness-110 disabled:opacity-40 text-charcoal-950 flex items-center justify-center shrink-0 transition-all shadow-sm font-bold"
                aria-label="Send query"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="flex items-center justify-between mt-2 px-1 text-[9px] text-[#9CA3AF]">
              <span>Press Enter to send • Shift+Enter for newline</span>
              <span className="font-semibold text-[#D4AF37]">100% Deterministic & Private</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
