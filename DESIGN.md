# Stratus Design Brief — Phase 0.3

**Status:** ALL 8 MOCKUPS COMPLETE + MOBILE RESPONSIVE — Full mockup pipeline done. All pages verified at 390×844px. Ready for founder review before Next.js build begins.
**Date Started:** 2026-03-18
**Last Updated:** 2026-03-21 (session 5)
**Owner:** 🎨 Creative Artist
**Handoff to:** Frontend Engineer — Next.js build can begin from these mockups

---

## Mockup Pipeline

All designs are built as **standalone HTML mockups** before any Next.js code is written.

**Location:** `/Users/25200422/stratus/mockups/`
**Preview:** `python3 -m http.server 7654` from project root → open `localhost:7654/mockups/`
**Screenshots:** Playwright MCP (`browser_navigate` + `browser_take_screenshot`)

| File | Page | Status |
|---|---|---|
| `01-component-library.html` | Component Library | ✅ Built |
| `02-landing-page.html` | Landing Page | ✅ LOCKED — scroll animations, category tab marketplace preview, Satoshi, yellow rule enforced |
| `03-auth.html` | Auth (Sign Up / Sign In / Reset) | ✅ Built |
| `04-dashboard.html` | Dashboard (Your Team) | ✅ Built — category tabs (Personal/Business/Health) replace state toggle |
| `05-agent-detail.html` | Agent Detail | ✅ Built + Mobile Fixed (min-width:0 flex fix, log card overflow) |
| `06-marketplace.html` | Marketplace | ✅ Built — category tabs + sub-category groups + live search |
| `07-billing.html` | Billing | ✅ Built + Mobile Fixed (2-col stats, sub-row wrapping, invoice table contained) |
| `08-admin.html` | Admin War Room | ✅ Built + Mobile Fixed (html/body overflow-x, 2-col status grid, card overflow) |

**Mobile:** All pages verified at 390×844px via Playwright. See `DESIGN-MOBILE.md` for full spec and fix log.

## Yellow Usage Rule (UPDATED + LOCKED 2026-03-18 session 2)

Yellow (`#FFD60A`) is used in **exactly 3 places** and nowhere else:
1. **Online status dot** — agent live/active indicator (6–8px animated pulse dot) — PRIMARY use
2. **SVG network active nodes** — hero animation only (2 active nodes in the network)
3. **Featured pricing plan** — "Most Popular" badge pill + featured card border glow + CTA button only

**Nav CTA and Hero CTA are GRAPHITE (`#3A3A3C`), NOT yellow.** Founder overrode this 2026-03-18.
**Dominant palette is graphite + white + grey.** Yellow is an accent you *notice*, not a colour you *feel*.

Anti-patterns (DO NOT repeat):
- ❌ Yellow on nav "Get Started" button (graphite now)
- ❌ Yellow on hero "Get Started" button (graphite now)
- ❌ Yellow on marketplace "Hire" buttons
- ❌ Yellow on tab active states (white underline, not yellow)
- ❌ Yellow as ambient blobs / atmospheric glow in background
- ❌ Yellow on SVG network lines (white at low opacity now)
- ❌ Yellow on eyebrow/label text
- ❌ Yellow as decorative accent outside the 3 allowed uses

---

## Agent Lineup (UPDATED — 2026-03-25)

### Live Now
Only one agent is live. The entire site is built around this product:

| Agent | Category | One-Liner | Price |
|---|---|---|---|
| **LinkedIn Post Agent** | Personal | "Writes thought leadership in your voice. Daily." | $50/mo |

### Coming Soon — DEFERRED
No other agents are shown on the site yet. Founder will decide what to add and when. No prices, no details, no "Coming Soon" cards. When new agents are ready, Frontend plugs them into the agent card template (see below).

### Agent Card Template (for future agents)
When founder adds a new agent, Frontend creates a card with:
- Agent name
- Category badge (Personal / Business / Health)
- One-liner description (1 sentence max)
- Price per month
- Status badge: "Live" (yellow dot) or "Coming Soon" (grey dot)
- "Hire" CTA (graphite button) — only shown on Live agents
- `data-cat` attribute for filtering

This is a **data-driven component**. No redesign needed to add agents — just plug in the fields. Category tabs (Personal / Business / Health) appear automatically once there are 2+ categories with live agents.

