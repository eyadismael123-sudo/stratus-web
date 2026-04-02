const LOGOS = [
  { name: "AbbVie", type: "pharma" },
  { name: "Emaar", type: "realestate" },
  { name: "Aldar", type: "proptech" },
  { name: "Aramex", type: "logistics" },
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
        <div className="flex flex-wrap justify-center gap-12 md:gap-20 items-center opacity-30">
          {LOGOS.map(({ name }) => (
            <span
              key={name}
              className="font-display font-bold text-[18px] tracking-[-0.02em] whitespace-nowrap"
              style={{ color: "#1A1A1A" }}
            >
              {name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
