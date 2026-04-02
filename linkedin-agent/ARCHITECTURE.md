# LinkedIn Post Agent — Architecture

> Designed by Architect. Phase 0 complete. Backend codes from this. Do not improvise.

---

## 1. Folder Structure

```
linkedin-agent/
├── app/
│   ├── main.py                    # FastAPI app entry, router registration, startup hooks
│   ├── config.py                  # env vars via pydantic-settings
│   ├── database.py                # SQLite connection, session factory
│   ├── models/
│   │   ├── client.py              # SQLAlchemy ORM models
│   │   ├── post.py
│   │   ├── briefing.py
│   │   ├── subscription.py
│   │   └── bot_state.py
│   ├── schemas/
│   │   ├── client.py              # Pydantic request/response schemas
│   │   ├── post.py
│   │   ├── briefing.py
│   │   └── subscription.py
│   ├── routers/
│   │   ├── admin.py               # Admin dashboard API routes
│   │   ├── stripe_webhook.py      # Stripe webhook handler
│   │   └── site.py                # Public routes (checkout, health)
│   ├── services/
│   │   ├── grok.py                # Grok API client
│   │   ├── claude.py              # Claude API client
│   │   ├── pipeline.py            # Grok → Claude research pipeline
│   │   ├── telegram_bot.py        # Bot logic, state machine
│   │   ├── linkedin.py            # Pre-fill URL generator
│   │   └── stripe.py              # Stripe checkout + webhook logic
│   ├── jobs/
│   │   └── morning_briefing.py    # APScheduler cron job
│   └── voice_profiles/            # JSON files per client (gitignored)
│       └── {client_id}.json
├── data/
│   └── stratus.db                 # SQLite database (gitignored)
├── tests/
│   ├── test_pipeline.py
│   ├── test_telegram.py
│   ├── test_stripe.py
│   └── test_admin.py
├── .env                           # gitignored
├── .env.example
├── requirements.txt
└── README.md
```

---

## 2. SQLite Schema

### clients
```sql
CREATE TABLE clients (
    id                    TEXT PRIMARY KEY,           -- UUID
    name                  TEXT NOT NULL,
    email                 TEXT UNIQUE NOT NULL,
    telegram_chat_id      TEXT UNIQUE,                -- set during onboarding
    industry              TEXT,                       -- e.g. "pharmaceutical"
    company               TEXT,
    timezone              TEXT DEFAULT 'Asia/Dubai',
    bot_active            INTEGER DEFAULT 0,          -- 0/1
    onboarded             INTEGER DEFAULT 0,          -- 0/1
    stripe_customer_id    TEXT,
    stripe_subscription_id TEXT,
    created_at            TEXT DEFAULT (datetime('now')),
    updated_at            TEXT DEFAULT (datetime('now'))
);
```

### subscriptions
```sql
CREATE TABLE subscriptions (
    id                      TEXT PRIMARY KEY,          -- UUID
    client_id               TEXT NOT NULL REFERENCES clients(id),
    stripe_subscription_id  TEXT UNIQUE NOT NULL,
    stripe_customer_id      TEXT NOT NULL,
    status                  TEXT NOT NULL,             -- active | cancelled | past_due
    current_period_start    TEXT,
    current_period_end      TEXT,
    amount_cents            INTEGER DEFAULT 5000,      -- $50.00
    created_at              TEXT DEFAULT (datetime('now')),
    updated_at              TEXT DEFAULT (datetime('now'))
);
```

### briefings
```sql
CREATE TABLE briefings (
    id          TEXT PRIMARY KEY,                      -- UUID
    client_id   TEXT NOT NULL REFERENCES clients(id),
    date        TEXT NOT NULL,                         -- YYYY-MM-DD
    topics      TEXT NOT NULL,                         -- JSON: array of 3 topic objects
    status      TEXT DEFAULT 'sent',                   -- sent | failed
    sent_at     TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);
```

### posts
```sql
CREATE TABLE posts (
    id               TEXT PRIMARY KEY,                 -- UUID
    client_id        TEXT NOT NULL REFERENCES clients(id),
    briefing_id      TEXT REFERENCES briefings(id),
    briefing_date    TEXT NOT NULL,                    -- YYYY-MM-DD
    topic            TEXT NOT NULL,                    -- selected topic headline
    variation_a      TEXT NOT NULL,
    variation_b      TEXT NOT NULL,
    final_post       TEXT,                             -- refined/selected text
    status           TEXT DEFAULT 'draft',             -- draft | approved | posted
    linkedin_url     TEXT,                             -- pre-fill URL sent to client
    research_signals TEXT,                             -- JSON: raw Grok output
    created_at       TEXT DEFAULT (datetime('now')),
    updated_at       TEXT DEFAULT (datetime('now'))
);
```

