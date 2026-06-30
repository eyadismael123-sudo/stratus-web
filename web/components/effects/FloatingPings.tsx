"use client";

import { useEffect, useState } from "react";

interface Ping {
  agent: string;
  initials: string;
  text: string;
  color: string;
}

const PINGS: Ping[] = [
  { agent: "Frame", initials: "Fr", text: "Generated a LinkedIn draft", color: "#EB0043" },
  { agent: "Scout", initials: "Sc", text: "Found a new listing under market", color: "#2C694E" },
  { agent: "Brief", initials: "Br", text: "Patient brief ready for review", color: "#2E4057" },
  { agent: "Frame", initials: "Fr", text: "Schedule updated — 3 posts queued", color: "#EB0043" },
  { agent: "Scout", initials: "Sc", text: "GCC market scan complete", color: "#2C694E" },
];

export function FloatingPings() {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const showTimer = setTimeout(() => setVisible(true), 2200);
    const interval = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIndex((i) => (i + 1) % PINGS.length);
        setVisible(true);
      }, 500);
    }, 4200);
    return () => {
      clearTimeout(showTimer);
      clearInterval(interval);
    };
  }, []);

  const ping = PINGS[index];

  return (
    <div
      className="hidden lg:block absolute z-20 pointer-events-none"
      style={{
        top: "30%",
        right: "-12px",
        transform: visible ? "translateX(0) scale(1)" : "translateX(20px) scale(0.95)",
        opacity: visible ? 1 : 0,
        transition: "all 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
      }}
    >
      <div
        className="flex items-center gap-3 rounded-[14px] py-2.5 px-3.5"
        style={{
          background: "rgba(255,255,255,0.95)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(235,0,67,0.15)",
          boxShadow: "0 12px 40px rgba(27,67,50,0.12)",
          minWidth: "240px",
        }}
      >
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0"
          style={{ background: ping.color, color: "#FFFFFF" }}
        >
          {ping.initials}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-black uppercase tracking-wide leading-tight" style={{ color: ping.color }}>
            {ping.agent} · just now
          </p>
          <p className="text-[12px] leading-tight mt-0.5" style={{ color: "#2E4057" }}>
            {ping.text}
          </p>
        </div>
        <span
          className="w-1.5 h-1.5 rounded-full flex-shrink-0"
          style={{ background: "#10b981", animation: "pulse-dot 1.6s ease-in-out infinite" }}
        />
      </div>
    </div>
  );
}
