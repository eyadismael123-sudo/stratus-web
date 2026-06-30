const LOGOS = [
  "AbbVie", "Emaar", "Aldar", "Aramex", "Etisalat", "Majid Al Futtaim", "Chalhoub",
];

export function LogoStrip() {
  const loop = [...LOGOS, ...LOGOS];
  return (
    <div
      className="border-t border-b py-12 overflow-hidden"
      style={{ borderColor: "rgba(193,200,194,0.15)", background: "#CCDAD1" }}
    >
      <div className="max-w-[1440px] mx-auto px-6 md:px-12">
        <p
          className="text-center text-[10px] font-bold uppercase tracking-[0.2em] mb-10"
          style={{ color: "rgba(26,28,26,0.3)" }}
        >
          Trusted by fast-growing MENA enterprises
        </p>
      </div>

      <div
        className="relative overflow-hidden"
        style={{
          maskImage: "linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent)",
          WebkitMaskImage: "linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent)",
        }}
      >
        <div className="flex items-center gap-20 whitespace-nowrap logo-marquee">
          {loop.map((label, i) => (
            <span
              key={`${label}-${i}`}
              className="font-display font-bold text-[22px] tracking-[-0.04em] select-none opacity-30 hover:opacity-70 transition-opacity duration-300"
              style={{ color: "#2E4057", letterSpacing: "-0.04em" }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      <style>{`
        .logo-marquee {
          animation: logo-scroll 32s linear infinite;
          width: max-content;
        }
        .logo-marquee:hover {
          animation-play-state: paused;
        }
        @keyframes logo-scroll {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
