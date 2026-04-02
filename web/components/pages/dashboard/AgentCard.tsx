import Link from "next/link";
import type { UserAgent, ConnectedPlatform } from "@/types";
import { StatusDot } from "@/components/common/StatusDot";

const PLATFORM_ICONS: Record<ConnectedPlatform, React.ReactNode> = {
  linkedin: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
    </svg>
  ),
  telegram: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
    </svg>
  ),
  whatsapp: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
    </svg>
  ),
  email: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
      <polyline points="22,6 12,13 2,6"/>
    </svg>
  ),
};

function AgentAvatar({ name, status }: { name: string; status: UserAgent["status"] }) {
  const initials = name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  const bg =
    status === "active"
      ? "linear-gradient(135deg, #3A3A3C 0%, #1c1c1e 100%)"
      : "linear-gradient(135deg, #AEAEB2 0%, #8E8E93 100%)";

  return (
    <div
      className="w-11 h-11 rounded-[12px] flex items-center justify-center text-[15px] font-black text-white flex-shrink-0"
      style={{ background: bg }}
    >
      {initials}
    </div>
  );
}

export function AgentCard({ agent }: { agent: UserAgent }) {
  return (
    <Link
      href={`/dashboard/agents/${agent.id}`}
      className="block no-underline"
    >
      <div
        className="bg-white rounded-[12px] p-5 relative border-[1.5px] border-transparent transition-all duration-250 hover:-translate-y-0.5 hover:border-[#D2D2D7] cursor-pointer"
        style={{
          boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
        }}
      >
        {/* Status dot — top right */}
        <div className="absolute top-4 right-4">
          <StatusDot status={agent.status} />
        </div>

        {/* Top: avatar + name */}
        <div className="flex items-start gap-3 pr-6">
          <AgentAvatar name={agent.name} status={agent.status} />
          <div className="flex-1 min-w-0">
            <div className="text-[15px] font-black text-[#3A3A3C] tracking-[-0.01em] truncate">
              {agent.name}
            </div>
            <div className="text-[12px] text-[#8E8E93] truncate mt-0.5">
              {agent.agent_template.role}
            </div>
          </div>
        </div>

        {/* Footer: platform + last run */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-[#F2F2F4]">
          <div className="flex items-center gap-1.5 text-[#8E8E93]">
            {agent.connected_platform && PLATFORM_ICONS[agent.connected_platform]}
            {agent.connected_platform && (
              <span className="text-[11px] font-medium capitalize">
                {agent.connected_platform}
              </span>
            )}
          </div>
          {agent.last_run_at && (
            <span className="text-[11px] text-[#AEAEB2]">
              {new Date(agent.last_run_at).toLocaleDateString("en-AE", {
                month: "short",
                day: "numeric",
              })}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
