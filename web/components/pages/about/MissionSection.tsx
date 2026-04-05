const STATS = [
  { value: "5", label: "agents live", sub: "and growing" },
  { value: "1", label: "region", sub: "built for MENA" },
  { value: "24/7", label: "uptime", sub: "no sick days" },
];

export default function MissionSection() {
  return (
    <section className="px-8 py-32 bg-[#EFEEEB]">
      <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-24 items-start">
        <div className="relative">
          <span className="text-9xl font-display text-[#1b4332] opacity-5 absolute -top-16 -left-8 select-none pointer-events-none">
            &ldquo;
          </span>
          <h2 className="text-4xl md:text-5xl font-black font-display leading-tight text-[#012d1d]">
            Every serious business in this region deserves a team that never sleeps.
          </h2>

          {/* Stat strip */}
          <div className="flex items-start gap-10 mt-14 pt-10" style={{ borderTop: "1px solid rgba(1,45,29,0.12)" }}>
            {STATS.map((s) => (
              <div key={s.label}>
                <p
                  className="text-4xl font-black font-display leading-none"
                  style={{ color: "#012d1d" }}
                >
                  {s.value}
                </p>
                <p className="text-[12px] font-bold uppercase tracking-wider mt-2" style={{ color: "#012d1d", opacity: 0.5 }}>
                  {s.label}
                </p>
                <p className="text-[11px] mt-0.5" style={{ color: "#414844", opacity: 0.6 }}>
                  {s.sub}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-8">
          <p className="text-xl font-body leading-relaxed text-[#414844]">
            Stratus was built in Dubai, for the way business actually works here.
            Not the generic version — the real one, with WhatsApp threads,
            bilingual clients, and decisions made at midnight. We build agents
            that understand the context, not just the task.
          </p>
          <p className="text-xl font-body leading-relaxed text-[#414844]">
            We started with one agent for one client. That's still the spirit.
            Build something specific, build it well, and put it to work for the
            businesses quietly shaping this part of the world.
          </p>

          {/* Inline callout */}
          <div
            className="rounded-xl p-6 mt-4"
            style={{
              background: "#012d1d",
              color: "#c1ecd4",
            }}
          >
            <p className="text-[13px] font-bold uppercase tracking-widest mb-2" style={{ opacity: 0.5 }}>
              Starting at
            </p>
            <p className="text-4xl font-black font-display leading-none">
              $49
              <span className="text-lg font-body font-medium ml-1" style={{ opacity: 0.6 }}>/month</span>
            </p>
            <p className="text-[13px] mt-2" style={{ opacity: 0.6 }}>
              Per agent. No setup fee. Cancel anytime.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
