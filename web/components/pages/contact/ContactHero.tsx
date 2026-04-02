export default function ContactHero() {
  return (
    <section className="relative pt-24 pb-20 px-8 max-w-7xl mx-auto overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
        <div className="z-10">
          <h1 className="font-display text-8xl md:text-9xl font-extrabold text-[#1a1c1a] tracking-tighter leading-[0.9] mb-8">
            Let&apos;s talk
          </h1>
          <p className="text-2xl text-[#414844] leading-relaxed max-w-lg">
            We&apos;re building for MENA. Tell us what you need. Our team is
            ready to welcome you into the Stratus ecosystem.
          </p>
        </div>
        <div className="relative">
          <div
            className="w-full aspect-[4/5] rounded-xl overflow-hidden bg-[#EFEEEB]"
            style={{ boxShadow: "0 8px 32px -4px rgba(1,45,29,0.04)" }}
          />
        </div>
      </div>
    </section>
  );
}
