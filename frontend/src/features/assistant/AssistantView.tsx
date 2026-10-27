import React, { useState, useRef, useEffect } from 'react';
import {
  BotMessageSquare,
  Send,
  Sparkles,
  BookOpen,
  Wrench,
  User as UserIcon,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { apiRequest, getAuthToken } from '../../services/api';
import { ChatMessage } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';

interface AssistantViewProps {
  onNavigateToTab?: (tab: string) => void;
}

const renderFormattedInline = (text: string) => {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let lastIdx = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.slice(lastIdx, match.index));
    }
    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      const inner = token.slice(2, -2);
      if (inner.toLowerCase().includes('comfortably affordable') || inner.toLowerCase() === 'affordable') {
        parts.push(
          <span key={match.index} className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30">
            ✓ {inner}
          </span>
        );
      } else if (inner.toLowerCase().includes('not affordable') || inner.toLowerCase().includes('deficit')) {
        parts.push(
          <span key={match.index} className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#EF4444]/20 text-[#EF4444] border border-[#EF4444]/30">
            ✕ {inner}
          </span>
        );
      } else {
        parts.push(<strong key={match.index} className="font-bold text-white">{inner}</strong>);
      }
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(<code key={match.index} className="bg-[#1A2232] text-[#ECC856] px-1.5 py-0.5 rounded text-[11px] font-mono border border-[rgba(212,175,55,0.2)]">{token.slice(1, -1)}</code>);
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(<em key={match.index} className="italic text-[#9CA3AF] text-xs">{token.slice(1, -1)}</em>);
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

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="my-2 space-y-1 pl-1">
          {currentList}
        </ul>
      );
      currentList = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const line = rawLine.trim();

    if (!line) {
      flushList();
      continue;
    }

    if (line.startsWith('#')) {
      flushList();
      const title = line.replace(/^#+\s*/, '');
      elements.push(
        <div key={`h-${i}`} className="text-sm font-bold text-[#F5DE88] mt-3 mb-1.5 border-b border-[rgba(212,175,55,0.15)] pb-1 tracking-tight">
          {renderFormattedInline(title)}
        </div>
      );
      continue;
    }

    if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ')) {
      const itemText = line.replace(/^[-*•]\s+/, '').trim();
      currentList.push(
        <li key={`li-${i}`} className="flex items-start gap-2 text-xs text-[#E5E7EB]">
          <span className="text-[#D4AF37] font-bold text-xs shrink-0 mt-0.5">•</span>
          <span className="flex-1 leading-relaxed">{renderFormattedInline(itemText)}</span>
        </li>
      );
      continue;
    }

    flushList();
    elements.push(
      <p key={`p-${i}`} className="text-xs text-[#D1D5DB] leading-relaxed my-1.5">
        {renderFormattedInline(line)}
      </p>
    );
  }

  flushList();

  return <div className="space-y-1">{elements}</div>;
};