### bot_states
```sql
CREATE TABLE bot_states (
    telegram_chat_id  TEXT PRIMARY KEY,
    state             TEXT NOT NULL DEFAULT 'idle',    -- see state machine section
    context           TEXT,                            -- JSON: temp data mid-conversation
    updated_at        TEXT DEFAULT (datetime('now'))
);
```

---

## 3. Voice Profile Model

`app/voice_profiles/{client_id}.json`

```json
{
  "client_id": "uuid",
  "name": "Dr. Ahmed Al-Rashid",
  "title": "Regional Medical Director, AbbVie MENA",
  "company": "AbbVie",
  "industry": "pharmaceutical",
  "audience": "Healthcare professionals, medical researchers, pharma executives in MENA",
  "tone": {
    "adjectives": ["authoritative", "empathetic", "data-driven", "forward-thinking"],
    "avoid": ["casual slang", "excessive jargon", "self-promotion"]
  },
  "writing_style": {
    "sentence_length": "medium",
    "uses_questions": true,
    "uses_statistics": true,
    "uses_personal_anecdotes": true,
    "cta_style": "invites discussion"
  },
  "recurring_themes": [
    "patient outcomes",
    "pharma innovation in MENA",
    "evidence-based medicine",
    "healthcare leadership"
  ],
  "competitor_topics": [
    "Pfizer MENA",
    "Novartis Middle East",
    "pharma regulatory updates UAE"
  ],
  "sample_posts": [
    "Paste of an actual LinkedIn post the client has written or approved"
  ],
  "linkedin_profile_url": "https://linkedin.com/in/...",
  "created_at": "2026-03-19T00:00:00Z",
  "updated_at": "2026-03-19T00:00:00Z"
}
```

---

## 4. Grok → Claude Pipeline

### Data Flow

```
APScheduler (8am per client timezone)
  → pipeline.run_morning_briefing(client_id)
      → load client + voice_profile.json
      → grok.scan_trends(client, voice_profile)      # 3 Grok API calls → raw_signals[]
      → claude.format_briefing(client, voice_profile, raw_signals)  # 1 Claude call → 3 topics
      → store briefing in DB
      → telegram_bot.send_briefing(client, briefing)
```

### Grok API — 3 Calls Per Client

```python
queries = [
    f"Latest trends and news in {industry} this week",
    f"{', '.join(competitor_topics)} recent news and updates",
    f"LinkedIn thought leadership topics for {title} in {industry} right now"
]
# Each query hits mcp__grok__chat_completion with web_search enabled
# Results concatenated into raw_signals string
```

### Claude API — Prompt Structure

```
System:
You are a LinkedIn ghostwriter for {name}, {title} at {company}.

Voice profile:
- Tone: {tone.adjectives joined}
- Audience: {audience}
- Recurring themes: {recurring_themes joined}
- Avoid: {tone.avoid joined}
- Writing style: {writing_style summary}

Sample posts for reference:
{sample_posts[0]}

Task:
Based on the research signals below, generate exactly 3 post ideas.
Each idea must be relevant to their industry, written in their voice,
and timely given today's signals.

Research signals:
{raw_signals}

Output (JSON only, no commentary):
{
  "topics": [
    {
      "id": "1",
      "headline": "One-sentence hook",
      "angle": "What the post argues or shares",
      "why_now": "Why this is timely",
      "suggested_cta": "Question or call to action to close with"
    }
  ]
}
```

### Output
3 topic objects stored as JSON in `briefings.topics`. Sent to Telegram immediately.

---

## 5. Cron Job Design

**Scheduler:** APScheduler (AsyncIOScheduler) — no Redis, no Celery. Sufficient for 1–5 clients.

```python
# app/jobs/morning_briefing.py

scheduler = AsyncIOScheduler()

def schedule_all_clients():
    """Called at app startup. One job per active client."""
    for client in get_active_clients():
        tz = pytz.timezone(client.timezone)
        scheduler.add_job(
            run_morning_briefing,
            CronTrigger(hour=8, minute=0, timezone=tz),
            args=[client.id],
            id=f"briefing_{client.id}",
            replace_existing=True
        )

async def run_morning_briefing(client_id: str):
    client = get_client(client_id)
    voice_profile = load_voice_profile(client_id)
    raw_signals = await grok.scan_trends(client, voice_profile)
    topics = await claude.format_briefing(client, voice_profile, raw_signals)
    briefing = store_briefing(client_id, topics)
    await telegram_bot.send_briefing(client, briefing)
```

