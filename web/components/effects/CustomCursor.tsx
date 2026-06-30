"use client";

import { useEffect, useRef, useState } from "react";

export function CustomCursor() {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(hover: none)").matches) return;
    setMounted(true);
    document.body.classList.add("has-custom-cursor");

    const dot = dotRef.current;
    const ring = ringRef.current;
    if (!dot || !ring) return;

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let ringX = mouseX;
    let ringY = mouseY;
    let rafId = 0;

    const tick = () => {
      ringX += (mouseX - ringX) * 0.18;
      ringY += (mouseY - ringY) * 0.18;
      dot.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0)`;
      ring.style.transform = `translate3d(${ringX}px, ${ringY}px, 0) translate(-50%, -50%) scale(var(--cursor-scale, 1))`;
      rafId = requestAnimationFrame(tick);
    };

    const onMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };

    const isInteractive = (el: EventTarget | null): boolean => {
      if (!(el instanceof Element)) return false;
      return !!el.closest("a, button, [data-cursor='hover'], input, textarea, select, [role='button']");
    };

    const onOver = (e: MouseEvent) => {
      if (isInteractive(e.target)) {
        ring.style.setProperty("--cursor-scale", "1.8");
        ring.dataset.hovering = "true";
      }
    };
    const onOut = (e: MouseEvent) => {
      if (isInteractive(e.target)) {
        ring.style.setProperty("--cursor-scale", "1");
        ring.dataset.hovering = "false";
      }
    };

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseover", onOver);
    window.addEventListener("mouseout", onOut);
    tick();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseover", onOver);
      window.removeEventListener("mouseout", onOut);
      document.body.classList.remove("has-custom-cursor");
    };
  }, []);

  if (!mounted) return null;

  return (
    <>
      <div
        ref={dotRef}
        className="custom-cursor-dot pointer-events-none fixed top-0 left-0 z-[9999] -translate-x-1/2 -translate-y-1/2"
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: "#EB0043",
          mixBlendMode: "normal",
        }}
      />
      <div
        ref={ringRef}
        className="custom-cursor-ring pointer-events-none fixed top-0 left-0 z-[9998]"
        style={{
          width: 36,
          height: 36,
          borderRadius: "50%",
          border: "1.5px solid #EB0043",
          transition: "border-color 0.2s ease, background 0.2s ease",
          willChange: "transform",
        }}
      />
    </>
  );
}
