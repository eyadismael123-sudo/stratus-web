# Stratus — Company Bible

## Who We Are
Stratus is an AI automation agency based in Dubai. We give business owners
a complete operating system — AI agents running in the background, morning
briefings, and a marketplace to buy new agents. Mobile-first. Real clients.

## The Founder
Name: [eyad ismael]
Background: First-year medical student, Dubai
Building: Stratus from scratch on MacBook M4
First client: Dad at AbbVie pharma (LinkedIn Post Agent via Telegram)

## ⚠️ Current Priority — 2026-03-19

### Why We Pivoted
The original platform (web app + mobile app) is infrastructure for an agency that has zero clients.
Building it first is backwards. The LinkedIn Post Agent is the proof of concept:
- Sell it → get a paying client → $50/month confirmed → now the platform makes sense to build
- First client already identified: Dad at AbbVie pharma
- One paying client proves the model. Then we resume the platform.

**Web app and mobile app production is paused until LinkedIn Post Agent has its first paying client.**

Full product spec in `/idea.md`.

---

### LinkedIn Post Agent — MVP Build Plan

**Pricing:** $50/month per client via Stripe (starting low, raising after proof)

**What we're building:**
1. Telegram bot — voice capture onboarding, post generation, 2 variations, refinement buttons
2. Morning research briefings — Grok searches real-time web + X/Twitter → Claude formats into 3 post ideas in client's voice → sent at 8am via Telegram
3. LinkedIn pre-fill link — zero friction posting, deep link sent via bot
4. Stripe subscription — $50/month, checkout from website, webhook activates/deactivates bot access
5. Admin dashboard — local Next.js app, client list + subscription status, voice profile editor, post history, bot status, manual override
6. Full Stratus website — all pages built with real structure, placeholder content where needed, ready to update at any time

**Two-model research pipeline:**
- Grok API → real-time web + X/Twitter trend scanning per client's industry
- Claude API → formats raw Grok signals into 3 post ideas using client's voice_profile.json
- Runs on a daily cron job at 8am per client timezone

**What's out of MVP:**
- Infographic generator (v2)
- Memory/learning loop (v2)

**Build Sequence:**

| Phase | Task | Owner | Est. Time |
|---|---|---|---|
| 0 | Architecture: folder structure, data models, Claude API plan, Grok integration design, cron job design, Telegram flow, Stripe webhook design, admin routes, site page map | 🏛️ Architect | 1 hr |
| 1 | Backend core: FastAPI + SQLite, client management, voice profile storage (JSON), Claude API integration | 👨‍💻 Backend | 2 hrs |
| 2 | Grok research pipeline: Grok API call per client (industry + competitor topics), raw signals → Claude formats into 3 post ideas in client voice, daily cron job at 8am per client timezone | 👨‍💻 Backend | 1.5 hrs |
| 3 | Stripe backend: $50/month product, checkout session, webhook handler (activate/deactivate client), access gate on bot | 👨‍💻 Backend | 2 hrs |
| 4 | Telegram bot: onboarding (voice capture), conversation state machine, post generation, 2 variations, refinement buttons, morning briefing delivery | 👨‍💻 Backend | 2.5 hrs |
| 5 | LinkedIn pre-fill: post approval → URL-encoded deep link button sent in Telegram | 👨‍💻 Backend | 45 min |
| 6 | Admin dashboard: local Next.js — client list, subscription status, voice profile editor, post history, research feed (topics surfaced), bot status, manual activate/deactivate | 👩‍💻 Frontend | 2 hrs |
| 7 | Full Stratus website: all pages listed below, Satoshi font, brand tokens, "Hire for $50/month" → Stripe checkout | 👩‍💻 Frontend | 3.5 hrs |
| 8 | Error review + full journey test: subscribe → bot activates → onboard → 8am briefing arrives → pick topic → generate post → LinkedIn link → cancel → bot blocks | 🔍 + 🧪 | 1.5 hrs |

**Total: ~3.5 days**

**Website Pages:**

