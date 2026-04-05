const FLOATING_PILLS = [
  {
    initials: "Fr",
    name: "Frame",
    task: "Drafting LinkedIn post",
    status: "Active",
    floatAnimation: "pill-float-a",
    style: { top: "22%", left: "6%", animationDelay: "0s" },
  },
  {
    initials: "Sc",
    name: "Scout",
    task: "4 listings found",
    status: "Done",
    floatAnimation: "pill-float-b",
    style: { bottom: "28%", left: "5%", animationDelay: "0.5s" },
  },
  {
    initials: "Br",
    name: "Brief",
    task: "Patient brief ready",
    status: "Done",
    floatAnimation: "pill-float-c",
    style: { bottom: "22%", right: "8%", animationDelay: "1.1s" },
  },
];

export default function AboutHero() {
  return (
    <section className="min-h-[716px] flex items-center justify-center px-8 text-center bg-[#FAF9F6] relative overflow-hidden">
      {/* Dot-grid background */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="hero-dots" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="#1b4332" opacity="0.12" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#hero-dots)" />
        <radialGradient id="dot-fade" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FAF9F6" stopOpacity="1" />
          <stop offset="60%" stopColor="#FAF9F6" stopOpacity="0" />
        </radialGradient>
        <rect width="100%" height="100%" fill="url(#dot-fade)" />
      </svg>

      {/* Decorative arches */}
      <svg
        className="absolute bottom-0 left-1/2 pointer-events-none opacity-[0.09]"
        style={{ transform: "translateX(-50%)", width: "900px", height: "400px" }}
        viewBox="0 0 900 400"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path d="M0 400 C0 400 150 0 450 0 C750 0 900 400 900 400" stroke="#012d1d" strokeWidth="3" fill="none"/>
        <path d="M60 400 C60 400 200 60 450 60 C700 60 840 400 840 400" stroke="#012d1d" strokeWidth="2" fill="none"/>
        <path d="M120 400 C120 400 250 120 450 120 C650 120 780 400 780 400" stroke="#012d1d" strokeWidth="1.5" fill="none"/>
      </svg>

      {/* Floating agent pills — desktop only */}
      {FLOATING_PILLS.map((pill) => (
        <div
          key={pill.name}
          className="absolute hidden lg:flex items-center gap-3 px-4 py-3 rounded-2xl pointer-events-none"
          style={{
            ...pill.style,
            background: "rgba(255,255,255,0.9)",
            border: "1px solid #E8E6E1",
            boxShadow: "0 8px 24px rgba(27,67,50,0.08)",
            backdropFilter: "blur(12px)",
            animation: `${pill.floatAnimation} 5s ease-in-out ${pill.style.animationDelay} infinite`,
          }}
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-black flex-shrink-0 text-white"
            style={{ background: "#1B4332" }}
          >
            {pill.initials}
          </div>
          <div className="text-left">
            <p className="text-[12px] font-bold leading-none" style={{ color: "#1a1c1a" }}>
              {pill.name}
            </p>
            <p className="text-[10px] mt-0.5" style={{ color: "#8A8A8A" }}>
              {pill.task}
            </p>
          </div>
          <div className="flex items-center gap-1.5 ml-1">
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{
                background: pill.status === "Active" ? "#10b981" : "#86efac",
                animation: pill.status === "Active" ? "hero-dot-pulse 2s ease-in-out infinite" : "none",
              }}
            />
            <span
              className="text-[9px] font-bold uppercase tracking-wide"
              style={{ color: pill.status === "Active" ? "#10b981" : "#8A8A8A" }}
            >
              {pill.status}
            </span>
          </div>
        </div>
      ))}

      <div className="relative z-10 max-w-5xl">
        <p className="uppercase tracking-widest text-[#1b4332]/60 font-bold text-sm mb-8">
          Our Heritage
        </p>
        <h1 className="text-5xl md:text-8xl font-black font-display text-[#1a1c1a] tracking-tighter leading-none mb-12">
          Built for the businesses <br className="hidden md:block" /> shaping
          MENA
        </h1>

        {/* Inline stat strip */}
        <div className="flex items-center justify-center gap-8 md:gap-16 mb-12 flex-wrap">
          {[
            { value: "5", label: "AI agents" },
            { value: "MENA", label: "First & only" },
            { value: "$50", label: "Per agent / mo" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-2xl md:text-3xl font-black font-display" style={{ color: "#012d1d" }}>
                {stat.value}
              </p>
              <p className="text-[11px] uppercase tracking-widest font-bold mt-1" style={{ color: "#1b4332", opacity: 0.45 }}>
                {stat.label}
              </p>
            </div>
          ))}
        </div>

        {/* Scroll indicator */}
        <div className="flex flex-col items-center gap-2 opacity-30">
          <div className="w-px h-12 bg-[#012d1d] relative overflow-hidden rounded-full">
            <div
              className="absolute top-0 left-0 w-full bg-[#1b4332] rounded-full"
              style={{ height: "40%", animation: "hero-scroll-line 1.8s ease-in-out infinite" }}
            />
          </div>
        </div>
      </div>

      <style>{`
        @keyframes hero-scroll-line {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(280%); }
        }
        @keyframes pill-float-a {
          0%   { transform: translate(0px, 0px) rotate(0deg); }
          25%  { transform: translate(6px, -14px) rotate(1deg); }
          50%  { transform: translate(-4px, -22px) rotate(-1.5deg); }
          75%  { transform: translate(-10px, -10px) rotate(0.5deg); }
          100% { transform: translate(0px, 0px) rotate(0deg); }
        }
        @keyframes pill-float-b {
          0%   { transform: translate(0px, 0px) rotate(0deg); }
          30%  { transform: translate(-8px, -18px) rotate(-1deg); }
          60%  { transform: translate(6px, -26px) rotate(1.5deg); }
          80%  { transform: translate(10px, -8px) rotate(-0.5deg); }
          100% { transform: translate(0px, 0px) rotate(0deg); }
        }
        @keyframes pill-float-c {
          0%   { transform: translate(0px, 0px) rotate(0deg); }
          20%  { transform: translate(-6px, -12px) rotate(1deg); }
          50%  { transform: translate(8px, -20px) rotate(-1deg); }
          75%  { transform: translate(4px, -8px) rotate(1.5deg); }
          100% { transform: translate(0px, 0px) rotate(0deg); }
        }
        @keyframes hero-dot-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </section>
  );
}
