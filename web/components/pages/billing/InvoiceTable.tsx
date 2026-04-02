import type { MockInvoice } from "@/constants/mock-data";

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

interface InvoiceTableProps {
  invoices: MockInvoice[];
}

export function InvoiceTable({ invoices }: InvoiceTableProps) {
  return (
    <div
      className="bg-white rounded-[12px] border border-black/[0.06] overflow-hidden"
      style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-black/[0.06]">
        <span className="text-[15px] font-bold text-[#3A3A3C]">Invoice History</span>
      </div>

      {invoices.length === 0 ? (
        <div className="px-6 py-10 text-center text-[14px] text-[#8E8E93]">
          No invoices yet.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[500px]">
            <thead>
              <tr className="border-b border-black/[0.04]">
                {["Date", "Description", "Amount", "Status", "Receipt"].map((col) => (
                  <th
                    key={col}
                    className="px-6 py-3 text-left text-[11px] font-semibold text-[#8E8E93] uppercase tracking-[0.5px]"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-black/[0.04]">
              {invoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-[#F5F5F7]/50 transition-colors">
                  <td className="px-6 py-3.5 text-[13px] text-[#6A6A6E] whitespace-nowrap">
                    {formatDate(inv.date)}
                  </td>
                  <td className="px-6 py-3.5 text-[13px] text-[#3A3A3C]">
                    {inv.description}
                  </td>
                  <td className="px-6 py-3.5 text-[13px] font-semibold text-[#3A3A3C] whitespace-nowrap">
                    {formatPrice(inv.amount_usd_cents)}
                  </td>
                  <td className="px-6 py-3.5">
                    <span
                      className="text-[10px] font-bold tracking-[0.5px] uppercase px-2 py-0.5 rounded-full"
                      style={
                        inv.status === "paid"
                          ? { background: "rgba(52,199,89,0.1)", color: "#1a7d39" }
                          : inv.status === "failed"
                          ? { background: "rgba(255,59,48,0.08)", color: "#FF3B30" }
                          : { background: "rgba(0,0,0,0.06)", color: "#6A6A6E" }
                      }
                    >
                      {inv.status}
                    </span>
                  </td>
                  <td className="px-6 py-3.5">
                    {inv.pdf_url ? (
                      <a
                        href={inv.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[12px] font-semibold text-[#3A3A3C] underline-offset-2 hover:underline"
                      >
                        PDF
                      </a>
                    ) : (
                      <span className="text-[12px] text-[#C7C7CC]">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
