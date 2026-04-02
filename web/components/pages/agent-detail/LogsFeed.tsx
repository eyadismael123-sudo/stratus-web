"use client";

import { useState } from "react";
import type { AgentLog, LogStatus } from "@/types";

type FilterType = "all" | "success" | "error" | "running";

const STATUS_ICON: Record<LogStatus, { emoji: string; bg: string }> = {
  success: { emoji: "✅", bg: "rgba(52,199,89,0.1)" },
  error: { emoji: "❌", bg: "rgba(255,59,48,0.1)" },
  running: { emoji: "🔍", bg: "rgba(0,122,255,0.08)" },
  timeout: { emoji: "⏱", bg: "rgba(255,214,10,0.12)" },
};

const BORDER_COLORS: Record<LogStatus, string> = {
  success: "#34C759",
  error: "#FF3B30",
  running: "#007AFF",
  timeout: "#FFD60A",
};

function groupByDay(logs: AgentLog[]): Map<string, AgentLog[]> {
  const groups = new Map<string, AgentLog[]>();
  for (const log of logs) {
    const date = new Date(log.started_at);
    const key = date.toLocaleDateString("en-AE", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
    const existing = groups.get(key) ?? [];
    groups.set(key, [...existing, log]);
  }
  return groups;
}

function formatTime(isoString: string) {
  return new Date(isoString).toLocaleTimeString("en-AE", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(ms: number | null): string {
  if (!ms) return "";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

interface LogEntryProps {
  log: AgentLog;
}

function LogEntry({ log }: LogEntryProps) {
  const [expanded, setExpanded] = useState(false);
  const icon = STATUS_ICON[log.status] ?? STATUS_ICON.running;
  const borderColor = BORDER_COLORS[log.status] ?? BORDER_COLORS.running;

  const title =
    log.status === "success"
      ? log.trigger_type === "manual"
        ? "Manual Run Completed"
        : "Scheduled Run Completed"
      : log.status === "error"
      ? "Run Failed"
      : log.status === "running"
      ? "Running"
      : "Run Timed Out";

  const outputKeys = log.output_data ? Object.keys(log.output_data) : [];
  const hasDetails = !!(log.error_message || (log.output_data && outputKeys.length > 0));

  return (
    <div className="flex gap-3 py-3.5 border-b border-black/[0.04] last:border-b-0 min-w-0">
      {/* Icon */}
      <div
        className="w-8 h-8 rounded-[8px] flex items-center justify-center text-[14px] flex-shrink-0 mt-0.5"
        style={{ background: icon.bg }}
      >
        {icon.emoji}
      </div>

      {/* Body */}
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-semibold text-[#3A3A3C] mb-0.5">{title}</div>
        <div className="text-[11px] text-[#8E8E93] mb-1.5">
          {log.trigger_type === "manual" ? "Triggered manually" : "Scheduled run"}
          {log.duration_ms ? ` · ${formatDuration(log.duration_ms)}` : ""}
        </div>

        {/* Error message */}
        {log.error_message && (
          <div
            className="rounded-[8px] px-3 py-2.5 text-[12px] text-[#3A3A3C] leading-relaxed font-mono border-l-[3px] bg-[#F5F5F7] overflow-wrap-break-word"
            style={{ borderLeftColor: borderColor }}
          >
            {log.error_message}
          </div>
        )}

        {/* Output preview */}
        {log.output_data && !log.error_message && (
          <div
            className="rounded-[8px] px-3 py-2.5 text-[12px] text-[#3A3A3C] leading-relaxed border-l-[3px] bg-[#F5F5F7]"
            style={{ borderLeftColor: borderColor }}
          >
            {expanded ? (
              <div className="flex flex-col gap-1">
                {outputKeys.map((key) => (
                  <div key={key}>
                    <span className="font-semibold text-[#6A6A6E]">{key}:</span>{" "}
                    <span className="overflow-wrap-break-word">
                      {typeof log.output_data![key] === "string"
                        ? (log.output_data![key] as string).slice(0, 120)
                        : JSON.stringify(log.output_data![key])}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-[#6A6A6E]">
                {outputKeys.length} output field{outputKeys.length !== 1 ? "s" : ""} —{" "}
                {outputKeys.slice(0, 3).join(", ")}
                {outputKeys.length > 3 ? "..." : ""}
              </span>
            )}
          </div>
        )}

        {hasDetails && (
          <button
            onClick={() => setExpanded((prev) => !prev)}
            className="text-[11px] text-[#007AFF] mt-1.5 cursor-pointer bg-none border-none p-0 font-medium"
          >
            {expanded ? "Collapse ↑" : "Expand details →"}
          </button>
        )}
      </div>

      {/* Time */}
      <div className="text-[11px] text-[#8E8E93] flex-shrink-0 mt-1.5 hidden sm:block">
        {formatTime(log.started_at)}
      </div>
    </div>
  );
}

interface LogsFeedProps {
  logs: AgentLog[];
}

export function LogsFeed({ logs }: LogsFeedProps) {
  const [filter, setFilter] = useState<FilterType>("all");

  const filtered =
    filter === "all" ? logs : logs.filter((l) => l.status === filter);

  const grouped = groupByDay(filtered);

  const FILTERS: { key: FilterType; label: string }[] = [
    { key: "all", label: "All" },
    { key: "success", label: "Success" },
    { key: "error", label: "Errors" },
    { key: "running", label: "Running" },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Header + filter pills */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[16px] font-bold text-[#3A3A3C]">Activity & Logs</h2>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {FILTERS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className="px-3 py-1 rounded-full text-[12px] font-medium border transition-all duration-150 cursor-pointer"
              style={
                filter === key
                  ? { background: "#3A3A3C", color: "#FFFFFF", borderColor: "#3A3A3C" }
                  : { background: "white", color: "#8E8E93", borderColor: "#D2D2D7" }
              }
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Log timeline */}
      {filtered.length === 0 ? (
        <p className="text-[14px] text-[#8E8E93] py-8 text-center">No logs for this filter.</p>
      ) : (
        <div className="flex flex-col gap-6">
          {Array.from(grouped.entries()).map(([day, dayLogs]) => (
            <div key={day}>
              <div className="text-[11px] font-semibold uppercase tracking-[0.5px] text-[#8E8E93] pb-3 border-b border-black/[0.06] mb-0">
                {day}
              </div>
              <div>
                {dayLogs.map((log) => (
                  <LogEntry key={log.id} log={log} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
