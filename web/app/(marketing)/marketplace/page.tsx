"use client";

import Link from "next/link";
import { useState } from "react";

type Tab = "personal" | "business" | "health";

const PERSONAL_AGENTS = [
  {
    name: "Frame",
    role: "LinkedIn Post Agent",
    description:
      "Writes thought leadership in your voice. Daily. Designed for founders and executives across the Gulf region.",
    status: "LIVE",
    price: "$50/mo",
    slug: "linkedin-post-agent",
    avatar: "Fr",
    avatarBg: "#AEEECB",
    avatarColor: "#1B4332",
  },
];

const BUSINESS_AGENTS = [
  {
    name: "Flash",
    role: "Car Reseller Intel",
    description:
      "Underpriced cars found before competitors wake up. Real-time scanning of major MENA auto marketplaces.",
    status: "Coming Soon",
    price: "$50/mo",
    avatar: "Fl",
    avatarBg: "#E8E6E1",
    avatarColor: "#8A8A8A",
  },
  {
    name: "Focus",
    role: "Property Market Briefing",
    description:
      "Dubai real estate moves. In your inbox at 8am. Deep analysis of RERA data and secondary market shifts.",
    status: "Coming Soon",
    price: "$50/mo",
    avatar: "Fo",
    avatarBg: "#E8E6E1",
    avatarColor: "#8A8A8A",
  },
  {
    name: "Shutter",
    role: "AI Receptionist",
    description:
      "Answers, books, follows up. 24/7 coverage in Arabic and English for boutique firms.",
    status: "Coming Soon",
    price: "$50/mo",
    avatar: "Sh",
    avatarBg: "#E8E6E1",
    avatarColor: "#8A8A8A",
  },
];

const HEALTH_AGENTS = [
  {
    name: "Develop",
    role: "Doctor Morning Briefing",
    description:
      "Clinical news + patient context. Synthesized journals and regional medical updates — curated for your specialty, delivered at 7am.",
    status: "Coming Soon",
    price: "$50/mo",
    avatar: "De",
    avatarBg: "rgba(13,115,119,0.12)",
    avatarColor: "#0D7377",
  },
];

function AgentCard({
  agent,
  isLive,
}: {
  agent: (typeof PERSONAL_AGENTS)[0];
  isLive: boolean;
}) {
  return (
    <div
      className="flex flex-col"
      style={{ opacity: isLive ? 1 : 0.6 }}
    >
      {/* Editorial image placeholder */}
      <div
        className="mb-8 relative"
        style={{
          aspectRatio: "4/5",
          background: isLive ? "#1B4332" : "#E8E6E1",
          overflow: "hidden",
          borderRadius: "2px",
        }}
      >
        {/* Avatar centered in placeholder */}
        <div
          className="absolute inset-0 flex items-center justify-center"
          style={{ opacity: isLive ? 0.15 : 0.08 }}
        >
          <span
            className="font-display font-black"
            style={{ fontSize: "120px", color: "#ffffff", lineHeight: 1 }}
          >
            {agent.avatar}
          </span>
        </div>
        {/* Status badge */}
        <div className="absolute top-4 left-4">
          <span
            className="px-3 py-1 text-[11px] font-bold tracking-widest uppercase"
            style={{
              background: isLive ? "#1B4332" : "#717973",
              color: "#ffffff",
              borderRadius: "100px",
            }}
          >
            STATUS: {agent.status}
          </span>
        </div>
      </div>

      <div className="flex-grow">
        <div className="mb-3">
          <span
            className="text-[11px] font-bold uppercase tracking-widest"
            style={{ color: "#1B4332" }}
          >
            Personal
          </span>
        </div>
        <h3
          className="font-display font-bold text-[24px] mb-1 tracking-tight"
          style={{ color: "#1A1A1A" }}
        >
          {agent.name}
        </h3>
        <p
          className="mb-3"
          style={{
            fontSize: "11px",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            fontWeight: 600,
            opacity: 0.55,
          }}
        >
          {agent.role}
        </p>
        <p
          className="mb-8 leading-relaxed"
          style={{ color: "#717973", fontSize: "15px" }}
        >
          {agent.description}
        </p>
      </div>

      {isLive ? (
        <Link
          href={`/agents/${"slug" in agent ? agent.slug : "#"}`}
          className="block w-full text-center py-4 font-bold text-white no-underline transition-all hover:bg-[#2D6A4F]"
          style={{ background: "#1B4332", borderRadius: "8px" }}
        >
          Hire Now — {agent.price}
        </Link>
      ) : (
        <button
          disabled
          className="w-full py-4 font-bold cursor-not-allowed"
          style={{
            border: "2px solid rgba(193,200,194,0.3)",
            color: "#717973",
            background: "transparent",
            borderRadius: "8px",
          }}
        >
          Waiting List
        </button>
      )}
    </div>
  );
}

