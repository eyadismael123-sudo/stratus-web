"use client";

import { useRef } from "react";
import Link from "next/link";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger);

export function BentoGrid() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!headerRef.current || !gridRef.current) return;
    gsap.fromTo(
      [headerRef.current, gridRef.current],
      { opacity: 0, y: 30 },
      {
        opacity: 1,
        y: 0,
        duration: 0.7,
        stagger: 0.15,
        ease: "power3.out",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 85%",
          once: true,
        },
      },
    );
  }, { scope: sectionRef });

  return (
    <section
      ref={sectionRef}
      className="py-24 px-6 md:px-12"
      style={{ background: "#FAF9F6" }}
    >
      <div className="max-w-[1440px] mx-auto">
        {/* Header */}
        <div ref={headerRef} className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-4 opacity-0">
          <div>
            <span
              className="text-[12px] font-bold tracking-widest uppercase mb-4 block"
              style={{ color: "#1B4332" }}
            >
              Our Roster
            </span>
            <h2
              className="font-display font-bold tracking-[-0.04em] leading-tight"
              style={{ fontSize: "clamp(36px, 5vw, 60px)", color: "#1B4332" }}
            >
              Meet your team.
            </h2>
          </div>
          <Link
            href="/marketplace"
            className="text-[14px] font-bold no-underline hover:underline underline-offset-8"
            style={{ color: "#1B4332" }}
          >
            Explore all agents →
          </Link>
        </div>

        {/* Grid */}
        <div ref={gridRef} className="grid grid-cols-1 md:grid-cols-3 gap-8 opacity-0">
          {/* Featured — LinkedIn Post Agent */}
          <div
            className="md:col-span-2 rounded-[16px] p-8 flex flex-col justify-between group hover:shadow-xl transition-all"
            style={{
              background: "#FFFFFF",
              borderTop: "4px solid #1B4332",
              border: "1px solid #E8E6E1",
              borderTopWidth: "4px",
              borderTopColor: "#1B4332",
            }}
          >
            <div>
              <div className="flex items-center justify-between mb-8">
                <span
                  className="text-[10px] font-black tracking-widest uppercase px-3 py-1 rounded-full text-white"
                  style={{ background: "#10b981" }}
                >
                  Live
                </span>
              </div>
              <h3
                className="font-display font-bold tracking-[-0.03em] mb-3"
                style={{ fontSize: "28px", color: "#1A1A1A" }}
              >
                LinkedIn Post Agent
              </h3>
              <p className="text-[15px] leading-relaxed max-w-sm" style={{ color: "#8A8A8A" }}>
                Generates thought-leadership content specifically tuned for the MENA tech scene.
              </p>
            </div>
            <div className="mt-12 flex items-center justify-between">
              <div className="flex -space-x-2">
                <div className="w-8 h-8 rounded-full border-2 border-white" style={{ background: "rgba(27,67,50,0.1)" }} />
                <div className="w-8 h-8 rounded-full border-2 border-white" style={{ background: "rgba(44,105,78,0.2)" }} />
              </div>
              <Link
                href="/agents/linkedin-post-agent"
                className="text-[14px] font-bold text-white px-6 py-2 rounded-[8px] no-underline transition-all hover:bg-[#2D6A4F]"
                style={{ background: "#1B4332" }}
              >
                Add to Team
              </Link>
            </div>
          </div>

          {/* Coming Soon — Flash */}
          <div
            className="rounded-[16px] p-8 flex flex-col justify-between opacity-60 grayscale hover:grayscale-0 hover:opacity-100 transition-all"
            style={{ background: "#FFFFFF", border: "1px solid #E8E6E1" }}
          >
            <div>
              <div className="flex items-center justify-between mb-8">
                <span
                  className="text-[10px] font-black tracking-widest uppercase px-3 py-1 rounded-full"
                  style={{ background: "#EFEEEB", color: "#8A8A8A" }}
                >
                  Coming Soon
                </span>
              </div>
              <h3
                className="font-display font-bold tracking-[-0.03em] mb-3"
                style={{ fontSize: "22px", color: "#1A1A1A" }}
              >
                Car Reseller Intel
              </h3>
              <p className="text-[14px] leading-relaxed" style={{ color: "#8A8A8A" }}>
                Real-time market sentiment for GCC used car listings.
              </p>
            </div>
            <div className="mt-12">
              <button
                className="w-full text-[13px] font-bold py-2 rounded-[8px] cursor-not-allowed"
                style={{ border: "1px solid #E8E6E1", color: "#8A8A8A" }}
              >
                Join Waitlist
              </button>
            </div>
          </div>

          {/* Coming Soon — Focus */}
          <div
            className="rounded-[16px] p-8 flex flex-col justify-between opacity-60 grayscale hover:grayscale-0 hover:opacity-100 transition-all"
            style={{ background: "#FFFFFF", border: "1px solid #E8E6E1" }}
          >
            <div>
              <div className="flex items-center justify-between mb-8">
                <span
                  className="text-[10px] font-black tracking-widest uppercase px-3 py-1 rounded-full"
                  style={{ background: "#EFEEEB", color: "#8A8A8A" }}
                >
                  Coming Soon
                </span>
              </div>
              <h3
                className="font-display font-bold tracking-[-0.03em] mb-3"
                style={{ fontSize: "22px", color: "#1A1A1A" }}
              >
                Doctor Briefing
              </h3>
              <p className="text-[14px] leading-relaxed" style={{ color: "#8A8A8A" }}>
                Clinical news before your first appointment.
              </p>
            </div>
            <div className="mt-12">
              <button
                className="w-full text-[13px] font-bold py-2 rounded-[8px] cursor-not-allowed"
                style={{ border: "1px solid #E8E6E1", color: "#8A8A8A" }}
              >
                Join Waitlist
              </button>
            </div>
          </div>

          {/* Custom Request */}
          <div
            className="md:col-span-2 rounded-[16px] p-8 flex items-center justify-between"
            style={{ background: "#1B4332" }}
          >
            <div>
              <h3
                className="font-display font-bold tracking-[-0.03em] mb-2"
                style={{ fontSize: "22px", color: "#FAF9F6" }}
              >
                Custom Request?
              </h3>
              <p className="text-[14px]" style={{ color: "rgba(250,249,246,0.6)" }}>
                Need an agent for a specific regional workflow?
              </p>
            </div>
            <Link
              href="/contact"
              className="text-[14px] font-bold rounded-[10px] px-8 py-3 no-underline transition-all hover:bg-[#FAF9F6]"
              style={{ background: "#FAF9F6", color: "#1B4332" }}
            >
              Contact Labs
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
