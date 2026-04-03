"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { notFound } from "next/navigation";
import { get, post, patch } from "@/lib/api";
import type { UserAgent, AgentLog, AgentSchedule } from "@/types";
import { AgentInfo } from "@/components/pages/agent-detail/AgentInfo";
import { LogsFeed } from "@/components/pages/agent-detail/LogsFeed";
import { ScheduleGrid } from "@/components/pages/agent-detail/ScheduleGrid";
import { AgentSettingsPanel } from "@/components/pages/agent-detail/AgentSettingsPanel";

function buildGridData(logs: AgentLog[]): Record<string, number[]> {
  const grid: Record<string, number[]> = {};
  for (const log of logs) {
    const date = log.started_at.slice(0, 10);
    if (!grid[date]) grid[date] = [];
    grid[date].push(1);
  }
  return grid;
}

export default function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [agent, setAgent] = useState<UserAgent | null>(null);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [schedule, setSchedule] = useState<AgentSchedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFoundError, setNotFoundError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [agentData, logsData] = await Promise.all([
          get<UserAgent>(`/agents/${id}`),
          get<AgentLog[]>(`/agents/${id}/logs`),
        ]);
        setAgent(agentData);
        setLogs(logsData);

        // Schedule is optional — 404 is fine
        try {
          const sched = await get<AgentSchedule>(`/agents/${id}/schedule`);
          setSchedule(sched);
        } catch {
          // no schedule set yet
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "";
        if (msg.includes("404") || msg.includes("not found")) {
          setNotFoundError(true);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  async function handleRunNow() {
    if (!agent) return;
    try {
      await post(`/agents/${id}/run`);
      // Refresh logs
      const logsData = await get<AgentLog[]>(`/agents/${id}/logs`);
      setLogs(logsData);
    } catch {
      // error logged
    }
  }

  async function handlePause() {
    if (!agent) return;
    const newStatus = agent.status === "paused" ? "active" : "paused";
    try {
      const updated = await patch<UserAgent>(`/agents/${id}`, { status: newStatus });
      setAgent(updated);
    } catch {
      // error logged
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen items-center justify-center">
        <div className="text-[14px] text-[#8E8E93]">Loading agent...</div>
      </div>
    );
  }

  if (notFoundError || !agent) {
    notFound();
  }

  const gridData = buildGridData(logs);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Sticky topbar / breadcrumb */}
      <div className="sticky top-0 z-50 bg-[rgba(245,245,247,0.85)] backdrop-blur-[12px] border-b border-black/[0.06] px-4 md:px-8 h-[60px] flex items-center gap-4">
        <nav className="flex items-center gap-2 text-[14px] text-[#8E8E93]">
          <Link
            href="/dashboard"
            className="hover:text-[#3A3A3C] transition-colors no-underline"
          >
            Your Team
          </Link>
          <span className="text-[#AEAEB2]">›</span>
          <span className="text-[#3A3A3C] font-semibold truncate max-w-[200px]">
            {agent.name}
          </span>
        </nav>

        <div className="ml-auto hidden md:flex items-center gap-2.5">
          <button
            onClick={handlePause}
            className="inline-flex items-center gap-1.5 px-4 h-9 rounded-[8px] text-[13px] font-semibold text-[#FF3B30] border border-[rgba(255,59,48,0.3)] bg-transparent transition-all hover:bg-[#FFF1F0] cursor-pointer"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="7" cy="7" r="5.5"/>
              <path d="M9 5L5 9M5 5l4 4"/>
            </svg>
            {agent.status === "paused" ? "Resume Agent" : "Pause Agent"}
          </button>
          <button
            onClick={handleRunNow}
            className="inline-flex items-center gap-1.5 px-4 h-9 rounded-[8px] text-[13px] font-semibold text-white bg-[#3A3A3C] transition-all hover:bg-[#2a2a2c] hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(0,0,0,0.2)] cursor-pointer"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M7 2v10M2 7h10"/>
            </svg>
            Run Now
          </button>
        </div>
      </div>

      {/* Mobile: Agent profile above feed */}
      <div className="lg:hidden border-b border-black/[0.06] px-4 py-6">
        <AgentInfo agent={agent} onPause={handlePause} onRunNow={handleRunNow} />
      </div>

      {/* 3-column content layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT: Agent profile (desktop only) */}
        <aside className="hidden lg:flex flex-col w-[260px] flex-shrink-0 border-r border-black/[0.06] px-6 py-7 overflow-y-auto">
          <AgentInfo agent={agent} onPause={handlePause} onRunNow={handleRunNow} />
        </aside>

        {/* CENTER: Activity feed */}
        <main className="flex-1 min-w-0 px-4 md:px-8 py-7 overflow-y-auto">
          <LogsFeed logs={logs} />
        </main>

        {/* RIGHT: Schedule + Settings (xl only) */}
        <aside className="hidden xl:flex flex-col w-[280px] flex-shrink-0 border-l border-black/[0.06] px-6 py-7 overflow-y-auto gap-5">
          {schedule && <ScheduleGrid schedule={schedule} gridData={gridData} />}
          <AgentSettingsPanel agent={agent} />
        </aside>
      </div>
    </div>
  );
}