function BusinessAgentCard({ agent }: { agent: (typeof BUSINESS_AGENTS)[0] }) {
  return (
    <div className="flex flex-col" style={{ opacity: 0.6 }}>
      <div
        className="mb-8 relative"
        style={{
          aspectRatio: "4/5",
          background: "#E8E6E1",
          overflow: "hidden",
          borderRadius: "2px",
          filter: "grayscale(1)",
        }}
      >
        <div
          className="absolute inset-0 flex items-center justify-center"
          style={{ opacity: 0.08 }}
        >
          <span
            className="font-display font-black"
            style={{ fontSize: "120px", color: "#1A1A1A", lineHeight: 1 }}
          >
            {agent.avatar}
          </span>
        </div>
        <div className="absolute top-4 left-4">
          <span
            className="px-3 py-1 text-[11px] font-bold tracking-widest uppercase text-white"
            style={{ background: "#717973", borderRadius: "100px" }}
          >
            STATUS: Coming Soon
          </span>
        </div>
      </div>
      <div className="flex-grow">
        <div className="mb-3">
          <span
            className="text-[11px] font-bold uppercase tracking-widest"
            style={{ color: "#8A8A8A" }}
          >
            Business
          </span>
        </div>
        <h3
          className="font-display font-bold text-[24px] mb-1 tracking-tight"
          style={{ color: "#1A1A1A" }}
        >
          {agent.name}
        </h3>
        <p
          className="mb-3"
          style={{
            fontSize: "11px",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            fontWeight: 600,
            opacity: 0.55,
          }}
        >
          {agent.role}
        </p>
        <p
          className="mb-8 leading-relaxed"
          style={{ color: "#717973", fontSize: "15px" }}
        >
          {agent.description}
        </p>
      </div>
      <button
        disabled
        className="w-full py-4 font-bold cursor-not-allowed"
        style={{
          border: "2px solid rgba(193,200,194,0.3)",
          color: "#717973",
          background: "transparent",
          borderRadius: "8px",
        }}
      >
        Waiting List
      </button>
    </div>
  );
}

