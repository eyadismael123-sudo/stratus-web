# Stratus — Complete UI Rebrand Plan

**Created:** 2026-03-31
**Status:** Approved by founder, not yet started
**Owner:** Creative Artist (design) -> Frontend Engineer (build)

---

## Why

The current site is built on the old palette (graphite/yellow/Apple-white) and looks like every other cold SaaS landing page. The brand-identity.md locked on March 27 says warm editorial premium — Patagonia, not Linear. The site doesn't match that. Additionally:

- `brand.ts` still exports yellow (`#FFD60A`) — dead since March 27
- Forest accent (`#1B4332`) doesn't exist in code at all
- Clash Display (headline font) is not loaded — every headline renders in Satoshi (body font)
- Background is `#F5F5F7` (Apple grey) instead of `#FAF9F6` (Cream)

---

## Brand System (Source of Truth: `/marketing/brand-identity.md`)

### Colors
| Token | Hex | Name | Usage |
|---|---|---|---|
| `--color-accent` | `#1B4332` | Forest | CTAs, online dots, focus rings, selected states |
| `--color-accent-hover` | `#2D6A4F` | Mid Green | Hover state for Forest elements only |
| `--color-fg` | `#1A1A1A` | Charcoal | Text, nav, dark elements |
| `--color-bg` | `#FAF9F6` | Cream | Page background, light surfaces |
| `--color-border` | `#E8E6E1` | Warm Grey | Borders, dividers |
| `--color-surface` | `#FFFFFF` | White | Cards, panels, inputs |

**Dead colors — never use:** Yellow `#FFD60A`, Navy `#0D1B2A`, Teal `#2DD4A0`

### Typography (2-Font Stack)
| Role | Font | Weights | CDN |
|---|---|---|---|
| Display / Headlines | Clash Display (Fontshare) | 600, 700 | `https://api.fontshare.com/v2/css?f[]=clash-display@700,600&display=swap` |
| Body / UI / Captions | Satoshi (Fontshare) | 400, 500, 700, 900 | `https://api.fontshare.com/v2/css?f[]=satoshi@900,700,500,400&display=swap` |
| Mono | SF Mono | — | system |

**Dead fonts:** Figtree (vibecoded), Klein (Canva-only)

### Aesthetic Direction
Warm editorial premium. Think Patagonia, not Linear. Nature-rooted, organic, trustworthy.
NOT cold startup, NOT abstract 3D, NOT generic AI aesthetics.

---

## Design Rules

### No emojis. Anywhere. Clean professional copy only.

### Visuals — Anti-AI Strategy
The visuals must feel real, not "AI made this." Rules:

1. **Texture over perfection** — grain overlays (CSS noise filter), paper textures on cream backgrounds, borders that feel tactile
2. **Photography (Nano Banana) direction** — imperfect editorial: slightly off-center, one thing out of focus, warm underexposed lighting, specific props (scratched marble, worn notebook, phone with screen glare). The more specific the prompt, the less AI it looks.
3. **Motion = life** — GSAP micro-movements, Rive interactive elements, parallax depth, tactile hover transitions. The site feels alive through motion, not through images.
4. **Real UI screenshots over fake mockups** — actual Stratus dashboard screenshots with shadow + tilt, not generated mockups
5. **Typography as the visual** — Clash Display at massive sizes IS the visual. No image needed when the type has enough presence.

### Nano Banana Rules
- Only use where a photo genuinely adds value (About page, maybe 1-2 agent cards)
- Every generated image gets reviewed — if it looks AI, it's killed
- Prompt for imperfection: "slightly overexposed", "edge of frame visible", "natural grain", "not centered"
- Less is more — 2 great images beats 10 mediocre ones
- Use `/nano-banana` skill for prompt optimization before generating

---

## Page-by-Page Design

### 1. Landing Page (Hero)
- Cream `#FAF9F6` background (not dark)
- Massive Clash Display headline — the type IS the visual
- No hero image — just type + subtle GSAP parallax layers + grain texture
- Lively through motion, not through a fake photo
- Subtle animated background: grain texture + soft parallax layers

### 2. Landing Page (Stats Strip)
- Forest `#1B4332` background, Cream text
- Clash Display numbers with GSAP counter animation on scroll
- The animation IS the visual

### 3. Landing Page (Hire.Watch.Grow Tabs)
- Cream background, Forest accent on active tab
- Real product screenshots (actual dashboard/marketplace) with tilt + shadow
- Not generated scenes

### 4. Landing Page (Bento Grid)
- White `#FFFFFF` cards with Warm Grey `#E8E6E1` borders
- Icons from Heroicons/Lucide + Clash Display stats
- No imagery — clean, Swiss, data-driven
- Subtle GSAP scroll-reveal stagger

