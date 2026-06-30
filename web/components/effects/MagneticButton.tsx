"use client";

import { ReactNode, useRef } from "react";
import { gsap } from "gsap";

interface MagneticButtonProps {
  children: ReactNode;
  className?: string;
  strength?: number;
}

export function MagneticButton({ children, className, strength = 0.4 }: MagneticButtonProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const wrap = wrapRef.current;
    const inner = innerRef.current;
    if (!wrap || !inner) return;
    const rect = wrap.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) * strength;
    const y = (e.clientY - rect.top - rect.height / 2) * strength;
    gsap.to(inner, { x, y, duration: 0.4, ease: "power3.out", overwrite: "auto" });
  };

  const onLeave = () => {
    const inner = innerRef.current;
    if (!inner) return;
    gsap.to(inner, { x: 0, y: 0, duration: 0.6, ease: "elastic.out(1, 0.4)" });
  };

  return (
    <div
      ref={wrapRef}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className={className}
      style={{ display: "inline-block" }}
    >
      <div ref={innerRef} style={{ willChange: "transform" }}>
        {children}
      </div>
    </div>
  );
}