| Page | Content |
|---|---|
| `/` | Hero (dark, animated agent cards), "Hire. Watch. Grow." tabs, Agents preview, Pricing, Nav, Footer |
| `/marketplace` | Agent hiring board — LinkedIn Agent live at $50/month, rest "Coming Soon" |
| `/agents/[slug]` | Agent name, what it does, who it's for, price, "Hire" CTA → Stripe |
| `/pricing` | Per-agent breakdown, $50/month, what's included, FAQ |
| `/about` | Who Stratus is, the vision, Dubai context |
| `/contact` | WhatsApp CTA, email, book a call |
| `/blog` | Blog index — grid built, empty, ready for posts |
| `/dashboard` | Teaser/locked — shows dashboard preview, CTA to sign up |
| `/auth/signup` | Sign up form UI (no backend yet) |
| `/auth/signin` | Sign in form UI (no backend yet) |

**After first paying client → resume platform Sprint 1 (web) then Sprint 2 (mobile).**

---

### Skill Assignments by Agent

**🏛️ Architect**
- `everything-claude-code:backend-patterns` — system architecture before any code
- `everything-claude-code:api-design` — all endpoint contracts defined upfront
- `everything-claude-code:database-migrations` — schema design, SQLite → Supabase migration path
- `everything-claude-code:postgres-patterns` — for when platform scales to Supabase
- `everything-claude-code:docker-patterns` — local dev environment design

**👨‍💻 Backend Engineer**
- `everything-claude-code:python-patterns` — Pythonic FastAPI code, type hints, clean structure
- `everything-claude-code:backend-patterns` — middleware, error handling, folder architecture
- `everything-claude-code:api-design` — implements contracts from Architect
- `claude-api` — Anthropic SDK for post generation + formatting Grok signals into client voice
- `everything-claude-code:claude-api` — Claude API Python patterns specifically
- `mcp__grok__chat_completion` — Grok API for real-time web + X/Twitter trend research per client
- `everything-claude-code:security-review` — Stripe webhook verification, API key safety, input validation
- `everything-claude-code:database-migrations` — SQLite schema + migrations
- `everything-claude-code:deployment-patterns` — Railway/Render deploy when ready
- `everything-claude-code:tdd-workflow` — tests before every endpoint
- `everything-claude-code:python-testing` — pytest, integration tests for all APIs

**👩‍💻 Frontend Engineer**
- `everything-claude-code:frontend-patterns` — Next.js app router, Tailwind, component structure
- `shadcn-ui` — admin dashboard components (accurate props, no hallucination)
- `ui-styling` — brand tokens applied correctly, accessible UI
- `ui-ux-pro-max` — full site UX, Hire/Watch/Grow tabs, agent cards, dashboard feel
- `everything-claude-code:e2e` — Playwright E2E for critical flows
- `everything-claude-code:e2e-testing` — Page Object pattern, test structure
- `analytics-tracking` — Vercel Analytics or Plausible on website
- `schema-markup` — SEO structured data on agent pages + pricing
- `page-cro` — landing page optimised to convert, not just look good
- `everything-claude-code:tdd-workflow` — tests before components
- `everything-claude-code:coding-standards` — clean TypeScript across all frontend
- `everything-claude-code:deployment-patterns` — Vercel deploy, env vars, preview branches

**🔍 Error Checker**
- `everything-claude-code:security-review` — Stripe webhook security, auth gates, no exposed secrets
- `everything-claude-code:security-scan` — scans codebase for leaked keys
- `everything-claude-code:python-review` — reviews all backend code before it ships
- `everything-claude-code:verification-loop` — systematic verification after every phase
- `everything-claude-code:build-error-resolver` — fixes any broken builds immediately

**🧪 Tester**
- `everything-claude-code:tdd` — enforces write-tests-first across all phases
- `everything-claude-code:tdd-workflow` — RED → GREEN → IMPROVE cycle
- `everything-claude-code:python-testing` — pytest for all backend endpoints + webhooks
- `everything-claude-code:e2e` — full user journey: land → hire → pay → bot activates → post generated → LinkedIn link
- `everything-claude-code:e2e-testing` — Playwright config, test artifacts
- `everything-claude-code:verification-loop` — nothing ships until loop passes