### Category System (dormant until needed)
Three top-level categories ready to activate when agents launch:
- **Personal** — agents for individual professionals
- **Business** — agents for Dubai SMEs and industry verticals
- **Health** — "Division launching 2026" badge on all health content

Category tabs, sub-category groups, and filter JS are all built in the mockups but **hidden until there are multiple live agents**. No empty categories shown.

---

## Design Philosophy

See `/BRAND.md` for full brand system (colours, typography, spacing, tokens).

**Quick refresh:**
- **Mood:** Premium, minimal, dark graphite anchoring clean white space with yellow energy
- **Colour palette:**
  - Background: `#F5F5F7` (near-white, Apple-style)
  - Primary dark: `#3A3A3C` (graphite — Stratus logo)
  - Accent: Yellow (CTAs, online status dots, highlights)
- **Style:** 3D Apple-style, scroll-triggered animations (Spline + Framer Motion)
- **Language:** "Hiring", not subscribing. Agents are "team members", not tools.

---

## Pages to Design (8 total)

All pages must:
- Support desktop (1280px+), tablet (768px), mobile (375px) responsive layouts
- Follow component library tokens (see below)
- CTAs are graphite (`#3A3A3C`). Yellow only for: status dots, SVG hero nodes, featured pricing badge (see Yellow Usage Rule)
- Maintain dark graphite anchors in headers/footers
- Include hover/active states for all interactive elements

### 1. Landing Page ✅ BUILT — `02-landing-page.html`

**Sections built:**
1. **Nav** — fixed, transparent → blur on scroll, "stratus" logo in Satoshi Black, graphite "Get Started →" CTA
2. **Hero** — "The Network" — SVG network animation, ambient dark blobs, scroll-driven 5-stage JS, agent cards floating left/right
3. **Stats strip** — 4 animated counters on light `#F5F5F7` bg (IntersectionObserver triggered)
4. **Hire. Watch. Grow. Tabs** — 3-tab section, dark bg, crossfade content, CSS mini-mockups per tab
5. **Bento grid** — 12-col CSS grid, 6 cards, IntersectionObserver scroll reveal, mousemove 3D tilt
6. **Product spotlight** — LinkedIn Post Agent as the sole featured product. Full card: name, one-liner ("Writes thought leadership in your voice. Daily."), what it does, who it's for, $50/mo, graphite "Hire" CTA. Dark bg. No category tabs (only 1 agent). A small "More agents arriving soon" teaser text below — no cards, no prices, just the promise.
7. **Pricing** — single clean section: "$50/mo. Your AI content team starts here." One agent, one price, one graphite CTA. No 3-tier cards. Add copy: "Your agents work better together" to plant the ecosystem seed.
8. **Final CTA** — "Ready to hire?" dark section, graphite button
9. **Footer** — 3-column links, social icons, "© 2026 Stratus. Built in Dubai.", add "Arabic + English" trust signal

**Font:** Satoshi from Fontshare CDN (900/700/500/400). NOT Figtree.
**CDN:** `https://api.fontshare.com/v2/css?f[]=satoshi@900,700,500,400&display=swap`

**JS modules (all vanilla, no libraries):**
- Scroll engine → `--hero-progress` CSS custom property
- Scroll reveals → IntersectionObserver on `[data-reveal]`
- Counter animation → rAF easeOutExpo counting
- Bento mousemove tilt → perspective 3D on cards
- Agent carousel → cycles 3 agents at hero stage 3, every 4s

**Hero background (dark, no yellow wash):**
- Base gradient: `#0a0a0f` → `#020203`
- Blob A (700px): `rgba(80,80,90,0.25)` blur 110px — cool grey
- Blob B (400px): `rgba(20,20,25,0.5)` blur 80px — near-black
- Blob C (300px): `rgba(58,58,60,0.3)` blur 120px — graphite
- Blob D (500px, pricing): `rgba(58,58,60,0.2)` blur 100px — graphite
- SVG network lines: `rgba(255,255,255,x)` — white, NOT yellow
- SVG active nodes (2): `rgba(255,214,10,0.95)` — yellow, intentional

**Hero Scroll Journey (LOCKED):**

All values are scroll % from page top. Uses Spline 3D model + Framer Motion scroll control.

- **0%:** Dark graphite background. 5–6 agent nodes arranged in network topology (hexagon or organic cluster). All nodes at 30% opacity, static (no rotation). Headline visible center-stage: "Hire your first AI employee".

