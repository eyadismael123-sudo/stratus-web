"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion, useMotionValueEvent, useScroll, useTransform } from "framer-motion";
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

const ALL_AGENTS = [
  { name: "Frame",  role: "LinkedIn Post Agent",      status: "Active", hired: true,  avatar: "/avatars/frame.svg"  },
  { name: "Scout",  role: "Car Reseller Intel",        status: "Hire",   hired: false, avatar: "/avatars/scout.svg"  },
  { name: "Brief",  role: "Doctor Morning Briefing",   status: "Soon",   hired: false, avatar: "/avatars/brief.svg"  },
  { name: "Pulse",  role: "Property Market Briefing",  status: "Soon",   hired: false, avatar: "/avatars/pulse.svg"  },
  { name: "Relay",  role: "AI Receptionist",           status: "Soon",   hired: false, avatar: "/avatars/relay.svg"  },
];

function AgentAvatar({ name, avatar }: { name: string; avatar: string }) {
  return (
    <div className="w-9 h-9 rounded-full flex-shrink-0 overflow-hidden bg-[#E8E6E1]">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={avatar}
        alt={name}
        className="w-full h-full object-cover"
        onError={(e) => {
          const el = e.currentTarget;
          el.style.display = "none";
          if (el.parentElement) {
            el.parentElement.style.display = "flex";
            el.parentElement.style.alignItems = "center";
            el.parentElement.style.justifyContent = "center";
            el.parentElement.style.background = "#1B4332";
            el.parentElement.style.color = "#fff";
            el.parentElement.style.fontSize = "12px";
            el.parentElement.style.fontWeight = "700";
            el.parentElement.textContent = name.slice(0, 2);
          }
        }}
      />
    </div>
  );
}

function HireMockup() {
  const VISIBLE = 3;
  const [offset, setOffset] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastTrigger = useRef(0);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  // Advance one step every ~25% of section scroll — weaker dependency
  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    const STEP = 0.18;
    const delta = latest - lastTrigger.current;
    if (delta >= STEP) {
      lastTrigger.current += STEP;
      setOffset((prev) => (prev + 1) % ALL_AGENTS.length);
    } else if (delta <= -STEP) {
      lastTrigger.current -= STEP;
      setOffset((prev) => (prev - 1 + ALL_AGENTS.length) % ALL_AGENTS.length);
    }
  });

  const visible = Array.from({ length: VISIBLE }, (_, i) => ALL_AGENTS[(offset + i) % ALL_AGENTS.length]);

  return (
    <div
      ref={containerRef}
      className="rounded-[16px] p-6 min-h-[280px]"
      style={{
        background: "#FFFFFF",
        border: "1px solid #E8E6E1",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
      }}
    >
      <div className="flex items-center justify-between mb-5">
        <span className="text-[11px] font-bold tracking-widest uppercase" style={{ color: "rgba(26,28,26,0.4)" }}>
          Active Agents
        </span>
        <span className="text-[11px] font-semibold" style={{ color: "#8A8A8A" }}>
          1 hired
        </span>
      </div>

      <div className="flex flex-col gap-3 overflow-hidden" style={{ minHeight: "210px" }}>
        <AnimatePresence mode="popLayout" initial={false}>
          {visible.map((member) => (
            <motion.div
              key={member.name}
              layout
              initial={{ opacity: 0, y: 52, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -36, scale: 0.97 }}
              transition={{
                type: "spring",
                damping: 20,
                stiffness: 260,
                mass: 0.8,
                layout: { type: "spring", damping: 22, stiffness: 280 },
              }}
              className="flex items-center justify-between p-3.5 rounded-[12px]"
              style={{
                background: member.hired ? "#FAF9F6" : "transparent",
                border: member.hired ? "1px solid #AEEECB" : "1px solid #E8E6E1",
                opacity: member.status === "Soon" ? 0.55 : 1,
              }}
            >
              <div className="flex items-center gap-3">
                <AgentAvatar name={member.name} avatar={member.avatar} />
                <div>
                  <p className="text-[13px] font-bold leading-none mb-0.5" style={{ color: member.hired ? "#1A1A1A" : "#8A8A8A" }}>
                    {member.name}
                  </p>
                  <p className="text-[11px]" style={{ color: "#8A8A8A" }}>{member.role}</p>
                </div>
              </div>

              {member.hired ? (
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#10b981" }} />
                  <span className="text-[11px] font-bold" style={{ color: "#10b981" }}>Active</span>
                </div>
              ) : member.status === "Hire" ? (
                <button
                  className="text-[11px] font-bold px-3 py-1.5 rounded-[6px]"
                  style={{ background: "#1B4332", color: "#FFFFFF" }}
                >
                  + Hire
                </button>
              ) : (
                <span className="text-[10px] font-bold tracking-wide uppercase" style={{ color: "#C0BDBA" }}>
                  Soon
                </span>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
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
  const contributions = [
    { agent: "Frame", action: "Drafted 2 posts, 1 published to LinkedIn", stat: "847 views", statColor: "#1B4332" },
    { agent: "Scout", action: "Scanned 47 listings, flagged 4 underpriced", stat: "4 leads", statColor: "#1B4332" },
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
      <div className="flex items-center gap-2 mb-5">
        <Smartphone size={14} color="#8A8A8A" />
        <span className="text-[12px] font-bold" style={{ color: "#8A8A8A" }}>
          Daily Team Report — 7:00 PM
        </span>
      </div>

      <p className="text-[13px] mb-4" style={{ color: "#4A4A4A" }}>
        Today your team accomplished:
      </p>

      <div className="flex flex-col gap-2.5 mb-4">
        {contributions.map((c) => (
          <div
            key={c.agent}
            className="flex items-center gap-3 p-3 rounded-[10px]"
            style={{ background: "#FAF9F6", border: "1px solid #E8E6E1" }}
          >
            <AgentAvatar name={c.agent} avatar={ALL_AGENTS.find(a => a.name === c.agent)?.avatar ?? ""} />
            <div className="flex-1 min-w-0">
              <p className="text-[12px] font-semibold leading-none mb-0.5" style={{ color: "#1A1A1A" }}>{c.agent}</p>
              <p className="text-[11px]" style={{ color: "#8A8A8A" }}>{c.action}</p>
            </div>
            <span className="text-[11px] font-bold flex-shrink-0" style={{ color: c.statColor }}>{c.stat}</span>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-3" style={{ borderTop: "1px solid #E8E6E1" }}>
        <p className="text-[12px]" style={{ color: "#8A8A8A" }}>847 impressions · ~2h saved</p>
        <p className="text-[11px]" style={{ color: "#8A8A8A" }}>Tomorrow: 2 posts at 9am</p>
      </div>
    </div>
  );
}

const TABS: TabContent[] = [
  {
    num: "01",
    label: "Hire",
    headline: "Build your team.\nOne hire at a time.",
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
