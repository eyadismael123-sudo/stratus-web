"use client";

import { AdminTabController } from "./AdminTabNav";
import { AgentStatusGrid } from "./AgentStatusGrid";
import { ClientRosterTable } from "./ClientRosterTable";
import { RevenueStats } from "./RevenueStats";
import type { AdminStats, AdminClient, UserAgent, Subscription } from "@/types";

interface AdminPageContentProps {
  stats: AdminStats;
  clients: AdminClient[];
  agents: UserAgent[];
  subscriptions: Subscription[];
}

export function AdminPageContent({
  stats,
  clients,
  agents,
  subscriptions,
}: AdminPageContentProps) {
  return (
    <AdminTabController>
      {(tab) => (
        <>
          {(tab === "overview" || tab === "agents") && (
            <AgentStatusGrid agents={agents} />
          )}
          {(tab === "overview" || tab === "clients") && (
            <ClientRosterTable clients={clients} />
          )}
          {(tab === "overview" || tab === "revenue") && (
            <RevenueStats stats={stats} subscriptions={subscriptions} />
          )}
        </>
      )}
    </AdminTabController>
  );
}
