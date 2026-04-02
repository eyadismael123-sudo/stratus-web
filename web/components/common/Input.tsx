"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  /** Icon shown on the left inside the input */
  leftIcon?: React.ReactNode;
  /** Icon or element on the right inside the input */
  rightElement?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    { label, error, hint, leftIcon, rightElement, className, id, ...props },
    ref
  ) => {
    const inputId = id ?? React.useId();

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-[#3A3A3C]"
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <span className="absolute left-3 text-[#A1A1A6] pointer-events-none">
              {leftIcon}
            </span>
          )}

          <input
            ref={ref}
            id={inputId}
            className={cn(
              "h-10 w-full rounded-lg border bg-white px-3 text-sm text-[#3A3A3C]",
              "placeholder:text-[#A1A1A6]",
              "transition-colors duration-150",
              "focus:outline-none focus:ring-2 focus:ring-[#FFD60A] focus:border-transparent",
              "disabled:bg-[#F2F2F4] disabled:text-[#A1A1A6] disabled:cursor-not-allowed",
              error
                ? "border-[#FF3B30] focus:ring-[#FF3B30]"
                : "border-[#D2D2D7] hover:border-[#A1A1A6]",
              leftIcon && "pl-9",
              rightElement && "pr-9",
              className
            )}
            aria-invalid={!!error}
            aria-describedby={
              error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined
            }
            {...props}
          />

          {rightElement && (
            <span className="absolute right-3 text-[#A1A1A6]">
              {rightElement}
            </span>
          )}
        </div>

        {error && (
          <p id={`${inputId}-error`} className="text-xs text-[#FF3B30]">
            {error}
          </p>
        )}
        {!error && hint && (
          <p id={`${inputId}-hint`} className="text-xs text-[#A1A1A6]">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
