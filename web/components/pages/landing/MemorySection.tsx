"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const MEMORY_LINES = [
  { label: "Voice", value: "Direct, data-first, confident tone" },
  { label: "Topics", value: "Pharma innovation, leadership, AI in health" },
  { label: "Wins", value: "3 posts hit 1k+ impressions this week" },
  { label: "Timing", value: "Best engagement: Tue + Thu 8–9am" },
];

const TELEGRAM_MESSAGES = [
  {
    from: "Stratus",
    text: "Good morning, Eyad. Here's what your team knows about you this week:",
    time: "08:01",
    isBot: true,
  },
  {
    from: "Stratus",
    text: "Flash noticed your audience responds 2× better to posts that open with a question. Frame will test that format in today's draft.",
    time: "08:01",
    isBot: true,
  },
  {
    from: "You",
    text: "Nice. What's lined up for today?",
    time: "08:03",
    isBot: false,
  },
  {
    from: "Stratus",
    text: "Frame is drafting 2 options now. You'll have them by 8:15.",
    time: "08:03",
    isBot: true,
  },
];

export function MemorySection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="py-[120px] px-6 md:px-10"
      style={{ background: "#1B4332" }}
    >
      <div className="max-w-[1100px] mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">

          {/* Left — text */}
          <motion.div
            initial={{ opacity: 0, x: -24 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
          >
            <div
              className="inline-flex items-center gap-2 mb-6 px-4 py-1.5 rounded-full text-[12px] font-semibold"
              style={{
                color: "#AEEECB",
                background: "rgba(174,238,203,0.12)",
                border: "1px solid rgba(174,238,203,0.25)",
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#AEEECB" }} />
              Built-in memory
            </div>

            <h2
              className="font-display font-bold tracking-[-0.04em] leading-tight mb-6"
              style={{ fontSize: "clamp(28px, 3.5vw, 44px)", color: "#FFFFFF" }}
            >
              Your team remembers.<br />Every. Single. Day.
            </h2>

            <p
              className="mb-8 max-w-md"
              style={{ fontSize: "16px", color: "rgba(255,255,255,0.65)", lineHeight: 1.7 }}
            >
              Every interaction builds a sharper picture of you — your voice, your audience, what works.
              Agents don&apos;t start fresh every morning. They get better.
            </p>

            {/* Memory profile snippet */}
            <div
              className="rounded-[14px] p-5"
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            >
              <p
                className="text-[10px] font-bold tracking-widest uppercase mb-4"
                style={{ color: "rgba(255,255,255,0.35)" }}
              >
                Your Profile — Updated Daily
              </p>
              <div className="flex flex-col gap-3">
                {MEMORY_LINES.map((line, i) => (
                  <motion.div
                    key={line.label}
                    initial={{ opacity: 0, x: -12 }}
                    animate={inView ? { opacity: 1, x: 0 } : {}}
                    transition={{ duration: 0.4, delay: 0.3 + i * 0.08, ease: "easeOut" }}
                    className="flex items-start gap-3"
                  >
                    <span
                      className="text-[11px] font-bold w-14 flex-shrink-0 pt-px"
                      style={{ color: "#AEEECB" }}
                    >
                      {line.label}
                    </span>
                    <span className="text-[12px] leading-relaxed" style={{ color: "rgba(255,255,255,0.7)" }}>
                      {line.value}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Right — Telegram mockup */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.65, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          >
            <div
              className="rounded-[20px] overflow-hidden"
              style={{
                background: "#FFFFFF",
                boxShadow: "0 24px 60px rgba(0,0,0,0.25)",
              }}
            >
              {/* Telegram header */}
              <div
                className="flex items-center gap-3 px-4 py-3"
                style={{ background: "#F5F5F5", borderBottom: "1px solid #E8E6E1" }}
              >
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold"
                  style={{ background: "#1B4332", color: "#FFFFFF" }}
                >
                  St
                </div>
                <div>
                  <p className="text-[13px] font-bold leading-none" style={{ color: "#1A1A1A" }}>Stratus</p>
                  <p className="text-[10px]" style={{ color: "#8A8A8A" }}>bot · online</p>
                </div>
              </div>

              {/* Messages */}
              <div className="flex flex-col gap-2.5 p-4" style={{ background: "#EFEEF0" }}>
                {TELEGRAM_MESSAGES.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={inView ? { opacity: 1, y: 0 } : {}}
                    transition={{ duration: 0.35, delay: 0.4 + i * 0.1, ease: "easeOut" }}
                    className={`flex ${msg.isBot ? "justify-start" : "justify-end"}`}
                  >
                    <div
                      className="max-w-[80%] rounded-[12px] px-3.5 py-2.5"
                      style={{
                        background: msg.isBot ? "#FFFFFF" : "#2AABEE",
                        borderRadius: msg.isBot
                          ? "4px 12px 12px 12px"
                          : "12px 4px 12px 12px",
                      }}
                    >
                      <p
                        className="text-[12px] leading-[1.5]"
                        style={{ color: msg.isBot ? "#1A1A1A" : "#FFFFFF" }}
                      >
                        {msg.text}
                      </p>
                      <p
                        className="text-[10px] text-right mt-1"
                        style={{ color: msg.isBot ? "#8A8A8A" : "rgba(255,255,255,0.75)" }}
                      >
                        {msg.time}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            <p
              className="text-center text-[12px] mt-4"
              style={{ color: "rgba(255,255,255,0.4)" }}
            >
              Weekly intelligence report · every Sunday 8am
            </p>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
