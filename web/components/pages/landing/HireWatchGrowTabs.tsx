"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import {
  Pencil,
  Zap,
  CreditCard,
  Radio,
  CircleDot,
  CalendarDays,
  Smartphone,
  TrendingUp,
  Users,
} from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

interface TabContent {
  num: string;
  label: string;
  headline: string;
  features: { icon: React.ReactNode; title: string; body: string }[];
  mockup: React.ReactNode;
}

function HireMockup() {
  return (
    <div
      className="rounded-[16px] p-6 min-h-[280px]"
      style={{
        background: "#FFFFFF",
        border: "1px solid #E8E6E1",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
      }}
    >
      <div
        className="rounded-[12px] p-5"
        style={{ background: "#FAF9F6", border: "1px solid #E8E6E1" }}
      >
        <div className="flex items-center gap-3 mb-4">
          <div
            className="w-11 h-11 rounded-[12px] flex items-center justify-center text-[14px] font-bold flex-shrink-0"
            style={{ background: "#1B4332", color: "#FAF9F6" }}
          >
            LP
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[15px] font-bold" style={{ color: "#1A1A1A" }}>
              LinkedIn Post Agent
            </div>
            <div className="text-[12px]" style={{ color: "#8A8A8A" }}>
              LinkedIn Ghostwriter
            </div>
          </div>
          <span
            className="text-[10px] font-bold tracking-[0.08em] uppercase px-2.5 py-1 rounded-full"
            style={{ color: "#FFFFFF", background: "#1B4332" }}
          >
            Live
          </span>
        </div>

        <p className="text-[13px] leading-relaxed mb-4" style={{ color: "#8A8A8A" }}>
          Writes thought leadership in your voice. Daily.
        </p>

        <div className="flex items-center justify-between">
          <span className="text-[14px] font-bold" style={{ color: "#4A4A4A" }}>
            $50/mo
          </span>
          <button
            className="text-[13px] font-bold text-white px-4 py-2 rounded-[8px] flex-shrink-0"
            style={{ background: "#1B4332" }}
          >
            Hire
          </button>
        </div>
      </div>
    </div>
  );
}

function WatchMockup() {
  const logs = [
    { time: "08:00:12", text: "Post ideas generated — 2 variations ready", ok: true },
    { time: "08:00:08", text: "Grok scan complete — 12 sources", ok: true },
    { time: "08:00:01", text: "Morning briefing started", ok: false },
  ];

  return (
    <div
      className="rounded-[16px] p-6 min-h-[280px]"
      style={{
        background: "#FFFFFF",
        border: "1px solid #E8E6E1",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
      }}
    >
      <div className="flex items-center gap-2.5 mb-5">
        <span className="status-dot-online" style={{ width: "7px", height: "7px" }} />
        <span className="text-[13px] font-bold" style={{ color: "#1A1A1A" }}>
          LinkedIn Post Agent
        </span>
        <span className="text-[11px] ml-auto" style={{ color: "#8A8A8A" }}>
          Online
        </span>
      </div>

      <div className="font-mono text-[11px] leading-[1.8]" style={{ color: "#8A8A8A" }}>
        {logs.map((l) => (
          <div key={l.time + l.text} className="flex gap-2.5">
            <span className="flex-shrink-0" style={{ color: "#E8E6E1" }}>
              {l.time}
            </span>
            <span style={{ color: l.ok ? "#1B4332" : "#8A8A8A" }}>{l.text}</span>
          </div>
        ))}
      </div>

      <div
        className="mt-5 pt-4 text-[11px]"
        style={{ borderTop: "1px solid #E8E6E1", color: "#8A8A8A" }}
      >
        Next run: Tomorrow 08:00 GST
      </div>
    </div>
  );
}

