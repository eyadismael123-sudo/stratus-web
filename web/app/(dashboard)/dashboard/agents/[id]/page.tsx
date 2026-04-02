import Link from "next/link";
import { notFound } from "next/navigation";
import {
  MOCK_USER_AGENTS,
  MOCK_AGENT_LOGS,
  MOCK_AGENT_SCHEDULE,
  MOCK_SCHEDULE_GRID,
} from "@/constants/mock-data";
import { AgentInfo } from "@/components/pages/agent-detail/AgentInfo";
import { LogsFeed } from "@/components/pages/agent-detail/LogsFeed";
import { ScheduleGrid } from "@/components/pages/agent-detail/ScheduleGrid";
import { AgentSettingsPanel } from "@/components/pages/agent-detail/AgentSettingsPanel";

interface AgentDetailPageProps {
  params: { id: string };
}

export default function AgentDetailPage({ params }: AgentDetailPageProps) {
  const agent = MOCK_USER_AGENTS.find((a) => a.id === params.id);

  if (!agent) {
    notFound();
  }

  const agentLogs = MOCK_AGENT_LOGS.filter((l) => l.user_agent_id === agent.id);
  const schedule = MOCK_AGENT_SCHEDULE;
  const gridData = MOCK_SCHEDULE_GRID;

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
          <button className="inline-flex items-center gap-1.5 px-4 h-9 rounded-[8px] text-[13px] font-semibold text-[#8E8E93] border border-[#D2D2D7] bg-transparent transition-all hover:bg-white hover:text-[#3A3A3C] cursor-pointer">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="7" cy="7" r="5.5"/>
              <path d="M7 4.5v2.5l1.5 1.5"/>
            </svg>
            View Schedule
          </button>
          <button className="inline-flex items-center gap-1.5 px-4 h-9 rounded-[8px] text-[13px] font-semibold text-[#FF3B30] border border-[rgba(255,59,48,0.3)] bg-transparent transition-all hover:bg-[#FFF1F0] cursor-pointer">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="7" cy="7" r="5.5"/>
              <path d="M9 5L5 9M5 5l4 4"/>
            </svg>
            Pause Agent
          </button>
          <button className="inline-flex items-center gap-1.5 px-4 h-9 rounded-[8px] text-[13px] font-semibold text-white bg-[#3A3A3C] transition-all hover:bg-[#2a2a2c] hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(0,0,0,0.2)] cursor-pointer">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M7 2v10M2 7h10"/>
            </svg>
            Run Now
          </button>
        </div>
      </div>

      {/* Mobile: Agent profile above feed */}
      <div className="lg:hidden border-b border-black/[0.06] px-4 py-6">
        <AgentInfo agent={agent} />
      </div>

      {/* 3-column content layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT: Agent profile (desktop only) */}
        <aside className="hidden lg:flex flex-col w-[260px] flex-shrink-0 border-r border-black/[0.06] px-6 py-7 overflow-y-auto">
          <AgentInfo agent={agent} />
        </aside>

        {/* CENTER: Activity feed */}
        <main className="flex-1 min-w-0 px-4 md:px-8 py-7 overflow-y-auto">
          <LogsFeed logs={agentLogs} />
        </main>

        {/* RIGHT: Schedule + Settings (xl only) */}
        <aside className="hidden xl:flex flex-col w-[280px] flex-shrink-0 border-l border-black/[0.06] px-6 py-7 overflow-y-auto gap-5">
          <ScheduleGrid schedule={schedule} gridData={gridData} />
          <AgentSettingsPanel agent={agent} />
        </aside>
      </div>
    </div>
  );
}
