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
    mint: 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30',
    lavender: 'bg-[#D4AF37]/15 text-[#F5DE88] border-[#D4AF37]/30',
    blue: 'bg-[#38BDF8]/15 text-[#38BDF8] border-[#38BDF8]/30',
    peach: 'bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30',
    danger: 'bg-[#F43F5E]/15 text-[#F43F5E] border-[#F43F5E]/30',
    neutral: 'bg-white/[0.06] text-[#9CA3AF] border-white/10',
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