function GrowMockup() {
  return (
    <div
      className="rounded-[16px] p-6 min-h-[280px]"
      style={{
        background: "#FFFFFF",
        border: "1px solid #E8E6E1",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
      }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Smartphone size={14} color="#8A8A8A" />
        <span className="text-[12px] font-bold" style={{ color: "#8A8A8A" }}>
          Daily Team Report — 7:00 PM
        </span>
      </div>

      <div
        className="rounded-[10px] p-4"
        style={{ background: "#FAF9F6", border: "1px solid #E8E6E1" }}
      >
        <p className="text-[13px] leading-[1.7] mb-0" style={{ color: "#4A4A4A" }}>
          Today your team accomplished:
        </p>
        <ul className="text-[12px] leading-[1.8] mt-2 mb-3 list-none pl-0" style={{ color: "#8A8A8A" }}>
          <li className="flex gap-2">
            <span style={{ color: "#E8E6E1" }}>—</span>
            LinkedIn Agent: drafted 3 posts, 1 published, 847 impressions
          </li>
          <li className="flex gap-2">
            <span style={{ color: "#E8E6E1" }}>—</span>
            Hours saved: ~1.5
          </li>
        </ul>
        <p className="text-[11px]" style={{ color: "#8A8A8A" }}>
          Tomorrow: 2 scheduled posts at 9am
        </p>
      </div>
    </div>
  );
}

const TABS: TabContent[] = [
  {
    num: "01",
    label: "Hire",
    headline: "Meet your first\nAI employee.",
    features: [
      {
        icon: <Pencil size={18} />,
        title: "LinkedIn Post Agent",
        body: "Your AI ghostwriter. Scans trends, drafts posts in your voice, delivers via Telegram every morning.",
      },
      {
        icon: <Zap size={18} />,
        title: "Hire in minutes",
        body: "Connect your profile, set your voice, and your agent starts working tomorrow morning.",
      },
      {
        icon: <CreditCard size={18} />,
        title: "$50/month. No surprises.",
        body: "One agent, one price. No seat fees. No contracts. Cancel anytime.",
      },
    ],
    mockup: <HireMockup />,
  },
  {
    num: "02",
    label: "Watch",
    headline: "Your team is\nworking right now.",
    features: [
      {
        icon: <Radio size={18} />,
        title: "Live activity feed",
        body: "See exactly what your agent did, when, and why. Full task logs in real time.",
      },
      {
        icon: <CircleDot size={18} />,
        title: "Online/offline status",
        body: "Live status dot. Green when running, grey when paused, red if something needs attention.",
      },
      {
        icon: <CalendarDays size={18} />,
        title: "Schedule visibility",
        body: "See when your agent runs next. Pause, resume, or trigger manually at any time.",
      },
    ],
    mockup: <WatchMockup />,
  },
  {
    num: "03",
    label: "Grow",
    headline: "See what your team\naccomplished today.",
    features: [
      {
        icon: <Smartphone size={18} />,
        title: "Daily outcome receipts",
        body: "Every evening at 7pm, a Telegram summary of what your team accomplished. Real numbers, real proof.",
      },
      {
        icon: <TrendingUp size={18} />,
        title: "Output tracking",
        body: "Posts published, impressions earned, hours saved — your agent logs everything it produced.",
      },
      {
        icon: <Users size={18} />,
        title: "Your agents work better together",
        body: "Start with one. As you add more agents, they share intelligence and compound results.",
      },
    ],
    mockup: <GrowMockup />,
  },
];

export function HireWatchGrowTabs() {
  const [active, setActive] = useState(0);
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!headerRef.current) return;

    gsap.fromTo(
      headerRef.current,
      { opacity: 0, y: 30 },
      {
        opacity: 1,
        y: 0,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: {
          trigger: headerRef.current,
          start: "top 85%",
          once: true,
        },
      },
    );
  }, { scope: sectionRef });

  return (
    <section
      ref={sectionRef}
      id="how-it-works"
      className="py-[120px] px-6 md:px-10"
      style={{ background: "#FFFFFF" }}
    >
      <div className="max-w-[1440px] mx-auto">
        {/* Header */}
        <div ref={headerRef} className="text-center mb-16">
          <h2
            className="font-display font-bold tracking-[-0.04em] leading-tight mb-4"
            style={{ fontSize: "clamp(32px, 4vw, 48px)", color: "#1B4332" }}
          >
            The AI Workforce Platform
          </h2>
          <p className="text-[16px] max-w-sm mx-auto" style={{ color: "#8A8A8A" }}>
            Three steps. One system. Your business, fully staffed.
          </p>
        </div>

        {/* Pill tab nav */}
        <div className="flex justify-center mb-16">
          <div
            className="inline-flex p-1 rounded-[10px]"
            style={{ background: "#EFEEEB" }}
          >
            {TABS.map((tab, i) => (
              <button
                key={tab.label}
                onClick={() => setActive(i)}
                className="px-8 py-3 rounded-[8px] text-[14px] font-bold transition-all duration-200"
                style={
                  active === i
                    ? { background: "#FFFFFF", color: "#1B4332", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }
                    : { background: "transparent", color: "#8A8A8A" }
                }
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab panels */}
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-20 items-center max-w-[1100px] mx-auto"
          >
            {/* Left: text */}
            <div>
              <h3
                className="font-display font-bold tracking-[-0.02em] leading-[1.1] mb-8 whitespace-pre-line"
                style={{
                  fontSize: "clamp(28px, 3vw, 40px)",
                  color: "#1A1A1A",
                }}
              >
                {TABS[active].headline}
              </h3>
              <ul className="flex flex-col gap-6 list-none">
                {TABS[active].features.map((f) => (
                  <li key={f.title} className="flex gap-4 items-start">
                    <span
                      className="flex-shrink-0 mt-0.5"
                      style={{ color: "#1B4332" }}
                    >
                      {f.icon}
                    </span>
                    <div>
                      <div
                        className="text-[15px] font-bold mb-1"
                        style={{ color: "#1A1A1A" }}
                      >
                        {f.title}
                      </div>
                      <div
                        className="text-[14px] leading-relaxed"
                        style={{ color: "#8A8A8A" }}
                      >
                        {f.body}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Right: mockup */}
            <div>{TABS[active].mockup}</div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
