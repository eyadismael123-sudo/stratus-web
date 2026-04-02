"use client";

import { useRef } from "react";
import Link from "next/link";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger);

export function FinalCTASection() {
  const sectionRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!contentRef.current) return;
    gsap.fromTo(
      contentRef.current,
      { opacity: 0, y: 30 },
      {
        opacity: 1,
        y: 0,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: {
          trigger: contentRef.current,
          start: "top 85%",
          once: true,
        },
      },
    );
  }, { scope: sectionRef });

  return (
    <section
      ref={sectionRef}
      className="py-32 px-6 text-center"
      style={{ background: "#EFEEEB", borderTop: "1px solid #E8E6E1" }}
    >
      <div ref={contentRef} className="max-w-3xl mx-auto opacity-0">
        <h2
          className="font-display font-bold tracking-[-0.04em] leading-tight mb-8"
          style={{ fontSize: "clamp(36px, 5vw, 60px)", color: "#1B4332" }}
        >
          Ready to hire your first
          <br />
          AI employee?
        </h2>
        <p
          className="text-[18px] mb-12 max-w-xl mx-auto leading-relaxed"
          style={{ color: "#8A8A8A" }}
        >
          Join leading individuals and businesses across MENA. It takes less than 5 minutes to get started.
        </p>
        <div className="flex flex-col md:flex-row items-center justify-center gap-4">
          <Link
            href="/agents/linkedin-post-agent"
            className="inline-flex items-center text-[18px] font-black text-white rounded-[12px] px-10 py-5 no-underline hover:bg-[#2D6A4F] transition-all"
            style={{
              background: "#1B4332",
              boxShadow: "0 8px 32px rgba(27,67,50,0.15)",
            }}
          >
            Hire an Agent
          </Link>
          <Link
            href="/contact"
            className="inline-flex items-center text-[18px] font-black rounded-[12px] px-10 py-5 no-underline hover:bg-white transition-all"
            style={{
              background: "#FFFFFF",
              color: "#1B4332",
              border: "1px solid #E8E6E1",
            }}
          >
            Talk to Support
          </Link>
        </div>
      </div>
    </section>
  );
}