## Tech Stack
Backend: FastAPI (Python)
Web Frontend: Next.js + Tailwind CSS + Framer Motion (beautiful UI priority)
Mobile: Expo (React Native) + NativeWind — iOS + Android from one codebase
Database: Supabase (Postgres) — production from day 1, no SQLite
Payments: Stripe (per-agent monthly subscription)
Bots/interfaces: Telegram — ACTIVE for LinkedIn Post Agent. Deferred for platform (Sprint 1+2) until founder decides delivery model post-launch.
Device: MacBook M4
Language: Python 3.11+ (backend), TypeScript (web + mobile)

### Why Expo for Mobile
- One codebase → iOS + Android simultaneously
- NativeWind = same Tailwind classes from web, no re-learning
- Expo Router = same file-based routing pattern as Next.js
- Shares FastAPI backend 100% — no backend changes needed for mobile
- Claude Code agents are highly capable with Expo — fastest path to ship

## Our Agents (Products We Are Building)

**Positioning:** "Your AI workforce. Built for Dubai. Hired by the month."

| # | Agent | Category | One-Liner | Status | Price |
|---|---|---|---|---|---|
| 1 | **LinkedIn Post Agent** | Personal | "Writes thought leadership in your voice. Daily." | Live | $50/mo |
| 2 | **Car Reseller Morning Intel** | Business | "Underpriced cars found before your competitors wake up." | Coming Soon | $50/mo |
| 3 | **Property Market Briefing** | Business | "Dubai real estate moves. In your inbox at 8am." | Coming Soon | $50/mo |
| 4 | **Doctor Morning Briefing** | Health | "Clinical news + patient context. Before your first appointment." | Coming Soon | $50/mo |
| 5 | **AI Receptionist** | Business | "Answers, books, follows up. 24/7. Never calls in sick." | Coming Soon | $50/mo |

**Killed (approved 2026-03-25):** Content Calendar Agent, CV/Resume Optimizer, Job Alert Agent — all commodity, ChatGPT/LinkedIn do them for free.

**On Hold:** CV Screener + Scheduler (only if a Dubai recruiter asks AND will pay), Clinic Receptionist (after health vertical has traction).

**Launch Order:** LinkedIn Agent (now) → Car Reseller (Week 2) → Doctor Briefing (Week 3) → Property Market (Month 2) → AI Receptionist (Month 2-3)

**Categories:**
| Category | Agents |
|---|---|
| **Personal** | LinkedIn Post Agent (Live) |
| **Business** | Car Reseller Morning Intel, Property Market Briefing, AI Receptionist (all Coming Soon) |
| **Health** | Doctor Morning Briefing (Coming Soon) — "Division launching 2026" badge |

## Rules Every Agent Follows
- Always read this file before doing anything
- Never write code without understanding the context
- Clean, commented code only — no spaghetti
- Mobile-first thinking always
- Dubai market context always
- When in doubt, ask before building
- After every session, update your memory file if something meaningful happened

## Communication Style
Founder prefers casual tone — talk like a teammate, not a tool.
Short answers unless depth is needed. No fluff.

## Master Roadmap (Claude Code Edition)

### Why Claude Code Changes Everything
With Claude Code running your agents sequentially, each task that would take a solo developer
1 full day gets done in 1-2 hours including your review time. Net result:
- Web app: traditionally 4 weeks → **~2 weeks with Claude Code**
- Mobile app: traditionally 4 weeks → **~1.5 weeks with Claude Code**
- Total: **~3.5 weeks for web + iOS + Android** (vs 8 weeks without)

### Full Roadmap at a Glance
- **Week 1** — Architecture + Design + Backend foundation + Web landing + Auth
- **Week 2** — Web dashboard + Marketplace + Stripe + Admin panel + Deploy web
- **Week 3** — Mobile foundation + Core mobile screens + Marketplace + Payments
- **Week 3.5** — Mobile polish + App Store submit (iOS + Android)
- **Parallel always** — Growth track (market research, content, brand)