- **25%:** Nodes brighten to 60% opacity. Yellow pulses travel along connecting lines (like electricity flowing). Agents come online one by one (subtle glow animation). Supporting text fades in below headline: "Your staff. No salary. No sick days."

- **50%:** All nodes at 100% opacity, fully saturated. Yellow particles flow between nodes (organic flow, not mechanical). Slow 3D scene rotation (maybe 2–3 RPM). Faint supporting text fades in center: "5 agents working. Logging 2,847 tasks today." (example stats, real-time data pulled from backend once API is live).

- **75%:** The LinkedIn Post Agent node expands and moves center-stage. Other nodes step back, dim slightly (70% opacity). The expanded node displays:
  - Agent name: "LinkedIn Post Agent"
  - One-liner: "Writes thought leadership in your voice. Daily."
  - Graphite "Hire — $50/mo" CTA button inside the node
  - LinkedIn icon
  - Background subtly shows network still rotating

- **100%:** 3D network fades out. "Hire. Watch. Grow." tabs section slides in (from below, smooth 0.6s transition).

**Tab Specs (Hire. Watch. Grow.):**

Three horizontal tabs, each with icon + text + content block below.

| Tab | Icon | Headline | Subtext | Content |
|---|---|---|---|---|
| **Hire** | Briefcase + person silhouette | Meet your first AI employee | Hire in minutes. Working by tomorrow. | LinkedIn Post Agent spotlight card: name, one-liner, $50/mo, "Hire" CTA. One product, full focus. |
| **Watch** | Eye / Monitor | Your team is working right now | Live status, logs, schedule — always visible | Mock dashboard showing LinkedIn Agent running: live logs stream, status dot (online), last activity timestamp |
| **Grow** | Arrow up / Growth chart | See what your team accomplished today | Daily proof. Real numbers. No fluff. | Mock Telegram outcome receipt: "Today: LinkedIn Agent drafted 3 posts, 1 published, 847 impressions. Hours saved: ~1.5. Tomorrow: 2 scheduled posts at 9am." |

Each tab content lazy-loads on click, smooth fade-in.

**Pricing section:**
- Headline: "$50/mo. Your AI content team starts here."
- Single product card: LinkedIn Post Agent — what's included (daily posts, morning briefing, voice matching, Telegram delivery)
- Subtext: "Your agents work better together." (ecosystem teaser — no action needed yet, just plants the seed)
- CTA: "Hire Now" (graphite button → Stripe checkout)
- No tiers. No "Starter/Pro/Enterprise." One agent, one price.

---

### 2. Auth Pages (3 pages)

**Sign Up:**
- Headline: "Hire your first AI employee"
- Email input
- Password input (with strength indicator)
- Confirm password
- Company name (optional)
- "Sign Up" CTA (graphite)
- Already have account? "Sign In" link
- OAuth option: "Sign up with Google" (secondary grey button)

**Sign In:**
- Headline: "Welcome back"
- Email input
- Password input
- "Remember me" checkbox
- "Sign In" CTA (graphite)
- "Forgot password?" link
- Don't have account? "Sign Up" link
- OAuth option: "Sign in with Google"

**Password Reset:**
- Headline: "Reset your password"
- Email input
- "Send reset link" CTA (graphite)
- "Back to sign in" link
- Success state: "Check your email for a reset link"

All auth pages: centred form, white card on `#F5F5F7` background, graphite accents.

---

### 3. Dashboard ("Your Team" Roster)

**Header:**
- Left: Stratus logo + "Your Team"
- Right: User avatar dropdown (settings, billing, logout)

**Sidebar (left, collapsible on mobile):**
- Dashboard (active)
- Marketplace
- Billing
- Settings
- Admin (founder-only, hidden for regular users)

**Main area:**
- **Search bar** — find agents by name
- **Agent cards grid** (3 columns on desktop, 1 on mobile)
  - Each card: agent name, role, current activity (e.g., "Processing task"), connected platform icon (Telegram/LinkedIn/WhatsApp), online/offline yellow dot (top-right), last activity timestamp
  - Click → Agent Detail page
  - Hover: subtle shadow lift, "View Details" text

**Empty state (no agents hired yet):**
- Illustration (minimal, graphite + white)
- Headline: "Your team is empty"
- Subtext: "Hire your first agent to get started"
- CTA: "Browse Marketplace" (yellow)

