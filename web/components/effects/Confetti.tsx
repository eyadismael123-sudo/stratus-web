"use client";

const COLORS = ["#EB0043", "#FF99A8", "#FFD5DC", "#2C694E", "#FFFFFF"];

export function burstConfetti(originX: number, originY: number, count = 36) {
  if (typeof window === "undefined") return;
  const container = document.createElement("div");
  container.style.cssText = `
    position: fixed;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 9999;
  `;
  document.body.appendChild(container);

  for (let i = 0; i < count; i++) {
    const piece = document.createElement("div");
    const color = COLORS[Math.floor(Math.random() * COLORS.length)];
    const size = 6 + Math.random() * 6;
    const angle = Math.random() * Math.PI * 2;
    const velocity = 200 + Math.random() * 280;
    const dx = Math.cos(angle) * velocity;
    const dy = Math.sin(angle) * velocity - 200;
    const rotation = (Math.random() - 0.5) * 720;
    const duration = 900 + Math.random() * 700;
    const shape = Math.random() > 0.5 ? "50%" : "2px";

    piece.style.cssText = `
      position: absolute;
      left: ${originX}px;
      top: ${originY}px;
      width: ${size}px;
      height: ${size}px;
      background: ${color};
      border-radius: ${shape};
      transform: translate(-50%, -50%);
      will-change: transform, opacity;
    `;
    container.appendChild(piece);

    piece.animate(
      [
        { transform: `translate(-50%, -50%) rotate(0deg)`, opacity: 1 },
        {
          transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy + 400}px)) rotate(${rotation}deg)`,
          opacity: 0,
        },
      ],
      {
        duration,
        easing: "cubic-bezier(0.16, 1, 0.3, 1)",
        fill: "forwards",
      }
    );
  }

  setTimeout(() => container.remove(), 2000);
}
