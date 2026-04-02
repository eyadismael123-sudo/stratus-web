import { AgentGrid } from "@/components/pages/dashboard/AgentGrid";
import { MOCK_USER_AGENTS } from "@/constants/mock-data";
import Link from "next/link";

export default function DashboardPage() {
  const activeCount = MOCK_USER_AGENTS.filter((a) => a.status === "active").length;

  return (
    <div className="px-6 md:px-8 py-7">
      {/* Page header */}
      <div className="flex items-center justify-between mb-7 flex-wrap gap-4">
        <div>
          <h1 className="text-[22px] font-black text-[#3A3A3C] tracking-[-0.03em]">
            Your Team
          </h1>
          <p className="text-[13px] text-[#8E8E93] mt-0.5">
            {activeCount} agent{activeCount !== 1 ? "s" : ""} running right now
          </p>
        </div>
        <Link
          href="/marketplace"
          className="inline-flex items-center gap-1.5 bg-[#3A3A3C] text-white text-[13px] font-bold rounded-[9px] px-4 py-2.5 no-underline transition-all hover:bg-[#2c2c2e] hover:shadow-[0_4px_12px_rgba(0,0,0,0.18)]"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Hire agent
        </Link>
      </div>

      <AgentGrid agents={MOCK_USER_AGENTS} />
    </div>
  );
}
