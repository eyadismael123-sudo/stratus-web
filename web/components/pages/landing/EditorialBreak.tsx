"use client";

import { useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger);

export function EditorialBreak() {
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
        duration: 0.8,
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
      className="py-32 text-center px-6"
      style={{ background: "#1B4332" }}
    >
      <div ref={contentRef} className="max-w-4xl mx-auto opacity-0">
        <p
          className="text-[12px] font-bold tracking-[0.4em] uppercase mb-8"
          style={{ color: "rgba(161,210,185,0.6)" }}
        >
          Continuous Performance
        </p>
        <h2
          className="font-display font-bold tracking-[-0.04em] leading-tight mb-10"
          style={{ fontSize: "clamp(40px, 6vw, 72px)", color: "#FAF9F6" }}
        >
          Your team never sleeps.
        </h2>
        <p
          className="text-[20px] max-w-2xl mx-auto leading-relaxed italic"
          style={{ color: "rgba(161,210,185,0.8)" }}
        >
          &ldquo;Stratus allows us to scale our operations across three time zones in the GCC without adding a single headcount.&rdquo;
        </p>
        <div className="mt-12 flex flex-col items-center">
          <div className="w-12 mb-6" style={{ height: "1px", background: "rgba(161,210,185,0.3)" }} />
          <p className="text-[14px] font-bold" style={{ color: "#FAF9F6" }}>— A Stratus client</p>
        </div>
      </div>
    </section>
  );
}
