const IDEAL_FOR = [
  "Founders scaling in MENA",
  "Executives at fast-growing firms",
  "Sales leaders building trust",
  "Personal brands globally",
];

const STEPS = [
  {
    n: "1",
    title: "Onboard via Telegram",
    description: "Quick 5-minute setup to connect your profile and preferences.",
  },
  {
    n: "2",
    title: "Voice Alignment",
    description: "The agent analyzes your past writing to mirror your tone perfectly.",
  },
  {
    n: "3",
    title: "Morning Ideas",
    description: "Receive 3 curated ideas every morning at 8:00 AM AST.",
  },
  {
    n: "4",
    title: "One-Click Post",
    description: "Pick your favorite idea, refine if needed, and hit publish.",
  },
];

export default function HowItWorks() {
  return (
    <section className="px-8 max-w-7xl mx-auto mb-32">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-24">
        {/* Ideal For */}
        <div>
          <h2 className="text-sm font-body uppercase tracking-[0.3em] text-[#414844] mb-12 border-b border-[#c1c8c2]/20 pb-4">
            Ideal For
          </h2>
          <ul className="space-y-6">
            {IDEAL_FOR.map((item, i) => (
              <li key={item} className="flex items-center gap-6 group">
                <span className="text-4xl font-display font-extrabold text-[#012d1d]/10 group-hover:text-[#012d1d] transition-colors tabular-nums">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="text-xl font-medium text-[#1a1c1a]">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Onboarding Flow */}
        <div>
          <h2 className="text-sm font-body uppercase tracking-[0.3em] text-[#414844] mb-12 border-b border-[#c1c8c2]/20 pb-4">
            Onboarding Flow
          </h2>
          <div className="space-y-12">
            {STEPS.map((step, i) => (
              <div key={step.n} className="flex gap-6">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full border border-[#012d1d] flex items-center justify-center text-xs font-bold text-[#012d1d] flex-shrink-0">
                    {step.n}
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className="flex-grow w-px bg-[#c1c8c2]/30 mt-2" />
                  )}
                </div>
                <div>
                  <h4 className="font-display font-bold text-[#012d1d] mb-2">{step.title}</h4>
                  <p className="text-[#414844] text-sm">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
