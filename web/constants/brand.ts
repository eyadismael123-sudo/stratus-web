/**
 * Stratus Brand Constants
 * Source of truth: /BRAND.md (locked 2026-03-27)
 * DO NOT hardcode these hex values elsewhere — always import from here.
 */

export const COLORS = {
  // Primary palette
  bg:           "#FAF9F6",  // Cream — warm, premium canvas
  fg:           "#1A1A1A",  // Charcoal — text, nav, dark elements
  accent:       "#1B4332",  // Forest — CTAs, online dots, highlights
  accentHover:  "#2D6A4F",  // Mid Green — hover state of Forest
  border:       "#E8E6E1",  // Warm Grey — borders, dividers
  surface:      "#FFFFFF",  // White — cards, panels

  // Grey scale (5-grey system)
  grey900: "#1A1A1A",  // Primary text, headings
  grey700: "#4A4A4A",  // Secondary text, metadata
  grey500: "#8A8A8A",  // Tertiary text, timestamps
  grey300: "#E8E6E1",  // Borders, dividers (Warm Grey)
  grey100: "#FAF9F6",  // Subtle backgrounds (Cream)

  // Semantic / status
  success: "#1B4332",  // Forest green — matches brand accent
  error:   "#C0392B",  // Deep red
  warning: "#D97706",  // Amber
  info:    "#2563EB",  // Blue
} as const;

export const TYPOGRAPHY = {
  fontDisplay: "'Clash Display', system-ui, sans-serif",
  fontSans:    "'Satoshi', system-ui, sans-serif",
  fontMono:    "'SF Mono', 'Fira Code', 'Fira Mono', monospace",

  fontDisplayCDN: "https://api.fontshare.com/v2/css?f[]=clash-display@700,600&display=swap",
  fontSansCDN:    "https://api.fontshare.com/v2/css?f[]=satoshi@900,700,500,400&display=swap",

  // Type scale (px)
  h1: { size: "48px", weight: "900", lineHeight: "1.1" },
  h2: { size: "36px", weight: "700", lineHeight: "1.2" },
  h3: { size: "28px", weight: "700", lineHeight: "1.3" },
  h4: { size: "20px", weight: "700", lineHeight: "1.4" },
  body:      { size: "16px", weight: "400", lineHeight: "1.5" },
  bodySmall: { size: "14px", weight: "400", lineHeight: "1.5" },
  caption:   { size: "12px", weight: "400", lineHeight: "1.4" },
  mono:      { size: "13px", weight: "400", lineHeight: "1.5" },
} as const;

export const SPACING = {
  xs:  "4px",
  sm:  "8px",
  md:  "12px",
  lg:  "16px",
  xl:  "24px",
  xl2: "32px",
  xl3: "48px",
  xl4: "64px",
  xl5: "80px",
} as const;

export const RADIUS = {
  sm:   "4px",
  md:   "8px",
  lg:   "12px",
  xl:   "16px",
  full: "9999px",
} as const;

export const SHADOWS = {
  card:     "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
  elevated: "0 10px 30px rgba(0,0,0,0.12), 0 4px 6px rgba(0,0,0,0.08)",
} as const;

export const TRANSITIONS = {
  fast:    "150ms cubic-bezier(0.4, 0, 0.2, 1)",
  slow:    "300ms cubic-bezier(0.4, 0, 0.2, 1)",
  instant: "0ms",
} as const;

// Agent category taxonomy (LOCKED 2026-03-21)
export const AGENT_CATEGORIES = ["Personal", "Business", "Health"] as const;
export type AgentCategory = (typeof AGENT_CATEGORIES)[number];

export const AGENT_SUBCATEGORIES: Record<AgentCategory, string[]> = {
  Personal: ["Personal Brand", "Career & Jobs"],
  Business: ["Automotive", "Real Estate", "Restaurants & F&B", "HR & Recruitment"],
  Health:   ["Doctors & Clinicians", "Clinic Operations"],
} as const;

// Pricing (confirmed 2026-03-21)
export const PRICING = {
  linkedInPostAgent: {
    usdCents:    5000,
    displayText: "$50/mo",
    currency:    "USD",
  },
} as const;
