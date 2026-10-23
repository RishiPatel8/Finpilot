import React, { useState, useRef, useEffect } from 'react';
import {
  BotMessageSquare,
  Send,
  Sparkles,
  BookOpen,
  Wrench,
  User as UserIcon,
  ShieldCheck
} from 'lucide-react';
import { apiRequest } from '../../services/api';
import { ChatMessage } from '../../types';

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
        "SEBI Mutual Fund Regulations (Liquid Scheme Norms)"
      ]
    }
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const samplePrompts = [
    "I earn ₹60,000 per month, spend ₹35,000 and have ₹2 lakh in savings. I want to buy a car in 18 months. What are my options?",
    "Compare tax for 15 LPA salary in new vs old regime",
    "Should I invest 3 lakh in liquid fund or bond for 6 months?",
    "How much to save per month for 20 lakh house downpayment in 3 years?",
    "What is the standard deduction in AY 2025-26 under Finance Act 2024?"
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
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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
        tool_invocations: res.tool_invocations
      };

      setMessages((prev) => [...prev, asstMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        content: `I encountered an issue processing your query: ${err.message || 'Service unavailable'}. Please verify your connection.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 flex flex-col h-[calc(100vh-140px)]">
      {/* Top Header */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/40 border border-slate-800 shrink-0">
        <div className="flex items-center gap-2">
          <BotMessageSquare className="w-5 h-5 text-emerald-400" />
          <h1 className="text-xl font-extrabold text-slate-100">Conversational Financial Assistant</h1>
          <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            Grounded & Deterministic
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Orchestrates calculation tools and retrieves official tax & SEBI statutory citations.
        </p>
      </div>

      {/* Chat Messages Body */}
      <div className="flex-1 overflow-y-auto p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.sender === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-2xl p-4 text-xs space-y-3 ${
                m.sender === 'user'
                  ? 'bg-emerald-600 text-white rounded-tr-none font-medium'
                  : 'bg-slate-950/90 border border-slate-800 text-slate-200 rounded-tl-none'
              }`}
            >
              {/* Tool Execution Badge */}
              {m.tool_invocations && m.tool_invocations.length > 0 && (
                <div className="space-y-1 pb-2 border-b border-slate-800/80">
                  {m.tool_invocations.map((t, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-[10px] text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20 font-semibold">
                      <Wrench className="w-3 h-3" />
                      <span>{t.summary}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Message Content */}
              <div className="leading-relaxed whitespace-pre-wrap font-sans">
                {m.content}
              </div>

              {/* Citations Box */}
              {m.citations && m.citations.length > 0 && (
                <div className="pt-2 border-t border-slate-800/80 space-y-1">
                  <div className="flex items-center gap-1 text-[10px] font-bold text-slate-400">
                    <BookOpen className="w-3 h-3 text-emerald-400" />
                    <span>Statutory Sources & Citations:</span>
                  </div>
                  <ul className="list-disc list-inside text-[10px] text-slate-400 space-y-0.5">
                    {m.citations.map((cite, idx) => (
                      <li key={idx}>{cite}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="text-[9px] text-right text-slate-400 opacity-60">
                {m.timestamp}
              </div>
            </div>

            {m.sender === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                <UserIcon className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="rounded-2xl rounded-tl-none p-3.5 bg-slate-950/90 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Orchestrating financial engines and checking citations...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Chips */}
      <div className="flex items-center gap-2 overflow-x-auto py-1 shrink-0 scrollbar-none">
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="text-[11px] whitespace-nowrap px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-emerald-300 transition-colors shrink-0"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Field */}
      <div className="flex items-center gap-2 shrink-0">
        <input
          type="text"
          placeholder="Ask any tax, investment, or goal question in plain English (e.g. 15 LPA salary tax)..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSend();
          }}
          className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="p-3 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 rounded-2xl transition-all shadow-md shadow-emerald-500/20"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};
