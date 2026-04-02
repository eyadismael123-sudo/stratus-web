"use client";

import { useState, useMemo } from "react";
import type { AgentTemplate } from "@/types";
import { AgentListingCard } from "./AgentListingCard";

type CategoryFilter = "all" | "Personal" | "Business" | "Health";

const FILTERS: { key: CategoryFilter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "Personal", label: "Personal" },
  { key: "Business", label: "Business" },
  { key: "Health", label: "Health" },
];

interface SearchAndFilterProps {
  templates: AgentTemplate[];
}

export function SearchAndFilter({ templates }: SearchAndFilterProps) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<CategoryFilter>("all");

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    return templates.filter((t) => {
      const matchesCat = category === "all" || t.category === category;
      const matchesQuery =
        !q ||
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.industries.some((i) => i.toLowerCase().includes(q)) ||
        t.role.toLowerCase().includes(q);
      return matchesCat && matchesQuery;
    });
  }, [templates, query, category]);

  // Group by category for display
  const groups = useMemo(() => {
    const map = new Map<string, AgentTemplate[]>();
    for (const t of filtered) {
      const existing = map.get(t.category) ?? [];
      map.set(t.category, [...existing, t]);
    }
    return map;
  }, [filtered]);

  const CATEGORY_META: Record<string, { icon: string; desc: string }> = {
    Personal: { icon: "👤", desc: "Agents for your personal brand and career" },
    Business: { icon: "🏢", desc: "Industry-specific agents for your business" },
    Health: { icon: "🩺", desc: "Clinical intelligence for medical professionals" },
  };

  return (
    <div className="flex flex-col gap-8">
      {/* Search + filter bar */}
      <div className="bg-white rounded-[12px] border border-black/[0.06] p-5 flex flex-col sm:flex-row items-stretch sm:items-center gap-4"
        style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
      >
        {/* Search input */}
        <div className="flex-1 flex items-center gap-2.5 bg-[#F5F5F7] rounded-[8px] px-3.5 border border-[#D2D2D7] h-[42px] transition-colors focus-within:border-[#3A3A3C]">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            className="text-[#6A6A6E] flex-shrink-0"
          >
            <circle cx="7" cy="7" r="5" />
            <path d="M11 11l3 3" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search agents by name, industry, or task..."
            className="flex-1 bg-transparent border-none outline-none text-[14px] text-[#3A3A3C] placeholder:text-[#8E8E93]"
          />
        </div>

        {/* Category filter chips */}
        <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
          <span className="text-[12px] font-semibold text-[#6A6A6E] whitespace-nowrap">
            Filter:
          </span>
          {FILTERS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setCategory(key)}
              className="px-3.5 py-1.5 rounded-full text-[12px] font-medium border transition-all duration-150 cursor-pointer whitespace-nowrap"
              style={
                category === key
                  ? { background: "#3A3A3C", color: "#FFFFFF", borderColor: "#3A3A3C" }
                  : { background: "white", color: "#6A6A6E", borderColor: "#D2D2D7" }
              }
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-[14px] text-[#8E8E93]">
          No agents match your search.
        </div>
      ) : (
        <div className="flex flex-col gap-10">
          {Array.from(groups.entries()).map(([cat, catTemplates]) => {
            const meta = CATEGORY_META[cat] ?? { icon: "🤖", desc: "" };
            return (
              <div key={cat}>
                {/* Category header */}
                <div className="flex items-center gap-2.5 mb-6 pb-3.5 border-b-2 border-black/[0.06]">
                  <span className="text-[22px] leading-none">{meta.icon}</span>
                  <span className="text-[18px] font-black text-[#3A3A3C] tracking-[-0.4px]">
                    {cat}
                  </span>
                  <span className="text-[13px] text-[#6A6A6E]">{meta.desc}</span>
                  {cat === "Health" && (
                    <span
                      className="text-[10px] font-bold tracking-[0.5px] uppercase px-2.5 py-0.5 rounded-full ml-1"
                      style={{ background: "rgba(0,0,0,0.06)", color: "#6A6A6E" }}
                    >
                      Division launching 2026
                    </span>
                  )}
                </div>

                {/* Agent grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {catTemplates.map((t) => (
                    <AgentListingCard key={t.id} template={t} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