---

### 4. Agent Detail

**Header:**
- Back button
- Agent name + role
- Online/offline yellow dot
- Settings icon (top-right)

**Layout (3 columns on desktop, 1 on mobile):**

**Left column — Agent info:**
- Large agent icon/avatar
- Name + role
- Connected platform (Telegram, LinkedIn, WhatsApp)
- Price per month
- Status badge: "Active" (green) / "Paused" / "Error"
- "Pause Agent" and "Delete Agent" buttons (secondary, grey)

**Center column — Logs feed:**
- Headline: "Recent Activity"
- Reverse-chronological feed of agent tasks:
  - Timestamp (e.g., "Today at 2:34 PM")
  - Task type icon (e.g., post icon for LinkedIn)
  - Task description (e.g., "Posted to LinkedIn")
  - Status: "Completed" (green) / "Failed" (red) / "Pending" (yellow)
  - Click to expand full log
- "View all logs" link at bottom

**Right column — Schedule + Settings:**
- **Schedule section:**
  - Headline: "This Week's Schedule"
  - Simple grid: Mon–Sun, shows number of tasks per day
  - Click day → detailed view of tasks for that day
- **Settings section:**
  - Agent configuration options (e.g., "Post frequency: 2x daily", "Time zone", etc.) — exact config TBD per agent
  - "Save changes" button (yellow)

---

### 5. Marketplace → LinkedIn Post Agent Page (Single Product for Now)

**DEFERRED:** Full marketplace with grid/search/filters is not needed with 1 agent. `/marketplace` redirects to `/agents/linkedin-post-agent` for now. When agent #2 goes live, rebuild this as a proper hiring board.

**LinkedIn Post Agent page (`/agents/linkedin-post-agent`):**
- Hero section: agent name, one-liner ("Writes thought leadership in your voice. Daily."), category badge (Personal)
- What it does: 4-5 bullet points (daily posts in your voice, morning research briefing, 2 variations to choose from, LinkedIn pre-fill link, Telegram delivery)
- Who it's for: "Founders, executives, and professionals who want a LinkedIn presence without the effort"
- Price: $50/mo — graphite "Hire Now" CTA → Stripe checkout
- Platform icon: LinkedIn + Telegram
- Status: Live (yellow dot)

**Future marketplace (when 2+ agents are live):**
- Reactivate hiring board layout with agent card grid
- Category tabs appear automatically (Personal / Business / Health)
- Search + filter bar
- Each card uses the agent card template from the Agent Lineup section above
- Price text in graphite (NOT yellow — per yellow rule)
- "Hire" CTA in graphite (NOT yellow)

---

### 6. Billing

**Header:**
- "Your Subscriptions"

**Main area:**

**Active subscriptions section:**
- Table or card grid showing each hired agent:
  - Agent name + role
  - Price per month
  - Start date
  - Next billing date
  - Status: "Active" (green)
  - "Manage" button (dropdown: pause/cancel) → grey secondary button
  - "Manage" opens a modal to confirm cancellation

**Invoice history section:**
- Headline: "Invoices"
- Table: Date, Agent, Amount, Status (Paid), Download link (PDF icon)
- Pagination if >10 invoices

**Payment method section (future):**
- Headline: "Payment Method"
- Card ending in ****1234 (blurred)
- "Update payment method" link (yellow)

---

### 7. Admin Panel (War Room) — Founder Only

**Header:**
- Stratus logo + "War Room" (red accent, danger zone vibe)
- Founder name (top-right)

**Left sidebar:**
- Dashboard
- Agents
- Clients
- Revenue
- Feedback Hub

**Dashboard tab:**
- **System health cards:**
  - Total agents running
  - Total clients
  - Total revenue (this month)
  - Churn rate
- **Live agent status grid:**
  - All marketplace agents listed
  - Each row: agent name, status (Running/Paused/Error), uptime %, action buttons (Restart, Kill, Edit)
- **Recent client activity feed:**
  - Real-time log of client signups, agent hires, cancellations, errors

**Agents tab:**
- **Agent master list:**
  - All agents in marketplace (editable)
  - Columns: name, category, price, status (Live/Hidden/Draft), created date, actions (Edit, Preview, Publish)
  - Add new agent form (inline or modal)