### Sprint 1: Web App (2026-03-17 to 2026-03-28, ~2 weeks)
Build the complete Stratus web platform — landing page, auth, dashboard, marketplace, payments, admin.

### Sprint 2: Mobile App (2026-03-28 to 2026-04-07, ~1.5 weeks)
Build the Expo app — same backend, same design language, iOS + Android from one codebase.

### Open Decisions (Blocking Phase 3)
- [x] Price per agent per month — **$50/mo USD** (decided 2026-03-25, AED pricing via Stripe dashboard setting)
- [x] Setup fee — **No setup fee** (decided 2026-03-25)
- [ ] Domain confirmed — needed by end of Week 1

## Cofounder Session — Product & UI Vision (2026-03-16)
*These are founder + cofounder agreed ideas. Planner must pick these up and build around them.*

### Brand & Messaging
- **Positioning (LOCKED):** "Your AI workforce. Built for Dubai. Hired by the month."
- Tagline direction: **"Hire your first AI employee"**
- Supporting line: **"Your staff. No salary. No sick days."**
- Frame everything around *hiring*, not subscribing or automating
- Agents are employees. The marketplace is a hiring board. The dashboard is a team roster.
- UI language throughout: "Your Team", "Hire", "Add Member", "Member Details"
- **Language rules:** Agents = "team members" you "hire" (never "tools" you "subscribe to"). Marketplace = "hiring board" (never "store" or "catalog"). Dashboard = "Your Team" (never "Your Agents" or "Your Tools").
- **Trust signals:** "Built in Dubai", "Arabic + English" somewhere on landing page
- **Grow tab update:** show outcome receipts concept — daily proof of what the team accomplished

### Visual Identity
- Style: **3D Apple-style** — scroll-triggered 3D objects using Spline, animations via Framer Motion
- Colour palette:
  - Background: `#F5F5F7` (near-white, Apple-style)
  - Primary dark: `#3A3A3C` (graphite — from Stratus logo)
  - Accent: **Yellow** — for CTAs, online status dots, highlights
- Mood: premium, minimal, dark graphite anchoring clean white space with yellow energy

### Landing Page
- Hero: dark/minimal, headline + CTA + live agent cards animating in background (agents visibly working)
- Product section uses **3 tabs: Hire. Watch. Grow.**
  - **Hire** — Browse marketplace, pick agent, deploy in minutes
  - **Watch** — Real-time team view. Logs, status, schedule
  - **Grow** — What your agents have done for your business
- These tabs tell the full client journey in 3 words

### Dashboard (Client View)
- Feels like a **team roster**, not a software dashboard
- Agent card shows: Name, current activity, connected app (WhatsApp/Telegram/LinkedIn icon), Online/Offline status dot
- Click agent → detailed view: logs, schedule, settings, history
- Simple. Minimal. No noise.

### Marketplace
- Built from day 1 — architecture must support it from the start
- New agent added every ~2 days
- Clients pay **per agent** (monthly subscription per agent hired)
- Each listing: agent name + role, one-line description, industries, price
- Browsing agents = hiring, not shopping

### Pricing
- **$50/mo per agent.** Simple. No tiers yet.
- Add copy: **"Your agents work better together"**
- No bundle pricing yet — sell one agent first, bundles after 10 clients
- Setup fee: none

### Tech for UI
- Spline for 3D objects embedded in Next.js
- Framer Motion for scroll-triggered animations
- Tailwind CSS for layout

## The Team

**Leadership**
| Agent | Role |
|---|---|
| 🤝 Cofounder | Shapes every idea before it's built. First stop for anything new. |
| 📋 Planner | Breaks approved ideas into tasks. Assigns owners. Nothing moves without founder Go. |
| 👔 Chief of Staff | Orchestrates the team, runs meetings, tracks everything, logs decisions. |

