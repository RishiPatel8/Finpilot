import React, { useState, useEffect, useRef } from 'react';
import {
  HelpCircle,
  X,
  BookOpen,
  Sparkles,
  AlertCircle,
  Calculator,
  IndianRupee,
  ShieldCheck,
  ChevronRight,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import {
  FINANCIAL_TERMS_REGISTRY,
  FinancialTermExplanation,
} from '../content/financialTerms';

export interface KnowMoreProps {
  /** The registry key of the term to explain */
  termId: string;
  /** Optional custom button label (default: 'Know More' or icon) */
  label?: string;
  /** Presentation style of the trigger button */
  variant?: 'icon' | 'badge' | 'button' | 'link';
  /** Optional custom size */
  size?: 'xs' | 'sm' | 'md';
  /** Optional custom class for the trigger */
  className?: string;
  /** Optional live contextual dynamic details to display in the modal */
  contextualValue?: {
    label: string;
    value: string | number;
    isEstimate?: boolean;
  };
}

export const KnowMore: React.FC<KnowMoreProps> = ({
  termId,
  label,
  variant = 'icon',
  size = 'sm',
  className = '',
  contextualValue,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const term: FinancialTermExplanation | undefined = FINANCIAL_TERMS_REGISTRY[termId];
  const modalRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Close on Escape key press & handle focus
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!term) {
    console.warn(`KnowMore: Term ID "${termId}" not found in FINANCIAL_TERMS_REGISTRY.`);
    return null;
  }

  const renderTrigger = () => {
    switch (variant) {
      case 'badge':
        return (
          <button
            ref={triggerRef}
            type="button"
            onClick={() => setIsOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={isOpen}
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-[rgba(212,175,55,0.12)] text-[#F5DE88] border border-[rgba(212,175,55,0.28)] hover:bg-[rgba(212,175,55,0.2)] transition-all ${className}`}
            title={`Know More about ${term.title}`}
          >
            <HelpCircle className="w-3 h-3 shrink-0 text-[#D4AF37]" />
            <span>{label || 'Know More'}</span>
          </button>
        );

      case 'button':
        return (
          <button
            ref={triggerRef}
            type="button"
            onClick={() => setIsOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={isOpen}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-semibold bg-white/[0.04] border border-[rgba(212,175,55,0.25)] text-[#F3F4F6] hover:text-[#F5DE88] hover:border-[#D4AF37] shadow-sm transition-all ${className}`}
          >
            <BookOpen className="w-3.5 h-3.5 text-[#D4AF37]" />
            <span>{label || 'Know More'}</span>
          </button>
        );

      case 'link':
        return (
          <button
            ref={triggerRef}
            type="button"
            onClick={() => setIsOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={isOpen}
            className={`inline-flex items-center gap-1 text-xs font-medium text-[#D4AF37] hover:text-[#F5DE88] hover:underline focus:outline-none transition-colors ${className}`}
          >
            <span>{label || 'Know More'}</span>
            <HelpCircle className="w-3 h-3 shrink-0" />
          </button>
        );

      case 'icon':
      default:
        return (
          <button
            ref={triggerRef}
            type="button"
            onClick={() => setIsOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={isOpen}
            aria-label={`Know more about ${term.title}`}
            className={`inline-flex items-center justify-center p-1 rounded-lg text-[#D4AF37] hover:text-[#F5DE88] hover:bg-white/[0.06] transition-colors focus:outline-none focus:ring-2 focus:ring-[#D4AF37]/30 ${className}`}
            title={`Know More: ${term.title}`}
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </button>
        );
    }
  };

  return (
    <>
      {renderTrigger()}

      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby={`knowmore-title-${term.id}`}
        >
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity"
            onClick={() => setIsOpen(false)}
          />

          {/* Modal Container */}
          <div
            ref={modalRef}
            className="relative w-full max-w-xl max-h-[85vh] bg-[#0D111A] border border-[rgba(212,175,55,0.3)] rounded-2xl shadow-[0_25px_50px_rgba(0,0,0,0.85)] flex flex-col z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150 text-[#F3F4F6]"
          >
            {/* Header */}
            <div className="px-6 py-4 border-b border-white/10 flex items-start justify-between bg-[#111622] shrink-0">
              <div className="space-y-1 pr-4">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded-lg bg-[rgba(212,175,55,0.15)] text-[#F5DE88]">
                    <BookOpen className="w-4 h-4" />
                  </span>
                  <span className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded bg-white/[0.04] border border-[rgba(212,175,55,0.2)] text-[#D4AF37]">
                    FinPilot Knowledge
                  </span>
                </div>
                <h2
                  id={`knowmore-title-${term.id}`}
                  className="text-lg font-bold text-[#F3F4F6]"
                >
                  {term.title}
                </h2>
                {term.technicalTerm && (
                  <p className="text-xs text-[#9CA3AF]">
                    Also known as: <span className="font-mono text-[#D4AF37]">{term.technicalTerm}</span>
                  </p>
                )}
              </div>

              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-xl text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-white/[0.06] transition-colors focus:outline-none focus:ring-2 focus:ring-[#D4AF37]/30"
                aria-label="Close dialog"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scrollable Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs text-[#F3F4F6] leading-relaxed">
              {/* Optional Contextual Display Value */}
              {contextualValue && (
                <div className="p-3.5 rounded-xl bg-white/[0.03] border border-[rgba(212,175,55,0.2)] flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-semibold text-[#9CA3AF]">
                      {contextualValue.label}
                    </span>
                    <p className="text-base font-bold text-[#F5DE88] mt-0.5 tabular-nums">
                      {contextualValue.value}
                    </p>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      contextualValue.isEstimate
                        ? 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
                        : 'bg-emerald-400/15 text-emerald-300 border border-emerald-400/30'
                    }`}
                  >
                    {contextualValue.isEstimate ? 'Model Estimate' : 'Verified Data'}
                  </span>
                </div>
              )}

              {/* 1. What It Means */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-sm font-bold text-[#F3F4F6]">
                  <Sparkles className="w-4 h-4 text-[#D4AF37]" />
                  <h3>1. What It Means</h3>
                </div>
                <p className="pl-5 text-[#9CA3AF] text-xs leading-relaxed">
                  {term.simpleMeaning}
                </p>
              </div>

              {/* 2. Why It Matters */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-sm font-bold text-[#F3F4F6]">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <h3>2. Why It Matters</h3>
                </div>
                <p className="pl-5 text-[#9CA3AF] text-xs leading-relaxed">
                  {term.whyItMatters}
                </p>
              </div>

              {/* 3. Simple Real-Life Example (Using Indian Rupees) */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-sm font-bold text-[#F3F4F6]">
                  <IndianRupee className="w-4 h-4 text-[#F5DE88]" />
                  <h3>3. Simple Real-Life Example</h3>
                </div>
                <div className="ml-5 p-3.5 rounded-xl bg-white/[0.03] border border-[rgba(212,175,55,0.2)] text-[#F3F4F6] text-xs leading-relaxed">
                  {term.example}
                </div>
              </div>

              {/* 4. How FinPilot Calculates or Uses It */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-sm font-bold text-[#F3F4F6]">
                  <Calculator className="w-4 h-4 text-[#38BDF8]" />
                  <h3>4. How FinPilot Calculates It</h3>
                </div>
                <div className="ml-5 p-3.5 rounded-xl bg-white/[0.03] border border-white/10 text-[#9CA3AF] text-xs leading-relaxed space-y-1">
                  <p>{term.calculation}</p>
                </div>
              </div>

              {/* 5. Important Limitations & Assumptions */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-sm font-bold text-[#F3F4F6]">
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                  <h3>5. Important Limitations & Assumptions</h3>
                </div>
                <div className="ml-5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-[#9CA3AF] text-[11px] leading-relaxed">
                  {term.limitations}
                </div>
              </div>

              {term.actionableTip && (
                <div className="p-3 rounded-xl bg-[rgba(212,175,55,0.1)] border border-[rgba(212,175,55,0.25)] flex items-start gap-2.5 text-xs text-[#F3F4F6]">
                  <Sparkles className="w-4 h-4 text-[#6478E8] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-[#6478E8]">Actionable Tip: </span>
                    <span>{term.actionableTip}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-[#E6EAF0] bg-[#F6F8FC] flex items-center justify-between shrink-0">
              <span className="text-[11px] text-[#8896A6]">
                Educational guide · FinPilot Zero Mock Data Engine
              </span>
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-1.5 bg-[#172033] hover:bg-[#2C384E] text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
