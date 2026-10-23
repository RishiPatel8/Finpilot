import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export type BadgeVariant = 'mint' | 'lavender' | 'blue' | 'peach' | 'danger' | 'neutral';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
  icon?: React.ReactNode;
  title?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'sm',
  className = '',
  icon,
  title,
}) => {

  const variantStyles: Record<BadgeVariant, string> = {
    mint: 'bg-[#E5F7EF] text-[#16865C] border-[#16865C]/15',
    lavender: 'bg-[#EEF0FF] text-[#6478E8] border-[#6478E8]/20',
    blue: 'bg-[#E8F2FF] text-[#2B6CB0] border-[#2B6CB0]/20',
    peach: 'bg-[#FFF0E5] text-[#B7791F] border-[#B7791F]/20',
    danger: 'bg-[#FDF2F4] text-[#D9485F] border-[#D9485F]/20',
    neutral: 'bg-[#F1F4F9] text-[#697386] border-[#E6EAF0]',
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-semibold',
  };

  return (
    <span
      title={title}
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1 rounded-lg border tracking-wide transition-colors',
          variantStyles[variant],
          sizeStyles[size],
          className
        )
      )}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};
