import Link from "next/link";
import type { AgentTemplate } from "@/types";

function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(0)}`;
}

interface AgentHeroProps {
  template: AgentTemplate;
}

export default function AgentHero({ template }: AgentHeroProps) {
  const price = formatPrice(template.price_usd_cents);

  return (
    <section className="pt-32 pb-0 px-8 max-w-7xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-start mb-32">
        {/* Left col */}
        <div className="lg:col-span-7">
          {/* Icon + badges */}
          <div className="flex items-center gap-4 mb-8">
            <div className="w-16 h-16 bg-[#1b4332] flex items-center justify-center rounded-lg">
              <span className="text-white text-2xl font-display font-bold">
                {template.name.charAt(0)}
              </span>
            </div>
            <div className="flex gap-2">
              <span className="bg-[#e2dfde] text-[#636262] px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase">
                {template.category}
              </span>
              {template.is_published && (
                <span className="bg-[#c1ecd4] text-[#002114] px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#012d1d] animate-pulse" />
                  Live
                </span>
              )}
            </div>
          </div>

          {/* Name + role subtitle */}
          <h1 className="text-5xl md:text-7xl font-display font-extrabold text-[#012d1d] tracking-tighter mb-6 leading-tight">
            {template.name}
            <br />
            <span className="text-xs font-body font-medium text-[#414844]/55 uppercase tracking-[0.08em] normal-case" style={{ fontSize: "12px" }}>
              {template.role}
            </span>
          </h1>

          {/* Description */}
          <p className="text-xl md:text-2xl text-[#414844] font-light leading-relaxed max-w-2xl">
            {template.long_description ?? template.description}
          </p>
        </div>

        {/* Right col — price card */}
        <div className="lg:col-span-5">
          <div
            className="bg-white p-8 rounded-lg border border-[#c1c8c2]/10"
            style={{ boxShadow: "0 20px 40px rgba(26,28,26,0.05)" }}
          >
            <div className="flex justify-between items-baseline mb-8">
              <span className="text-[#414844] font-body text-sm uppercase tracking-widest">
                Subscription
              </span>
              <div className="text-4xl font-display font-bold text-[#012d1d]">
                {price}
                <span className="text-lg font-body font-medium text-[#414844]">/month</span>
              </div>
            </div>
            <Link href="/marketplace">
              <button className="w-full bg-[#012d1d] text-white py-4 rounded font-display font-bold text-lg hover:bg-[#1b4332] transition-colors mb-4">
                Hire This Agent
              </button>
            </Link>
            <p className="text-center text-[#414844] text-sm font-body">
              No setup fee. Cancel anytime.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