**Build Team**
| Agent | Role |
|---|---|
| 🏛️ Architect | Designs all systems and API contracts. Phase 0 of every build. |
| 👨‍💻 Backend Engineer | FastAPI, Supabase, Python. All server-side logic. Telegram deferred. |
| 👩‍💻 Frontend Engineer | Next.js, Tailwind, Framer Motion, Vercel. All UI and deployment. |
| 🎨 Creative Artist | Designs everything before Frontend builds it. Jony Ive standard. |
| 🔍 Error Checker | Reviews all code before it ships. Non-negotiable quality gate. |
| 🧪 Tester | Nothing ships without passing tests. |

**Growth**
| Agent | Role |
|---|---|
| 📊 Market Researcher | Dubai market intelligence, competitive landscape, pricing benchmarks. |
| 📣 Marketing Director | Brand, content strategy, content briefs, launch planning. |
| 🤖 Grok X Researcher | Real-time X/Twitter trend intelligence. |
| ✏️ Content Executor | Visuals, Canva slides, captions. Executes Marketing Director briefs. |

---

## Execution Plan v3 — Web + Mobile (Claude Code Edition)

*Revised by Planner on 2026-03-17. Accounts for Claude Code sequential execution and 3-5x speed gain.*
*Eyad runs 1 agent at a time. All tasks are sequential. Backend always before Frontend.*

### Build Flow (non-negotiable sequence)
🏛️ Architect → 🎨 Creative Artist → 👨‍💻 Backend → 👩‍💻 Frontend → 🔍 Error Checker → 🧪 Tester → Ship

### Claude Code Time Reference
- Simple API endpoint or UI component: **~45 min** (Claude Code codes it, you review it)
- Complex feature (auth, Stripe, marketplace): **~1.5-2 hrs**
- Full phase with review + test: **~1 full day**
- You can realistically ship **3-5 tasks per focused session**

---

## ═══ SPRINT 1: WEB APP ═══

---

### PHASE 0 — Architecture + Design (Day 1)
*No code yet. Think first. Claude Code is fast but architecture mistakes cost more to undo.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 0.1 | ✅ Full system architecture — DB schema, all API contracts, auth flow, agent model, marketplace schema, Stripe webhook design, mobile-compatible API design. **Saved to `/ARCHITECTURE.md`** | 🏛️ Architect | DONE |
| 0.2 | ✅ Brand system — colour tokens, typography, spacing scale, component spec. **Saved to `/BRAND.md`** | 🎨 Creative Artist | DONE |
| 0.3 | ✅ DONE — All 8 HTML mockups complete. Category taxonomy (Personal/Business/Health) added across Dashboard, Marketplace, and Landing Page. Live search on Marketplace. Yellow rule enforced. See `/DESIGN.md` for full spec. Awaiting founder review before Next.js build. | 🎨 Creative Artist | DONE |

**Gate:** Both 0.1 and 0.3 complete before any code is written. No exceptions.

---

### PHASE 1 — Backend Foundation (Day 2)
*Backend first. Frontend cannot connect to nothing.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 1.1 | Scaffold FastAPI — folder structure, env config (.env), CORS, health endpoint, error handler | 👨‍💻 Backend | 45 min |
| 1.2 | Supabase setup + DB schema — users, agents, subscriptions, logs, marketplace tables per Architect spec | 👨‍💻 Backend | 1.5 hrs |
| 1.3 | Supabase Auth integration — profile endpoint, permission middleware (user owns their agents), admin role check. Supabase handles login/register/JWT/refresh natively. | 👨‍💻 Backend | 1.5 hrs |
| 1.4 | Create `agent_signals` table (empty, schema only) — ecosystem foundation for cross-agent intelligence. Schema: `id` (uuid), `client_id` (fk → users), `source_agent` (fk → user_agents), `signal_type` (enum: trend/news/opportunity/alert), `content` (text), `industries` (text[]), `consumed_by` (uuid[]), `created_at` (timestamp). No wiring yet — just the table. | 👨‍💻 Backend | 30 min |
| 1.5 | Code review — Phase 1 backend | 🔍 Error Checker | 45 min |

---

