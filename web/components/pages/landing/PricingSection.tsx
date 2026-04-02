"use client";

import { useRef } from "react";
import Link from "next/link";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import { Check } from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

export function PricingSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!gridRef.current) return;
    gsap.fromTo(
      gridRef.current,
      { opacity: 0, y: 40 },
      {
        opacity: 1,
        y: 0,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: {
          trigger: gridRef.current,
          start: "top 85%",
          once: true,
        },
      },
    );
  }, { scope: sectionRef });

  return (
    <section
      ref={sectionRef}
      id="pricing"
      className="py-24 px-6 md:px-12"
      style={{ background: "#FAF9F6" }}
    >
      <div className="max-w-[1440px] mx-auto">
        {/* Header */}
        <div className="text-center mb-20">
          <h2
            className="font-display font-bold tracking-[-0.04em] leading-tight mb-4"
            style={{ fontSize: "clamp(32px, 4vw, 48px)", color: "#1B4332" }}
          >
            Simple, predictable hiring.
          </h2>
          <p className="text-[16px] font-medium" style={{ color: "#8A8A8A" }}>
            No hidden fees. Scale up or down instantly.
          </p>
        </div>

        {/* 3-column grid */}
        <div ref={gridRef} className="grid md:grid-cols-3 gap-8 items-stretch opacity-0">
          {/* Entry */}
          <div
            className="rounded-[16px] p-8 flex flex-col"
            style={{ background: "#F4F3F1", border: "1px solid #E8E6E1" }}
          >
            <div className="mb-8">
              <p className="text-[11px] font-bold uppercase tracking-widest mb-2" style={{ color: "#1B4332" }}>Entry</p>
              <p className="text-[40px] font-black leading-none" style={{ color: "#1A1A1A" }}>
                $50<span className="text-[14px] font-bold" style={{ color: "#8A8A8A" }}>/mo</span>
              </p>
              <p className="text-[12px] mt-2" style={{ color: "#8A8A8A" }}>1 AI Agent</p>
            </div>
            <ul className="flex flex-col gap-4 mb-10 flex-grow list-none">
              {["Daily briefings", "Basic integrations", "500 tasks / month"].map((f) => (
                <li key={f} className="flex items-center gap-3 text-[14px] font-medium">
                  <Check size={16} style={{ color: "#1B4332", flexShrink: 0 }} />
                  {f}
                </li>
              ))}
            </ul>
            <Link
              href="/agents/linkedin-post-agent"
              className="block w-full text-center rounded-[10px] py-3 text-[14px] font-bold no-underline transition-all hover:bg-[#E8E6E1]"
              style={{ border: "1px solid #1B4332", color: "#1B4332" }}
            >
              Get Started
            </Link>
          </div>

          {/* Professional — featured */}
          <div
            className="rounded-[16px] p-8 flex flex-col relative md:-translate-y-4"
            style={{
              background: "#FFFFFF",
              border: "2px solid #1B4332",
              boxShadow: "0 20px 60px rgba(27,67,50,0.12)",
            }}
          >
            <div
              className="absolute -top-4 left-1/2 -translate-x-1/2 text-[10px] font-black uppercase tracking-widest px-4 py-1 rounded-full text-white whitespace-nowrap"
              style={{ background: "#1B4332" }}
            >
              Most Popular
            </div>
            <div className="mb-8">
              <p className="text-[11px] font-bold uppercase tracking-widest mb-2" style={{ color: "#1B4332" }}>Professional</p>
              <p className="text-[40px] font-black leading-none" style={{ color: "#1A1A1A" }}>
                $150<span className="text-[14px] font-bold" style={{ color: "#8A8A8A" }}>/mo</span>
              </p>
              <p className="text-[12px] mt-2" style={{ color: "#8A8A8A" }}>3 AI Agents</p>
            </div>
            <ul className="flex flex-col gap-4 mb-10 flex-grow list-none">
              {[
                "Priority regional support",
                "Custom integrations",
                "Unlimited tasks",
                "Multi-dialect support",
              ].map((f, i) => (
                <li key={f} className={`flex items-center gap-3 text-[14px] ${i === 0 ? "font-bold" : "font-medium"}`} style={{ color: i === 0 ? "#1B4332" : "#1A1A1A" }}>
                  <Check size={16} style={{ color: "#1B4332", flexShrink: 0 }} />
                  {f}
                </li>
              ))}
            </ul>
            <Link
              href="/agents/linkedin-post-agent"
              className="block w-full text-center rounded-[10px] py-4 text-[14px] font-bold text-white no-underline transition-all hover:bg-[#2D6A4F]"
              style={{
                background: "#1B4332",
                boxShadow: "0 4px 16px rgba(27,67,50,0.2)",
              }}
            >
              Hire Now
            </Link>
          </div>

          {/* Enterprise */}
          <div
            className="rounded-[16px] p-8 flex flex-col"
            style={{ background: "#F4F3F1", border: "1px solid #E8E6E1" }}
          >
            <div className="mb-8">
              <p className="text-[11px] font-bold uppercase tracking-widest mb-2" style={{ color: "#1B4332" }}>Enterprise</p>
              <p className="text-[40px] font-black leading-none" style={{ color: "#1A1A1A" }}>Custom</p>
              <p className="text-[12px] mt-2" style={{ color: "#8A8A8A" }}>Unlimited Agents</p>
            </div>
            <ul className="flex flex-col gap-4 mb-10 flex-grow list-none">
              {["On-prem deployment", "Custom agent training", "Dedicated manager"].map((f) => (
                <li key={f} className="flex items-center gap-3 text-[14px] font-medium">
                  <Check size={16} style={{ color: "#1B4332", flexShrink: 0 }} />
                  {f}
                </li>
              ))}
            </ul>
            <Link
              href="/contact"
              className="block w-full text-center rounded-[10px] py-3 text-[14px] font-bold no-underline transition-all hover:bg-[#E8E6E1]"
              style={{ border: "1px solid #E8E6E1", color: "#8A8A8A" }}
            >
              Contact Sales
            </Link>
          </div>
        </div>

        <p className="text-center text-[14px] mt-10" style={{ color: "#8A8A8A" }}>
          Your agents work better together. Start with one.
        </p>
      </div>
    </section>
  );
}
