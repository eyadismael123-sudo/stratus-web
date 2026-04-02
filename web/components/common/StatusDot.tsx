import * as React from "react";
import { cn } from "@/lib/utils";
import type { AgentStatus } from "@/types";

export interface StatusDotProps {
  status: AgentStatus;
  /** Show label text next to the dot */
  showLabel?: boolean;
  className?: string;
}

/** Maps agent status to colour class and label */
const STATUS_MAP: Record<AgentStatus, { dotClass: string; label: string }> = {
  // Yellow (#FFD60A) — the ONE approved use per yellow rule
  active:   { dotClass: "bg-[#FFD60A]", label: "Online" },
  // All other statuses use semantic colours, never yellow
  inactive: { dotClass: "bg-[#A1A1A6]", label: "Offline" },
  paused:   { dotClass: "bg-[#FF9500]", label: "Paused" },
  error:    { dotClass: "bg-[#FF3B30]", label: "Error" },
};

export function StatusDot({ status, showLabel = false, className }: StatusDotProps) {
  const { dotClass, label } = STATUS_MAP[status];

  return (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      <span
        className={cn(
          "block w-2 h-2 rounded-full shrink-0",
          dotClass,
          status === "active" && "animate-pulse"
        )}
        aria-label={label}
      />
      {showLabel && (
        <span className="text-xs font-medium text-[#6A6A6E]">{label}</span>
      )}
    </span>
  );
}
