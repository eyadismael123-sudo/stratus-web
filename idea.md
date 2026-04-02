# LinkedIn Agent — Product Idea

## What It Is
A LinkedIn Chief of Staff. Not a post generator — a personal content strategist that lives in your pocket, learns your voice, does your research, and makes you look like a thought leader with zero effort.

Delivered via Telegram. Priced at $150/month.

---

## Core Layers

### 1. Voice Capture (The Moat)
Deep onboarding that builds a Voice Profile per client:
- Name, company, role, industry, target audience
- 10-20 past LinkedIn posts (copy-paste or URL)
- Tone words: thought leader / storyteller / data-driven / controversial / humble
- Topics they want to OWN
- Topics they never touch

Output: `voice_profile.json` — travels with every API call. Makes output sound like *them* on their best day.

### 2. Memory & Learning Loop (The Compounding Value)
Per-client `preference_memory.json` that evolves over time:
- Tracks what post versions they pick, what they reject
- Learns hook style, length preference, hashtag preferences, format choices
- Self-trims to last ~30 signals (keeps tokens lean)
- Auto-updates after every approved post

Result: output gets better every month. Switching costs go up. Churn goes down.

Token efficiency: load `voice_profile.json` + `preference_memory.json` + `recent_context.json` instead of full history every call. API costs go down as quality goes up.

### 3. Research Engine (The Proactive Brain)
Every morning the agent:
- Scans trending topics in client's industry (Perplexity API / web search)
- Monitors 3-5 competitor LinkedIn profiles they specified
- Checks recent field news
- Surfaces 3 post ideas with one-line angles

Client wakes up to: "Good morning [name]. Here are 3 post ideas for today." — with buttons.

Also researches hashtags per post:
- Mix of broad reach (`#Leadership`) and niche (`#DubaiRealEstate`)
- 5-8 hashtags per post, appended clean at the bottom

### 4. Content Generation Pipeline
When client picks a topic:
1. Agent researches deeper (sources, stats, angles)
2. Generates 2 post variations — different hooks, same core idea
3. Client picks one via button
4. Refinement via buttons: "shorter" / "more personal" / "add a story"
5. Final approval → post + hashtags ready

### 5. Visual Layer (The Differentiator)
Two types:
- **Quote cards** — clean, branded, best line from the post
- **Infographic carousels** — 5-7 slide breakdowns of a concept

MVP: template-based (Pillow / Canva API). Consistent quality, fast generation.

### 6. Delivery Interface (Telegram)
Why Telegram over WhatsApp:
- Free API, no approval process
- Inline keyboard buttons = the entire UX
- Handles images, documents, rich text
- python-telegram-bot library is excellent

Everything is buttons. Client never types unless giving feedback.

### 7. LinkedIn Pre-Fill Link (Zero Friction Posting)
Final message from bot:
```
✅ Your post is ready.
[📋 Copy text]  [🔗 Open in LinkedIn]  [🖼 Download infographic]
```

LinkedIn URL format:
```
https://www.linkedin.com/feed/?shareActive=true&text=URL_ENCODED_POST_HERE
```
Works on desktop. On mobile, opens LinkedIn app directly with post pre-filled.
Client adds photo or infographic → posts. Done. 5 minutes. Zero mental effort.

---

## Full User Journey
```
8:00am — 3 topic ideas arrive [Button 1] [Button 2] [Button 3]
Client picks one
Agent generates 2 versions → client picks + optional refinement
"Want an infographic?" [Yes] [No]
Infographic generated if yes
LinkedIn pre-fill link sent
Client opens LinkedIn → post ready → adds image → posts
```

---

## Pricing
- $150/month per person
- Framing: "This is your ghostwriter. Less than a coffee meeting per week."
- Comparison: LinkedIn ghostwriters charge $500-2000/month

---

## Admin Dashboard (Localhost — Eyad Only)
Internal ops tool. Not client-facing.
- Client list — status, last activity
- Voice profile editor — tweak without touching code
- Post history — what was generated, approved, posted
- Research feed — topics surfaced, topics picked
- Hashtag sets — manage per client
- Bot status — running, last ping, errors

---

## Landing Page
Simple one-pager. Explains the agent. "Book a call" or WhatsApp CTA.
Looks official when pitching clients.

---

## Future Directions (v2+)
1. **Team Play** — agency signs one contract, deploys 12 voice profiles. $150 x 12 = $1,800/month from one client
2. **Content Calendar Mode** — agent plans full month of posts in one session, executes daily
3. **Repurposing Engine** — same post auto-reformatted for Twitter/X, Instagram, WhatsApp status
4. **Lead Magnet Angle** — posts engineered to generate DMs from ideal prospects, tracks which types drive most profile visits
5. **LinkedIn OAuth (later)** — auto-posting directly, performance stats (avoid for now — API restrictions)

---

## What Makes This Different
- Voice capture = sounds like them, not AI
- Proactive research = agent comes to you, not the other way
- Learning loop = gets better every month, switching costs compound
- LinkedIn pre-fill = zero friction to posting
- Infographics = visual layer most tools skip
- Telegram buttons = dead simple, no app to download

---

## Build Order
1. Voice capture onboarding
2. Post generator (prompt engineering is the hard part)
3. Telegram bot + button interface
4. Memory/learning loop
5. Research engine + morning briefings
6. Infographic generator
7. Admin dashboard
8. Landing page
