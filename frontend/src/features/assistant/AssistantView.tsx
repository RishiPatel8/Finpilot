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
} from 'lucide-react';
import { apiRequest, getAuthToken } from '../../services/api';
import { ChatMessage } from '../../types';
import { Card, Badge, Button, PageHeader } from '../../components/ui';

export const AssistantView: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content: (
        "Namaste! I am **FinPilot AI**, your explainable personal finance assistant for Indian users.\n\n" +
        "You can ask me to calculate taxes across regimes, compare Liquid Mutual Funds vs Bonds vs FDs, " +
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
    "What recurring payments do I have next month?",
    "How much do I spend on subscriptions every month?",
    "What happens to my cash flow if I pause a ₹1,500 subscription?",
    "Why did I spend more this month and what are my spending anomalies?",
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

  const handleSend = async (textToSend?: string) => {
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
      }>('/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({ message: query }),
      });

      const asstMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        content: res.content,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: res.citations,
        tool_invocations: res.tool_invocations,
      };

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
              <div className="leading-relaxed whitespace-pre-wrap font-sans">
                {m.content}
              </div>

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
