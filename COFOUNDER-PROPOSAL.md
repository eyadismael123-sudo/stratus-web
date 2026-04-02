# Cofounder Proposal — Stratus Ecosystem Vision

**Date:** 2026-03-25
**Authors:** Cofounder Agent + Chief of Staff
**Status:** FOUNDER APPROVED — READY FOR PLANNER + FRONTEND
**Decision needed from:** Planner (update docs), Frontend Engineer (build from this)

---

## What Changed and Why

The original Stratus plan was a **vending machine** — 10 agents, each works alone, half are generic filler that ChatGPT already does for free. No reason a client would need Stratus specifically.

This proposal refines the direction into an **ecosystem** — fewer agents, all vertical and defensible, with a shared intelligence layer that makes the product compound in value the more agents a client hires.

**What stays the same:** Tech stack, build sequence, auth, Stripe, dashboard, admin panel, Sprint 1/2 structure, "Hire. Watch. Grow." framework.

**What changes:** Agent lineup (10 → 5), positioning language, one new backend table, one new cron job.

---

## Brand Direction (LOCKED)

**Positioning:** "Your AI workforce. Built for Dubai. Hired by the month."

- Not a platform (clients don't build anything)
- Not a consultancy (no AED 20K+ setup fees)
- Not a chatbot (agents work autonomously while you sleep)
- It's **staff.** They show up. They work. You see the receipts.

**Tagline:** "Hire. Watch. Grow." (already locked in design)

**Language rules:**
- Agents are "team members" you "hire" — never "tools" you "subscribe to"
- The marketplace is a "hiring board" — never a "store" or "catalog"
- The dashboard is "Your Team" — never "Your Agents" or "Your Tools"

---

## Website Direction — Section by Section

### Hero
- **Headline:** "Hire your first AI employee"
- **Sub-headline:** "Your staff. No salary. No sick days."
- **CTA:** "Get Started" (graphite button, NOT yellow)
- No changes from current design. This still works.

### Hire. Watch. Grow. Tabs

| Tab | Content | What's New |
|---|---|---|
| **Hire** | Browse 5 real agents, each with a clear industry vertical | Trimmed from 10 to 5. Quality over quantity. |
| **Watch** | "Your team is working right now" — live status, logs, schedule | Emphasize "team" not "tools." Same concept. |
| **Grow** | "See what your team accomplished today" — daily outcome receipts | NEW — show the daily Telegram summary concept. Real numbers, real proof. |

### Marketplace Section (Landing Page Preview)
- 5 agents grouped by category (Personal / Business / Health)
- LinkedIn Post Agent is the only "Live" listing
- All others show "Coming Soon"
- Health category keeps "Division launching 2026" badge

### Pricing Section
- $50/mo per agent. Simple. No tiers yet.
- Add one line of copy: **"Your agents work better together"**
- No bundle pricing yet — sell one agent first, bundles come later

### Footer / Trust Signals
- "Built in Dubai" stays
- Add "Arabic + English" somewhere as a trust signal
- "© 2026 Stratus. Built in Dubai."

---

## The 5 Agents — Final Lineup

### Kill List (APPROVED — remove from all docs)

| Agent | Reason |
|---|---|
| Content Calendar Agent | Feature, not a product. Every AI tool does this for free. |
| CV/Resume Optimizer | ChatGPT does this for free. Dead on arrival. |
| Job Alert Agent | LinkedIn already does this natively. |

### Live Lineup

| # | Agent | Category | Card One-Liner | Status | Price |
|---|---|---|---|---|---|
| 1 | **LinkedIn Post Agent** | Personal | "Writes thought leadership in your voice. Daily." | Live | $50/mo |
| 2 | **Car Reseller Morning Intel** | Business | "Underpriced cars found before your competitors wake up." | Coming Soon | $50/mo |
| 3 | **Property Market Briefing** | Business | "Dubai real estate moves. In your inbox at 8am." | Coming Soon | $50/mo |
| 4 | **Doctor Morning Briefing** | Health | "Clinical news + patient context. Before your first appointment." | Coming Soon | $50/mo |
| 5 | **AI Receptionist** | Business | "Answers, books, follows up. 24/7. Never calls in sick." | Coming Soon | $50/mo |

### On Hold (revisit after 10 paying clients)

| Agent | Condition |
|---|---|
| CV Screener + Scheduler | Only build if a Dubai recruiter asks AND will pay |
| Clinic Receptionist | Extension of Doctor play — build when health vertical has traction |

### Launch Order

1. **LinkedIn Post Agent** — NOW (Dad at AbbVie, $50/mo, first revenue)
2. **Car Reseller Morning Intel** — Week 2 (same architecture, different Grok queries)
3. **Doctor Morning Briefing** — Week 3 (Eyad's med school domain edge)
4. **Property Market Briefing** — Month 2
5. **AI Receptionist** — Month 2-3

---

## Updated Category Taxonomy

Replaces the 10-agent taxonomy in DESIGN.md:

| Category | Agents |
|---|---|
| **Personal** | LinkedIn Post Agent (Live, $50/mo) |
| **Business** | Car Reseller Morning Intel (soon), Property Market Briefing (soon), AI Receptionist (soon) |
| **Health** | Doctor Morning Briefing (soon) — "Division launching 2026" badge |

---

## Ecosystem Layer — Agent Fabric

### What It Is

Agents share intelligence through a shared signal layer. When one agent discovers something relevant to another agent's domain, that insight flows into the next agent's output automatically.

**Client experience:** The more agents you hire, the smarter all of them get.

### Example

Client has LinkedIn Post Agent + Car Reseller Intel:
> Car Intel Agent finds a trending Dubai car market story → writes it to the signals table → LinkedIn Agent picks it up next morning → drafts a thought leadership post about the trend → client gets one combined briefing with the insight AND the post ready to approve.

### Technical Implementation

**New table: `agent_signals`**

```
agent_signals:
  - id            (uuid)
  - client_id     (fk → users)
  - source_agent  (fk → user_agents)
  - signal_type   (enum: trend, news, opportunity, alert)
  - content       (text)
  - industries    (text[])
  - consumed_by   (uuid[])
  - created_at    (timestamp)
```

### Phasing (Chief of Staff recommendation)

| When | What | Effort |
|---|---|---|
| **Phase 1** (backend foundation) | Create `agent_signals` table — empty, schema only | 30 min |
| **Phase 4+** (after agent #2 is live) | Wire agents to read/write signals | 1-2 hrs per agent |

Don't build cross-agent plumbing until there are 2+ agents live. The table costs nothing to create early.

---

## Outcome Receipts — Daily Proof of Value

Every evening at 7pm, each client gets a Telegram message:

> "Today your team accomplished:
> - LinkedIn Agent: drafted 3 posts, 1 published, 847 impressions
> - Car Intel Agent: found 4 underpriced listings before competitors
> - Hours saved: ~3.2
>
> Tomorrow's agenda: 2 scheduled posts, morning market scan at 8am"

### How It Works

1. Query `agent_logs` for today's entries per client
2. Send to Claude API: "Summarize these logs into a friendly daily report"
3. Send via Telegram

### Phasing

- **Ships with Phase 4** (after LinkedIn Post Agent is live and logging)
- ~50 lines of Python, one cron job
- No extra auth, no extra compute beyond one Claude API call per client per day

---

## Dubai-Native Features

| Feature | Ship When | Effort | Notes |
|---|---|---|---|
| Arabic language toggle | v1 (Week 1) | One JSON field in voice profile | Claude API handles Arabic natively |
| AED pricing | v1 (Week 1) | Stripe dashboard setting | Trivial |
| Timezone-aware cron (GST) | v1 (Week 1) | Already in client model | Already designed |
| WhatsApp delivery | v2 (after 5 clients) | 2-day task | Meta Business API verification required |
| Government data feeds (RERA, DED) | v3 or never | High effort, low reliability | Use Grok web search instead — 90% as good |

---

## What Does NOT Change

- **Tech stack:** FastAPI, Supabase, Next.js, Stripe, Telegram, Vercel, Railway
- **Build sequence:** Architect → Creative → Backend → Frontend → Error Checker → Tester
- **Auth:** Supabase Auth (register/login/JWT/refresh)
- **Dashboard:** "Your Team" roster layout
- **Admin:** War Room, founder-only
- **Sprint structure:** Sprint 1 (web) → Sprint 2 (mobile)
- **Hero scroll journey:** "The Network" 5-stage animation — locked
- **Yellow rule:** Status dots + featured pricing + 2 SVG nodes only
- **Font:** Satoshi from Fontshare

---

## Action Items by Agent

### For Planner
- [ ] Update CLAUDE.md agent lineup (10 → 5, with kill list applied)
- [ ] Update CLAUDE.md build phases to include `agent_signals` table in Phase 1
- [ ] Add outcome receipts cron to Phase 4
- [ ] Update DESIGN.md category taxonomy (10 → 5 agents)

### For Architect
- [ ] Add `agent_signals` table to ARCHITECTURE.md schema
- [ ] Define signal read/write contract for agent pipeline
- [ ] Confirm no other schema changes needed

### For Frontend Engineer
- [ ] Build marketplace with 5 agents (not 10)
- [ ] Use the card one-liners from this doc
- [ ] Update Grow tab to show outcome receipts concept
- [ ] Add "Your agents work better together" copy near pricing
- [ ] Add "Arabic + English" trust signal somewhere on landing page
- [ ] All positioning language uses "hire" / "team" / "workforce" — never "subscribe" / "tools"

### For Creative Artist
- [ ] Update mockups to reflect 5-agent lineup
- [ ] Consider visual for "team intelligence" — how agents connect

### For Backend Engineer
- [ ] Create `agent_signals` table in Phase 1 (empty, schema only)
- [ ] Build outcome receipts cron job in Phase 4
- [ ] Add Arabic `language` field to voice profile JSON

---

## Founder Decisions (APPROVED 2026-03-25)

1. **Kill generic agents** (Content Calendar, CV Optimizer, Job Alerts) — APPROVED
2. **Add Agent Fabric** (`agent_signals` table in Phase 1, wiring in Phase 4+) — APPROVED
3. **Add outcome receipts** (daily Telegram summary, Phase 4) — APPROVED
4. **New positioning** ("Your AI workforce. Built for Dubai. Hired by the month.") — APPROVED
5. **Bundle pricing** — DEFERRED (sell 1 agent first, revisit after 10 clients)
6. **WhatsApp delivery** — DEFERRED to v2 (after 5 paying clients)

---

*"The marketplace is how they buy. The ecosystem is why they stay."*

— Cofounder Agent + Chief of Staff, 2026-03-25
