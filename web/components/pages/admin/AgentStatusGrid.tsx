import type { UserAgent } from "@/types";
import { StatusDot } from "@/components/common/StatusDot";

function formatRelativeTime(iso: string | null): string {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const PLATFORM_LABEL: Record<string, string> = {
  linkedin: "LinkedIn",
  telegram: "Telegram",
  whatsapp: "WhatsApp",
  email: "Email",
};

const STATUS_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  active: { bg: "rgba(52,199,89,0.1)", color: "#1a7d39", label: "Active" },
  error: { bg: "rgba(255,59,48,0.08)", color: "#FF3B30", label: "Error" },
  paused: { bg: "rgba(0,0,0,0.06)", color: "#6A6A6E", label: "Paused" },
  inactive: { bg: "rgba(0,0,0,0.06)", color: "#6A6A6E", label: "Inactive" },
};

interface AgentStatusGridProps {
  agents: UserAgent[];
}

export function AgentStatusGrid({ agents }: AgentStatusGridProps) {
  return (
    <div
      className="bg-white rounded-[12px] border border-black/[0.06] overflow-hidden"
      style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
    >
      <div className="px-6 py-4 border-b border-black/[0.06] flex items-center justify-between">
        <span className="text-[15px] font-bold text-[#3A3A3C]">All Agents</span>
        <span className="text-[12px] text-[#6A6A6E]">{agents.length} total</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px]">
          <thead>
            <tr className="border-b border-black/[0.04]">
              {["Agent", "Client", "Platform", "Status", "Last Run", "Runs", "Actions"].map((col) => (
                <th
                  key={col}
                  className="px-5 py-3 text-left text-[11px] font-semibold text-[#8E8E93] uppercase tracking-[0.5px]"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-black/[0.04]">
            {agents.map((agent) => {
              const statusStyle = STATUS_STYLE[agent.status] ?? STATUS_STYLE.inactive;
              const isOnline = agent.status === "active" && agent.is_active;

              return (
                <tr key={agent.id} className="hover:bg-[#F5F5F7]/50 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <StatusDot status={isOnline ? "active" : "inactive"} />
                      <span className="text-[13px] font-semibold text-[#3A3A3C] whitespace-nowrap">
                        {agent.name}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-[13px] text-[#6A6A6E] whitespace-nowrap">
                    {(agent.config as Record<string, string>)?.client ?? "—"}
                  </td>
                  <td className="px-5 py-3.5 text-[13px] text-[#6A6A6E] whitespace-nowrap">
                    {agent.connected_platform ? (PLATFORM_LABEL[agent.connected_platform] ?? agent.connected_platform) : "—"}
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className="text-[10px] font-bold tracking-[0.5px] uppercase px-2 py-0.5 rounded-full whitespace-nowrap"
                      style={{ background: statusStyle.bg, color: statusStyle.color }}
                    >
                      {statusStyle.label}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-[13px] text-[#6A6A6E] whitespace-nowrap">
                    {formatRelativeTime(agent.last_run_at)}
                  </td>
                  <td className="px-5 py-3.5 text-[13px] font-semibold text-[#3A3A3C]">
                    {agent.run_count}
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <button className="text-[12px] font-semibold text-[#3A3A3C] h-[28px] px-3 rounded-[6px] border border-[#D2D2D7] hover:border-[#3A3A3C] transition-colors cursor-pointer bg-transparent">
                        View
                      </button>
                      <button className="text-[12px] font-semibold text-[#FF3B30] h-[28px] px-3 rounded-[6px] border border-transparent hover:border-[#FF3B30]/30 transition-colors cursor-pointer bg-transparent">
                        {agent.is_active ? "Pause" : "Resume"}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
