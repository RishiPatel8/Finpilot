import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  interactive?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  interactive = false,
  padding = 'md',
  ...props
}) => {
  const paddingStyles = {
    none: '',
    sm: 'p-3.5',
    md: 'p-5 sm:p-6',
    lg: 'p-6 sm:p-8',
  };

  // Sanitize any legacy light mode classes passed in className so cards always stay luxury dark
  const sanitizedClassName = className
    .replace(/\bbg-white\b/g, '')
    .replace(/\bbg-\[#F6F8FC\]\b/g, '')
    .replace(/\bbg-\[#F8FAFC\]\b/g, '')
    .replace(/\bbg-\[#EEF0FF\]\b/g, '')
    .replace(/\bborder-\[#E6EAF0\]\b/g, '')
    .replace(/\btext-\[#172033\]\b/g, 'text-[#F3F4F6]')
    .replace(/\btext-\[#697386\]\b/g, 'text-[#9CA3AF]');

  return (
    <div
      className={twMerge(
        clsx(
          'bg-[#111622]/95 backdrop-blur-md border border-[rgba(212,175,55,0.18)] rounded-2xl shadow-[0_4px_25px_-2px_rgba(0,0,0,0.6),0_0_0_1px_rgba(255,255,255,0.04)] text-[#F3F4F6]',
          interactive && 'transition-all duration-200 hover:border-[#D4AF37]/50 hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.8),0_0_20px_rgba(212,175,55,0.2)] hover:-translate-y-0.5 cursor-pointer',
          paddingStyles[padding],
          sanitizedClassName
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};
