import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface PageHeaderProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  icon,
  badge,
  actions,
  className = '',
}) => {
  return (
    <div
      className={twMerge(
        clsx(
          'bg-[#111622]/90 backdrop-blur-md border border-[rgba(212,175,55,0.18)] rounded-2xl p-5 sm:p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5),0_0_0_1px_rgba(255,255,255,0.04)] flex flex-col sm:flex-row sm:items-center justify-between gap-4',
          className
        )
      )}
    >
      <div className="space-y-1">
        <div className="flex flex-wrap items-center gap-2.5">
          {icon && (
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#D4AF37]/20 to-[#B89327]/10 text-[#F5DE88] border border-[#D4AF37]/30 flex items-center justify-center shrink-0 shadow-sm shadow-[#D4AF37]/15">
              {icon}
            </div>
          )}
          <h1 className="text-xl sm:text-2xl font-extrabold text-[#F3F4F6] tracking-tight">
            {title}
          </h1>
          {badge && <div className="shrink-0">{badge}</div>}
        </div>
        <p className="text-xs sm:text-sm text-[#9CA3AF] max-w-2xl leading-relaxed">
          {description}
        </p>
      </div>

      {actions && (
        <div className="flex flex-wrap items-center gap-2.5 shrink-0 self-start sm:self-center">
          {actions}
        </div>
      )}
    </div>
  );
};