**App startup:**
```python
@app.on_event("startup")
async def startup():
    init_db()
    schedule_all_clients()
    scheduler.start()
```

**When Stripe activates a new client:**
```python
def add_client_to_scheduler(client):
    tz = pytz.timezone(client.timezone)
    scheduler.add_job(
        run_morning_briefing,
        CronTrigger(hour=8, minute=0, timezone=tz),
        args=[client.id],
        id=f"briefing_{client.id}",
        replace_existing=True
    )

def remove_client_from_scheduler(client_id: str):
    scheduler.remove_job(f"briefing_{client_id}")
```

---

## 6. Telegram Bot State Machine

### States

| State | Description |
|---|---|
| `idle` | Default. Waiting for /start or briefing delivery. |
| `onboarding_name` | Collecting full name |
| `onboarding_title` | Collecting job title |
| `onboarding_company` | Collecting company |
| `onboarding_industry` | Collecting industry |
| `onboarding_audience` | Collecting LinkedIn audience description |
| `onboarding_tone` | Collecting tone adjectives |
| `onboarding_sample_post` | Collecting a sample post |
| `awaiting_topic_selection` | Morning briefing sent, waiting for topic pick (1/2/3/Skip) |
| `awaiting_refinement` | 2 variations shown, waiting for button action |
| `refining` | Client asked for changes, waiting for refinement instructions |

### Full Conversation Flow

```
/start
  → check subscription status
    → NOT subscribed: "To activate your LinkedIn Post Agent, subscribe at {checkout_url}. 💳"
    → SUBSCRIBED + ONBOARDED: "Welcome back {name}. Your briefing arrives at 8am."
    → SUBSCRIBED + NOT ONBOARDED: begin ONBOARDING

ONBOARDING
  "Let's set up your voice profile so I write exactly like you."
  "What's your full name?"                                   [ONBOARDING_NAME]
  "What's your job title?"                                   [ONBOARDING_TITLE]
  "What company do you work for?"                            [ONBOARDING_COMPANY]
  "What industry are you in? (e.g. pharmaceutical, tech)"   [ONBOARDING_INDUSTRY]
  "Who's your target audience on LinkedIn?"                  [ONBOARDING_AUDIENCE]
  "Describe your tone in 3 words (e.g. authoritative, data-driven, empathetic)"
                                                             [ONBOARDING_TONE]
  "Paste one LinkedIn post you've written or loved — I'll use it to match your style."
                                                             [ONBOARDING_SAMPLE_POST]
  → save voice_profile.json
  → set client.onboarded = 1
  → add to scheduler
  "Done. Your first morning briefing arrives tomorrow at 8am. 🎯"
                                                             [→ IDLE]

MORNING BRIEFING (sent by cron job)
  "Good morning {name}. Here are today's 3 post ideas:

  1️⃣ {topic1.headline}
  {topic1.angle}

  2️⃣ {topic2.headline}
  {topic2.angle}

  3️⃣ {topic3.headline}
  {topic3.angle}

  Which one do you want to post today?"
  [Inline keyboard: "1" | "2" | "3" | "Skip today"]
                                                             [→ AWAITING_TOPIC_SELECTION]

TOPIC SELECTED (1, 2, or 3)
  → generate 2 variations via Claude
  "Here are 2 versions:

  📝 Version A:
  {variation_a}

  ---

  📝 Version B:
  {variation_b}"
  [Inline keyboard: "Use A" | "Use B" | "Refine A" | "Refine B" | "Start over"]
                                                             [→ AWAITING_REFINEMENT]

REFINE A / REFINE B
  "What should I change?" [free text input]                 [→ REFINING]
  → re-generate with refinement note in prompt
  → show updated version
  [Inline keyboard: "Use this" | "Refine again" | "Start over"]

POST APPROVED ("Use A" / "Use B" / "Use this")
  → generate LinkedIn pre-fill URL
  → store final_post, set status = 'approved'
  "Your post is ready. Hit the button to publish:"
  [Button: "Post to LinkedIn →" → deep link URL]
  "See you tomorrow. 🎯"
                                                             [→ IDLE]

SKIP TODAY
  "No problem. See you tomorrow."                           [→ IDLE]
```

### LinkedIn Pre-fill URL Format

```python
import urllib.parse

def generate_prefill_url(post_text: str) -> str:
    encoded = urllib.parse.quote(post_text)
    return f"https://www.linkedin.com/sharing/share-offsite/?text={encoded}"
```

---

