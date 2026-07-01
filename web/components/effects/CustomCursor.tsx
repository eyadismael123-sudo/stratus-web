"use client";

import { useEffect, useRef, useState } from "react";

export function CustomCursor() {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const [enabled, setEnabled] = useState(false);

  // Detect hover capability — runs once, paints the divs on next render
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(hover: none)").matches) return;
    setEnabled(true);
    document.body.classList.add("has-custom-cursor");
    return () => {
      document.body.classList.remove("has-custom-cursor");
    };
  }, []);

  // Wire up the RAF loop AFTER the divs exist
  useEffect(() => {
    if (!enabled) return;
    const dot = dotRef.current;
    const ring = ringRef.current;
    if (!dot || !ring) return;

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let ringX = mouseX;
    let ringY = mouseY;
    let visible = false;
    let rafId = 0;

    const tick = () => {
      ringX += (mouseX - ringX) * 0.18;
      ringY += (mouseY - ringY) * 0.18;
      dot.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0) translate(-50%, -50%)`;
      ring.style.transform = `translate3d(${ringX}px, ${ringY}px, 0) translate(-50%, -50%) scale(var(--cursor-scale, 1))`;
      rafId = requestAnimationFrame(tick);
    };

    const onMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (!visible) {
        dot.style.opacity = "1";
        ring.style.opacity = "1";
        visible = true;
      }
    };

    const onLeaveWindow = () => {
      dot.style.opacity = "0";
      ring.style.opacity = "0";
      visible = false;
    };
    const onEnterWindow = () => {
      dot.style.opacity = "1";
      ring.style.opacity = "1";
      visible = true;
    };

    const isInteractive = (el: EventTarget | null): boolean => {
      if (!(el instanceof Element)) return false;
      return !!el.closest("a, button, [data-cursor='hover'], input, textarea, select, [role='button']");
    };

    const onOver = (e: MouseEvent) => {
      if (isInteractive(e.target)) {
        ring.style.setProperty("--cursor-scale", "1.8");
        ring.style.background = "rgba(235,0,67,0.12)";
      }
    };
    const onOut = (e: MouseEvent) => {
      if (isInteractive(e.target)) {
        ring.style.setProperty("--cursor-scale", "1");
        ring.style.background = "transparent";
      }
    };

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseover", onOver);
    window.addEventListener("mouseout", onOut);
    document.addEventListener("mouseleave", onLeaveWindow);
    document.addEventListener("mouseenter", onEnterWindow);
    tick();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseover", onOver);
      window.removeEventListener("mouseout", onOut);
      document.removeEventListener("mouseleave", onLeaveWindow);
      document.removeEventListener("mouseenter", onEnterWindow);
    };
  }, [enabled]);

  if (!enabled) return null;

  return (
    <>
      <div
        ref={dotRef}
        className="pointer-events-none fixed top-0 left-0 z-[9999]"
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: "#EB0043",
          opacity: 0,
          transition: "opacity 0.2s ease",
          willChange: "transform",
          boxShadow: "0 0 12px rgba(235,0,67,0.5)",
        }}
      />
      <div
        ref={ringRef}
        className="pointer-events-none fixed top-0 left-0 z-[9998]"
        style={{
          width: 36,
          height: 36,
          borderRadius: "50%",
          border: "1.5px solid #EB0043",
          opacity: 0,
          transition: "opacity 0.2s ease, background 0.25s ease, border-color 0.25s ease",
          willChange: "transform",
        }}
      />
    </>
  );
}
