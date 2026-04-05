import Link from "next/link";

const AGENTS = [
  {
    slug: "linkedin-post-agent",
    name: "Frame",
    role: "LinkedIn Post Agent",
    description: "Automated thought leadership for executives.",
    live: true,
    price: "$99/mo",
  },
  {
    slug: "car-reseller-intel",
    name: "Flash",
    role: "Car Reseller Intel",
    description: "Underpriced cars found before competitors wake up.",
    live: false,
    price: "$149/mo",
  },
  {
    slug: "property-market-briefing",
    name: "Focus",
    role: "Property Market Briefing",
    description: "Dubai real estate moves. In your inbox at 8am.",
    live: false,
    price: "$99/mo",
  },
  {
    slug: "doctor-morning-briefing",
    name: "Develop",
    role: "Doctor Morning Briefing",
    description: "Clinical news + patient context. Before your first appointment.",
    live: false,
    price: "$49/mo",
  },
];

export default function AgentPricingTable() {
  return (
    <section className="bg-[#f4f3f1] py-24">
      <div className="max-w-7xl mx-auto px-8">
        <h2 className="font-display text-3xl font-bold text-[#012d1d] mb-12">
          Available Agents
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {AGENTS.map((agent) => (
            <div
              key={agent.slug}
              className={`bg-white p-8 rounded-lg border flex flex-col justify-between h-64 ${
                agent.live
                  ? "border-[#1b4332]/10"
                  : "border-[#c1c8c2]/30 opacity-70 grayscale hover:grayscale-0 transition-all"
              }`}
            >
              <div>
                <div className="flex justify-between items-start mb-4">
                  <span className="text-3xl">{agent.live ? "💼" : "⏳"}</span>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-tighter px-2 py-1 rounded ${
                      agent.live
                        ? "bg-[#1b4332]/10 text-[#1b4332]"
                        : "bg-[#e9e8e5] text-[#414844]"
                    }`}
                  >
                    {agent.live ? "Live Now" : "Coming Soon"}
                  </span>
                </div>
                <h3 className="font-display font-bold text-lg mb-1 text-[#1a1c1a]">
                  {agent.name}
                </h3>
                <p className="text-xs text-[#414844]/60 uppercase tracking-widest mb-1">
                  {agent.role}
                </p>
                <p className="text-sm text-[#414844]">{agent.description}</p>
              </div>
              <div className="text-[#012d1d] font-bold">{agent.price}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
