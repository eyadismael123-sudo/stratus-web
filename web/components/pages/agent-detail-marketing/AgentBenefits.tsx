import type { AgentTemplate } from "@/types";

interface AgentBenefitsProps {
  template: AgentTemplate;
}

export default function AgentBenefits({ template }: AgentBenefitsProps) {
  return (
    <section className="px-8 max-w-7xl mx-auto mb-32">
      <h2 className="text-sm font-body uppercase tracking-[0.3em] text-[#414844] mb-12 border-b border-[#c1c8c2]/20 pb-4">
        Capabilities
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {template.features.slice(0, 3).map((feature) => (
          <div
            key={feature}
            className="bg-[#f4f3f1] p-10 group hover:bg-[#e9e8e5] transition-colors rounded-lg"
          >
            <div className="w-10 h-10 bg-[#1b4332]/10 rounded-lg flex items-center justify-center mb-6">
              <span className="text-[#012d1d] text-lg font-display font-bold">✦</span>
            </div>
            <p className="text-[#414844] leading-relaxed">{feature}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