- **Per-agent testing controls:**
  - Spin up / Restart / Kill individual agents
  - Test agent with mock input (e.g., "Post a test LinkedIn article")
  - View test output
  - Full agent logs (debug level)

**Clients tab:**
- **Client roster table:**
  - Client name (company)
  - Contact email
  - Agents hired (comma-separated list with count)
  - Lifetime value (total spent)
  - Status: Active / Cancelled / At-risk (churn warning)
  - Last activity date
  - Actions dropdown: View details, Send message, Pause all agents
- **Client detail view** (click client row):
  - Full profile: name, email, phone, company, created date
  - Agents hired: each with subscription status, next billing date
  - Live logs from all their agents (merged feed, sortable)
  - Feedback section: any complaints/feature requests clients have submitted
  - Action buttons: Restart all agents, Pause all agents, Emergency kill

**Revenue tab:**
- **Summary cards:**
  - MRR (Monthly Recurring Revenue)
  - Total revenue (all-time)
  - Average revenue per client
  - Churn rate (%)
- **Revenue chart:**
  - Line graph: MRR over last 3 months
- **Subscription breakdown:**
  - Table: agent name, # of subscriptions, total MRR contribution, churn this month

**Feedback Hub tab:**
- **Client feedback list:**
  - Sortable table: date, client, agent, feedback type (Bug report / Feature request / Complaint), message, status (New / In-progress / Resolved)
  - Click to expand full feedback thread
  - Action buttons: assign to self, mark resolved
- **Agent feedback dashboard:**
  - Per-agent feedback summary: # of complaints, # of feature requests
  - Heat map showing which agents have most feedback (red = most issues)

**Master controls (top-right, always visible):**
- Big red button: "⚠️ Kill All Agents" (confirmation modal required)
- Big yellow button: "🔄 Restart All Agents" (no confirmation, just does it)
- Status indicator: "System: OK" (green) or "System: Warning" (yellow) or "System: Critical" (red)

**Design notes for War Room:**
- Red/orange accents for danger actions (Kill, Emergency)
- Yellow accents for safe actions (Restart, Edit)
- Lots of white space for readability (data-heavy page)
- Monospace font for logs/debug output
- Real-time updates on all metrics (WebSocket or polling from backend)

---

### 8. Component Library

Design once, use everywhere. All pages use these.

**Buttons:**
- Primary (yellow bg, dark text, hover: lighter yellow)
- Secondary (white/light bg, dark border, hover: light bg)
- Danger (red bg, white text, hover: darker red)
- Disabled (grey bg, grey text)
- Sizes: sm, md, lg
- States: default, hover, active, disabled

**Input fields:**
- Text input (dark border, light bg)
- Hover: darker border
- Focus: yellow border, subtle glow
- Error: red border, error text below
- Success: green border
- Disabled: grey bg, grey text
- Label above, helper text below

**Cards:**
- White bg, light shadow, rounded corners (8px)
- Hover: subtle shadow lift
- Padding: consistent spacing from brand tokens
- Variants: default, elevated, bordered

**Badges:**
- Small colored pills (green, yellow, red, grey)
- Text: role/category/status

**Status dots:**
- Online: yellow/green, filled circle (8px)
- Offline: grey, filled circle
- Error: red, filled circle
- Animated pulse on online state

**Navigation:**
- Top bar: logo, nav links, user dropdown
- Sidebar (collapsible): dashboard, marketplace, billing, settings, admin (founder-only)
- Mobile: hamburger menu opens sidebar

**Loading states:**
- Skeleton screens (grey placeholder boxes)
- Spinner (yellow + graphite, smooth rotation)
- Fade-in animation on content load

**Modals/Dialogs:**
- Centred overlay, white card, shadow
- Close button (X, top-right)
- Actions at bottom (primary/secondary buttons)
- Smooth fade-in/out

**Tables:**
- Header row: dark graphite bg, white text, sortable columns (chevron icons)
- Body rows: white bg, light grey alternate row
- Hover: subtle bg highlight
- Pagination: simple controls at bottom

---

## Tech Stack & Implementation Notes

**Frontend:** Next.js 15 (app router) + Tailwind CSS + Framer Motion

**3D/Animation:**
- **Landing hero:** Spline (3D network model) + Framer Motion (scroll-triggered controls)
- **Other animations:** Framer Motion (page transitions, hover states, scroll reveals)

