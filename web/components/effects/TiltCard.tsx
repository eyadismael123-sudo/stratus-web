"use client";

import { ReactNode, useCallback, useRef } from "react";
import { gsap } from "gsap";

interface TiltCardProps {
  children: ReactNode;
  className?: string;
  style?: React.CSSProperties;
  maxTilt?: number;
  scale?: number;
}

export function TiltCard({
  children,
  className,
  style,
  maxTilt = 6,
  scale = 1.015,
}: TiltCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const glareRef = useRef<HTMLDivElement>(null);

  const onMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const el = ref.current;
      const glare = glareRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      const tiltX = -(y - 0.5) * 2 * maxTilt;
      const tiltY = (x - 0.5) * 2 * maxTilt;
      gsap.to(el, {
        rotateX: tiltX,
        rotateY: tiltY,
        scale,
        duration: 0.4,
        ease: "power2.out",
        transformPerspective: 900,
        overwrite: "auto",
      });
      if (glare) {
        glare.style.opacity = "1";
        glare.style.background = `radial-gradient(circle at ${x * 100}% ${y * 100}%, rgba(255,255,255,0.5), transparent 50%)`;
      }
    },
    [maxTilt, scale]
  );

  const onLeave = useCallback(() => {
    const el = ref.current;
    const glare = glareRef.current;
    if (!el) return;
    gsap.to(el, {
      rotateX: 0,
      rotateY: 0,
      scale: 1,
      duration: 0.6,
      ease: "power3.out",
    });
    if (glare) glare.style.opacity = "0";
  }, []);

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className={className}
      style={{ ...style, willChange: "transform", position: "relative" }}
    >
      {children}
      <div
        ref={glareRef}
        aria-hidden="true"
        className="absolute inset-0 rounded-[inherit] pointer-events-none"
        style={{
          opacity: 0,
          transition: "opacity 0.3s ease",
          mixBlendMode: "overlay",
        }}
      />
    </div>
  );
}
