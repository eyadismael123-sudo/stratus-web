import Link from "next/link";
import type { ReactNode } from "react";

const PROTOCOL_STEPS = [
  {
    number: "01",
    title: "Browse the marketplace",
    description:
      "Discover pre-trained AI agents specialized in regional functions—from LinkedIn posting to car market intelligence.",
  },
  {
    number: "02",
    title: "Hire your agent in minutes",
    description:
      "Simple onboarding. No complex APIs or coding required. Deploy your workforce with a single click and define their operational hours.",
  },
  {
    number: "03",
    title: "Watch your team work",
    description:
      "Monitor progress through your centralized dashboard. Your agents report, learn, and adapt to your business needs in real-time.",
  },
];

const FOUNDATIONS = [
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Arabic arch / dome — MENA silhouette */}
        <path d="M4 28 C4 28 8 10 16 10 C24 10 28 28 28 28" stroke="#012d1d" strokeWidth="2" strokeLinecap="round" fill="none"/>
        <path d="M8 28 C8 28 10 16 16 16 C22 16 24 28 24 28" stroke="#012d1d" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.4"/>
        <line x1="2" y1="28" x2="30" y2="28" stroke="#012d1d" strokeWidth="2" strokeLinecap="round"/>
        <circle cx="16" cy="7" r="2" fill="#012d1d"/>
      </svg>
    ),
    title: "Made for this market",
    description:
      "Built in Dubai, for the way business works here — not adapted from somewhere else.",
  },
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="10" cy="13" r="5" stroke="#012d1d" strokeWidth="2" fill="none"/>
        <circle cx="22" cy="13" r="5" stroke="#012d1d" strokeWidth="2" fill="none"/>
        <path d="M15 13 L17 13" stroke="#012d1d" strokeWidth="2" strokeLinecap="round"/>
        <path d="M4 26 C4 21.6 6.7 18 10 18" stroke="#012d1d" strokeWidth="2" strokeLinecap="round" fill="none"/>
        <path d="M22 18 C25.3 18 28 21.6 28 26" stroke="#012d1d" strokeWidth="2" strokeLinecap="round" fill="none"/>
        <path d="M10 18 C10 22 14 24 16 24 C18 24 22 22 22 18" stroke="#012d1d" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.4"/>
      </svg>
    ),
    title: "Hired, not installed",
    description:
      "Each agent has a job, a schedule, and a purpose. You manage them like people, not settings.",
  },
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="3" y="20" width="5" height="9" rx="1.5" fill="#012d1d" opacity="0.35"/>
        <rect x="11" y="14" width="5" height="15" rx="1.5" fill="#012d1d" opacity="0.6"/>
        <rect x="19" y="8" width="5" height="21" rx="1.5" fill="#012d1d"/>
        <path d="M2 6 L8 12 L14 9 L20 4 L28 8" stroke="#012d1d" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="2 2" opacity="0.4"/>
      </svg>
    ),
    title: "From $49 a month",
    description:
      "No setup fees, no annual commitments. Cancel whenever it stops making sense.",
  },
];

export default function VisionSection() {
  return (
    <>
      {/* Protocol Steps */}
      <section className="py-32 px-8 bg-[#EFEEEB]">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-sm uppercase tracking-widest font-black text-[#012d1d]/40 mb-16">
            The Stratus Protocol
          </h2>
          <div className="grid md:grid-cols-3 gap-16">
            {PROTOCOL_STEPS.map((step) => (
              <div key={step.number} className="group">
                <div className="text-8xl font-black font-display text-[#c1c8c2] opacity-20 group-hover:text-[#012d1d] group-hover:opacity-100 transition-all duration-500 mb-8">
                  {step.number}
                </div>
                <h4 className="text-2xl font-black font-display mb-4 text-[#1a1c1a]">
                  {step.title}
                </h4>
                <p className="text-[#414844] leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Foundations / Values */}
      <section className="py-16 px-8 bg-[#FAF9F6]">
        <div className="max-w-7xl mx-auto grid md:grid-cols-3 gap-4">
          {FOUNDATIONS.map((item) => (
            <div
              key={item.title}
              className="bg-white p-8 rounded-xl flex flex-col items-start"
              style={{ boxShadow: "0 12px 32px rgba(27,67,50,0.04)" }}
            >
              <span className="mb-4 flex items-center justify-center w-12 h-12 rounded-xl" style={{ background: "#F0F7F4" }}>{item.icon}</span>
              <h5 className="text-lg font-black font-display mb-2 text-[#1a1c1a]">
                {item.title}
              </h5>
              <p className="text-sm text-[#414844] leading-relaxed">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-8 mb-32 rounded-3xl bg-[#1b4332] py-24 px-8 text-center relative overflow-hidden">
        {/* Dot grid fading left → right */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="cta-dots" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="1" fill="#AEEECB" opacity="0.35" />
            </pattern>
            <linearGradient id="cta-dot-fade" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#1b4332" stopOpacity="0" />
              <stop offset="55%" stopColor="#1b4332" stopOpacity="1" />
              <stop offset="100%" stopColor="#1b4332" stopOpacity="1" />
            </linearGradient>
          </defs>
          <rect width="100%" height="100%" fill="url(#cta-dots)" />
          <rect width="100%" height="100%" fill="url(#cta-dot-fade)" />
        </svg>
        <div
          className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(circle at center, #2D6A4F 0%, transparent 70%)",
          }}
        />
        <div className="relative z-10 max-w-3xl mx-auto">
          <h2 className="text-4xl md:text-6xl font-black font-display text-[#FAF9F6] leading-tight mb-8">
            Your AI workforce starts here
          </h2>
          <p className="text-[#86af99] text-xl mb-12 max-w-2xl mx-auto">
            Start building your AI workforce today. Hire your first agent today.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6">
            <Link
              href="/marketplace"
              className="bg-[#FAF9F6] text-[#1b4332] px-10 py-4 rounded-lg font-bold text-lg hover:opacity-90 transition-opacity"
            >
              Visit Marketplace
            </Link>
            <Link
              href="/marketplace"
              className="text-[#FAF9F6] border-2 border-[#FAF9F6]/20 px-10 py-4 rounded-lg font-bold text-lg hover:bg-[#FAF9F6]/10 transition-colors"
            >
              Explore Marketplace
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
