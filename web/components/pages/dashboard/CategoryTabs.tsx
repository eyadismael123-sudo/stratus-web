import type { AgentCategory } from "@/types";

const TABS: AgentCategory[] = ["All", "Personal", "Business", "Health"];

interface CategoryTabsProps {
  active: AgentCategory;
  onChange: (tab: AgentCategory) => void;
  counts: Record<AgentCategory, number>;
}

export function CategoryTabs({ active, onChange, counts }: CategoryTabsProps) {
  return (
    <div className="flex items-center gap-2 flex-wrap mb-6">
      {TABS.map((tab) => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[13px] font-semibold transition-all duration-150"
          style={
            active === tab
              ? {
                  background: "#3A3A3C",
                  color: "#FFFFFF",
                }
              : {
                  background: "#FFFFFF",
                  color: "#6A6A6E",
                  border: "1.5px solid #D2D2D7",
                }
          }
        >
          {tab}
          <span
            className="text-[11px] font-bold rounded-full px-1.5 min-w-[18px] text-center"
            style={
              active === tab
                ? { background: "rgba(255,255,255,0.2)", color: "#FFFFFF" }
                : { background: "#EFEFEF", color: "#8E8E93" }
            }
          >
            {counts[tab]}
          </span>
        </button>
      ))}
    </div>
  );
}
