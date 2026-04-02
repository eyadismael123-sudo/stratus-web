"use client";

import { useState } from "react";
import type { UserAgent, AgentCategory } from "@/types";
import { AgentCard } from "./AgentCard";
import { CategoryTabs } from "./CategoryTabs";
import { EmptyState } from "./EmptyState";

// Map agent category from template to AgentCategory
function getAgentCategory(agent: UserAgent): AgentCategory {
  // role-based heuristic — matches MOCK_AGENT_TEMPLATES categories
  if (agent.name.toLowerCase().includes("linkedin") || agent.name.toLowerCase().includes("career")) {
    return "Personal";
  }
  if (agent.name.toLowerCase().includes("doctor") || agent.name.toLowerCase().includes("clinic")) {
    return "Health";
  }
  return "Business";
}

export function AgentGrid({ agents }: { agents: UserAgent[] }) {
  const [activeTab, setActiveTab] = useState<AgentCategory>("All");

  const counts: Record<AgentCategory, number> = {
    All: agents.length,
    Personal: agents.filter((a) => getAgentCategory(a) === "Personal").length,
    Business: agents.filter((a) => getAgentCategory(a) === "Business").length,
    Health: agents.filter((a) => getAgentCategory(a) === "Health").length,
  };

  const filtered =
    activeTab === "All"
      ? agents
      : agents.filter((a) => getAgentCategory(a) === activeTab);

  if (agents.length === 0) {
    return <EmptyState />;
  }

  return (
    <div>
      <CategoryTabs active={activeTab} onChange={setActiveTab} counts={counts} />

      {filtered.length === 0 ? (
        <p className="text-[14px] text-[#8E8E93] py-12 text-center">
          No agents in this category yet.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  );
}
