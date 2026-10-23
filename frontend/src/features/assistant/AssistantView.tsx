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
import { apiRequest } from '../../services/api';
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const samplePrompts = [
    "I earn ₹60,000 per month, spend ₹35,000 and have ₹2 lakh in savings. I want to buy a car in 18 months. What are my options?",
    "Compare tax for 15 LPA salary in new vs old regime",
    "Should I invest 3 lakh in liquid fund or bond for 6 months?",
    "How much to save per month for 20 lakh house downpayment in 3 years?",
    "What is the standard deduction in AY 2025-26 under Finance Act 2024?",
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
        description="Grounded conversational intelligence with statutory Income Tax & SEBI RAG citations. Zero hallucinated formulas."
        icon={<BotMessageSquare className="w-4 h-4 text-[#6478E8]" />}
        badge={
          <Badge variant="mint" size="sm">
            Statutory Citations Verified
          </Badge>
        }
      />

      {/* Messages Canvas */}
      <Card
        padding="none"
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 bg-[#F6F8FC]/50"
      >
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-3 ${
              m.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {m.sender === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-[#EEF0FF] border border-[#6478E8]/20 flex items-center justify-center text-[#6478E8] shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-2xl p-4 sm:p-5 text-xs sm:text-sm space-y-3 shadow-sm ${
                m.sender === 'user'
                  ? 'bg-[#6478E8] text-white rounded-tr-none font-medium'
                  : 'bg-white border border-[#E6EAF0] text-[#172033] rounded-tl-none'
              }`}
            >
              {/* Tool Execution Badges */}
              {m.tool_invocations && m.tool_invocations.length > 0 && (
                <div className="space-y-1.5 pb-2.5 border-b border-[#E6EAF0]">
                  {m.tool_invocations.map((t, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-1.5 text-[11px] font-semibold text-[#16865C] bg-[#E5F7EF] px-2.5 py-1 rounded-lg border border-[#16865C]/15"
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
                <div className="pt-2.5 border-t border-[#E6EAF0] space-y-1.5">
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#697386]">
                    <BookOpen className="w-3.5 h-3.5 text-[#6478E8]" />
                    <span>Statutory Citations:</span>
                  </div>
                  <ul className="list-disc list-inside text-[11px] text-[#697386] space-y-0.5">
                    {m.citations.map((cite, idx) => (
                      <li key={idx}>{cite}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div
                className={`text-[10px] text-right ${
                  m.sender === 'user' ? 'text-white/80' : 'text-[#697386]'
                }`}
              >
                {m.timestamp}
              </div>
            </div>

            {m.sender === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-[#EEF0FF] border border-[#6478E8]/30 flex items-center justify-center text-[#6478E8] shrink-0 mt-0.5 font-bold text-xs">
                <UserIcon className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#EEF0FF] border border-[#6478E8]/20 flex items-center justify-center text-[#6478E8] shrink-0">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="rounded-2xl rounded-tl-none p-3.5 bg-white border border-[#E6EAF0] text-xs text-[#697386] flex items-center gap-2 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#6478E8] animate-pulse" />
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
            className="text-[11px] whitespace-nowrap px-3 py-1.5 rounded-xl bg-white hover:bg-[#F6F8FC] border border-[#E6EAF0] text-[#697386] hover:text-[#172033] shadow-sm transition-colors shrink-0"
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
          className="flex-1 bg-white border border-[#E6EAF0] rounded-2xl px-4 py-3 text-xs sm:text-sm text-[#172033] placeholder-[#697386]/60 shadow-sm focus:outline-none focus:border-[#6478E8] focus:ring-2 focus:ring-[#6478E8]/10 transition-all"
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