### PHASE 2 — Web Foundation + Landing (Days 2–3)
*Frontend scaffold + the most important page: the landing page.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 2.1 | Scaffold Next.js — app router, Tailwind brand tokens, Framer Motion installed, Spline package, shared API client (axios instance pointing at FastAPI) | 👩‍💻 Frontend | 1 hr |
| 2.2 | Landing page — Hero (dark, animated agent cards in bg), "Hire. Watch. Grow." tabs, Pricing section, Nav, Footer | 👩‍💻 Frontend | 2.5 hrs |
| 2.3 | Auth pages — Sign Up, Sign In, Password Reset (connected to Phase 1 API) | 👩‍💻 Frontend | 1.5 hrs |
| 2.4 | Code review — Phase 2 frontend | 🔍 Error Checker | 45 min |
| 2.5 | Test auth flow end-to-end — register → login → JWT stored → logout | 🧪 Tester | 1 hr |

---

### PHASE 3 — Agent + Marketplace APIs (Day 4)
*Backend for dashboard and marketplace. Frontend needs these to build on.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 3.1 | Agent APIs — CRUD, status update, logs endpoint, schedule endpoint | 👨‍💻 Backend | 1.5 hrs |
| 3.2 | Marketplace API — list agents, agent detail, hire endpoint (creates subscription record) | 👨‍💻 Backend | 1.5 hrs |
| 3.3 | Code review — Phase 3 backend | 🔍 Error Checker | 45 min |

---

### PHASE 4 — Dashboard + Marketplace UI (Days 4–5)
*The core product. Team roster feel, not software dashboard.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 4.1 | Dashboard shell — "Your Team" layout, protected route, sidebar nav | 👩‍💻 Frontend | 1.5 hrs |
| 4.2 | Agent Card component — name, current activity, platform icon (Telegram/LinkedIn/WhatsApp), Online/Offline yellow dot | 👩‍💻 Frontend | 1 hr |
| 4.3 | Agent Detail page — logs feed, schedule view, settings panel, activity history | 👩‍💻 Frontend | 1.5 hrs |
| 4.4 | Calendar view — scheduled runs per agent per day (simple grid, not over-engineered) | 👩‍💻 Frontend | 1 hr |
| 4.5 | Marketplace page — hiring board layout, 5 agents (use one-liners from "Our Agents" section), LinkedIn Agent = "Live", rest = "Coming Soon", "Your agents work better together" copy near pricing | 👩‍💻 Frontend | 1.5 hrs |
| 4.6 | Outcome receipts cron job — daily 7pm Telegram summary per client. Query `agent_logs` for today's entries → Claude API summarizes into friendly daily report → send via Telegram. ~50 lines Python, one cron job. | 👨‍💻 Backend | 1.5 hrs |
| 4.7 | Code review — all Phase 4 | 🔍 Error Checker | 45 min |
| 4.8 | Test dashboard + marketplace — data loads, hire flow works, status dots update | 🧪 Tester | 1 hr |

---

### PHASE 5 — Payments + Admin (Days 6–7)
*Money and control. Stripe must be airtight.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 5.1 | Stripe backend — per-agent monthly subscription, checkout session, webhook handler (payment succeeded / subscription cancelled) | 👨‍💻 Backend | 2 hrs |
| 5.2 | Billing API — active subscriptions, invoice list, cancel subscription | 👨‍💻 Backend | 1 hr |
| 5.3 | Access gate — agent access blocked unless active Stripe subscription exists | 👨‍💻 Backend | 45 min |
| 5.4 | Billing page UI — active subscriptions, invoice history, manage/cancel | 👩‍💻 Frontend | 1.5 hrs |
| 5.5 | Admin panel — all clients table, all agents, total earnings, agent health monitoring | 👩‍💻 Frontend | 2 hrs |
| 5.6 | Admin controls — add/edit/remove marketplace listings, toggle agent live/hidden | 👩‍💻 Frontend | 1 hr |
| 5.7 | Code review — all Phase 5, especially Stripe webhook security (signature verification) | 🔍 Error Checker | 1 hr |
| 5.8 | Test full payment flow — subscribe → access granted → cancel → access revoked | 🧪 Tester | 1 hr |

---

