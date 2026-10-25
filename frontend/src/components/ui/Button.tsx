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
      'bg-gradient-to-r from-[#ECC856] via-[#D4AF37] to-[#B89327] hover:brightness-110 text-[#07090E] font-bold shadow-md shadow-[#D4AF37]/25 focus-visible:ring-2 focus-visible:ring-[#D4AF37]/50 active:scale-[0.98]',
    secondary:
      'bg-[#131824] hover:bg-[#1A2131] text-[#F3F4F6] border border-[#D4AF37]/25 shadow-sm shadow-black/40 focus-visible:ring-2 focus-visible:ring-[#D4AF37]/30',
    soft:
      'bg-[#D4AF37]/15 hover:bg-[#D4AF37]/25 text-[#F5DE88] border border-[#D4AF37]/25 font-semibold focus-visible:ring-2 focus-visible:ring-[#D4AF37]/30',
    outline:
      'bg-transparent hover:bg-[#D4AF37]/10 text-[#F3F4F6] border border-[#D4AF37]/35 hover:border-[#D4AF37]/60',
    ghost:
      'bg-transparent hover:bg-white/[0.06] text-[#9CA3AF] hover:text-[#F3F4F6]',
    danger:
      'bg-[#F43F5E] hover:bg-[#E11D48] text-white shadow-sm shadow-[#F43F5E]/20',
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
