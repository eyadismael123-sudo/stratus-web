"use client";

import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";

const AGENTS = [
  {
    name: "Frame",
    role: "LinkedIn Post Agent",
    price: "$99",
    for: "Founders & executives",
    stat: { value: "3x", label: "more LinkedIn reach" },
    features: [
      "Daily post drafts in your voice",
      "Morning industry briefings",
      "One-click LinkedIn pre-fill",
    ],
    color: "#1B4332",
    bg: "#E8F5EF",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <rect width="48" height="48" rx="12" fill="#1B4332" />
        <rect x="10" y="14" width="28" height="4" rx="2" fill="white" opacity="0.9" />
        <rect x="10" y="22" width="20" height="3" rx="1.5" fill="white" opacity="0.5" />
        <rect x="10" y="29" width="24" height="3" rx="1.5" fill="white" opacity="0.5" />
        <circle cx="38" cy="36" r="6" fill="#AEEECB" />
        <path d="M35.5 36l1.5 1.5 3-3" stroke="#1B4332" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    name: "Flash",
    role: "Car Reseller Intel",
    price: "$149",
    for: "Car dealers & resellers",
    stat: { value: "4+", label: "leads found daily" },
    features: [
      "Scans 1,000s of listings overnight",
      "Flags underpriced cars before rivals",
      "Direct WhatsApp alert on deals",
    ],
    color: "#7C3F00",
    bg: "#FFF3E0",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <rect width="48" height="48" rx="12" fill="#7C3F00" />
        <path d="M10 30 L16 22 L22 24 L28 18 L38 26" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
        <circle cx="38" cy="26" r="3" fill="#FFD97D" />
        <rect x="10" y="32" width="28" height="2" rx="1" fill="white" opacity="0.2" />
        <path d="M24 14 L26 18 L30 18 L27 21 L28 25 L24 22.5 L20 25 L21 21 L18 18 L22 18 Z" fill="#FFD97D" opacity="0.8" />
      </svg>
    ),
  },
  {
    name: "Focus",
    role: "Property Market Briefing",
    price: "$99",
    for: "Real estate agents & investors",
    stat: { value: "12", label: "market signals/day" },
    features: [
      "Daily Dubai off-plan updates",
      "Price movement alerts by area",
      "Competitive listing analysis",
    ],
    color: "#012d1d",
    bg: "#E6F4EF",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <rect width="48" height="48" rx="12" fill="#012d1d" />
        <rect x="12" y="20" width="10" height="14" rx="2" fill="white" opacity="0.4" />
        <rect x="25" y="14" width="10" height="20" rx="2" fill="white" opacity="0.7" />
        <rect x="19" y="26" width="5" height="8" rx="1" fill="#AEEECB" />
        <path d="M10 34 L38 34" stroke="white" strokeWidth="1.5" opacity="0.3" />
      </svg>
    ),
  },
  {
    name: "Develop",
    role: "Doctor Morning Briefing",
    price: "$49",
    for: "Doctors & medical professionals",
    stat: { value: "45 min", label: "saved each morning" },
    features: [
      "Patient context before rounds",
      "Clinical news digest daily",
      "Appointment prep summary",
    ],
    color: "#1a3a5c",
    bg: "#E8F0FB",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <rect width="48" height="48" rx="12" fill="#1a3a5c" />
        <circle cx="24" cy="20" r="7" stroke="white" strokeWidth="2" opacity="0.8" />
        <path d="M24 17 L24 23 M21 20 L27 20" stroke="white" strokeWidth="2" strokeLinecap="round" />
        <path d="M14 36 C14 31 34 31 34 36" stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
        <circle cx="36" cy="12" r="4" fill="#93C5FD" />
        <path d="M34.5 12 L36 13.5 L38 11" stroke="#1a3a5c" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    name: "Shutter",
    role: "AI Receptionist",
    price: "$199",
    for: "Clinics, agencies & shops",
    stat: { value: "24/7", label: "always on, never tired" },
    features: [
      "Answers queries in Arabic & English",
      "Books appointments automatically",
      "Follow-up reminders on autopilot",
    ],
    color: "#3B1F6E",
    bg: "#EEE8FB",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <rect width="48" height="48" rx="12" fill="#3B1F6E" />
        <rect x="12" y="14" width="24" height="20" rx="4" stroke="white" strokeWidth="2" opacity="0.8" />
        <circle cx="24" cy="24" r="4" fill="white" opacity="0.9" />
        <circle cx="24" cy="24" r="2" fill="#C4B5FD" />
        <path d="M18 34 L18 38 M30 34 L30 38" stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
        <circle cx="36" cy="16" r="4" fill="#A78BFA" />
        <path d="M35 16 Q36 14.5 37 16" stroke="white" strokeWidth="1.2" strokeLinecap="round" fill="none" />
        <circle cx="36" cy="17.5" r="0.7" fill="white" />
      </svg>
    ),
  },
];

