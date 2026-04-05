"use client";

import { useEffect, useRef, useState } from "react";

const FOUNDERS = [
  {
    initials: "EI",
    name: "Eyad Ismael",
    role: "Co-Founder & CEO",
    university: "Mohammed Bin Rashid University",
    location: "Dubai, UAE",
    bio: "First-year medical student building the AI workforce for the businesses shaping MENA. Stratus started with one client — his father.",
    locationIcon: (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <circle cx="6" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.2" fill="none"/>
        <path d="M6 1C3.79 1 2 2.79 2 5c0 3.25 4 6 4 6s4-2.75 4-6c0-2.21-1.79-4-4-4z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
      </svg>
    ),
  },
  {
    initials: "ME",
    name: "Malek Elsawy",
    role: "Co-Founder",
    university: "Charité Medizinuniversität Berlin",
    location: "Berlin, Germany",
    bio: "Medical student at one of Europe's oldest universities. Shapes the vision, the product, and the thinking behind Stratus from across the continent.",
    locationIcon: (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <circle cx="6" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.2" fill="none"/>
        <path d="M6 1C3.79 1 2 2.79 2 5c0 3.25 4 6 4 6s4-2.75 4-6c0-2.21-1.79-4-4-4z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
      </svg>
    ),
  },
];

export default function FoundersSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const [lit, setLit] = useState(false);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    // rootMargin "-75% 0px 0px 0px" shrinks the detection zone to the bottom 25% of the viewport
    const enterObserver = new IntersectionObserver(
      ([entry]) => setLit(entry.isIntersecting),
      { rootMargin: "-75% 0px 0px 0px", threshold: 0 }
    );
    enterObserver.observe(el);
    return () => enterObserver.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="py-32 px-8 bg-[#FAF9F6] relative overflow-hidden">
      {/* Faint background text */}
      <span
        className="absolute bottom-0 right-0 font-display font-black select-none pointer-events-none leading-none"
        style={{
          fontSize: "clamp(80px, 14vw, 180px)",
          color: "#d0d0d0",
          opacity: lit ? 0.35 : 0.18,
          lineHeight: 0.85,
          transition: "opacity 0.4s ease, color 0.4s ease",
        }}
      >
        Founders
      </span>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-20">
          <p className="text-[11px] font-bold uppercase tracking-widest mb-4" style={{ color: "#1b4332", opacity: 0.5 }}>
            The team behind Stratus
          </p>
          <h2 className="text-4xl md:text-6xl font-black font-display tracking-tighter" style={{ color: "#012d1d" }}>
            Two med students.<br />One mission.
          </h2>
        </div>

        {/* Founder cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {FOUNDERS.map((founder) => (
            <div
              key={founder.name}
              className="group rounded-2xl p-8 md:p-10 flex flex-col gap-6 transition-all duration-300"
              style={{
                background: "#FFFFFF",
                border: "1px solid #E8E6E1",
                boxShadow: "0 4px 20px rgba(27,67,50,0.04)",
              }}
            >
              {/* Avatar + badge row */}
              <div className="flex items-start justify-between">
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center text-[17px] font-black flex-shrink-0"
                  style={{ background: "#012d1d", color: "#c1ecd4" }}
                >
                  {founder.initials}
                </div>
              </div>

              {/* Name */}
              <div>
                <h3
                  className="text-3xl md:text-4xl font-black font-display tracking-tight leading-none"
                  style={{ color: "#012d1d" }}
                >
                  {founder.name}
                </h3>
              </div>

              {/* Bio */}
              <p className="text-base leading-relaxed" style={{ color: "#414844" }}>
                {founder.bio}
              </p>

              {/* Metadata */}
              <div
                className="flex flex-col gap-2 pt-5 mt-auto"
                style={{ borderTop: "1px solid #E8E6E1" }}
              >
                <div className="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <rect x="1" y="2" width="12" height="10" rx="1.5" stroke="#1b4332" strokeWidth="1.2" strokeOpacity="0.5" fill="none"/>
                    <path d="M1 5h12" stroke="#1b4332" strokeWidth="1.2" strokeOpacity="0.5"/>
                    <path d="M5 2V1M9 2V1" stroke="#1b4332" strokeWidth="1.2" strokeLinecap="round" strokeOpacity="0.5"/>
                  </svg>
                  <span className="text-[12px] font-medium" style={{ color: "#414844", opacity: 0.7 }}>
                    {founder.university}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span style={{ color: "#1b4332", opacity: 0.5 }}>{founder.locationIcon}</span>
                  <span className="text-[12px] font-medium" style={{ color: "#414844", opacity: 0.7 }}>
                    {founder.location}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer callout */}
        <div className="mt-10 flex items-center gap-4">
          <div className="flex -space-x-2">
            {["EI", "ME"].map((i) => (
              <div
                key={i}
                className="w-7 h-7 rounded-full border-2 border-white flex items-center justify-center text-[9px] font-black"
                style={{ background: "#012d1d", color: "#c1ecd4" }}
              >
                {i}
              </div>
            ))}
          </div>
          <p className="text-[13px]" style={{ color: "#414844", opacity: 0.6 }}>
            Building from Dubai and Berlin — two cities, one product.
          </p>
        </div>
      </div>
    </section>
  );
}