export default function MarketplacePage() {
  const [tab, setTab] = useState<Tab>("personal");

  return (
    <main style={{ background: "#FAF9F6", minHeight: "100vh" }}>
      {/* Hero */}
      <section className="px-6 md:px-8 pt-24 pb-20 max-w-screen-2xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end">
          <div className="lg:col-span-8">
            <h1
              className="font-display font-black leading-[0.9] tracking-[-0.04em] mb-8"
              style={{
                fontSize: "clamp(48px, 8vw, 96px)",
                color: "#1B4332",
              }}
            >
              Your AI Workforce.
              <br />
              Hire in minutes.
            </h1>
            <p
              className="text-[20px] md:text-[24px] leading-relaxed max-w-2xl"
              style={{ color: "#717973" }}
            >
              The first marketplace of specialized AI agents tailored for the
              high-growth MENA business ecosystem. Scale without limits.
            </p>
          </div>
          <div className="lg:col-span-4">
            <div
              className="rounded-[8px] p-6"
              style={{
                background: "#FFFFFF",
                border: "1px solid #E8E6E1",
                boxShadow: "0 24px 48px rgba(26,28,26,0.06)",
              }}
            >
              <p
                className="text-[11px] font-bold uppercase tracking-widest mb-6"
                style={{ color: "#8A8A8A" }}
              >
                Live Now
              </p>
              <div className="flex items-center gap-4 mb-4">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-black flex-shrink-0"
                  style={{ background: "#AEEECB", color: "#1B4332" }}
                >
                  Fr
                </div>
                <div>
                  <p
                    className="text-[14px] font-bold"
                    style={{ color: "#1A1A1A" }}
                  >
                    Frame — LinkedIn Post Agent
                  </p>
                  <p className="text-[12px]" style={{ color: "#8A8A8A" }}>
                    Thought leadership in your voice. Daily.
                  </p>
                </div>
                <div className="ml-auto flex-shrink-0">
                  <span
                    className="text-[11px] font-black text-white px-2 py-1 rounded-full"
                    style={{ background: "#10b981" }}
                  >
                    LIVE
                  </span>
                </div>
              </div>
              <Link
                href="/agents/linkedin-post-agent"
                className="block w-full text-center py-3 text-[14px] font-bold text-white no-underline hover:bg-[#2D6A4F] transition-all"
                style={{ background: "#1B4332", borderRadius: "8px" }}
              >
                Hire Now — $50/mo
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Tab bar */}
      <section
        className="px-6 md:px-8"
        style={{ borderBottom: "1px solid rgba(193,200,194,0.15)" }}
      >
        <div className="max-w-screen-2xl mx-auto flex flex-wrap items-center gap-0">
          {(
            [
              { id: "personal", label: "Personal" },
              { id: "business", label: "Business" },
              { id: "health", label: "Stratus Health" },
            ] as { id: Tab; label: string }[]
          ).map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className="font-display font-bold text-[15px] px-6 py-4 transition-all"
              style={{
                borderBottom: `2px solid ${tab === id ? (id === "health" ? "#0D7377" : "#1B4332") : "transparent"}`,
                color:
                  tab === id
                    ? id === "health"
                      ? "#0D7377"
                      : "#1B4332"
                    : "rgba(26,28,26,0.4)",
              }}
            >
              {id === "health" && (
                <span
                  className="inline-block w-2 h-2 rounded-full mr-2"
                  style={{
                    background: "#0D7377",
                    opacity: 0.7,
                    verticalAlign: "middle",
                  }}
                />
              )}
              {label}
            </button>
          ))}
        </div>
      </section>

      {/* Personal panel */}
      {tab === "personal" && (
        <section className="px-6 md:px-8 py-20 pb-32 max-w-screen-2xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-16">
            {PERSONAL_AGENTS.map((agent) => (
              <AgentCard key={agent.name} agent={agent} isLive={true} />
            ))}
          </div>
        </section>
      )}

      {/* Business panel */}
      {tab === "business" && (
        <section className="px-6 md:px-8 py-20 pb-32 max-w-screen-2xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-16">
            {BUSINESS_AGENTS.map((agent) => (
              <BusinessAgentCard key={agent.name} agent={agent} />
            ))}
          </div>
        </section>
      )}

      {/* Health panel */}
      {tab === "health" && (
        <section className="pb-32">
          <div
            className="py-20 px-6 text-center relative overflow-hidden"
            style={{
              background: "linear-gradient(135deg, #0a2e2e 0%, #0D7377 100%)",
            }}
          >
            <p
              className="text-[11px] font-bold uppercase tracking-[0.18em] mb-4"
              style={{ color: "rgba(255,255,255,0.5)" }}
            >
              A Stratus Division
            </p>
            <h2
              className="font-display font-black mb-5 leading-[0.95] tracking-[-0.03em]"
              style={{
                fontSize: "clamp(40px, 6vw, 72px)",
                color: "#ffffff",
              }}
            >
              Stratus Health
            </h2>
            <p
              className="text-[17px] max-w-lg mx-auto mb-8 leading-relaxed"
              style={{ color: "rgba(255,255,255,0.65)" }}
            >
              AI agents built specifically for healthcare professionals. Clinical
              intelligence. Delivered before your first patient.
            </p>
            <span
              className="inline-block text-[11px] font-bold uppercase tracking-[0.12em] px-4 py-2 rounded-full"
              style={{
                background: "rgba(255,255,255,0.12)",
                color: "rgba(255,255,255,0.8)",
                border: "1px solid rgba(255,255,255,0.2)",
              }}
            >
              Division launching 2026
            </span>
          </div>
          <div className="px-6 md:px-8 pt-20 max-w-screen-2xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-16">
              {HEALTH_AGENTS.map((agent) => (
                <div
                  key={agent.name}
                  className="flex flex-col"
                  style={{ opacity: 0.7 }}
                >
                  <div
                    className="mb-8 relative"
                    style={{
                      aspectRatio: "4/5",
                      background: "rgba(13,115,119,0.1)",
                      overflow: "hidden",
                      borderRadius: "2px",
                    }}
                  >
                    <div
                      className="absolute inset-0 flex items-center justify-center"
                      style={{ opacity: 0.12 }}
                    >
                      <span
                        className="font-display font-black"
                        style={{
                          fontSize: "120px",
                          color: "#0D7377",
                          lineHeight: 1,
                        }}
                      >
                        {agent.avatar}
                      </span>
                    </div>
                    <div className="absolute top-4 left-4">
                      <span
                        className="px-3 py-1 text-[11px] font-bold tracking-widest uppercase text-white"
                        style={{ background: "#0D7377", borderRadius: "100px" }}
                      >
                        Coming Soon
                      </span>
                    </div>
                  </div>
                  <div className="flex-grow">
                    <div className="mb-3">
                      <span
                        className="text-[11px] font-bold uppercase tracking-widest"
                        style={{ color: "#0D7377" }}
                      >
                        Health
                      </span>
                    </div>
                    <h3
                      className="font-display font-bold text-[24px] mb-1 tracking-tight"
                      style={{ color: "#1A1A1A" }}
                    >
                      {agent.name}
                    </h3>
                    <p
                      className="mb-3"
                      style={{
                        fontSize: "11px",
                        textTransform: "uppercase",
                        letterSpacing: "0.1em",
                        fontWeight: 600,
                        opacity: 0.55,
                      }}
                    >
                      {agent.role}
                    </p>
                    <p
                      className="mb-8 leading-relaxed"
                      style={{ color: "#717973", fontSize: "15px" }}
                    >
                      {agent.description}
                    </p>
                  </div>
                  <button
                    disabled
                    className="w-full py-4 font-bold cursor-not-allowed"
                    style={{
                      border: "2px solid #0D7377",
                      color: "#0D7377",
                      background: "transparent",
                      borderRadius: "8px",
                    }}
                  >
                    Join Waitlist
                  </button>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Bottom banner */}
      <section
        className="mx-6 md:mx-8 mb-20 py-24 px-12 text-center"
        style={{
          background: "#F4F3F1",
          borderRadius: "8px",
        }}
      >
        <h2
          className="font-display font-black mb-6 tracking-[-0.03em]"
          style={{
            fontSize: "clamp(28px, 4vw, 48px)",
            color: "#1B4332",
          }}
        >
          Your agents work better together
        </h2>
        <p
          className="text-[17px] max-w-xl mx-auto mb-10 leading-relaxed"
          style={{ color: "rgba(26,28,26,0.6)" }}
        >
          When your agents share data, they don&apos;t just work — they
          orchestrate growth.
        </p>
        <Link
          href="/agents/linkedin-post-agent"
          className="inline-block py-3 px-8 font-bold text-white no-underline transition-all hover:bg-[#2D6A4F]"
          style={{ background: "#1B4332", borderRadius: "8px" }}
        >
          Start with one agent →
        </Link>
      </section>
    </main>
  );
}
