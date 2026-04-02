export default function MissionSection() {
  return (
    <section className="px-8 py-32 bg-[#EFEEEB]">
      <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-24 items-start">
        <div className="relative">
          <span className="text-9xl font-display text-[#1b4332] opacity-5 absolute -top-16 -left-8 select-none pointer-events-none">
            &ldquo;
          </span>
          <h2 className="text-4xl md:text-5xl font-black font-display leading-tight text-[#012d1d]">
            We believe every MENA business deserves an AI workforce — not just
            the ones with enterprise budgets.
          </h2>
        </div>
        <div className="space-y-8">
          <p className="text-xl font-body leading-relaxed text-[#414844]">
            Since our inception, Stratus has been more than just a technology
            provider. We are an architect for the new regional economy. While
            global tech giants focus on general-purpose tools, we build digital
            labor specifically designed for the unique dynamics of the Middle
            East and North Africa.
          </p>
          <p className="text-xl font-body leading-relaxed text-[#414844]">
            Our vision is a democratized landscape where a small consultancy in
            Riyadh or a bustling creative agency in Dubai has access to the same
            operational power as a Fortune 500 entity, powered by specialized AI
            agents.
          </p>
        </div>
      </div>
    </section>
  );
}