### PHASE 6 — Web Polish + Deploy (Day 8)
*Ship the web app. AbbVie onboarded. Web done.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 6.1 | Spline 3D hero object — scroll-responsive, embedded in landing hero section | 👩‍💻 Frontend | 1.5 hrs |
| 6.2 | Responsive pass — every page tested at 375px, 768px, 1280px | 👩‍💻 Frontend | 1 hr |
| 6.3 | Performance pass — image optimisation, lazy loading, bundle check | 👩‍💻 Frontend | 45 min |
| 6.4 | Deploy — Vercel (Next.js) + Railway (FastAPI) | 👨‍💻 Backend | 1 hr |
| 6.5 | Final smoke test — land → sign up → hire agent → pay → dashboard loads | 🧪 Tester | 1 hr |
| 6.6 | Onboard AbbVie (Dad) as first client | Eyad | — |

**WEB APP SHIPPED. Sprint 1 complete.**

---

## ═══ SPRINT 2: MOBILE APP (Expo) ═══

*Same FastAPI backend. No backend changes needed. 100% of the API work is already done.*
*Expo shares your Tailwind knowledge (NativeWind) and Next.js routing patterns (Expo Router).*

---

### PHASE 7 — Mobile Architecture + Design (Day 9, half day)
*Much shorter than Phase 0 — architecture is already done. Just mobile-specific adaptations.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 7.1 | Mobile architecture — navigation structure (tab bar + stack), shared API client plan, push notification setup, offline strategy | 🏛️ Architect | 1 hr |
| 7.2 | Mobile design — all screens adapted for mobile (375px native): Home, Auth, Dashboard, Agent Card, Agent Detail, Marketplace, Billing, Settings | 🎨 Creative Artist | 1.5 hrs |

---

### PHASE 8 — Mobile Foundation + Auth (Day 9–10)
*Expo scaffold + auth. Same JWT tokens from the web backend.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 8.1 | Scaffold Expo app — Expo Router, NativeWind, shared TypeScript API client (reused from web), SecureStore for JWT, navigation structure (tabs + auth stack) | 👩‍💻 Frontend | 1.5 hrs |
| 8.2 | Auth screens — Sign In, Sign Up, Password Reset (hitting same FastAPI /auth endpoints) | 👩‍💻 Frontend | 1.5 hrs |
| 8.3 | Tab bar — Dashboard, Marketplace, Billing, Settings | 👩‍💻 Frontend | 45 min |
| 8.4 | Code review — mobile foundation | 🔍 Error Checker | 45 min |

---

### PHASE 9 — Core Mobile Screens (Days 10–11)
*The product in your pocket.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 9.1 | Dashboard screen — "Your Team" agent list, pull-to-refresh, real-time status dots | 👩‍💻 Frontend | 1.5 hrs |
| 9.2 | Agent Detail screen — logs feed, schedule, settings, activity history | 👩‍💻 Frontend | 1.5 hrs |
| 9.3 | Marketplace screen — agent hiring board, agent card, "Hire" flow with Stripe checkout (web redirect or native) | 👩‍💻 Frontend | 1.5 hrs |
| 9.4 | Billing screen — active subscriptions, manage/cancel | 👩‍💻 Frontend | 1 hr |
| 9.5 | Push notifications — agent status changes, job completed, error alerts (Expo Push Notifications) | 👩‍💻 Frontend | 1 hr |
| 9.6 | Code review — all Phase 9 | 🔍 Error Checker | 45 min |
| 9.7 | Test mobile flows — login → dashboard → hire → billing → receive push notification | 🧪 Tester | 1 hr |

---

### PHASE 10 — Mobile Polish + App Store (Days 12–13)
*Submit to both stores. You're live.*

