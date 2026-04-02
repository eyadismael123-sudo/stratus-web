import type { AdminStats } from "@/types";
import type { Subscription } from "@/types";

interface RevenueStatsProps {
  stats: AdminStats;
  subscriptions: Subscription[];
}

export function RevenueStats({ stats, subscriptions }: RevenueStatsProps) {
  const active = subscriptions.filter((s) => s.status === "active" && !s.cancel_at_period_end);
  const cancelling = subscriptions.filter((s) => s.cancel_at_period_end);
  const totalRevenue = stats.total_revenue_cents;

  return (
    <div
      className="bg-white rounded-[12px] border border-black/[0.06] overflow-hidden"
      style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
    >
      <div className="px-6 py-4 border-b border-black/[0.06]">
        <span className="text-[15px] font-bold text-[#3A3A3C]">Revenue Overview</span>
      </div>

      <div className="px-6 py-5 grid grid-cols-2 sm:grid-cols-3 gap-6 border-b border-black/[0.06]">
        {[
          { label: "MRR", value: `$${(stats.mrr_cents / 100).toFixed(0)}` },
          { label: "Total Revenue", value: `$${(totalRevenue / 100).toFixed(0)}` },
          { label: "Churn Rate", value: `${(stats.churn_rate * 100).toFixed(0)}%` },
        ].map(({ label, value }) => (
          <div key={label}>
            <div className="text-[22px] font-black text-[#3A3A3C] tracking-[-0.5px] mb-1">{value}</div>
            <div className="text-[12px] text-[#6A6A6E] font-medium">{label}</div>
          </div>
        ))}
      </div>

      {/* Subscription breakdown */}
      <div className="px-6 py-5">
        <div className="text-[12px] font-semibold text-[#6A6A6E] uppercase tracking-[0.5px] mb-3">
          Subscription Breakdown
        </div>
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-[#34C759]" />
              <span className="text-[13px] text-[#3A3A3C]">Active</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-[12px] text-[#6A6A6E]">{active.length} subs</span>
              <span className="text-[13px] font-semibold text-[#3A3A3C]">
                ${(active.reduce((s, sub) => s + sub.amount_usd_cents, 0) / 100).toFixed(0)}/mo
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-[#FF9500]" />
              <span className="text-[13px] text-[#3A3A3C]">Cancelling</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-[12px] text-[#6A6A6E]">{cancelling.length} subs</span>
              <span className="text-[13px] font-semibold text-[#3A3A3C]">
                ${(cancelling.reduce((s, sub) => s + sub.amount_usd_cents, 0) / 100).toFixed(0)}/mo
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
