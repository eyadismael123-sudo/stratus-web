import type { AdminClient } from "@/types";

function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(0)}`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-AE", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

const CHURN_STYLE: Record<string, { bg: string; color: string }> = {
  low: { bg: "rgba(52,199,89,0.1)", color: "#1a7d39" },
  medium: { bg: "rgba(255,149,0,0.12)", color: "#C47700" },
  high: { bg: "rgba(255,59,48,0.08)", color: "#FF3B30" },
};

interface ClientRosterTableProps {
  clients: AdminClient[];
}

export function ClientRosterTable({ clients }: ClientRosterTableProps) {
  return (
    <div
      className="bg-white rounded-[12px] border border-black/[0.06] overflow-hidden"
      style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
    >
      <div className="px-6 py-4 border-b border-black/[0.06] flex items-center justify-between">
        <span className="text-[15px] font-bold text-[#3A3A3C]">Clients</span>
        <span className="text-[12px] text-[#6A6A6E]">{clients.length} accounts</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[600px]">
          <thead>
            <tr className="border-b border-black/[0.04]">
              {["Client", "Company", "Agents", "LTV", "Last Active", "Churn Risk", "Actions"].map((col) => (
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
            {clients.map((client) => {
              const churnStyle = CHURN_STYLE[client.churn_risk] ?? CHURN_STYLE.medium;

              return (
                <tr key={client.id} className="hover:bg-[#F5F5F7]/50 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="text-[13px] font-semibold text-[#3A3A3C]">
                      {client.full_name}
                    </div>
                    <div className="text-[11px] text-[#8E8E93] mt-0.5">{client.email}</div>
                  </td>
                  <td className="px-5 py-3.5 text-[13px] text-[#6A6A6E] whitespace-nowrap">
                    {client.company_name ?? "—"}
                  </td>
                  <td className="px-5 py-3.5 text-[13px] font-semibold text-[#3A3A3C]">
                    {client.agents_hired.length}
                  </td>
                  <td className="px-5 py-3.5 text-[13px] font-semibold text-[#3A3A3C] whitespace-nowrap">
                    {formatPrice(client.lifetime_value_cents)}
                  </td>
                  <td className="px-5 py-3.5 text-[13px] text-[#6A6A6E] whitespace-nowrap">
                    {client.last_activity_at ? formatDate(client.last_activity_at) : "—"}
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className="text-[10px] font-bold tracking-[0.5px] uppercase px-2 py-0.5 rounded-full capitalize"
                      style={{ background: churnStyle.bg, color: churnStyle.color }}
                    >
                      {client.churn_risk}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <button className="text-[12px] font-semibold text-[#3A3A3C] h-[28px] px-3 rounded-[6px] border border-[#D2D2D7] hover:border-[#3A3A3C] transition-colors cursor-pointer bg-transparent">
                      View
                    </button>
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
