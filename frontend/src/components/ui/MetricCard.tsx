import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface MetricCardProps {
  label: string;
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
    lavender: 'bg-[#EEF0FF] text-[#6478E8]',
    mint: 'bg-[#E5F7EF] text-[#16865C]',
    blue: 'bg-[#E8F2FF] text-[#2B6CB0]',
    peach: 'bg-[#FFF0E5] text-[#B7791F]',
    danger: 'bg-[#FDF2F4] text-[#D9485F]',
  };

  return (
    <div
      className={twMerge(
        clsx(
          'bg-white border border-[#E6EAF0] rounded-2xl p-5 shadow-[0_1px_3px_rgba(0,0,0,0.03),0_1px_2px_rgba(0,0,0,0.02)] flex flex-col justify-between transition-all duration-200 hover:shadow-[0_4px_12px_rgba(23,32,51,0.04)]',
          className
        )
      )}
    >
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-[#697386] tracking-wide">{label}</span>
          {icon && (
            <div className={clsx('w-8 h-8 rounded-xl flex items-center justify-center transition-colors', iconToneStyles[iconTone])}>
              {icon}
            </div>
          )}
        </div>

        <div className="flex items-baseline gap-2">
          <p className="text-2xl lg:text-[26px] font-extrabold text-[#172033] tracking-tight tabular-nums">
            {value}
          </p>
          {trend && (
            <span
              className={clsx(
                'text-[11px] font-semibold px-1.5 py-0.5 rounded-md',
                trend.isPositive ? 'bg-[#E5F7EF] text-[#16865C]' : 'bg-[#FDF2F4] text-[#D9485F]'
              )}
            >
              {trend.value}
            </span>
          )}
        </div>
      </div>

      {progress && (
        <div className="mt-3.5 space-y-1.5">
          <div className="w-full bg-[#F1F4F9] h-2 rounded-full overflow-hidden">
            <div
              className={clsx('h-full rounded-full transition-all duration-500', progress.color || 'bg-[#6478E8]')}
              style={{ width: `${Math.min(100, Math.max(0, (progress.current / progress.target) * 100))}%` }}
            />
          </div>
        </div>
      )}

      {subtext && (
        <div className="mt-3.5 pt-3 border-t border-[#F1F4F9] text-xs text-[#697386] flex items-center justify-between">
          {subtext}
        </div>
      )}
    </div>
  );
};