export default function PricingCards() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      setIndex((i) => (i + 1) % AGENTS.length);
    }, 2600);
    return () => clearInterval(t);
  }, []);

  const agent = AGENTS[index];

  return (
    <section className="max-w-7xl mx-auto px-8 pb-32">
      <div>
      <div
        className="pricing-card max-w-lg mx-auto rounded-2xl overflow-hidden relative"
        style={{ boxShadow: "0 30px 80px -12px rgba(26,28,26,0.10)" }}
      >
        {/* Background: concentric arcs from bottom-center */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          preserveAspectRatio="xMidYMax slice"
          viewBox="0 0 480 700"
          aria-hidden="true"
        >
          {[120, 220, 320, 420, 520, 620].map((r) => (
            <circle key={r} cx="240" cy="700" r={r} fill="none" stroke="#012d1d" strokeOpacity="0.07" strokeWidth="1" />
          ))}
        </svg>

        {/* Slot window */}
        <div
          className="relative px-12 pt-12 pb-10"
          style={{ borderBottom: "1px solid #F0EFEC" }}
        >
          {/* Reel lines */}
          <div
            className="absolute left-0 right-0 pointer-events-none"
            style={{ top: "72px", height: "1px", background: "rgba(1,45,29,0.06)" }}
          />
          <div
            className="absolute left-0 right-0 pointer-events-none"
            style={{ bottom: "72px", height: "1px", background: "rgba(1,45,29,0.06)" }}
          />

          <div className="overflow-hidden relative" style={{ height: "120px" }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={index}
                className="text-center absolute inset-0 flex flex-col justify-center"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -24 }}
                transition={{ duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
              >
                <p className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: "#1b4332", opacity: 0.45 }}>
                  {agent.name} · {agent.role}
                </p>
                <div className="flex items-baseline justify-center gap-2">
                  <span
                    className="font-display font-black leading-none"
                    style={{ fontSize: "80px", color: "#012d1d", letterSpacing: "-0.04em" }}
                  >
                    {agent.price}
                  </span>
                  <span className="text-base font-medium" style={{ color: "#8A8A8A" }}>
                    /mo
                  </span>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Dot indicators */}
          <div className="flex items-center justify-center gap-2 mt-6">
            {AGENTS.map((_, i) => (
              <button
                key={i}
                onClick={() => setIndex(i)}
                className="rounded-full transition-all duration-300"
                style={{
                  width: i === index ? "20px" : "6px",
                  height: "6px",
                  background: i === index ? "#012d1d" : "#D4D2CE",
                }}
              />
            ))}
          </div>
        </div>

        {/* Agent detail */}
        <div
          key={`detail-${index}`}
          className="px-12 pt-8 pb-10"
          style={{ animation: "slot-up 0.45s cubic-bezier(0.22,1,0.36,1) both" }}
        >
          {/* Icon + stat row */}
          <div className="flex items-center justify-between mb-6">
            <div>{agent.icon}</div>
            <div
              className="text-right px-4 py-3 rounded-xl"
              style={{ background: agent.bg }}
            >
              <p className="text-[22px] font-black leading-none" style={{ color: agent.color }}>
                {agent.stat.value}
              </p>
              <p className="text-[10px] font-bold uppercase tracking-wider mt-0.5" style={{ color: agent.color, opacity: 0.6 }}>
                {agent.stat.label}
              </p>
            </div>
          </div>

          {/* For who */}
          <p className="text-[11px] font-bold uppercase tracking-widest mb-4" style={{ color: "#8A8A8A" }}>
            Built for · {agent.for}
          </p>

          {/* Features */}
          <ul className="space-y-2 mb-8">
            {agent.features.map((f) => (
              <li key={f} className="flex items-start gap-3">
                <span
                  className="mt-[3px] w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: agent.bg }}
                >
                  <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                    <path d="M1.5 4L3 5.5L6.5 2" stroke={agent.color} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                <span className="text-[13px]" style={{ color: "#414844" }}>{f}</span>
              </li>
            ))}
          </ul>

          <p className="text-center text-[12px] mb-5" style={{ color: "#8A8A8A" }}>
            No setup fee. No contract. Cancel anytime.
          </p>
          <Link
            href="/agents/linkedin-post-agent"
            className="block w-full text-center text-white py-4 rounded-xl font-bold text-[15px] transition-colors"
            style={{ background: agent.color }}
          >
            Hire {agent.name} →
          </Link>
        </div>
      </div>

      <style>{`
        @keyframes slot-up {
          from { transform: translateY(40px); opacity: 0; }
          to   { transform: translateY(0);   opacity: 1; }
        }
        .pricing-card {
          background-color: #ffffff;
          background-image: radial-gradient(rgba(1,45,29,0.1) 1px, transparent 1px);
          background-size: 20px 20px;
        }
      `}</style>
      </div>
    </section>
  );
}
