import * as React from "react";
import { cn } from "@/lib/utils";

export type BadgeVariant =
  | "default"
  | "success"
  | "error"
  | "warning"
  | "info"
  | "outline";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantClasses: Record<BadgeVariant, string> = {
  default:  "bg-[#F2F2F4] text-[#3A3A3C]",
  success:  "bg-[#E8F9EE] text-[#1a7a35]",
  error:    "bg-[#FFEDEC] text-[#c0281e]",
  warning:  "bg-[#FFF4E5] text-[#a85c00]",
  info:     "bg-[#E5F2FF] text-[#0058b3]",
  outline:  "bg-transparent text-[#6A6A6E] border border-[#D2D2D7]",
};

export function Badge({
  variant = "default",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
