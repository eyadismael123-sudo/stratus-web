import Link from "next/link";
import type { AgentTemplate } from "@/types";

function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(0)}`;
}

interface AgentPricingCTAProps {
  template: AgentTemplate;
}

export default function AgentPricingCTA({ template }: AgentPricingCTAProps) {
  const price = formatPrice(template.price_usd_cents);

  return (
    <section className="px-8 max-w-7xl mx-auto mb-24">
      <div className="bg-[#012d1d] p-16 rounded-xl text-center relative overflow-hidden">
        <div className="relative z-10">
          <h2 className="text-4xl md:text-5xl font-display font-extrabold text-white mb-6">
            Ready to hire?
          </h2>
          <div className="text-6xl md:text-7xl font-display font-extrabold text-[#c1ecd4] mb-12">
            {price}
            <span className="text-xl font-body font-medium text-[#c1ecd4]/60">/month</span>
          </div>
          <Link href="/auth/signup">
            <button className="bg-[#FAF9F6] text-[#012d1d] px-12 py-5 rounded font-display font-bold text-lg hover:bg-white transition-colors">
              Get Started Now
            </button>
          </Link>
        </div>
        <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(circle_at_50%_120%,#1B4332,transparent)]" />
      </div>
    </section>
  );
}
