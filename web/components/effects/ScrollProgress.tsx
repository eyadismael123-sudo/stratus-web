"use client";

import { useEffect, useRef } from "react";

export function ScrollProgress() {
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onScroll = () => {
      const bar = barRef.current;
      if (!bar) return;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
      bar.style.transform = `scaleX(${pct / 100})`;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[300] pointer-events-none"
      style={{ height: 2 }}
    >
      <div
        ref={barRef}
        style={{
          height: "100%",
          background: "linear-gradient(90deg, #EB0043 0%, #FF99A8 50%, #EB0043 100%)",
          transformOrigin: "left center",
          transform: "scaleX(0)",
          transition: "transform 0.1s linear",
          boxShadow: "0 0 12px rgba(235,0,67,0.4)",
        }}
      />
    </div>
  );
}
