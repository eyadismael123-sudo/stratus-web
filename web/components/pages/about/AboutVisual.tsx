"use client";

import { useEffect, useState } from "react";

const TOASTS = [
  { emoji: "✓", text: "Frame posted to LinkedIn", color: "#4ade80" },
  { emoji: "↗", text: "Scout found 4 new listings", color: "#60a5fa" },
  { emoji: "✓", text: "Brief sent patient summary", color: "#4ade80" },
];

export default function AboutVisual() {
  const [toastIndex, setToastIndex] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const cycle = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setToastIndex((i) => (i + 1) % TOASTS.length);
        setVisible(true);
      }, 400);
    }, 3200);
    return () => clearInterval(cycle);
  }, []);

  const toast = TOASTS[toastIndex];

  return (
    <div
      className="w-full h-full rounded-xl overflow-hidden relative"
      style={{ background: "#012d1d", minHeight: "420px" }}
    >
      {/* Cycling toast notification */}
      <div
        className="absolute top-3 left-3 right-3 z-20 flex items-center gap-2 px-3 py-2 rounded-lg"
        style={{
          background: "rgba(255,255,255,0.06)",
          border: "1px solid rgba(174,238,203,0.15)",
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(-4px)",
          transition: "opacity 0.35s ease, transform 0.35s ease",
        }}
      >
        <span
          className="text-[11px] font-bold w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ background: toast.color, color: "#012d1d", fontSize: "9px" }}
        >
          {toast.emoji}
        </span>
        <span className="text-[11px] font-medium" style={{ color: "rgba(193,236,212,0.8)" }}>
          {toast.text}
        </span>
        <span className="ml-auto text-[9px]" style={{ color: "rgba(174,238,203,0.3)" }}>just now</span>
      </div>
      {/* Subtle grid pattern */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.07]"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#AEEECB" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Radial glow */}
      <div
        className="absolute pointer-events-none"
        style={{
          width: "300px",
          height: "300px",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          background: "radial-gradient(circle, rgba(44,105,78,0.4) 0%, transparent 70%)",
        }}
      />

      {/* Dashboard card */}
      <div className="absolute inset-4 flex flex-col gap-3 pt-10">

        {/* Header */}
        <div className="flex items-center justify-between">
          <span
            className="text-[10px] font-bold tracking-widest uppercase"
            style={{ color: "rgba(174,238,203,0.5)" }}
          >
            Live Activity
          </span>
          <div className="flex items-center gap-1.5">
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{
                background: "#4ade80",
                boxShadow: "0 0 6px #4ade80",
                animation: "about-pulse 2s ease-in-out infinite",
              }}
            />
            <span className="text-[10px] font-semibold" style={{ color: "#4ade80" }}>
              3 running
            </span>
          </div>
        </div>

        {/* Agent rows */}
        <AgentRow
          initials="Fr"
          name="Frame"
          task="Drafting LinkedIn post"
          progress={73}
          status="active"
          delay="0s"
        />
        <AgentRow
          initials="Sc"
          name="Scout"
          task="Found 4 underpriced cars"
          progress={100}
          status="done"
          delay="0.3s"
        />
        <AgentRow
          initials="Br"
          name="Brief"
          task="Building patient report"
          progress={41}
          status="active"
          delay="0.6s"
        />

        {/* Divider */}
        <div className="mt-auto" style={{ borderTop: "1px solid rgba(174,238,203,0.12)" }} />

        {/* Stats row */}
        <div className="flex items-end justify-between pt-1">
          <div>
            <p
              className="text-[28px] font-black leading-none"
              style={{ color: "#c1ecd4" }}
            >
              1,247
            </p>
            <p
              className="text-[9px] font-bold uppercase tracking-wider mt-1"
              style={{ color: "rgba(174,238,203,0.4)" }}
            >
              tasks this month
            </p>
          </div>

          {/* Mini sparkline */}
          <div className="flex items-end gap-[3px]" style={{ height: "36px" }}>
            {[30, 55, 40, 70, 60, 85, 100].map((h, i) => (
              <div
                key={i}
                className="w-[6px] rounded-sm"
                style={{
                  height: `${h}%`,
                  background: `rgba(174,238,203,${0.15 + (h / 100) * 0.6})`,
                  animation: `about-bar-grow 0.6s ease-out ${i * 0.08}s both`,
                }}
              />
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes about-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        @keyframes about-bar-grow {
          from { transform: scaleY(0); transform-origin: bottom; }
          to { transform: scaleY(1); transform-origin: bottom; }
        }
        @keyframes about-progress {
          from { width: 0%; }
        }
      `}</style>
    </div>
  );
}

function AgentRow({
  initials,
  name,
  task,
  progress,
  status,
  delay,
}: {
  initials: string;
  name: string;
  task: string;
  progress: number;
  status: "active" | "done";
  delay: string;
}) {
  const isActive = status === "active";

  return (
    <div
      className="rounded-xl p-3 flex flex-col gap-2"
      style={{
        background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(174,238,203,0.08)",
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-black flex-shrink-0"
            style={{
              background: isActive ? "rgba(174,238,203,0.15)" : "rgba(174,238,203,0.08)",
              color: "#c1ecd4",
              border: "1px solid rgba(174,238,203,0.2)",
            }}
          >
            {initials}
          </div>
          <div>
            <p className="text-[12px] font-bold leading-none" style={{ color: "#FAF9F6" }}>
              {name}
            </p>
            <p className="text-[10px] mt-0.5 leading-none" style={{ color: "rgba(174,238,203,0.5)" }}>
              {task}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{
              background: isActive ? "#4ade80" : "#86efac",
              animation: isActive ? `about-pulse 2s ease-in-out ${delay} infinite` : "none",
            }}
          />
          <span
            className="text-[9px] font-bold uppercase tracking-wide"
            style={{ color: isActive ? "#4ade80" : "rgba(174,238,203,0.5)" }}
          >
            {isActive ? "Active" : "Done"}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div
        className="rounded-full overflow-hidden"
        style={{ height: "3px", background: "rgba(174,238,203,0.08)" }}
      >
        <div
          className="h-full rounded-full"
          style={{
            width: `${progress}%`,
            background: isActive
              ? "linear-gradient(90deg, #1B4332, #4ade80)"
              : "rgba(174,238,203,0.3)",
            animation: `about-progress 1s ease-out ${delay} both`,
          }}
        />
      </div>
    </div>
  );
}