export const AssistantView: React.FC<AssistantViewProps> = ({ onNavigateToTab }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content: (
        "Namaste! I am **FinPilot AI**, your explainable personal finance assistant for Indian users.\n\n" +
        "You can ask me to calculate taxes across regimes, compare Liquid Mutual Funds vs Bonds vs FDs, " +
        "record debts or loan liabilities (e.g. 'I borrowed ₹50,000 from Rohan'), " +
        "or compute required monthly contributions for your financial milestones. " +
        "All calculations are computed deterministically using official statutory rules."
      ),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations: [
        "Income Tax Act 1961 (Section 115BAC)",
        "SEBI Mutual Fund Regulations (Liquid Scheme Norms)",
      ],
    },
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [providerStatus, setProviderStatus] = useState<{ provider: string; model: string; ready: boolean } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiRequest<{ provider: string; model: string; ready: boolean }>('/assistant/provider-status')
      .then((data) => setProviderStatus(data))
      .catch(() => setProviderStatus(null));

    if (getAuthToken()) {
      apiRequest<Array<{ id: string; sender: 'user' | 'assistant'; content: string; citations?: string[]; created_at: string }>>('/assistant/history')
        .then((data) => {
          if (data && data.length > 0) {
            const mapped: ChatMessage[] = data.map((m) => ({
              id: m.id,
              sender: m.sender,
              content: m.content,
              timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              citations: m.citations || [],
            }));
            setMessages(mapped);
          }
        })
        .catch((err) => {
          console.error('Failed to load chat history:', err);
        });
    }
  }, []);

  const samplePrompts = [
    "I borrowed ₹50,000 from Rohan at 0% interest",
    "What are my active debts and liabilities?",
    "What recurring payments do I have next month?",
    "What is my projected cash flow and ending balance for the next 30 days?",
    "Am I on track for my savings goals with my current surplus?",
    "Compare tax for 15 LPA salary in new vs old regime",
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

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
        pending_action?: any;
        clarification?: any;
      }>('/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: query,
          clarification_id: clarificationId,
          option_id: optionId,
          page_context: {
            page: 'assistant',
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
        content: `I encountered an issue processing your query: ${err.message || 'Service temporarily unavailable'}. Please verify your connection or retry.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 flex flex-col h-[calc(100vh-140px)]">
      {/* Page Header */}
      <PageHeader
        title="AI CFO Assistant"
        description="Grounded conversational intelligence with verified Income Tax Act & SEBI guidelines. Zero hallucinated formulas."
        icon={<BotMessageSquare className="w-5 h-5 text-[#ECC856]" />}
        badge={
          <div className="flex items-center gap-2">
            <Badge variant="mint" size="sm">
              Intelligence Engine
            </Badge>
            <Badge variant="blue" size="sm">
              Verified Rules
            </Badge>
          </div>
        }
      />

      {/* Messages Canvas */}
      <Card
        padding="none"
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 border border-[rgba(212,175,55,0.2)] bg-[#0D111A]/95 backdrop-blur-md"
      >
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-3 ${
              m.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {m.sender === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-[#D4AF37]/15 border border-[#D4AF37]/30 flex items-center justify-center text-[#ECC856] shrink-0 mt-0.5 shadow-sm shadow-[#D4AF37]/10">
                <Sparkles className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-2xl p-4 sm:p-5 text-xs sm:text-sm space-y-3 shadow-md ${
                m.sender === 'user'
                  ? 'bg-gradient-to-r from-[#ECC856] via-[#D4AF37] to-[#B89327] text-black font-medium rounded-tr-none shadow-[#D4AF37]/20'
                  : 'bg-[#141A26]/90 border border-[rgba(212,175,55,0.22)] text-[#F3F4F6] rounded-tl-none'
              }`}
            >
              {/* Tool Execution Badges */}
              {m.tool_invocations && m.tool_invocations.length > 0 && (
                <div className="space-y-1.5 pb-2.5 border-b border-white/10">
                  {m.tool_invocations.map((t, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-1.5 text-[11px] font-semibold text-[#10B981] bg-[#10B981]/15 px-2.5 py-1 rounded-lg border border-[#10B981]/25"
                    >
                      <Wrench className="w-3.5 h-3.5 shrink-0" />
                      <span>{t.summary}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Message Content */}
              <div className="leading-relaxed font-sans">
                <FormattedMessage content={m.content} isUser={m.sender === 'user'} />
              </div>

              {/* Clarification Disambiguation Options */}
              {m.clarification && m.clarification.options && m.clarification.options.length > 0 && (
                <div className="pt-2.5 border-t border-white/10 space-y-2">
                  <div className="text-[11px] font-bold text-[#F5DE88] flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-[#D4AF37]" />
                    <span>Please choose an option to proceed:</span>
                  </div>
                  <div className="grid grid-cols-1 gap-1.5">
                    {m.clarification.options.map((opt, oIdx) => {
                      const label = typeof opt === 'string' ? opt : opt.label;
                      const optId = typeof opt === 'string' ? `opt_${oIdx + 1}` : opt.id;
                      return (
                        <button
                          key={optId || oIdx}
                          disabled={loading}
                          onClick={() => handleSend(label, m.clarification?.id, optId)}
                          className="text-left px-3 py-2 bg-[#1A2232] hover:bg-[#222C40] border border-[rgba(212,175,55,0.25)] hover:border-[#D4AF37] text-[#E5E7EB] hover:text-[#F5DE88] text-[11px] font-medium rounded-xl transition-all shadow-sm flex items-center justify-between group disabled:opacity-50 cursor-pointer"
                        >
                          <span>
                            <strong className="font-bold mr-1.5 text-[#D4AF37]">{oIdx + 1}.</strong>
                            {label}
                          </span>
                          <ArrowRight className="w-3 h-3 text-[#D4AF37] opacity-0 group-hover:opacity-100 transition-opacity" />
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Pending Action Proposal Card */}
              {m.pending_action && (
                <div className="pt-2.5 border-t border-white/10">
                  <div className="bg-[#0B0F17] border border-[#D4AF37]/30 rounded-2xl p-3.5 space-y-3 shadow-md">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4 text-[#D4AF37]" />
                        <span className="text-xs font-bold text-[#F5DE88]">
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

                    <div className="text-xs text-[#D1D5DB]">
                      {m.pending_action.preview?.summary}
                    </div>

                    {/* Preview Key-Value Items */}
                    {m.pending_action.preview?.items && (
                      <div className="bg-[#141A26] border border-white/5 rounded-xl p-2.5 space-y-1.5 text-[11px]">
                        {m.pending_action.preview.items.map((it, itIdx) => (
                          <div key={itIdx} className="flex justify-between items-center text-[#F3F4F6]">
                            <span className="text-[#9CA3AF] font-medium">{it.label}</span>
                            <span className="font-bold text-[#D4AF37]">{it.value}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Safety Disclaimer */}
                    <div className="text-[10px] text-[#9CA3AF] bg-[#D4AF37]/10 border border-[#D4AF37]/20 p-2 rounded-xl flex items-start gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-[#D4AF37] shrink-0 mt-0.5" />
                      <span>{m.pending_action.preview?.disclaimer}</span>
                    </div>

                    {/* Action Controls */}
                    {m.pending_action.status === 'awaiting_confirmation' && (
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => handleConfirmAction(m.pending_action!.id, m.id)}
                          disabled={actionLoadingId === m.pending_action.id}
                          className="flex-1 py-2 px-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-charcoal-950 text-xs font-extrabold rounded-xl transition-all shadow-sm flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
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
                          className="py-2 px-3 bg-white/[0.04] hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-bold rounded-xl transition-all disabled:opacity-50 cursor-pointer"
                        >
                          Cancel
                        </button>
                      </div>
                    )}

                    {m.pending_action.status === 'succeeded' && (
                      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-2.5 text-xs text-emerald-400 font-medium flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                          <span>Action Verified & Persisted to FinPilot</span>
                        </div>
                        {m.pending_action.target_entity === 'liability' && onNavigateToTab && (
                          <button
                            onClick={() => onNavigateToTab('debts')}
                            className="text-[11px] font-bold text-[#D4AF37] underline hover:text-[#ECC856] cursor-pointer"
                          >
                            View in Debt & Liabilities →
                          </button>
                        )}
                        {m.pending_action.target_entity === 'recurring_transaction' && onNavigateToTab && (
                          <button
                            onClick={() => onNavigateToTab('recurring')}
                            className="text-[11px] font-bold text-[#D4AF37] underline hover:text-[#ECC856] cursor-pointer"
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
                <div className="pt-2.5 border-t border-white/10 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#ECC856]">
                    <BookOpen className="w-3.5 h-3.5 text-[#ECC856]" />
                    <span>Statutory Citations:</span>
                  </div>
                  <ul className="list-disc list-inside text-[11px] text-[#9CA3AF] space-y-0.5">
                    {m.citations.map((cite, idx) => (
                      <li key={idx}>{cite}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div
                className={`text-[10px] text-right ${
                  m.sender === 'user' ? 'text-black/70 font-semibold' : 'text-[#9CA3AF]'
                }`}
              >
                {m.timestamp}
              </div>
            </div>

            {m.sender === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-[#141A26] border border-[#D4AF37]/40 flex items-center justify-center text-[#F5DE88] shrink-0 mt-0.5 font-bold text-xs shadow-sm">
                <UserIcon className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#D4AF37]/15 border border-[#D4AF37]/30 flex items-center justify-center text-[#ECC856] shrink-0">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="rounded-2xl rounded-tl-none p-3.5 bg-[#141A26]/90 border border-[rgba(212,175,55,0.22)] text-xs text-[#9CA3AF] flex items-center gap-2 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#ECC856] animate-pulse" />
              <span>Evaluating statutory calculations and citation models...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </Card>

      {/* Suggested Quick Prompts */}
      <div className="flex items-center gap-2 overflow-x-auto py-1 shrink-0 scrollbar-none">
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="text-[11px] whitespace-nowrap px-3 py-1.5 rounded-xl bg-[#141A26] hover:bg-[#1A2232] border border-[rgba(212,175,55,0.2)] hover:border-[#D4AF37] text-[#9CA3AF] hover:text-[#F3F4F6] shadow-sm transition-all shrink-0"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Composer Input */}
      <div className="flex items-center gap-2.5 shrink-0">
        <input
          type="text"
          placeholder="Ask any tax, investment, or goal question in plain English (e.g. 15 LPA salary tax in new vs old regime)..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSend();
          }}
          className="flex-1 bg-[#141A26] border border-white/15 rounded-2xl px-4 py-3 text-xs sm:text-sm text-[#F3F4F6] placeholder-[#6B7280] shadow-sm focus:outline-none focus:border-[#D4AF37] focus:ring-1 focus:ring-[#D4AF37]/50 transition-all"
        />
        <Button
          variant="primary"
          size="lg"
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          icon={<Send className="w-4 h-4" />}
          className="rounded-2xl px-5"
        >
          Send
        </Button>
      </div>
    </div>
  );
};