| # | Task | Owner | Est. Time |
|---|---|---|---|
| 10.1 | Animations — screen transitions, loading skeletons, haptic feedback on key actions | 👩‍💻 Frontend | 1.5 hrs |
| 10.2 | App icons + splash screen — graphite + yellow brand, both iOS and Android sizes | 🎨 Creative Artist | 45 min |
| 10.3 | EAS Build — production build for iOS (IPA) and Android (AAB) via Expo Application Services | 👩‍💻 Frontend | 1 hr |
| 10.4 | App Store Connect submission — screenshots, description, review notes | Eyad | — |
| 10.5 | Google Play Console submission — screenshots, description, content rating | Eyad | — |
| 10.6 | Final end-to-end test on real device — full journey on iPhone + Android emulator | 🧪 Tester | 1 hr |

**MOBILE APP SHIPPED. Sprint 2 complete. Both platforms live.**

---

## GROWTH TRACK — Parallel Throughout

*Run these between build sessions or assign to growth agents while you review build output.*

| # | Task | Owner | When |
|---|---|---|---|
| G.1 | Dubai market research — competitors, pricing benchmarks, target SME verticals | 📊 Market Researcher | Week 1 |
| G.2 | Brand strategy + content pillars — positioning, audience, platform focus | 📣 Marketing Director | Week 1 |
| G.3 | Monitor X/Twitter — AI agent trends, Dubai startup signals, competitor moves | 🤖 Grok X Researcher | Ongoing |
| G.4 | Launch assets — hero visuals, Canva slides, captions, demo video script | ✏️ Content Executor | Week 2–3 |
| G.5 | Launch content brief — multi-platform announcement strategy | 📣 Marketing Director | Week 3 |

---

## Architecture Decisions (Locked — 2026-03-17)

*These decisions were made by the Architect and approved by the founder. Do not revisit unless founder says so.*

| Decision | Chosen | Rejected | Reason |
|---|---|---|---|
| Database | Supabase (Postgres) | SQLite | SQLite can't handle concurrent web + mobile clients. Supabase gives Realtime, Auth, and Storage in one. |
| Auth | Supabase Auth | Custom JWT | Building JWT from scratch is a security risk. Supabase Auth gives register/login/refresh/reset out of the box. |
| Agent model | Two tables: `agent_templates` + `user_agents` | Single table | Templates = marketplace blueprints (reusable). Instances = what a user hired (per-client, has Stripe sub). |
| Real-time status | Supabase Realtime subscriptions | Polling | No battery drain on mobile, no scaling cost, works on Expo natively. |
| Telegram | Deferred | Sprint 1 | Founder decides delivery model after app ships. No scope in Sprint 1 or 2. |

**Architecture Document:** `/ARCHITECTURE.md` — full DB schema, all API contracts, Stripe flow, auth flow, folder structure. Backend codes from this. Do not improvise.

> 👨‍💻 **Backend Engineer:** Before writing any code in Phases 1–5, read `/ARCHITECTURE.md` in full. It contains the exact table definitions, indexes, API contracts, error codes, and FastAPI folder structure. Your source of truth.

---

## Conflict Resolution
When agents disagree on how to build something, present both sides
clearly in plain English and let the founder decide. Log the decision.

---

## Agent Toolkit

### Skills (available to all agents)
- everything-claude-code — agents, hooks, commands, rules (all agents)
- claude-ads — 186-point ad audit across Google, Meta, LinkedIn, TikTok, YouTube (Marketing Director)
- marketingskills — CRO, copywriting, SEO, email sequences, content calendars (Marketing Director)

### MCPs (enable per session as needed)
- figma — read Figma designs directly, pixel-perfect design-to-code (Creative Artist + Frontend)
- nano-banana — generate images via Gemini API (ALL agents)
- grok — real-time X/Twitter trends and competitor intelligence (Grok X Researcher)
- github — repos, PRs, issues, CI/CD workflows (Backend + Frontend)
- playwright — browser automation, E2E testing, screen recording (Tester + Frontend)
- context7 — live Next.js/React docs, never uses deprecated APIs (Frontend Engineer)
- shadcn — accurate shadcn/ui components, no hallucinated props (Frontend Engineer)

### Token Management
Keep active MCPs under 5 per session. Disable what you don't need:
- Frontend build session: figma, context7, shadcn, github
- Image generation: nano-banana only
- X research: grok only
- E2E testing: playwright only
- General building: context7, github, playwright

