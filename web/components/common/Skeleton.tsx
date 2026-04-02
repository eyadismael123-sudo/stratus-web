import * as React from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Override default shimmer with a static grey block */
  noAnimation?: boolean;
}

export function Skeleton({ className, noAnimation = false, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-lg bg-[#F2F2F4]",
        !noAnimation && "animate-shimmer bg-gradient-to-r from-[#F2F2F4] via-[#E5E5EA] to-[#F2F2F4] bg-[length:400%_100%]",
        className
      )}
      aria-hidden="true"
      {...props}
    />
  );
}

/** Pre-built skeleton for an agent card */
export function AgentCardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-[#E5E5EA] p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <Skeleton className="w-10 h-10 rounded-xl shrink-0" />
        <Skeleton className="w-12 h-5 rounded-full" />
      </div>
      <div className="flex flex-col gap-2">
        <Skeleton className="w-3/4 h-4" />
        <Skeleton className="w-1/2 h-3" />
      </div>
      <div className="flex gap-2 mt-1">
        <Skeleton className="w-16 h-5 rounded-full" />
        <Skeleton className="w-20 h-5 rounded-full" />
      </div>
      <Skeleton className="w-full h-9 rounded-lg mt-1" />
    </div>
  );
}

/** Pre-built skeleton for a log row */
export function LogRowSkeleton() {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-[#F2F2F4]">
      <Skeleton className="w-5 h-5 rounded-full shrink-0" />
      <div className="flex-1 flex flex-col gap-1.5">
        <Skeleton className="w-2/3 h-3" />
        <Skeleton className="w-1/3 h-3" />
      </div>
      <Skeleton className="w-14 h-4 rounded-full shrink-0" />
    </div>
  );
}
