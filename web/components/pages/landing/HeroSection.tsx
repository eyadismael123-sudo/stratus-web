"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger);

const NAV_LINKS = [
  { label: "Marketplace", href: "/marketplace" },
  { label: "Pricing", href: "#pricing" },
  { label: "About", href: "/about" },
];

export function HeroSection() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const heroRef = useRef<HTMLElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const subtextRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const pillsRef = useRef<HTMLDivElement>(null);
  const eyebrowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // GSAP entrance animations
  useGSAP(() => {
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    tl.fromTo(
      eyebrowRef.current,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.6 }
    )
      .fromTo(
        headlineRef.current,
        { opacity: 0, y: 40 },
        { opacity: 1, y: 0, duration: 0.8 },
        "-=0.3"
      )
      .fromTo(
        subtextRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6 },
        "-=0.4"
      )
      .fromTo(
        ctaRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6 },
        "-=0.3"
      )
      .fromTo(
        pillsRef.current,
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, duration: 0.5 },
        "-=0.2"
      );

  }, { scope: heroRef });

  return (
    <>
      {/* Global grain texture overlay */}
      <div className="grain-overlay" />

      {/* ── Nav ── */}
      <nav
        className="fixed top-0 left-0 right-0 z-[200] h-[60px] flex items-center justify-between px-6 md:px-10 transition-all duration-300"
        style={
          scrolled
            ? {
                background: "rgba(250,249,246,0.85)",
                backdropFilter: "blur(20px) saturate(180%)",
                WebkitBackdropFilter: "blur(20px) saturate(180%)",
                borderBottom: "1px solid #E8E6E1",
              }
            : { background: "transparent" }
        }
      >
        <Link
          href="/"
          className="flex items-center gap-2 no-underline"
        >
          <Image
            src="/logo.png"
            alt="Stratus"
            width={28}
            height={28}
            className="rounded-[6px]"
          />
          <span className="font-display text-[18px] font-bold tracking-[-0.03em]" style={{ color: "#1A1A1A" }}>
            Stratus
          </span>
        </Link>

        {/* Desktop links */}
        <ul className="hidden md:flex items-center gap-8 list-none">
          {NAV_LINKS.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="text-[14px] font-medium no-underline hover:text-[#1B4332] transition-colors"
                style={{ color: "#4A4A4A" }}
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>

        {/* Desktop actions */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/agents/linkedin-post-agent"
            className="text-[14px] font-bold text-white rounded-[8px] px-[18px] py-2 no-underline hover:bg-[#2D6A4F] hover:-translate-y-px transition-all"
            style={{
              background: "#1B4332",
              boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
            }}
          >
            Get Started
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2"
          style={{ color: "#1A1A1A" }}
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            {menuOpen ? (
              <>
                <line x1="3" y1="3" x2="19" y2="19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                <line x1="19" y1="3" x2="3" y2="19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </>
            ) : (
              <>
                <line x1="3" y1="6" x2="19" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                <line x1="3" y1="11" x2="19" y2="11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                <line x1="3" y1="16" x2="19" y2="16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </>
            )}
          </svg>
        </button>

        {/* Mobile menu */}
        {menuOpen && (
          <div
            className="absolute top-[60px] left-0 right-0 flex flex-col px-6 py-6 gap-4"
            style={{
              background: "rgba(250,249,246,0.97)",
              backdropFilter: "blur(20px)",
              borderBottom: "1px solid #E8E6E1",
            }}
          >
            {NAV_LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="text-[15px] font-medium no-underline"
                style={{ color: "#4A4A4A" }}
                onClick={() => setMenuOpen(false)}
              >
                {l.label}
              </Link>
            ))}
            <Link
              href="/marketplace"
              className="text-[15px] font-bold text-white rounded-[8px] px-5 py-3 no-underline text-center"
              style={{ background: "#1B4332" }}
              onClick={() => setMenuOpen(false)}
            >
              Hire an agent
            </Link>
          </div>
        )}
      </nav>

      {/* ── Hero ── */}
      <section
        ref={heroRef}
        className="relative overflow-hidden pt-[60px]"
        style={{ background: "#FAF9F6" }}
      >
        <div className="max-w-[1440px] mx-auto px-6 md:px-12 pt-20 pb-24">
          <div className="grid md:grid-cols-2 gap-12 items-center">

            {/* Left — headline + CTAs */}
            <div className="z-10">
              {/* Eyebrow */}
              <div
                ref={eyebrowRef}
                className="inline-flex items-center gap-2 mb-8 px-4 py-1.5 rounded-full text-[13px] font-semibold opacity-0"
                style={{
                  color: "#4A4A4A",
                  background: "#FFFFFF",
                  border: "1px solid #E8E6E1",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                }}
              >
                <span className="status-dot-online" style={{ width: "6px", height: "6px" }} />
                Your AI employee is ready to hire
              </div>

              {/* Headline */}
              <h1
                ref={headlineRef}
                className="font-display font-bold leading-[0.92] tracking-[-0.04em] mb-8 opacity-0"
                style={{ fontSize: "clamp(48px, 7vw, 88px)", color: "#1B4332" }}
              >
                Your AI workforce.<br />Built for MENA.
              </h1>

              {/* Subtext */}
              <p
                ref={subtextRef}
                className="mb-10 max-w-md opacity-0"
                style={{ fontSize: "20px", color: "#4A4A4A", lineHeight: 1.6 }}
              >
                Automate operations with culture-aware AI agents designed for the growth dynamics of the Middle East. Starting at $49/month.
              </p>

              {/* CTAs */}
              <div ref={ctaRef} className="flex flex-wrap gap-4 opacity-0">
                <Link
                  href="/agents/linkedin-post-agent"
                  className="inline-flex items-center gap-2 text-[16px] font-bold text-white rounded-[10px] px-8 py-4 no-underline hover:bg-[#2D6A4F] hover:-translate-y-0.5 transition-all"
                  style={{
                    background: "#1B4332",
                    boxShadow: "0 4px 20px rgba(27,67,50,0.18)",
                  }}
                >
                  Hire an Agent
                </Link>
                <Link
                  href="#how-it-works"
                  className="inline-flex items-center gap-2 text-[16px] font-semibold rounded-[10px] px-8 py-4 no-underline hover:bg-[#E8E6E1] transition-all"
                  style={{ color: "#1B4332", background: "#FFFFFF", border: "1px solid #E8E6E1" }}
                >
                  See how it works
                </Link>
              </div>
            </div>

            {/* Right — live agent dashboard widget */}
            <div
              ref={pillsRef}
              className="relative opacity-0"
            >
              <div
                className="rounded-[20px] p-6"
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #E8E6E1",
                  boxShadow: "0 12px 32px rgba(27,67,50,0.06)",
                }}
              >
                <div className="flex items-center justify-between mb-8">
                  <span
                    className="text-[11px] font-bold tracking-widest uppercase"
                    style={{ color: "rgba(26,28,26,0.4)" }}
                  >
                    Active Agents
                  </span>
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full" style={{ background: "rgba(186,26,26,0.2)" }} />
                    <div className="w-2 h-2 rounded-full" style={{ background: "rgba(44,105,78,0.2)" }} />
                    <div className="w-2 h-2 rounded-full" style={{ background: "rgba(1,45,29,0.2)" }} />
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  {/* Frame — LinkedIn Post Agent */}
                  <div
                    className="flex items-center justify-between p-4 rounded-[12px]"
                    style={{ background: "#FAF9F6", border: "1px solid #AEEECB" }}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-bold flex-shrink-0"
                        style={{ background: "#1B4332", color: "#FFFFFF" }}
                      >
                        Fr
                      </div>
                      <div>
                        <p className="text-[14px] font-bold" style={{ color: "#1A1A1A" }}>Frame</p>
                        <p className="text-[12px]" style={{ color: "#8A8A8A" }}>Drafting today&apos;s LinkedIn post</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ background: "#10b981", animation: "pulse-dot 2s ease-in-out infinite" }}
                      />
                      <span className="text-[12px] font-bold" style={{ color: "#10b981" }}>Active</span>
                    </div>
                  </div>

                  {/* Scout — Car Reseller Intel */}
                  <div
                    className="flex items-center justify-between p-4 rounded-[12px]"
                    style={{ background: "#FAF9F6" }}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-bold flex-shrink-0"
                        style={{ background: "#E8F5EF", color: "#1B4332" }}
                      >
                        Sc
                      </div>
                      <div>
                        <p className="text-[14px] font-bold" style={{ color: "#1A1A1A" }}>Scout</p>
                        <p className="text-[12px]" style={{ color: "#8A8A8A" }}>Found 4 underpriced listings</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ background: "#10b981" }}
                      />
                      <span className="text-[12px] font-bold" style={{ color: "#10b981" }}>Done</span>
                    </div>
                  </div>

                  {/* Brief — Doctor Morning Briefing */}
                  <div
                    className="flex items-center justify-between p-4 rounded-[12px]"
                    style={{ background: "#FAF9F6" }}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-bold flex-shrink-0"
                        style={{ background: "#E8F5EF", color: "#1B4332" }}
                      >
                        Br
                      </div>
                      <div>
                        <p className="text-[14px] font-bold" style={{ color: "#1A1A1A" }}>Brief</p>
                        <p className="text-[12px]" style={{ color: "#8A8A8A" }}>Prepping tomorrow&apos;s patient brief</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ background: "#10b981", animation: "pulse-dot 2s ease-in-out infinite" }}
                      />
                      <span className="text-[12px] font-bold" style={{ color: "#10b981" }}>Active</span>
                    </div>
                  </div>
                </div>

                {/* Bottom stat */}
                <div
                  className="mt-6 pt-5 flex justify-between items-end"
                  style={{ borderTop: "1px solid #E8E6E1" }}
                >
                  <div>
                    <p className="text-[32px] font-black leading-none" style={{ color: "#1B4332" }}>1.2k</p>
                    <p className="text-[11px] font-bold uppercase tracking-tight mt-1" style={{ color: "#8A8A8A" }}>
                      Tasks completed today
                    </p>
                  </div>
                  {/* Mini bar chart */}
                  <div
                    className="flex items-end gap-1 p-2 rounded-[8px]"
                    style={{ background: "rgba(174,238,203,0.3)", height: "48px", width: "80px" }}
                  >
                    {[40, 60, 90, 75, 100].map((h, i) => (
                      <div
                        key={i}
                        className="flex-1 rounded-sm"
                        style={{ height: `${h}%`, background: "#2C694E" }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Decorative blur */}
              <div
                className="absolute -z-10 pointer-events-none rounded-full"
                style={{
                  width: "300px",
                  height: "300px",
                  bottom: "-40px",
                  right: "-40px",
                  background: "radial-gradient(circle, rgba(27,67,50,0.05) 0%, transparent 70%)",
                }}
              />
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