**Responsive strategy:**
- Mobile-first CSS
- Breakpoints: 375px (mobile), 768px (tablet), 1280px (desktop)
- Touch-friendly interactive elements (min 44px tappable area)

**Component structure:**
- `/components/common/` — Button, Input, Card, Badge, Modal, etc.
- `/components/layouts/` — Header, Sidebar, Footer
- `/components/pages/` — LandingHero, DashboardGrid, MarketplaceGrid, etc.
- `/styles/` — Tailwind theme tokens (from `/BRAND.md`)

**Brand tokens in Tailwind config:**
```javascript
module.exports = {
  theme: {
    colors: {
      'bg-primary': '#F5F5F7',
      'text-dark': '#3A3A3C',
      'accent': '#FFCC00', // yellow (exact hex TBD)
      'success': '#34C759',
      'error': '#FF3B30',
      'warning': '#FF9500',
    },
  },
}
```

---

## Handoff to Next Session

**What's locked:**
- All 8 pages and their layouts
- Landing hero scroll journey (5 stages, Spline + Framer Motion)
- Admin war room full scope and controls
- Component library specifications

**What's complete (all sessions):**
- ✅ `02-landing-page.html` — full landing page, 9 sections, scroll animations, Satoshi font, yellow rule enforced
- ✅ `03-auth.html` — Sign Up, Sign In, Password Reset (3 states)
- ✅ `04-dashboard.html` — Your Team roster, agent cards grid
- ✅ `05-agent-detail.html` — 3-column layout, logs feed, schedule grid, settings
- ✅ `06-marketplace.html` — **STALE: built for 10 agents, now single product page** (see section 5 above)
- ✅ `07-billing.html` — subscriptions table, invoice history
- ✅ `08-admin.html` — War Room, all tabs, red/orange danger language
- ✅ `01-component-library.html` — built
- ✅ Yellow rule locked: graphite dominant, yellow = status dots + featured pricing + 2 SVG nodes only

**What changed (2026-03-25 — Cofounder Proposal approved):**
- Agent lineup: 10 → 1 live (LinkedIn Post Agent only). All other agents removed from site. Founder will add new agents when ready.
- Marketplace: deferred. `/marketplace` → LinkedIn Post Agent page for now.
- Pricing: 3-tier cards killed. Single product: $50/mo.
- Grow tab: generic stats → outcome receipts (mock Telegram daily summary)
- All CTAs: graphite, not yellow (yellow rule enforced)
- Trust signals added: "Arabic + English", "Built in Dubai"
- Mockups `02` and `06` need rebuilding to match. Other mockups are fine.

**What's pending:**
- Rebuild `02-landing-page.html` marketplace preview + pricing sections (or Frontend builds directly from this spec)
- Rebuild `06-marketplace.html` as single product page (or Frontend builds directly)
- Backend API contracts finalized

**Next actions:**
1. Frontend Engineer builds from this updated spec + CLAUDE.md + COFOUNDER-PROPOSAL.md
2. Mockups `02` and `06` can be rebuilt if founder wants HTML preview first, or Frontend can go direct

**Dependencies:**
- Backend API contracts finalized (for dashboard data structure)
- Stripe webhook setup confirmed (for billing page flow)

---

## Locked Decisions (Do Not Revisit)

| Decision | Outcome | Rationale |
|---|---|---|
| Landing hero concept | "The Network" (scroll-triggered 3D animation, 5-stage journey) | Differentiates from generic landing pages, showcases AI agents as a connected system, founder approved |
| Hero tech stack | Spline 3D + Framer Motion scroll control | Spline handles 3D, Framer Motion provides scroll binding, integrates cleanly with Next.js |
| Admin access | Founder-only, hidden from regular users | War room is internal tool, not client-facing |
| Agent language | "Hire", "team members", "roster" (not "subscribe", "tools", "agents") | Aligns with founder's brand vision of AI as employees |
| Colour accents | Yellow for status dots + featured pricing + SVG nodes ONLY. All CTAs are graphite. | Founder override 2026-03-18: "stop with the yellow" |
| Site scope | LinkedIn Post Agent is the only product shown. No other agents on site until founder adds them. | Cofounder proposal approved 2026-03-25: don't show pricing for things that don't exist |

---

**Status:** Design spec updated for single-product launch. Mockups `02` and `06` are stale — Frontend builds from this spec. All other mockups are current.

**Last updated:** 2026-03-25 by 🎨 Creative Artist
