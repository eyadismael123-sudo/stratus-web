"use client";

import { useState } from "react";

export type AdminTab = "overview" | "agents" | "clients" | "revenue";

const TABS: { key: AdminTab; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "agents", label: "Agents" },
  { key: "clients", label: "Clients" },
  { key: "revenue", label: "Revenue" },
];

interface AdminTabNavProps {
  active: AdminTab;
  onChange: (tab: AdminTab) => void;
}

export function AdminTabNav({ active, onChange }: AdminTabNavProps) {
  return (
    <div className="flex items-center gap-1 bg-[#EBEBED] rounded-[10px] p-1">
      {TABS.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className="flex-1 h-[34px] rounded-[8px] text-[13px] font-semibold transition-all duration-150 cursor-pointer border-none whitespace-nowrap px-4"
          style={
            active === key
              ? { background: "white", color: "#3A3A3C", boxShadow: "0 1px 3px rgba(0,0,0,0.12)" }
              : { background: "transparent", color: "#6A6A6E" }
          }
        >
          {label}
        </button>
      ))}
    </div>
  );
}

/** Wrapper that manages tab state — used by the admin page */
export function AdminTabController({
  children,
}: {
  children: (tab: AdminTab) => React.ReactNode;
}) {
  const [tab, setTab] = useState<AdminTab>("overview");
  return (
    <div className="flex flex-col gap-6">
      <AdminTabNav active={tab} onChange={setTab} />
      {children(tab)}
    </div>
  );
}
