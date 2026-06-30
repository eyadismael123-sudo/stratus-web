"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import { AuroraMesh } from "../../effects/AuroraMesh";
import { MagneticButton } from "../../effects/MagneticButton";
import { FloatingPings } from "../../effects/FloatingPings";
import { burstConfetti } from "../../effects/Confetti";

gsap.registerPlugin(ScrollTrigger);

const NAV_LINKS = [
  { label: "Marketplace", href: "/marketplace" },
  { label: "Pricing", href: "#pricing" },
  { label: "About", href: "/about" },
];

const BAR_HEIGHTS = [40, 60, 90, 75, 100];

const FRAME_STATUSES = [
  "Drafting today's LinkedIn post",
  "Studying your top 3 performing posts",
  "Adjusting tone — more direct",
  "Scheduling for 8:42am Tue + Thu",
  "Reviewing audience signals",
];

export function HeroSection() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [statusIndex, setStatusIndex] = useState(0);
  const [typedText, setTypedText] = useState("");
  const [typingDone, setTypingDone] = useState(false);
  const heroRef = useRef<HTMLElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const subtextRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const pillsRef = useRef<HTMLDivElement>(null);
  const eyebrowRef = useRef<HTMLDivElement>(null);
  const statRef = useRef<HTMLSpanElement>(null);
  const barsRef = useRef<HTMLDivElement>(null);
  const primaryCtaRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Mouse parallax — widget drifts with cursor
  useEffect(() => {
    const hero = heroRef.current;
    const widget = pillsRef.current;
    if (!hero || !widget) return;

    let rafId: number;
    const onMove = (e: MouseEvent) => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        const rect = hero.getBoundingClientRect();
        const x = (e.clientX - rect.left - rect.width / 2) / rect.width;
        const y = (e.clientY - rect.top - rect.height / 2) / rect.height;
        gsap.to(widget, { x: x * 16, y: y * 10, duration: 0.9, ease: "power2.out", overwrite: "auto" });
      });
    };
    const onLeave = () => {
      gsap.to(widget, { x: 0, y: 0, duration: 1, ease: "power3.out" });
    };

    hero.addEventListener("mousemove", onMove);
    hero.addEventListener("mouseleave", onLeave);
    return () => {
      cancelAnimationFrame(rafId);
      hero.removeEventListener("mousemove", onMove);
      hero.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  // Looping typewriter — cycles through Frame statuses
  useEffect(() => {
    const target = FRAME_STATUSES[statusIndex];
    let i = 0;
    let typingInterval: ReturnType<typeof setInterval>;
    let holdTimer: ReturnType<typeof setTimeout>;
    let eraseInterval: ReturnType<typeof setInterval>;

    const startDelay = setTimeout(() => {
      setTypingDone(false);
      typingInterval = setInterval(() => {
        i++;
        setTypedText(target.slice(0, i));
        if (i >= target.length) {
          clearInterval(typingInterval);
          setTypingDone(true);
          holdTimer = setTimeout(() => {
            let j = target.length;
            eraseInterval = setInterval(() => {
              j--;
              setTypedText(target.slice(0, j));
              if (j <= 0) {
                clearInterval(eraseInterval);
                setStatusIndex((s) => (s + 1) % FRAME_STATUSES.length);
              }
            }, 22);
          }, 1800);
        }
      }, 50);
    }, statusIndex === 0 ? 1600 : 200);

    return () => {
      clearTimeout(startDelay);
      clearInterval(typingInterval);
      clearTimeout(holdTimer);
      clearInterval(eraseInterval);
    };
  }, [statusIndex]);

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

    if (barsRef.current) {
      const bars = barsRef.current.querySelectorAll(".hero-bar");
      tl.fromTo(
        bars,
        { scaleY: 0, transformOrigin: "bottom" },
        { scaleY: 1, duration: 0.5, stagger: 0.08, ease: "back.out(1.6)" },
        "-=0.15"
      );
    }

    if (statRef.current) {
      const counter = { val: 0 };
      tl.to(
        counter,
        {
          val: 1200,
          duration: 1.8,
          ease: "power2.out",
          onUpdate() {
            if (!statRef.current) return;
            const v = Math.round(counter.val);
            statRef.current.textContent = v >= 1000 ? (v / 1000).toFixed(1) + "k" : String(v);
          },
        },
        "-=0.4"
      );
    }
  }, { scope: heroRef });

  const onPrimaryCtaClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    const rect = primaryCtaRef.current?.getBoundingClientRect();
    if (rect) {
      burstConfetti(rect.left + rect.width / 2, rect.top + rect.height / 2, 42);
    }
    // Let navigation continue after a tick so confetti shows briefly
    e.preventDefault();
    const href = primaryCtaRef.current?.getAttribute("href") ?? "/agents/linkedin-post-agent";
    setTimeout(() => {
      window.location.href = href;
    }, 350);
  };

  return (
    <>
      <div className="grain-overlay" />

      <nav
        className="fixed top-0 left-0 right-0 z-[200] h-[60px] flex items-center justify-between px-6 md:px-10 transition-all duration-300"
        style={
          scrolled
            ? {
                background: "rgba(250,249,246,0.85)",
                backdropFilter: "blur(20px) saturate(180%)",
                WebkitBackdropFilter: "blur(20px) saturate(180%)",
                borderBottom: "1px solid #B5C9C0",
              }
            : { background: "transparent" }
        }
      >
        <Link href="/" className="flex items-center gap-2 no-underline">
          <Image src="/logo.png" alt="Stratus" width={28} height={28} className="rounded-[6px]" />
          <span className="font-display text-[18px] font-bold tracking-[-0.03em]" style={{ color: "#2E4057" }}>
            Stratus
          </span>
        </Link>

        <ul className="hidden md:flex items-center gap-8 list-none">
          {NAV_LINKS.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="text-[14px] font-medium no-underline hover:text-[#EB0043] transition-colors"
                style={{ color: "#4A4A4A" }}
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/agents/linkedin-post-agent"
            className="text-[14px] font-bold text-white rounded-[8px] px-[18px] py-2 no-underline hover:bg-[#4E0110] hover:-translate-y-px transition-all"
            style={{ background: "#EB0043", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}
          >
            Get Started
          </Link>
        </div>

        <button
          className="md:hidden p-2"
          style={{ color: "#2E4057" }}
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

        {menuOpen && (
          <div
            className="absolute top-[60px] left-0 right-0 flex flex-col px-6 py-6 gap-4"
            style={{
              background: "rgba(250,249,246,0.97)",
              backdropFilter: "blur(20px)",
              borderBottom: "1px solid #B5C9C0",
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
              style={{ background: "#EB0043" }}
              onClick={() => setMenuOpen(false)}
            >
              Hire an agent
            </Link>
          </div>
        )}
      </nav>

      <section
        ref={heroRef}
        className="relative overflow-hidden pt-[60px]"
        style={{ background: "#CCDAD1" }}
      >
        {/* Aurora mesh background */}
        <AuroraMesh />

        {/* Mascot — happy octopus sitting at bottom-right corner */}
        <img
          src="/mascot-happy.png"
          alt=""
          aria-hidden="true"
          className="absolute bottom-0 right-10 pointer-events-none select-none hidden md:block"
          style={{ width: "150px", transform: "translateY(6%)", zIndex: 1 }}
        />

        <div className="relative z-10 max-w-[1440px] mx-auto px-6 md:px-12 pt-20 pb-24">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left — headline + CTAs */}
            <div className="z-10">
              <div
                ref={eyebrowRef}
                className="inline-flex items-center gap-2 mb-8 px-4 py-1.5 rounded-full text-[13px] font-semibold opacity-0"
                style={{
                  color: "#4A4A4A",
                  background: "#FFFFFF",
                  border: "1px solid #B5C9C0",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                }}
              >
                <span className="status-dot-online" style={{ width: "6px", height: "6px" }} />
                Your AI employee is ready to hire
              </div>

              <h1
                ref={headlineRef}
                className="font-display font-bold leading-[0.92] tracking-[-0.04em] mb-8 opacity-0"
                style={{ fontSize: "clamp(48px, 7vw, 88px)", color: "#EB0043" }}
              >
                Your AI workforce.
                <br />
                Built for{" "}
                <span className="relative inline-block">
                  MENA
                  <svg
                    className="absolute left-0 -bottom-2 w-full pointer-events-none"
                    height="14"
                    viewBox="0 0 200 14"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                  >
                    <path
                      d="M2 8 C 40 2, 80 12, 120 6 S 180 4, 198 8"
                      stroke="#EB0043"
                      strokeWidth="3"
                      strokeLinecap="round"
                      fill="none"
                      className="underline-draw"
                    />
                  </svg>
                </span>
                .
              </h1>

              <p
                ref={subtextRef}
                className="mb-10 max-w-md opacity-0"
                style={{ fontSize: "20px", color: "#4A4A4A", lineHeight: 1.6 }}
              >
                Automate operations with culture-aware AI agents designed for the growth dynamics of the Middle East. Starting at $49/month.
              </p>

              <div ref={ctaRef} className="flex flex-wrap gap-4 opacity-0">
                <MagneticButton strength={0.35}>
                  <a
                    ref={primaryCtaRef}
                    href="/agents/linkedin-post-agent"
                    onClick={onPrimaryCtaClick}
                    className="inline-flex items-center gap-2 text-[16px] font-bold text-white rounded-[10px] px-8 py-4 no-underline hover:bg-[#4E0110] transition-colors"
                    style={{
                      background: "#EB0043",
                      boxShadow: "0 4px 20px rgba(27,67,50,0.18)",
                    }}
                  >
                    Hire an Agent
                  </a>
                </MagneticButton>
                <MagneticButton strength={0.25}>
                  <Link
                    href="#how-it-works"
                    className="inline-flex items-center gap-2 text-[16px] font-semibold rounded-[10px] px-8 py-4 no-underline hover:bg-[#B5C9C0] transition-colors"
                    style={{ color: "#EB0043", background: "#FFFFFF", border: "1px solid #B5C9C0" }}
                  >
                    See how it works
                  </Link>
                </MagneticButton>
              </div>
            </div>

            {/* Right — live agent dashboard widget */}
            <div
              ref={pillsRef}
              className="relative opacity-0"
              style={{ willChange: "transform" }}
            >
              {/* Floating live notifications */}
              <FloatingPings />

              <div
                className="rounded-[20px] p-6"
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #B5C9C0",
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
                  <div
                    className="flex items-center justify-between p-4 rounded-[12px]"
                    style={{ background: "#CCDAD1", border: "1px solid #FF99A8" }}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-bold flex-shrink-0"
                        style={{ background: "#EB0043", color: "#FFFFFF" }}
                      >
                        Fr
                      </div>
                      <div>
                        <p className="text-[14px] font-bold" style={{ color: "#2E4057" }}>Frame</p>
                        <p className="text-[12px] font-mono" style={{ color: "#8A8A8A", minHeight: "16px" }}>
                          {typedText || " "}
                          <span
                            className="inline-block w-[2px] h-[12px] ml-[1px] align-middle"
                            style={{
                              background: "#8A8A8A",
                              animation: typingDone ? "blink-cursor 0.9s step-end infinite" : "none",
                            }}
                          />
                        </p>
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

                  <div
                    className="flex items-center justify-between p-4 rounded-[12px]"
                    style={{ background: "#CCDAD1" }}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-bold flex-shrink-0"
                        style={{ background: "#FFD5DC", color: "#EB0043" }}
                      >
                        Sc
                      </div>
                      <div>
                        <p className="text-[14px] font-bold" style={{ color: "#2E4057" }}>Scout</p>
                        <p className="text-[12px]" style={{ color: "#8A8A8A" }}>Found 4 underpriced listings</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ background: "#10b981" }} />
                      <span className="text-[12px] font-bold" style={{ color: "#10b981" }}>Done</span>
                    </div>
                  </div>

                  <div
                    className="flex items-center justify-between p-4 rounded-[12px]"
                    style={{ background: "#CCDAD1" }}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-bold flex-shrink-0"
                        style={{ background: "#FFD5DC", color: "#EB0043" }}
                      >
                        Br
                      </div>
                      <div>
                        <p className="text-[14px] font-bold" style={{ color: "#2E4057" }}>Brief</p>
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

                <div
                  className="mt-6 pt-5 flex justify-between items-end"
                  style={{ borderTop: "1px solid #B5C9C0" }}
                >
                  <div>
                    <p className="text-[32px] font-black leading-none" style={{ color: "#EB0043" }}>
                      <span ref={statRef}>0</span>
                    </p>
                    <p className="text-[11px] font-bold uppercase tracking-tight mt-1" style={{ color: "#8A8A8A" }}>
                      Tasks completed today
                    </p>
                  </div>
                  <div
                    ref={barsRef}
                    className="flex items-end gap-1 p-2 rounded-[8px]"
                    style={{ background: "rgba(174,238,203,0.3)", height: "48px", width: "80px" }}
                  >
                    {BAR_HEIGHTS.map((h, i) => (
                      <div
                        key={i}
                        className="hero-bar flex-1 rounded-sm"
                        style={{ height: `${h}%`, background: "#2C694E" }}
                      />
                    ))}
                  </div>
                </div>
              </div>

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
