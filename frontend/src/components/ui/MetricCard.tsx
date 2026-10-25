import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface MetricCardProps {
  label: React.ReactNode;
  value: string | number;
  subtext?: React.ReactNode;
  icon?: React.ReactNode;
  iconTone?: 'lavender' | 'mint' | 'blue' | 'peach' | 'danger';
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  progress?: {
    current: number;
    target: number;
    color?: string;
  };
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon,
  iconTone = 'lavender',
  trend,
  progress,
  className = '',
}) => {
  const iconToneStyles = {
    lavender: 'bg-[#D4AF37]/15 text-[#F5DE88] border border-[#D4AF37]/20 shadow-sm shadow-[#D4AF37]/10',
    mint: 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/20',
    blue: 'bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/20',
    peach: 'bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/20',
    danger: 'bg-[#F43F5E]/15 text-[#F43F5E] border border-[#F43F5E]/20',
  };

  return (
    <div
      className={twMerge(
        clsx(
          'bg-[#111622]/90 backdrop-blur-md border border-[rgba(212,175,55,0.15)] rounded-2xl p-5 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5),0_0_0_1px_rgba(255,255,255,0.04)] flex flex-col justify-between transition-all duration-200 hover:border-[#D4AF37]/35 hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.7),0_0_20px_rgba(212,175,55,0.12)] hover:-translate-y-0.5',
          className
        )
      )}
    >
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-[#9CA3AF] tracking-wide">{label}</span>
          {icon && (
            <div className={clsx('w-8 h-8 rounded-xl flex items-center justify-center transition-colors', iconToneStyles[iconTone])}>
              {icon}
            </div>
          )}
        </div>

        <div className="flex items-baseline gap-2">
          <p className="text-2xl lg:text-[26px] font-extrabold text-[#F3F4F6] tracking-tight tabular-nums">
            {value}
          </p>
          {trend && (
            <span
              className={clsx(
                'text-[11px] font-semibold px-2 py-0.5 rounded-md border',
                trend.isPositive
                  ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30'
                  : 'bg-[#F43F5E]/15 text-[#F43F5E] border-[#F43F5E]/30'
              )}
            >
              {trend.value}
            </span>
          )}
        </div>
      </div>

      {progress && (
        <div className="mt-3.5 space-y-1.5">
          <div className="w-full bg-white/[0.08] h-2 rounded-full overflow-hidden">
            <div
              className={clsx('h-full rounded-full transition-all duration-500', progress.color || 'bg-gradient-to-r from-[#D4AF37] to-[#F5DE88]')}
              style={{ width: `${Math.min(100, Math.max(0, (progress.current / progress.target) * 100))}%` }}
            />
          </div>
        </div>
      )}

      {subtext && (
        <div className="mt-3.5 pt-3 border-t border-white/[0.06] text-xs text-[#9CA3AF] flex items-center justify-between">
          {subtext}
        </div>
      )}
    </div>
  );
};
