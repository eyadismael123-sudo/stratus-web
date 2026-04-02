import type { AdminStats } from "@/types";

interface SystemHealthCardsProps {
  stats: AdminStats;
}

export function SystemHealthCards({ stats }: SystemHealthCardsProps) {
  const cards = [
    {
      label: "Agents Running",
      value: stats.total_agents_running.toString(),
      sub: "across all clients",
      color: "#1a7d39",
      bg: "rgba(52,199,89,0.08)",
    },
    {
      label: "Total Clients",
      value: stats.total_clients.toString(),
      sub: "active accounts",
      color: "#3A3A3C",
      bg: "rgba(0,0,0,0.04)",
    },
    {
      label: "MRR",
      value: `$${(stats.mrr_cents / 100).toFixed(0)}`,
      sub: "monthly recurring revenue",
      color: "#3A3A3C",
      bg: "rgba(0,0,0,0.04)",
    },
    {
      label: "Churn Rate",
      value: `${(stats.churn_rate * 100).toFixed(0)}%`,
      sub: "last 30 days",
      color: stats.churn_rate > 0.1 ? "#FF3B30" : "#1a7d39",
      bg: stats.churn_rate > 0.1 ? "rgba(255,59,48,0.08)" : "rgba(52,199,89,0.08)",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ label, value, sub, color, bg }) => (
        <div
          key={label}
          className="bg-white rounded-[12px] border border-black/[0.06] px-6 py-5"
          style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
        >
          <div
            className="inline-flex items-center justify-center w-8 h-8 rounded-[8px] mb-3"
            style={{ background: bg }}
          />
          <div
            className="text-[28px] font-black tracking-[-1px] leading-none mb-1"
            style={{ color }}
          >
            {value}
          </div>
          <div className="text-[13px] font-semibold text-[#3A3A3C] mb-0.5">{label}</div>
          <div className="text-[11px] text-[#8E8E93]">{sub}</div>
        </div>
      ))}
    </div>
  );
}