### 5. Landing Page (Marketplace Preview)
- Agent cards with Forest accent badges, Cream background
- Life comes from hover animations + Rive status dots (Forest green pulse, not yellow)
- Editorial feel — magazine product listings, not tech cards

### 6. Landing Page (Pricing)
- Clean, minimal. Forest CTA button. No yellow.
- Pure typography — Clash Display price, Satoshi details

### 7. Landing Page (Footer)
- Forest background, Cream text. Warm, not cold.

### 8. Marketplace
- Hiring board aesthetic
- Agent cards: industry-specific Nano Banana photo ONLY if it passes the "does this look real" test. Otherwise, bold Forest/Cream color block with Clash Display agent name.
- Forest "Hire" buttons, Warm Grey borders, Cream background
- Category tabs with Forest underline indicator

### 9. Dashboard ("Your Team")
- Cream page background, White agent cards
- Rive status dots — Forest green pulse for online, grey for offline, red for error
- Agent cards feel like team member profiles, not software widgets
- Lottie empty state animation when no agents hired

### 10. Agent Detail
- Clean log feed, Satoshi body text, Forest accent for active states
- GSAP scroll animations on the activity timeline

### 11. About Page
- One strong Nano Banana editorial — Dubai skyline, golden hour, through office windows
- This is the ONE image we invest in getting right
- Clash Display "Built in Dubai." massive headline over the photo
- Founder section with warm, editorial treatment

### 12. Pricing Page
- Pure typography. Clash Display price, Satoshi details, Forest CTA
- Swiss grid layout. One card per agent.
- "Your agents work better together" in Clash Display
- No visuals needed

---

## Tools Per Section

| Tool | Where |
|---|---|
| **GSAP ScrollTrigger** | Hero scroll reveal, stats counter, bento stagger, section reveals |
| **Rive** | Status dots (online/offline state machine), agent activity indicators |
| **Lottie** | Empty states, loading skeletons, success animations |
| **Nano Banana** | About page hero, possibly 1-2 agent cards (only if it looks real) |
| **Framer Motion** | Page transitions, layout animations, hover states |
| **Heroicons** | Nav icons, UI chrome |
| **Lucide** | Dashboard, agent detail, settings icons |
| **react-icons** | Platform logos (LinkedIn, Telegram, WhatsApp) |

---

## Build Sequence

### Step 1: Brand Sync (Foundation)
- Update `web/constants/brand.ts` — replace yellow with Forest, add Cream/Charcoal/Warm Grey, add Clash Display font, kill all yellow references
- Update `web/app/layout.tsx` — load Clash Display font from Fontshare CDN
- Update `web/app/globals.css` — add `--font-display` CSS variable, apply to h1-h4
- Sweep codebase — find every `#FFD60A`, `#F5F5F7`, yellow reference and replace

### Step 2: Landing Page Hero Redesign
- Cream background, Clash Display headline, GSAP parallax, grain texture
- Remove dark theme, SVG network, yellow dots, blobs
- Prove the new direction works

### Step 3: Component Library Update
- StatusDot → Rive interactive (Forest/grey/red)
- Buttons → Forest accent CTAs
- Cards → White surface, Warm Grey border
- Badges → Forest or Charcoal, no yellow

### Step 4: Remaining Landing Sections
- Stats Strip, Hire.Watch.Grow, Bento, Marketplace Preview, Pricing, Footer

### Step 5: Inner Pages
- Marketplace, Dashboard, Agent Detail, About, Pricing, Contact, Blog

### Step 6: Nano Banana Images
- Generate About page hero (the one that matters)
- Test agent card images (only keep if they pass the real test)

### Step 7: Motion Polish
- GSAP scroll animations across all sections
- Rive micro-interactions
- Lottie empty/loading states
- Framer Motion page transitions

---

## Nano Banana Image List (only if they look real)

| Image | Prompt Direction | Used Where |
|---|---|---|
| Dubai office golden hour | Dubai Marina through floor-to-ceiling windows, modern desk, laptop, forest green accents, warm lighting, slightly overexposed, natural grain | About page hero |
| LinkedIn agent context | Professional workspace, laptop, warm morning light, shallow DOF, edge of coffee cup | LinkedIn agent card (maybe) |
| Car reseller context | Dubai car showroom morning, premium, warm tones | Car agent card (maybe) |

---

## What We DON'T Do
- No emojis anywhere
- No yellow anywhere
- No AI-looking imagery (oversaturated, too perfect, plastic, uncanny)
- No abstract 3D shapes
- No text-on-background Canva template look
- No vintage/retro aesthetics
- No dark hero (old direction — killed)
- No flat design without texture or motion
