"use client";

import { useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger);

interface Stat {
  value: string;
  label: string;
  countTo?: number;
  format?: (v: number) => string;
}

const STATS: Stat[] = [
  {
    value: "5+",
    label: "AI Agents",
    countTo: 5,
    format: (v) => Math.round(v) + "+",
  },
  { value: "MENA 🌍", label: "Locally Optimized" },
  { value: "Daily", label: "Briefings" },
  {
    value: "From $49",
    label: "Per Agent / mo",
    countTo: 49,
    format: (v) => "From $" + Math.round(v),
  },
];

function StatItem({ stat, index }: { stat: Stat; index: number }) {
  const itemRef = useRef<HTMLDivElement>(null);
  const valueRef = useRef<HTMLParagraphElement>(null);

  useGSAP(() => {
    if (!itemRef.current) return;
    gsap.fromTo(
      itemRef.current,
      { opacity: 0, y: 20 },
      {
        opacity: 1,
        y: 0,
        duration: 0.6,
        delay: index * 0.08,
        ease: "power3.out",
        scrollTrigger: {
          trigger: itemRef.current,
          start: "top 88%",
          once: true,
        },
      },
    );

    if (stat.countTo && stat.format && valueRef.current) {
      const counter = { val: 0 };
      gsap.to(counter, {
        val: stat.countTo,
        duration: 1.4,
        delay: 0.15 + index * 0.08,
        ease: "power2.out",
        onUpdate() {
          if (valueRef.current && stat.format) {
            valueRef.current.textContent = stat.format(counter.val);
          }
        },
        scrollTrigger: {
          trigger: itemRef.current,
          start: "top 88%",
          once: true,
        },
      });
    }
  }, { scope: itemRef });

  return (
    <div
      ref={itemRef}
      className="py-10 px-8 text-center md:text-left opacity-0 transition-colors hover:bg-[#B5C9C0]"
      style={{ background: "#CCDAD1" }}
    >
      <p
        ref={valueRef}
        className="text-[36px] font-black leading-none mb-2"
        style={{ color: "#EB0043" }}
      >
        {stat.countTo && stat.format ? stat.format(0) : stat.value}
      </p>
      <p className="text-[13px] font-bold uppercase tracking-tight" style={{ color: "#8A8A8A" }}>
        {stat.label}
      </p>
    </div>
  );
}

export function StatsStrip() {
  return (
    <section style={{ background: "#B5C9C0" }}>
      <div className="max-w-[1440px] mx-auto px-6 md:px-12">
        <div
          className="grid grid-cols-2 md:grid-cols-4"
          style={{ gap: "1px", background: "rgba(193,200,194,0.4)" }}
        >
          {STATS.map((stat, i) => (
            <StatItem key={stat.label} stat={stat} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
