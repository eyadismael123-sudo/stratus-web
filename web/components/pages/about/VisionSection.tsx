import Link from "next/link";

const PROTOCOL_STEPS = [
  {
    number: "01",
    title: "Browse the marketplace",
    description:
      "Discover pre-trained AI agents specialized in regional functions—from LinkedIn posting to car market intelligence.",
  },
  {
    number: "02",
    title: "Hire your agent in minutes",
    description:
      "Simple onboarding. No complex APIs or coding required. Deploy your workforce with a single click and define their operational hours.",
  },
  {
    number: "03",
    title: "Watch your team work",
    description:
      "Monitor progress through your centralized dashboard. Your agents report, learn, and adapt to your business needs in real-time.",
  },
];

const FOUNDATIONS = [
  {
    icon: "📍",
    title: "Built for MENA",
    description:
      "Culturally conscious AI that understands regional nuances, languages, and business etiquette.",
  },
  {
    icon: "👥",
    title: "Agents as employees, not tools",
    description:
      "We move beyond workflows into the realm of digital colleagues who take responsibility.",
  },
  {
    icon: "💳",
    title: "No enterprise budget required",
    description:
      "Institutional-grade automation priced for the scaling middle market of the MENA region.",
  },
];

export default function VisionSection() {
  return (
    <>
      {/* Protocol Steps */}
      <section className="py-32 px-8 bg-[#EFEEEB]">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-sm uppercase tracking-widest font-black text-[#012d1d]/40 mb-16">
            The Stratus Protocol
          </h2>
          <div className="grid md:grid-cols-3 gap-16">
            {PROTOCOL_STEPS.map((step) => (
              <div key={step.number} className="group">
                <div className="text-8xl font-black font-display text-[#c1c8c2] opacity-20 group-hover:text-[#012d1d] group-hover:opacity-100 transition-all duration-500 mb-8">
                  {step.number}
                </div>
                <h4 className="text-2xl font-black font-display mb-4 text-[#1a1c1a]">
                  {step.title}
                </h4>
                <p className="text-[#414844] leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Foundations / Values */}
      <section className="py-32 px-8 bg-[#FAF9F6]">
        <div className="max-w-7xl mx-auto text-center mb-24">
          <h2 className="text-4xl md:text-5xl font-black font-display text-[#1a1c1a]">
            Our Foundations
          </h2>
        </div>
        <div className="max-w-7xl mx-auto grid md:grid-cols-3 gap-8">
          {FOUNDATIONS.map((item) => (
            <div
              key={item.title}
              className="bg-white p-12 rounded-xl text-center flex flex-col items-center"
              style={{ boxShadow: "0 12px 32px rgba(27,67,50,0.04)" }}
            >
              <span className="text-4xl text-[#012d1d] mb-6">{item.icon}</span>
              <h5 className="text-xl font-black font-display mb-4 text-[#1a1c1a]">
                {item.title}
              </h5>
              <p className="text-[#414844]">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-8 mb-32 rounded-3xl bg-[#1b4332] py-24 px-8 text-center relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(circle at center, #2D6A4F 0%, transparent 70%)",
          }}
        />
        <div className="relative z-10 max-w-3xl mx-auto">
          <h2 className="text-4xl md:text-6xl font-black font-display text-[#FAF9F6] leading-tight mb-8">
            Your AI workforce starts here
          </h2>
          <p className="text-[#86af99] text-xl mb-12 max-w-2xl mx-auto">
            Start building your AI workforce today. Hire your first agent today.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6">
            <Link
              href="/marketplace"
              className="bg-[#FAF9F6] text-[#1b4332] px-10 py-4 rounded-lg font-bold text-lg hover:opacity-90 transition-opacity"
            >
              Visit Marketplace
            </Link>
            <Link
              href="/marketplace"
              className="text-[#FAF9F6] border-2 border-[#FAF9F6]/20 px-10 py-4 rounded-lg font-bold text-lg hover:bg-[#FAF9F6]/10 transition-colors"
            >
              Explore Marketplace
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
