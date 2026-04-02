"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  /** Full-width block button */
  block?: boolean;
  children: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  /** Graphite fill — nav CTA, hire CTA. NOT yellow. */
  primary:
    "bg-[#3A3A3C] text-white hover:bg-[#2a2a2c] active:bg-[#1a1a1c] disabled:bg-[#D2D2D7] disabled:text-[#A1A1A6]",
  secondary:
    "bg-white text-[#3A3A3C] border border-[#D2D2D7] hover:border-[#3A3A3C] hover:bg-[#F2F2F4] active:bg-[#E5E5EA] disabled:bg-[#F2F2F4] disabled:text-[#A1A1A6]",
  ghost:
    "bg-transparent text-[#3A3A3C] hover:bg-[#F2F2F4] active:bg-[#E5E5EA] disabled:text-[#A1A1A6]",
  danger:
    "bg-[#FF3B30] text-white hover:bg-[#e02e23] active:bg-[#c02016] disabled:bg-[#D2D2D7] disabled:text-[#A1A1A6]",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm rounded-lg gap-1.5",
  md: "h-10 px-4 text-sm rounded-lg gap-2",
  lg: "h-12 px-6 text-base rounded-xl gap-2",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      block = false,
      className,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          // Base
          "inline-flex items-center justify-center font-medium",
          "transition-colors duration-150 cursor-pointer select-none",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:pointer-events-none",
          variantClasses[variant],
          sizeClasses[size],
          block && "w-full",
          className
        )}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin shrink-0"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
          >
            <circle
              cx="8"
              cy="8"
              r="6"
              stroke="currentColor"
              strokeWidth="2"
              strokeDasharray="28"
              strokeDashoffset="10"
              strokeLinecap="round"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
