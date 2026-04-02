import Link from "next/link";

const AGENTS = [
  {
    slug: "car-reseller-intel",
    name: "Flash",
    role: "Car Reseller Intel",
    description: "Underpriced cars found before competitors wake up.",
    category: "Business",
  },
  {
    slug: "property-market-briefing",
    name: "Focus",
    role: "Property Market Briefing",
    description: "Dubai real estate moves. In your inbox at 8am.",
    category: "Business",
  },
  {
    slug: "doctor-morning-briefing",
    name: "Develop",
    role: "Doctor Morning Briefing",
    description: "Clinical news + patient context. Before your first appointment.",
    category: "Health",
  },
];

interface RelatedAgentsProps {
  currentSlug: string;
}

export default function RelatedAgents({ currentSlug }: RelatedAgentsProps) {
  const related = AGENTS.filter((a) => a.slug !== currentSlug);

  if (related.length === 0) return null;

  return (
    <section className="px-8 max-w-7xl mx-auto mb-32">
      <h2 className="text-sm font-body uppercase tracking-[0.3em] text-[#414844] mb-12 border-b border-[#c1c8c2]/20 pb-4">
        More Agents
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {related.map((agent) => (
          <Link
            key={agent.slug}
            href={`/agents/${agent.slug}`}
            className="group block bg-white p-8 rounded-lg border border-[#c1c8c2]/20 hover:-translate-y-1 transition-transform"
            style={{ boxShadow: "0 8px 32px -4px rgba(1,45,29,0.04)" }}
          >
            <div className="w-10 h-10 bg-[#f4f3f1] rounded-lg flex items-center justify-center mb-4">
              <span className="text-[#012d1d] text-sm font-display font-bold">
                {agent.name.charAt(0)}
              </span>
            </div>
            <p className="text-[#414844]/60 text-[10px] font-body uppercase tracking-widest mb-1">
              {agent.role}
            </p>
            <h3 className="font-display font-bold text-lg text-[#1a1c1a] mb-2">
              {agent.name}
            </h3>
            <p className="text-sm text-[#414844] leading-relaxed mb-4">
              {agent.description}
            </p>
            <span className="text-[10px] font-bold uppercase tracking-tighter px-2 py-1 rounded bg-[#e9e8e5] text-[#414844]">
              Coming Soon
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
