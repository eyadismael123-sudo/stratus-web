# Cofounder Proposal — Stratus Ecosystem Vision (Malek Edition)

**Date:** 2026-03-25 (original) + 2026-04-03 (Architect additions)
**Authors:** Cofounder Agent + Chief of Staff + Architect
**Status:** FOUNDER APPROVED — READY FOR PLANNER + FRONTEND + BACKEND
**Decision needed from:** Backend Engineer (schema + context assembly), Frontend Engineer (chat UI in Sprint 2)

---

## What Changed and Why

The original Stratus plan was a **vending machine** — 10 agents, each works alone, half are generic filler that ChatGPT already does for free. No reason a client would need Stratus specifically.

This proposal refines the direction into an **ecosystem** — fewer agents, all vertical and defensible, with a shared intelligence layer that makes the product compound in value the more agents a client hires.

**What stays the same:** Tech stack, build sequence, auth, Stripe, dashboard, admin panel, Sprint 1/2 structure, "Hire. Watch. Grow." framework.

**What changes:** Agent lineup (10 → 5), positioning language, memory architecture, context management, client-facing chat.

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

| Category | Agents |
|---|---|
| **Personal** | LinkedIn Post Agent (Live, $50/mo) |
| **Business** | Car Reseller Morning Intel (soon), Property Market Briefing (soon), AI Receptionist (soon) |
| **Health** | Doctor Morning Briefing (soon) — "Division launching 2026" badge |

---

## Memory Architecture — Full Stack

**Core rule: every client is completely isolated. No data ever crosses between clients.**

### The 4 Layers Per Client

| Layer | Where | What |
|---|---|---|
| **Identity** | `profiles` table | Name, timezone, language preference |
| **Voice** | `user_agents.config` JSONB | Tone, topics, style, example posts — per agent |
| **Intelligence** | `agent_signals` table | What their own agents have discovered for them |
| **History** | `agent_logs` table | Everything their agents have done |

### Voice Profile (per client, per agent)

Captured during Telegram onboarding. Stored in `user_agents.config`:

```json
{
  "tone": "authoritative but approachable",
  "industry": "pharma",
  "topics": ["leadership", "innovation", "Dubai healthcare"],
  "language": "en",
  "posting_frequency": "daily",
  "example_posts": ["..."]
}
```

Claude reads this JSON before every generation. Different client = completely separate `user_agents` row.

---

## Ecosystem Layer — Agent Fabric

### What It Is

Agents share intelligence within a single client's context. When one agent discovers something relevant to another agent's domain, that insight flows into the next agent's output automatically.

**Client experience:** The more agents you hire, the smarter all of them get.

**Hard rule:** Signals are scoped to `client_id`. Client A's agents never see Client B's signals.

### Example

Client has LinkedIn Post Agent + Car Reseller Intel:
> Car Intel Agent finds a trending Dubai car market story → writes it to the signals table → LinkedIn Agent picks it up next morning → drafts a thought leadership post about the trend → client gets one combined briefing with the insight AND the post ready to approve.

### Schema

```sql
CREATE TABLE agent_signals (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id    uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  source_agent uuid NOT NULL REFERENCES user_agents(id) ON DELETE CASCADE,
  signal_type  text NOT NULL CHECK (signal_type IN ('trend', 'news', 'opportunity', 'alert')),
  content      text NOT NULL,
  industries   text[] DEFAULT '{}',
  consumed_by  uuid[] DEFAULT '{}',
  expires_at   timestamp DEFAULT (now() + interval '7 days'),
  created_at   timestamp DEFAULT now()
);

CREATE INDEX idx_signals_client     ON agent_signals(client_id);
CREATE INDEX idx_signals_industries ON agent_signals USING GIN(industries);
CREATE INDEX idx_signals_type       ON agent_signals(signal_type);
CREATE INDEX idx_signals_expires    ON agent_signals(expires_at);
```

### Phasing

| When | What | Effort |
|---|---|---|
| **Phase 1** | Create `agent_signals` table — empty, schema only | 30 min |
| **Phase 4+** | Wire agents to read/write signals (after 2 agents are live) | 1-2 hrs per agent |