## 7. Stripe Webhook Design

### Checkout Flow

1. Client visits `/marketplace/linkedin-agent` on Stratus website
2. Clicks "Hire for $50/month" → `POST /stripe/create-checkout` with `{email, name}`
3. Backend creates Stripe Checkout Session (mode: `subscription`, price: `$50/month`)
4. Client redirected to Stripe-hosted payment page
5. Payment complete → Stripe fires `checkout.session.completed`
6. Webhook handler creates client, sets `bot_active=1`, adds to scheduler
7. Client receives Telegram bot link via email (sent by backend)

### Webhook Events Handled

| Event | Action |
|---|---|
| `checkout.session.completed` | Create client record, `bot_active=1`, add to scheduler, email bot link |
| `customer.subscription.deleted` | `bot_active=0`, remove from scheduler |
| `customer.subscription.updated` | Sync subscription status in DB |
| `invoice.payment_failed` | `bot_active=0`, send warning message via Telegram |

### Security
Every webhook request verified with:
```python
stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
```
Any unverified request → `400 Bad Request`. No exceptions.

### Routes

```
POST /stripe/create-checkout     # body: {email, name} → returns {checkout_url}
POST /stripe/webhook             # Stripe sends events here
GET  /stripe/success             # redirect after successful payment
GET  /stripe/cancel              # redirect if client cancels checkout
```

---

## 8. Admin Routes

All routes prefixed `/admin`. Protected by `X-Admin-Key` header (secret in `.env`).

```
# Overview
GET    /admin/dashboard                                  # all clients, active count, MRR

# Client management
GET    /admin/clients                                    # list all clients + subscription status
GET    /admin/clients/{client_id}                        # client detail
POST   /admin/clients/{client_id}/activate               # manually set bot_active=1
POST   /admin/clients/{client_id}/deactivate             # manually set bot_active=0
DELETE /admin/clients/{client_id}                        # remove client

# Voice profile
GET    /admin/clients/{client_id}/voice-profile          # get voice_profile.json
PUT    /admin/clients/{client_id}/voice-profile          # overwrite voice_profile.json

# Post history
GET    /admin/clients/{client_id}/posts                  # all posts for client
GET    /admin/clients/{client_id}/posts/{post_id}        # single post detail

# Research feed
GET    /admin/clients/{client_id}/briefings              # all briefings with topics + signals

# Bot controls
GET    /admin/bot/status                                 # scheduler status, active jobs
POST   /admin/bot/trigger-briefing/{client_id}           # manually fire morning briefing
```

---

## 9. Site Page Map

The 10-page Stratus website is Next.js static/SSG. It does **not** need a backend API for content — all pages are hardcoded or use placeholder data.

The only two backend touchpoints from the website:

```
POST /stripe/create-checkout    # "Hire for $50/month" CTA on marketplace + agent pages
GET  /health                    # site can display live agent status indicator
```

Auth forms (`/auth/signup`, `/auth/signin`) are UI-only in MVP — no backend until platform Sprint 1.

---

## Environment Variables

```env
# App
APP_ENV=development
SECRET_KEY=...

# Database
DATABASE_URL=sqlite:///./data/stratus.db

# Claude API
ANTHROPIC_API_KEY=...

# Grok API
GROK_API_KEY=...

# Telegram
TELEGRAM_BOT_TOKEN=...

# Stripe
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
STRIPE_PRICE_ID=...              # $50/month recurring price ID

# Admin
ADMIN_KEY=...                    # X-Admin-Key header value

# Email (for sending bot link after payment)
SENDGRID_API_KEY=...
FROM_EMAIL=hello@stratusagency.ai
```

---

## Architecture Decisions

| Decision | Chosen | Rationale |
|---|---|---|
| Database | SQLite | MVP serves 1–5 clients. No concurrency pressure. Zero ops overhead. Migrate to Supabase when scaling. |
| Auth | Admin key only | No user auth in MVP. Admin dashboard is local. Bot access gated by `bot_active` flag checked against Telegram chat ID. |
| Scheduler | APScheduler | Lightweight, async-native, no Redis. Sufficient for 5 clients. Replace with Celery Beat at scale. |
| Research | Grok API | Real-time web + X/Twitter. Claude alone cannot do this. Two-model pipeline is the differentiator. |
| Delivery | Telegram | Primary interface. Zero friction for client. Inline keyboards keep everything in one thread. |
| Voice storage | JSON files | Simple. Human-editable via admin dashboard. No ORM overhead for a profile that changes rarely. |

---

*Architecture locked. Backend starts from here. Nothing in this document is improvised.*
