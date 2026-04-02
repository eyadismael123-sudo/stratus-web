import {
  MOCK_SUBSCRIPTIONS,
  MOCK_USER_AGENTS,
  MOCK_INVOICES,
} from "@/constants/mock-data";
import { SubscriptionsTable } from "@/components/pages/billing/SubscriptionsTable";
import { InvoiceTable } from "@/components/pages/billing/InvoiceTable";

export const metadata = {
  title: "Billing — Stratus",
  description: "Manage your Stratus subscriptions and invoices.",
};

export default function BillingPage() {
  const totalMonthly = MOCK_SUBSCRIPTIONS.filter(
    (s) => s.status === "active" && !s.cancel_at_period_end,
  ).reduce((sum, s) => sum + s.amount_usd_cents, 0);

  return (
    <div className="min-h-screen" style={{ background: "#F5F5F7" }}>
      {/* Page header */}
      <div className="border-b border-black/[0.06] bg-[rgba(245,245,247,0.85)] backdrop-blur-[12px] sticky top-[60px] z-40 px-4 md:px-10 h-[60px] flex items-center justify-between">
        <div>
          <span className="text-[17px] font-bold text-[#3A3A3C]">Billing</span>
          <span className="ml-3 text-[13px] text-[#6A6A6E] hidden sm:inline">
            Manage subscriptions &amp; invoices
          </span>
        </div>
        <div className="text-right hidden sm:block">
          <div className="text-[13px] font-bold text-[#3A3A3C]">
            ${(totalMonthly / 100).toFixed(0)}/mo
          </div>
          <div className="text-[11px] text-[#6A6A6E]">Total spend</div>
        </div>
      </div>

      <div className="px-4 md:px-10 py-8 max-w-5xl mx-auto flex flex-col gap-8">

        {/* Summary strip */}
        <div
          className="bg-white rounded-[12px] border border-black/[0.06] px-8 py-6 grid grid-cols-2 sm:grid-cols-4 gap-6"
          style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
        >
          {[
            {
              num: MOCK_SUBSCRIPTIONS.filter((s) => s.status === "active" && !s.cancel_at_period_end).length.toString(),
              label: "Active Agents",
            },
            {
              num: `$${(totalMonthly / 100).toFixed(0)}`,
              label: "Monthly Spend",
            },
            {
              num: MOCK_INVOICES.length.toString(),
              label: "Invoices",
            },
            {
              num: "Visa •••• 4242",
              label: "Payment Method",
            },
          ].map(({ num, label }) => (
            <div key={label} className="text-center">
              <div className="text-[22px] font-black text-[#3A3A3C] tracking-[-0.5px] mb-1">
                {num}
              </div>
              <div className="text-[12px] text-[#6A6A6E] font-medium">{label}</div>
            </div>
          ))}
        </div>

        {/* Active subscriptions */}
        <SubscriptionsTable
          subscriptions={MOCK_SUBSCRIPTIONS}
          agents={MOCK_USER_AGENTS}
        />

        {/* Invoice history */}
        <InvoiceTable invoices={MOCK_INVOICES} />

        {/* Danger zone */}
        <div
          className="bg-white rounded-[12px] border border-[#FF3B30]/20 px-6 py-5 flex items-center justify-between gap-4"
          style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}
        >
          <div>
            <div className="text-[14px] font-bold text-[#3A3A3C] mb-0.5">Cancel All Subscriptions</div>
            <div className="text-[12px] text-[#6A6A6E]">
              All your agents will be deactivated at the end of their billing periods.
            </div>
          </div>
          <button className="h-[38px] px-4 rounded-[8px] text-[13px] font-semibold text-[#FF3B30] border border-[#FF3B30]/30 bg-transparent hover:bg-[#FF3B30]/[0.04] transition-all cursor-pointer flex-shrink-0">
            Cancel All
          </button>
        </div>
      </div>
    </div>
  );
}