---

## Context Window Management

**Problem:** Without a strategy, the agent's prompt bloats over time → hallucination, slow responses, wasted tokens.

### Tiered Context Assembly

Before every agent run, a context builder assembles the prompt with hard token budgets:

| Tier | Content | Budget | How |
|---|---|---|---|
| **Static** | Voice profile | ~400 tokens | Stored compressed, updated rarely |
| **Summary** | Rolling memory of past work | ~600 tokens | Pre-summarized weekly, not raw logs |
| **Live** | Today's signals + Grok research | ~1,000 tokens | Last 24h only, top 3 signals |

**Total injected context: ~2,000 tokens max. Generation gets the rest.**

### Rolling Memory Summary

Raw logs are never injected directly.

```
Every Sunday at midnight (per client):
  → Pull last 7 days of agent_logs
  → Call Claude Sonnet: "Summarize what this agent accomplished and learned"
  → Write compressed summary to user_agents.memory_summary
  → Old summary replaced, not appended
```

**New columns needed:**
```sql
ALTER TABLE user_agents ADD COLUMN memory_summary      text;
ALTER TABLE user_agents ADD COLUMN memory_updated_at   timestamp;
```

### Signal Injection — Top 3 Only

Never inject all signals. Inject the 3 most relevant by recency + relevance:

```python
signals = read_signals(client_id, industries, agent_id, limit=3)
```

### Context Assembly Function

```python
def build_agent_context(client_id, agent_id, today_research):
    voice    = get_voice_profile(agent_id)       # ~400 tokens
    summary  = get_memory_summary(agent_id)       # ~600 tokens
    signals  = read_signals(client_id, limit=3)   # ~500 tokens
    research = truncate(today_research, max=800)  # hard cap

    return f"""
## Your Voice
{voice}

## What You've Been Doing
{summary}

## What Your Team Discovered
{signals}

## Today's Research
{research}
"""
```

---

## Client-Facing Chat

### The Concept

Clients can talk directly to their agents and to a Chief of Staff that coordinates the whole team.

- **Chief of Staff** — knows everything about all their agents, answers questions, routes requests
- **Individual agents** — direct conversation about their specific domain

### New Schema

```sql
CREATE TABLE conversations (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id    uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  agent_id     uuid REFERENCES user_agents(id),  -- NULL = Chief of Staff
  created_at   timestamp DEFAULT now()
);

CREATE TABLE messages (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role            text NOT NULL CHECK (role IN ('user', 'assistant')),
  content         text NOT NULL,
  tokens_used     integer,
  created_at      timestamp DEFAULT now()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
```

### Chief of Staff Context

When a client messages the CoS, it gets injected with:
- All hired agents + their current status
- Last `memory_summary` from each agent
- Recent `agent_signals` (last 48h)
- Today's outcome receipts
- Last 10 messages of conversation history

### Conversation History — Context Management

| What | Budget | How |
|---|---|---|
| Last 10 messages | ~800 tokens | Always injected verbatim |
| Older messages | ~400 tokens | Summarized by Haiku on-the-fly |
| Agent context | ~1,000 tokens | Memory summary + recent signals |

Hard cap: 2,200 tokens for conversation context.

### Delivery

| Phase | Surface |
|---|---|
| Sprint 1 | Telegram (per-agent bot + CoS as separate bot) |
| Sprint 2 | Web dashboard chat panel |

Same backend. Different surface.

---

## Model Map (LOCKED)

| Task | Model | Frequency | Why |
|---|---|---|---|
| Telegram onboarding bot | **Haiku** | Once per client | Simple Q&A, no reasoning needed |
| Conversation history compression | **Haiku** | On-demand | Low stakes, needs to be fast |
| Outcome receipts summary | **Haiku** | Daily per client | Friendly recap, low stakes |
| Weekly memory summarization | **Sonnet** | Weekly per client | Quality matters — compounds daily |
| Daily post generation | **Sonnet** | Daily per client | Core product, must be excellent |
| Client chat (agent or CoS) | **Sonnet** | On-demand | Client-facing, quality matters |

---

## Outcome Receipts — Daily Proof of Value

