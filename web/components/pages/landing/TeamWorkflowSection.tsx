"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const AGENTS = [
  {
    initials: "Fr",
    name: "Frame",
    role: "LinkedIn Post Agent",
    action: "Writes thought leadership in your voice. Delivered every morning.",
    avatarBg: "#1B4332",
    avatarColor: "#FFFFFF",
  },
  {
    initials: "Sc",
    name: "Scout",
    role: "Car Reseller Intel",
    action: "Surfaces underpriced cars before your competitors are even awake.",
    avatarBg: "#E8F5EF",
    avatarColor: "#1B4332",
    comingSoon: true,
  },
  {
    initials: "Br",
    name: "Brief",
    role: "Doctor Morning Briefing",
    action: "Clinical news + patient context ready before your first appointment.",
    avatarBg: "#E8F5EF",
    avatarColor: "#1B4332",
    comingSoon: true,
  },
];


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
            One for every part<br />of your business.
          </h2>
          <p
            className="text-[16px] max-w-md mx-auto"
            style={{ color: "#8A8A8A", lineHeight: 1.6 }}
          >
            Each agent runs a different operation — content, intelligence, research — all in the background while you focus on what matters.
          </p>
        </motion.div>

        {/* Agent grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-[900px] mx-auto">
          {AGENTS.map((agent, i) => (
            <motion.div
              key={agent.name}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.55, delay: i * 0.12, ease: [0.16, 1, 0.3, 1] }}
              className="relative rounded-[16px] p-5 flex flex-col gap-3"
              style={{
                background: "#FFFFFF",
                border: agent.comingSoon ? "1px dashed #D8D5CF" : "1px solid #E8E6E1",
                boxShadow: agent.comingSoon ? "none" : "0 4px 16px rgba(27,67,50,0.06)",
                opacity: agent.comingSoon ? 0.6 : 1,
              }}
            >
              {agent.comingSoon && (
                <span
                  className="absolute top-3 right-3 text-[9px] font-bold tracking-widest uppercase px-2 py-0.5 rounded-full"
                  style={{ background: "#F0EFEC", color: "#8A8A8A" }}
                >
                  Coming soon
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
                  <span className="text-[11px] font-bold" style={{ color: "#10b981" }}>Active now</span>
                </div>
              )}
            </motion.div>
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
