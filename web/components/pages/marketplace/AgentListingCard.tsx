import type React from "react";
import type { AgentTemplate } from "@/types";

const CATEGORY_ICON: Record<string, React.ReactNode> = {
  Personal: (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="36" height="36" rx="10" fill="#F0F4FF"/>
      <circle cx="18" cy="14" r="5" fill="#3A3A3C"/>
      <path d="M8 28c0-5.523 4.477-10 10-10s10 4.477 10 10" stroke="#3A3A3C" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  ),
  Business: (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="36" height="36" rx="10" fill="#FFF7E6"/>
      <rect x="10" y="14" width="16" height="14" rx="1.5" stroke="#3A3A3C" strokeWidth="1.8"/>
      <path d="M14 14v-3a4 4 0 0 1 8 0v3" stroke="#3A3A3C" strokeWidth="1.8" strokeLinecap="round"/>
      <line x1="18" y1="18" x2="18" y2="24" stroke="#3A3A3C" strokeWidth="1.8" strokeLinecap="round"/>
      <line x1="14" y1="21" x2="22" y2="21" stroke="#3A3A3C" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  ),
  Health: (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="36" height="36" rx="10" fill="#F0FFF4"/>
      <path d="M18 26s-8-5.5-8-11a6 6 0 0 1 8-5.66A6 6 0 0 1 26 15c0 5.5-8 11-8 11z" stroke="#3A3A3C" strokeWidth="1.8" strokeLinejoin="round"/>
    </svg>
  ),
};

const DEFAULT_ICON = (
  <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="36" height="36" rx="10" fill="#F5F5F7"/>
    <circle cx="18" cy="18" r="6" stroke="#3A3A3C" strokeWidth="1.8"/>
    <path d="M18 14v4l3 2" stroke="#3A3A3C" strokeWidth="1.8" strokeLinecap="round"/>
  </svg>
);

function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(0)}`;
}

interface AgentListingCardProps {
  template: AgentTemplate;
}

export function AgentListingCard({ template }: AgentListingCardProps) {
  const icon = CATEGORY_ICON[template.category] ?? DEFAULT_ICON;
  const isLive = template.is_published;

  return (
    <div
      className="bg-white rounded-[10px] border border-black/[0.06] p-6 flex flex-col gap-4 transition-all duration-200"
      style={{
        boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
        opacity: isLive ? 1 : 0.7,
      }}
    >
      {/* Header: icon + badge */}
      <div className="flex items-start justify-between">
        <span className="leading-none">{icon}</span>
        {isLive ? (
          <span
            className="text-[10px] font-bold tracking-[0.5px] uppercase px-2 py-0.5 rounded-full"
            style={{ background: "rgba(52,199,89,0.1)", color: "#1a7d39" }}
          >
            Live
          </span>
        ) : (
          <span
            className="text-[10px] font-bold tracking-[0.5px] uppercase px-2 py-0.5 rounded-full"
            style={{ background: "rgba(0,0,0,0.06)", color: "#6A6A6E" }}
          >
            Coming Soon
          </span>
        )}
      </div>

      {/* Body */}
      <div className="flex-1">
        <div className="text-[15px] font-bold text-[#3A3A3C] mb-1.5">
          {template.name}
        </div>
        <div className="text-[13px] text-[#6A6A6E] leading-relaxed">
          {template.description}
        </div>
      </div>

      {/* Industries */}
      {template.industries.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {template.industries.slice(0, 3).map((ind) => (
            <span
              key={ind}
              className="text-[11px] font-medium px-2 py-0.5 rounded-full border border-black/[0.06] text-[#6A6A6E]"
              style={{ background: "#F5F5F7" }}
            >
              {ind}
            </span>
          ))}
        </div>
      )}

      {/* Footer: price + CTA */}
      <div className="flex items-center justify-between pt-3.5 border-t border-black/[0.06]">
        {isLive ? (
          <>
            <div className="text-[15px] font-bold text-[#3A3A3C]">
              {formatPrice(template.price_usd_cents)}{" "}
              <span className="text-[12px] font-normal text-[#6A6A6E]">
                / month
              </span>
            </div>
            <button className="h-[34px] px-4 rounded-[8px] text-[12px] font-bold text-white bg-[#3A3A3C] transition-all hover:bg-[#2a2a2c] hover:-translate-y-px cursor-pointer border-none">
              Hire
            </button>
          </>
        ) : (
          <>
            <div className="text-[13px] text-[#6A6A6E]">Notify me</div>
            <button className="h-[34px] px-4 rounded-[8px] text-[12px] font-semibold text-[#6A6A6E] bg-transparent border border-[#D2D2D7] transition-all hover:border-[#3A3A3C] hover:text-[#3A3A3C] cursor-pointer">
              Notify Me
            </button>
          </>
        )}
      </div>
    </div>
  );
}
