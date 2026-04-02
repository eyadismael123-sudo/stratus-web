import {
  MOCK_ADMIN_STATS,
  MOCK_ADMIN_CLIENTS,
  MOCK_ALL_AGENTS,
  MOCK_SUBSCRIPTIONS,
} from "@/constants/mock-data";
import { SystemHealthCards } from "@/components/pages/admin/SystemHealthCards";
import { AdminPageContent } from "@/components/pages/admin/AdminPageContent";

export const metadata = {
  title: "Admin War Room — Stratus",
  description: "Stratus internal admin dashboard.",
};

export default function AdminPage() {
  return (
    <div className="min-h-screen" style={{ background: "#F5F5F7" }}>
      {/* Page header */}
      <div className="border-b border-black/[0.06] bg-[rgba(245,245,247,0.85)] backdrop-blur-[12px] sticky top-0 z-40 px-4 md:px-10 h-[60px] flex items-center justify-between">
        <div>
          <span className="text-[17px] font-bold text-[#3A3A3C]">War Room</span>
          <span className="ml-3 text-[13px] text-[#6A6A6E] hidden sm:inline">
            Internal admin dashboard
          </span>
        </div>
        <span
          className="text-[10px] font-bold tracking-[0.5px] uppercase px-2.5 py-1 rounded-full"
          style={{ background: "rgba(255,59,48,0.08)", color: "#FF3B30" }}
        >
          Admin Only
        </span>
      </div>

      <div className="px-4 md:px-10 py-8 max-w-7xl mx-auto flex flex-col gap-8">
        {/* System health strip */}
        <SystemHealthCards stats={MOCK_ADMIN_STATS} />

        {/* Tab-driven sections */}
        <AdminPageContent
          stats={MOCK_ADMIN_STATS}
          clients={MOCK_ADMIN_CLIENTS}
          agents={MOCK_ALL_AGENTS}
          subscriptions={MOCK_SUBSCRIPTIONS}
        />
      </div>
    </div>
  );
}