Every evening at 7pm GST, each client gets a Telegram message:

> "Today your team accomplished:
> - LinkedIn Agent: drafted 3 posts, 1 published, 847 impressions
> - Car Intel Agent: found 4 underpriced listings before competitors
> - Hours saved: ~3.2
>
> Tomorrow's agenda: 2 scheduled posts, morning market scan at 8am"

### How It Works

1. Query `agent_logs` for today's entries per client
2. Send to Claude Haiku: "Summarize these logs into a friendly daily report"
3. Send via Telegram

Ships with Phase 4. ~50 lines Python, one cron job.

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
- **Yellow rule:** Status dots + featured pricing + 2 SVG nodes only
- **Font:** Satoshi from Fontshare

---

## Updated Build Additions

| Phase | Addition | Effort |
|---|---|---|
| Phase 1 | `agent_signals` table (empty) | 30 min |
| Phase 1 | `conversations` + `messages` tables | 20 min |
| Phase 1 | `memory_summary` + `memory_updated_at` columns on `user_agents` | 10 min |
| Phase 3 | Chat API endpoints (send message, get history) | 1 hr |
| Phase 4 | Context assembly function | 1 hr |
| Phase 4 | Chief of Staff agent logic | 2 hrs |
| Phase 4 | Per-agent chat context injection | 1 hr per agent |
| Phase 4 | Weekly memory summarization cron | 1 hr |
| Phase 4 | Outcome receipts cron | 1 hr |
| Phase 4 | Agent signal read/write wiring | 1-2 hrs per agent |

---

## Action Items by Agent

### For Backend Engineer
- [ ] Add `agent_signals`, `conversations`, `messages` tables in Phase 1
- [ ] Add `memory_summary` + `memory_updated_at` to `user_agents` in Phase 1
- [ ] Build chat API endpoints in Phase 3
- [ ] Build context assembly function in Phase 4
- [ ] Build Chief of Staff agent logic in Phase 4
- [ ] Build weekly memory summarization cron (Sonnet) in Phase 4
- [ ] Build outcome receipts cron (Haiku) in Phase 4
- [ ] Wire agent signal read/write after 2 agents are live

### For Frontend Engineer
- [ ] Build marketplace with 5 agents (not 10)
- [ ] Use the card one-liners from this doc
- [ ] Update Grow tab to show outcome receipts concept
- [ ] Add "Your agents work better together" copy near pricing
- [ ] Add "Arabic + English" trust signal somewhere on landing page
- [ ] All positioning language uses "hire" / "team" / "workforce"
- [ ] Sprint 2: web dashboard chat panel (per-agent + Chief of Staff threads)

### For Architect
- [ ] Update ARCHITECTURE.md with all new schema additions from this doc
- [ ] Define signal read/write contract for agent pipeline
- [ ] Define context assembly function contract for Backend

---

## Founder Decisions (APPROVED)

| Decision | Status | Date |
|---|---|---|
| Kill generic agents (Content Calendar, CV Optimizer, Job Alerts) | APPROVED | 2026-03-25 |
| Add Agent Fabric (`agent_signals` table in Phase 1, wiring in Phase 4+) | APPROVED | 2026-03-25 |
| Add outcome receipts (daily Telegram summary, Phase 4) | APPROVED | 2026-03-25 |
| New positioning ("Your AI workforce. Built for Dubai. Hired by the month.") | APPROVED | 2026-03-25 |
| Bundle pricing | DEFERRED (after 10 clients) | 2026-03-25 |
| WhatsApp delivery | DEFERRED (after 5 paying clients) | 2026-03-25 |
| Tiered context assembly + rolling memory summaries | APPROVED | 2026-04-03 |
| Model map (Haiku for chatbot/receipts, Sonnet for summaries/generation/chat) | APPROVED | 2026-04-03 |
| Client-facing chat with agents + Chief of Staff | APPROVED | 2026-04-03 |
| Chat on Telegram first (Sprint 1), web dashboard in Sprint 2 | APPROVED | 2026-04-03 |

---

*"The marketplace is how they buy. The ecosystem is why they stay."*

— Cofounder Agent + Chief of Staff + Architect, 2026-04-03
