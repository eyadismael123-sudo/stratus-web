const LOGOS = [
  { name: "AbbVie",  label: "AbbVie" },
  { name: "Emaar",   label: "Emaar" },
  { name: "Aldar",   label: "Aldar" },
  { name: "Aramex",  label: "Aramex" },
];

export function LogoStrip() {
  return (
    <div
      className="border-t border-b px-6 md:px-12 py-12"
      style={{ borderColor: "rgba(193,200,194,0.15)", background: "#FAF9F6" }}
    >
      <div className="max-w-[1440px] mx-auto">
        <p
          className="text-center text-[10px] font-bold uppercase tracking-[0.2em] mb-10"
          style={{ color: "rgba(26,28,26,0.3)" }}
        >
          Trusted by fast-growing MENA enterprises
        </p>
        <div className="flex flex-wrap justify-center gap-12 md:gap-20 items-center">
          {LOGOS.map(({ name, label }) => (
            <span
              key={name}
              className="font-display font-bold text-[22px] tracking-[-0.04em] whitespace-nowrap select-none opacity-25 hover:opacity-50 transition-opacity duration-300"
              style={{ color: "#1A1A1A", letterSpacing: "-0.04em" }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
