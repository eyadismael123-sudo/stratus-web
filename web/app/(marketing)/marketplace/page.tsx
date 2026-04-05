"use client";

import { useState } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function WaitlistModal({
  agent,
  onClose,
}: {
  agent: { name: string; role: string };
  onClose: () => void;
}) {
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const email = (e.currentTarget.elements.namedItem("email") as HTMLInputElement).value;
    try {
      const res = await fetch(`${API_URL}/waitlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, agent: agent.name }),
      });
      if (!res.ok) throw new Error("Failed");
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
      style={{ background: "rgba(1,45,29,0.5)", backdropFilter: "blur(6px)" }}
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl p-8 w-full max-w-md relative"
        style={{ boxShadow: "0 24px 64px rgba(1,45,29,0.18)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-[20px] leading-none"
          style={{ color: "rgba(1,45,29,0.3)" }}
        >
          ×
        </button>

        {submitted ? (
          <div className="text-center py-4">
            <div
              className="w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center"
              style={{ background: "#D9EEE5" }}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M4 10l4 4 8-8" stroke="#012d1d" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h3 className="font-display font-black text-[22px] mb-2" style={{ color: "#012d1d" }}>
              You&apos;re on the list.
            </h3>
            <p className="text-[14px]" style={{ color: "#717973" }}>
              We&apos;ll let you know the moment {agent.name} goes live.
            </p>
          </div>
        ) : (
          <>
            <p className="text-[11px] font-bold uppercase tracking-widest mb-1" style={{ color: "rgba(1,45,29,0.4)" }}>
              Coming soon
            </p>
            <h3 className="font-display font-black text-[24px] mb-1" style={{ color: "#012d1d" }}>
              Join the waitlist for {agent.name}
            </h3>
            <p className="text-[14px] mb-6" style={{ color: "#717973" }}>
              {agent.role} — we&apos;ll notify you when it&apos;s ready.
            </p>

            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <input
                type="email"
                name="email"
                placeholder="Your email address"
                required
                disabled={loading}
                className="w-full px-4 py-3 rounded-xl text-[15px] outline-none disabled:opacity-60"
                style={{
                  background: "#F5F4F1",
                  color: "#1A1A1A",
                  border: "1px solid #E8E6E1",
                  fontFamily: "inherit",
                }}
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl text-[15px] font-bold transition-all hover:opacity-90 disabled:opacity-60"
                style={{ background: "#012d1d", color: "#FAF9F6", fontFamily: "inherit" }}
              >
                {loading ? "Joining..." : "Notify me →"}
              </button>
            </form>
            {error && (
              <p className="text-[13px] mt-3" style={{ color: "rgba(200,50,50,0.9)" }}>{error}</p>
            )}
            <p className="text-[11px] mt-4 text-center" style={{ color: "rgba(1,45,29,0.3)" }}>
              No spam. Just a heads-up when your agent is ready.
            </p>
          </>
        )}
      </div>
    </div>
  );
}

const LIVE_AGENT = {
  name: "Frame",
  role: "LinkedIn Post Agent",
  category: "Personal",
  price: "$99",
  slug: "linkedin-post-agent",
  initials: "Fr",
  description:
    "Scans your industry every morning. Picks the best angles. Writes two drafts in your voice. You pick one and post. Takes 30 seconds.",
  features: ["Daily post drafts", "Morning briefings", "One-click LinkedIn"],
};

const COMING_SOON = [
  {
    name: "Flash",
    role: "Car Reseller Intel",
    category: "Business",
    price: "$149",
    initials: "Fl",
    accent: "#7C3F00",
    accentBg: "#FFF3E0",
    description:
      "Scans thousands of listings overnight and flags underpriced cars before your competitors wake up.",
  },
  {
    name: "Focus",
    role: "Property Market Briefing",
    category: "Business",
    price: "$99",
    initials: "Fo",
    accent: "#012d1d",
    accentBg: "#D9EEE5",
    description:
      "Dubai real estate at 8am. Off-plan updates, RERA data, secondary market shifts — one brief.",
  },
  {
    name: "Develop",
    role: "Doctor Morning Briefing",
    category: "Health",
    price: "$49",
    initials: "De",
    accent: "#1a3a5c",
    accentBg: "#E8F0FB",
    description:
      "Clinical news and patient context before your first appointment. Built for doctors in MENA.",
  },
  {
    name: "Shutter",
    role: "AI Receptionist",
    category: "Business",
    price: "$199",
    initials: "Sh",
    accent: "#3B1F6E",
    accentBg: "#EEE8FB",
    description:
      "Answers queries, books appointments, follows up. Arabic and English. 24/7. Never calls in sick.",
  },
];

export default function MarketplacePage() {
  const [waitlistAgent, setWaitlistAgent] = useState<{ name: string; role: string } | null>(null);

  return (
    <main style={{ background: "#FAF9F6", minHeight: "100vh" }}>
      {waitlistAgent && (
        <WaitlistModal agent={waitlistAgent} onClose={() => setWaitlistAgent(null)} />
      )}

      {/* ── Hero ── */}
      <section className="px-6 md:px-12 pt-28 pb-16 max-w-7xl mx-auto">
        <p
          className="text-[11px] font-bold uppercase tracking-[0.18em] mb-5"
          style={{ color: "rgba(1,45,29,0.4)" }}
        >
          The Hiring Board
        </p>
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
          <h1
            className="font-display font-black leading-[0.92] tracking-[-0.04em]"
            style={{ fontSize: "clamp(48px, 7vw, 84px)", color: "#012d1d" }}
          >
            Pick your<br />first hire.
          </h1>
          <p
            className="max-w-sm text-[17px] leading-relaxed md:text-right"
            style={{ color: "#717973" }}
          >
            Five agents. One live now.
            <br />
            The rest are on their way.
          </p>
        </div>
      </section>

      {/* ── Live Agent — Frame ── */}
      <section className="px-6 md:px-12 pb-16 max-w-7xl mx-auto">
        <div
          className="rounded-2xl overflow-hidden"
          style={{ background: "#012d1d" }}
        >
          <div className="flex flex-col md:flex-row md:items-stretch">

            {/* Left — info */}
            <div className="flex-1 p-10 md:p-14">
              {/* Live badge */}
              <div className="flex items-center gap-2 mb-10">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{
                    background: "#AEEECB",
                    boxShadow: "0 0 6px #AEEECB",
                    animation: "pulse-dot 2s ease-in-out infinite",
                  }}
                />
                <span
                  className="text-[11px] font-bold uppercase tracking-[0.16em]"
                  style={{ color: "rgba(174,238,203,0.8)" }}
                >
                  Live Now
                </span>
              </div>

              {/* Name + role */}
              <div className="flex items-center gap-5 mb-6">
                <div
                  className="w-14 h-14 rounded-xl flex items-center justify-center text-[16px] font-black flex-shrink-0"
                  style={{ background: "#AEEECB", color: "#012d1d" }}
                >
                  {LIVE_AGENT.initials}
                </div>
                <div>
                  <h2
                    className="font-display font-black text-[28px] leading-none tracking-tight"
                    style={{ color: "#FAF9F6" }}
                  >
                    {LIVE_AGENT.name}
                  </h2>
                  <p
                    className="text-[12px] font-bold uppercase tracking-widest mt-1"
                    style={{ color: "rgba(174,238,203,0.55)" }}
                  >
                    {LIVE_AGENT.role}
                  </p>
                </div>
              </div>

              {/* Description */}
              <p
                className="text-[17px] leading-relaxed mb-10 max-w-lg"
                style={{ color: "rgba(250,249,246,0.7)" }}
              >
                {LIVE_AGENT.description}
              </p>

              {/* Feature tags */}
              <div className="flex flex-wrap gap-2">
                {LIVE_AGENT.features.map((f) => (
                  <span
                    key={f}
                    className="text-[12px] font-semibold px-3 py-1.5 rounded-full"
                    style={{
                      background: "rgba(174,238,203,0.12)",
                      color: "rgba(174,238,203,0.85)",
                      border: "1px solid rgba(174,238,203,0.2)",
                    }}
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>

            {/* Right — price + CTA */}
            <div
              className="flex flex-col items-start md:items-end justify-between p-10 md:p-14 md:w-72"
              style={{ borderLeft: "1px solid rgba(174,238,203,0.1)" }}
            >
              <div className="mb-8 md:mb-0 md:text-right">
                <p
                  className="text-[11px] font-bold uppercase tracking-widest mb-1"
                  style={{ color: "rgba(174,238,203,0.4)" }}
                >
                  Monthly
                </p>
                <p
                  className="font-display font-black leading-none"
                  style={{ fontSize: "52px", color: "#FAF9F6", letterSpacing: "-0.03em" }}
                >
                  {LIVE_AGENT.price}
                </p>
                <p
                  className="text-[13px] mt-1"
                  style={{ color: "rgba(250,249,246,0.4)" }}
                >
                  No setup. Cancel anytime.
                </p>
              </div>

              <Link
                href={`/agents/${LIVE_AGENT.slug}`}
                className="block w-full md:w-auto text-center font-bold text-[15px] px-8 py-4 rounded-xl no-underline transition-all hover:opacity-90"
                style={{ background: "#AEEECB", color: "#012d1d" }}
              >
                Hire {LIVE_AGENT.name} →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Coming Soon Roster ── */}
      <section className="px-6 md:px-12 pb-32 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <p
            className="text-[11px] font-bold uppercase tracking-[0.18em]"
            style={{ color: "rgba(1,45,29,0.4)" }}
          >
            On deck — 4 agents
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {COMING_SOON.map((agent) => (
            <div
              key={agent.name}
              className="bg-white rounded-xl overflow-hidden flex"
              style={{
                border: "1px solid #ECEAE6",
                boxShadow: "0 2px 12px rgba(1,45,29,0.04)",
              }}
            >
              {/* Color accent strip */}
              <div
                className="w-1 flex-shrink-0"
                style={{ background: agent.accent, opacity: 0.6 }}
              />

              <div className="flex flex-col sm:flex-row sm:items-center gap-5 p-6 flex-1">
                {/* Avatar */}
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-[13px] font-black flex-shrink-0"
                  style={{ background: agent.accentBg, color: agent.accent }}
                >
                  {agent.initials}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3
                      className="font-display font-black text-[18px] tracking-tight"
                      style={{ color: "#1A1A1A" }}
                    >
                      {agent.name}
                    </h3>
                    <span
                      className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full"
                      style={{
                        background: agent.accentBg,
                        color: agent.accent,
                      }}
                    >
                      {agent.category}
                    </span>
                  </div>
                  <p
                    className="text-[12px] font-semibold uppercase tracking-wider mb-2"
                    style={{ color: "#8A8A8A" }}
                  >
                    {agent.role}
                  </p>
                  <p
                    className="text-[13px] leading-relaxed"
                    style={{ color: "#717973" }}
                  >
                    {agent.description}
                  </p>
                </div>

                {/* Price + action */}
                <div className="flex sm:flex-col items-center sm:items-end gap-4 sm:gap-3 flex-shrink-0">
                  <p
                    className="font-display font-black text-[20px]"
                    style={{ color: "#1A1A1A" }}
                  >
                    {agent.price}
                    <span
                      className="text-[12px] font-medium ml-0.5"
                      style={{ color: "#8A8A8A" }}
                    >
                      /mo
                    </span>
                  </p>
                  <button
                    onClick={() => setWaitlistAgent({ name: agent.name, role: agent.role })}
                    className="text-[12px] font-bold px-4 py-2 rounded-lg whitespace-nowrap transition-all hover:opacity-80"
                    style={{
                      background: agent.accentBg,
                      color: agent.accent,
                      border: `1px solid ${agent.accent}22`,
                    }}
                  >
                    Join Waitlist
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Bottom CTA ── */}
      <section
        className="mx-6 md:mx-12 mb-20 rounded-2xl px-10 py-16 flex flex-col md:flex-row items-center justify-between gap-8"
        style={{ background: "#F0EFEC" }}
      >
        <div>
          <h2
            className="font-display font-black text-[28px] md:text-[36px] tracking-tight mb-2"
            style={{ color: "#012d1d" }}
          >
            Your agents work better together.
          </h2>
          <p style={{ color: "#717973" }}>
            Start with one. Add more as your business grows.
          </p>
        </div>
        <Link
          href="/agents/linkedin-post-agent"
          className="flex-shrink-0 font-bold text-[15px] text-white px-8 py-4 rounded-xl no-underline transition-all hover:bg-[#1b4332]"
          style={{ background: "#012d1d" }}
        >
          Start with Frame →
        </Link>
      </section>

      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </main>
  );
}
