"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const AGENTS = [
  {
    initials: "Fl",
    name: "Flash",
    role: "Research Agent",
    action: "Scans 18 trending topics on X + web",
    avatarBg: "#E8F5EF",
    avatarColor: "#1B4332",
  },
  {
    initials: "Fr",
    name: "Frame",
    role: "LinkedIn Ghostwriter",
    action: "Turns Flash's intel into 2 post drafts",
    avatarBg: "#1B4332",
    avatarColor: "#FFFFFF",
  },
  {
    initials: "Fc",
    name: "Focus",
    role: "Analytics Agent",
    action: "Tracks impressions + optimises timing",
    avatarBg: "#E8F5EF",
    avatarColor: "#1B4332",
    comingSoon: true,
  },
];

const ARROW_DELAY = 0.15;

export function TeamWorkflowSection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="py-[120px] px-6 md:px-10"
      style={{ background: "#FAF9F6" }}
    >
      <div className="max-w-[1100px] mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-16"
        >
          <div
            className="inline-flex items-center gap-2 mb-6 px-4 py-1.5 rounded-full text-[12px] font-semibold"
            style={{
              color: "#1B4332",
              background: "#FFFFFF",
              border: "1px solid #AEEECB",
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#10b981" }} />
            Agents share intelligence
          </div>
          <h2
            className="font-display font-bold tracking-[-0.04em] leading-tight mb-4"
            style={{ fontSize: "clamp(28px, 3.5vw, 44px)", color: "#1B4332" }}
          >
            Not individual tools.<br />A team that works together.
          </h2>
          <p
            className="text-[16px] max-w-md mx-auto"
            style={{ color: "#8A8A8A", lineHeight: 1.6 }}
          >
            Each agent you hire passes its findings to the next. One team. Compounding results.
          </p>
        </motion.div>

        {/* Workflow row */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-center gap-0">
          {AGENTS.map((agent, i) => (
            <div key={agent.name} className="flex flex-col md:flex-row items-center md:items-stretch">
              {/* Agent card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.55, delay: i * 0.15, ease: [0.16, 1, 0.3, 1] }}
                className="relative rounded-[16px] p-5 flex flex-col gap-3 w-full md:w-[220px]"
                style={{
                  background: "#FFFFFF",
                  border: agent.comingSoon ? "1px dashed #D8D5CF" : "1px solid #E8E6E1",
                  boxShadow: agent.comingSoon ? "none" : "0 4px 16px rgba(27,67,50,0.06)",
                  opacity: agent.comingSoon ? 0.55 : 1,
                }}
              >
                {agent.comingSoon && (
                  <span
                    className="absolute top-3 right-3 text-[9px] font-bold tracking-widest uppercase px-2 py-0.5 rounded-full"
                    style={{ background: "#F0EFEC", color: "#8A8A8A" }}
                  >
                    Soon
                  </span>
                )}
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-bold flex-shrink-0"
                  style={{ background: agent.avatarBg, color: agent.avatarColor }}
                >
                  {agent.initials}
                </div>
                <div>
                  <p className="text-[14px] font-bold leading-none mb-1" style={{ color: "#1A1A1A" }}>
                    {agent.name}
                  </p>
                  <p className="text-[11px] font-semibold mb-2" style={{ color: "#1B4332" }}>
                    {agent.role}
                  </p>
                  <p className="text-[12px] leading-relaxed" style={{ color: "#8A8A8A" }}>
                    {agent.action}
                  </p>
                </div>
                {!agent.comingSoon && (
                  <div className="flex items-center gap-1.5 mt-auto pt-2" style={{ borderTop: "1px solid #E8E6E1" }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#10b981" }} />
                    <span className="text-[11px] font-bold" style={{ color: "#10b981" }}>Active</span>
                  </div>
                )}
              </motion.div>

              {/* Connector arrow — between cards, not after last */}
              {i < AGENTS.length - 1 && (
                <motion.div
                  initial={{ opacity: 0, scaleX: 0 }}
                  animate={inView ? { opacity: 1, scaleX: 1 } : {}}
                  transition={{ duration: 0.4, delay: i * 0.15 + ARROW_DELAY, ease: "easeOut" }}
                  style={{ transformOrigin: "left center" }}
                  className="flex items-center justify-center mx-3 my-3 md:my-0"
                >
                  {/* Desktop: horizontal arrow */}
                  <div className="hidden md:flex items-center gap-1" style={{ color: "#AEEECB" }}>
                    <div className="h-px w-8" style={{ background: "#AEEECB" }} />
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M2 6h8M7 3l3 3-3 3" stroke="#1B4332" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  {/* Mobile: vertical arrow */}
                  <div className="md:hidden flex flex-col items-center gap-1">
                    <div className="w-px h-6" style={{ background: "#AEEECB" }} />
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ transform: "rotate(90deg)" }}>
                      <path d="M2 6h8M7 3l3 3-3 3" stroke="#1B4332" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                </motion.div>
              )}
            </div>
          ))}
        </div>

        {/* Bottom callout */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.55, ease: [0.16, 1, 0.3, 1] }}
          className="mt-12 text-center"
        >
          <p className="text-[13px]" style={{ color: "#8A8A8A" }}>
            Start with one agent. Each one you add makes the whole team smarter.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
