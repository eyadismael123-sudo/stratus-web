import Link from "next/link";

const FEATURES = [
  "Morning briefings",
  "LinkedIn post generation",
  "2 post variations",
  "Refinement buttons",
  "Telegram delivery",
  "Voice profile setup",
];

export default function PricingCards() {
  return (
    <section className="max-w-7xl mx-auto px-8 pb-32">
      <div
        className="max-w-3xl mx-auto bg-white rounded-xl p-12 relative overflow-hidden"
        style={{ boxShadow: "0 30px 60px -12px rgba(26,28,26,0.05)" }}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-[#1b4332]/5 rounded-full -mr-16 -mt-16" />

        <div className="text-center mb-12">
          <div className="inline-flex items-baseline mb-2">
            <span className="font-display text-8xl font-extrabold text-[#012d1d]">
              $50
            </span>
            <span className="text-[#526259] font-medium text-lg ml-2">
              /month per agent
            </span>
          </div>
          <p className="text-[#414844] font-medium">
            Full access to your chosen AI workforce member.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-x-12 gap-y-6 mb-12 border-t border-[#c1c8c2]/20 pt-12">
          {FEATURES.map((f) => (
            <div key={f} className="flex items-start gap-3">
              <span className="text-[#1b4332] flex-shrink-0">✓</span>
              <span className="text-[#1a1c1a]">{f}</span>
            </div>
          ))}
        </div>

        <Link
          href="/agents/linkedin-post-agent"
          className="block w-full text-center bg-[#1b4332] text-white py-5 rounded-lg font-display font-bold text-lg hover:bg-[#012d1d] transition-colors"
        >
          Hire Your First Agent
        </Link>
        <p className="text-center text-xs text-[#414844]/60 mt-6 uppercase tracking-widest">
          Secure checkout via Stripe
        </p>
      </div>
    </section>
  );
}
