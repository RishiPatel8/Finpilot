import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export type ButtonVariant = 'primary' | 'secondary' | 'soft' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  loading = false,
  className = '',
  disabled,
  ...props
}) => {
  const variantStyles: Record<ButtonVariant, string> = {
    primary:
      'bg-[#6478E8] hover:bg-[#5365D6] text-white shadow-sm shadow-[#6478E8]/20 focus-visible:ring-2 focus-visible:ring-[#6478E8]/50 active:scale-[0.98]',
    secondary:
      'bg-white hover:bg-[#F6F8FC] text-[#172033] border border-[#E6EAF0] shadow-[0_1px_2px_rgba(0,0,0,0.03)] focus-visible:ring-2 focus-visible:ring-[#E6EAF0]',
    soft:
      'bg-[#EEF0FF] hover:bg-[#E2E6FF] text-[#6478E8] font-semibold focus-visible:ring-2 focus-visible:ring-[#6478E8]/30',
    outline:
      'bg-transparent hover:bg-[#F6F8FC] text-[#172033] border border-[#E6EAF0]',
    ghost:
      'bg-transparent hover:bg-[#F1F4F9] text-[#697386] hover:text-[#172033]',
    danger:
      'bg-[#D9485F] hover:bg-[#C23B51] text-white shadow-sm shadow-[#D9485F]/20',
  };

  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'text-xs px-3 py-1.5 rounded-xl gap-1.5 font-medium',
    md: 'text-xs sm:text-sm px-4 py-2 rounded-xl gap-2 font-semibold',
    lg: 'text-sm px-5 py-2.5 rounded-xl gap-2 font-semibold',
  };

  return (
    <button
      disabled={disabled || loading}
      className={twMerge(
        clsx(
          'inline-flex items-center justify-center transition-all duration-150 disabled:opacity-50 disabled:pointer-events-none select-none outline-none',
          variantStyles[variant],
          sizeStyles[size],
          className
        )
      )}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin shrink-0" />
      ) : (
        icon && iconPosition === 'left' && <span className="shrink-0">{icon}</span>
      )}
      <span>{children}</span>
      {!loading && icon && iconPosition === 'right' && (
        <span className="shrink-0">{icon}</span>
      )}
    </button>
  );
};
