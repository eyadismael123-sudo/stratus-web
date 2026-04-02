import type { AgentTemplate } from "@/types";

const CATEGORY_EMOJI: Record<string, string> = {
  Personal: "👤",
  Business: "🏢",
  Health: "🩺",
};

function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(0)}`;
}

interface AgentListingCardProps {
  template: AgentTemplate;
}

export function AgentListingCard({ template }: AgentListingCardProps) {
  const emoji = CATEGORY_EMOJI[template.category] ?? "🤖";
  const isLive = template.is_published;

  return (
    <div
      className="bg-white rounded-[10px] border border-black/[0.06] p-6 flex flex-col gap-4 transition-all duration-200"
      style={{
        boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
        opacity: isLive ? 1 : 0.7,
      }}
    >
      {/* Header: emoji + badge */}
      <div className="flex items-start justify-between">
        <span className="text-4xl leading-none">{emoji}</span>
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
