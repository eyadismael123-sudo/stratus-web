# ARCHITECTURE DOCUMENT — STRATUS

**Version:** 1.0  
**Date:** 2026-03-17  
**Status:** APPROVED (Phase 0.1)  
**Owner:** Architect  

## EXECUTIVE SUMMARY

Stratus is an AI automation agency platform with:
- **Backend:** FastAPI (Python 3.11+) on Railway
- **Frontend:** Next.js 15 on Vercel
- **Mobile:** Expo (React Native) sharing 100% of FastAPI backend
- **Database:** Supabase (Postgres) — production-grade from day 1
- **Auth:** Supabase Auth (no custom JWT)
- **Payments:** Stripe (per-agent monthly subscriptions)
- **Real-time:** Supabase Realtime for live status updates

This architecture enables:
- Single backend serving web + mobile simultaneously
- Marketplace of reusable agent templates
- Per-agent subscription model (users hire instances)
- Real-time agent status on dashboard + mobile
- Scalable to 100K+ users without architectural change

---

## 1. DATABASE SCHEMA

### Core Design Principles
1. **Two-table agent model:** `agent_templates` (what can be hired) + `user_agents` (what a user hired)
2. **Immutable logs:** `agent_logs` are append-only, never updated
3. **Supabase Auth integration:** `auth.users` is the source of truth, `profiles` extends it
4. **Stripe sync:** subscription records mirror Stripe, webhook-driven updates
5. **Normalized + indexed:** queries must be fast; marketplace loads instantly

### Schema Definitions

#### `auth.users` (Managed by Supabase Auth)
Supabase Auth creates and manages this table. We never write directly to it.
```sql
id                 uuid PRIMARY KEY
email              text UNIQUE NOT NULL
encrypted_password text
email_confirmed_at timestamp
created_at         timestamp
updated_at         timestamp
```

#### `profiles` (User Profile Extension)
Extends Supabase Auth with application-specific fields.
```sql
CREATE TABLE profiles (
  id                   uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email                text UNIQUE NOT NULL,
  full_name            text,
  company_name         text,
  avatar_url           text,
  is_admin             boolean DEFAULT false,
  timezone             text DEFAULT 'UTC',
  notification_email   text,
  created_at           timestamp DEFAULT now(),
  updated_at           timestamp DEFAULT now(),
  deleted_at           timestamp NULL
);

-- Indexes
CREATE INDEX idx_profiles_email ON profiles(email);
CREATE INDEX idx_profiles_is_admin ON profiles(is_admin);
```

**Invariants:**
- Every user has a profile (created on signup via Supabase trigger)
- `id` matches the Supabase Auth user ID
- `deleted_at` is NULL for active users, populated on soft delete

---

#### `agent_templates` (Marketplace Listings)
The blueprint for agents that can be hired. Immutable once created.
```sql
CREATE TABLE agent_templates (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name               text NOT NULL,
  slug               text UNIQUE NOT NULL,
  description        text NOT NULL,
  long_description   text,
  icon_url           text,
  category           text NOT NULL,
  role               text NOT NULL,
  features           text[] DEFAULT '{}',
  industries         text[] DEFAULT '{}',
  price_usd_cents    integer NOT NULL,
  setup_fee_cents    integer DEFAULT 0,
  billing_interval   text DEFAULT 'month',
  max_users          integer,
  api_endpoint       text,
  webhook_url        text,
  config_schema      jsonb,
  is_published       boolean DEFAULT false,
  is_featured        boolean DEFAULT false,
  created_by_id      uuid NOT NULL REFERENCES profiles(id),
  created_at         timestamp DEFAULT now(),
  updated_at         timestamp DEFAULT now(),
  deleted_at         timestamp NULL
);

-- Indexes
CREATE INDEX idx_agent_templates_slug ON agent_templates(slug);
CREATE INDEX idx_agent_templates_published ON agent_templates(is_published);
CREATE INDEX idx_agent_templates_featured ON agent_templates(is_featured);
CREATE INDEX idx_agent_templates_category ON agent_templates(category);
CREATE INDEX idx_agent_templates_created_at ON agent_templates(created_at DESC);
```

**Invariants:**
- `slug` is URL-safe, lowercase, hyphen-separated
- `price_usd_cents` must be > 0 if `is_published = true`
- `created_by_id` is the admin/founder who created this template
- `config_schema` is JSON Schema (Pydantic validation on hire endpoint)
- Only published agents appear in marketplace listing

---

#### `user_agents` (Hired Agent Instances)
Represents a user hiring an agent. Subscription state is in Stripe; this is the join record.
```sql
CREATE TABLE user_agents (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  agent_template_id       uuid NOT NULL REFERENCES agent_templates(id),
  name                    text NOT NULL,
  status                  text DEFAULT 'inactive',
  config                  jsonb DEFAULT '{}',
  stripe_subscription_id  text UNIQUE,
  stripe_subscription_status text DEFAULT 'inactive',
  last_run_at             timestamp,
  next_run_at             timestamp,
  run_count               integer DEFAULT 0,
  connected_platform      text,
  connected_platform_id   text,
  is_active               boolean DEFAULT false,
  created_at              timestamp DEFAULT now(),
  updated_at              timestamp DEFAULT now(),
  deleted_at              timestamp NULL
);

-- Indexes
CREATE INDEX idx_user_agents_user_id ON user_agents(user_id);
CREATE INDEX idx_user_agents_template_id ON user_agents(agent_template_id);
CREATE INDEX idx_user_agents_status ON user_agents(status);
CREATE INDEX idx_user_agents_stripe_sub_id ON user_agents(stripe_subscription_id);
CREATE INDEX idx_user_agents_is_active ON user_agents(is_active);
CREATE INDEX idx_user_agents_user_active ON user_agents(user_id, is_active);
```

**Invariants:**
- Every `user_agent` must have an active Stripe subscription (except during trial/setup)
- `stripe_subscription_id` is set when checkout succeeds (webhook)
- `stripe_subscription_status` mirrors Stripe: `active`, `past_due`, `canceled`, `unpaid`
- `status` tracks local state: `inactive`, `active`, `error`, `paused`
- `is_active = true` only if `stripe_subscription_status = 'active'`
- `config` is validated against `agent_template.config_schema` on hire
- Users can only see/manage their own agents (permission boundary)

---

#### `agent_logs` (Immutable Run History)
Append-only log of every agent execution. Never updated after creation.
```sql
CREATE TABLE agent_logs (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_agent_id       uuid NOT NULL REFERENCES user_agents(id) ON DELETE CASCADE,
  agent_template_id   uuid NOT NULL REFERENCES agent_templates(id),
  status              text NOT NULL,
  trigger_type        text,
  input_data          jsonb,
  output_data         jsonb,
  error_message       text,
  duration_ms         integer,
  started_at          timestamp DEFAULT now(),
  completed_at        timestamp,
  created_at          timestamp DEFAULT now()
);

-- Indexes
CREATE INDEX idx_agent_logs_user_agent_id ON agent_logs(user_agent_id);
CREATE INDEX idx_agent_logs_status ON agent_logs(status);
CREATE INDEX idx_agent_logs_created_at ON agent_logs(created_at DESC);
CREATE INDEX idx_agent_logs_user_agent_created ON agent_logs(user_agent_id, created_at DESC);
```

**Invariants:**
- Write-once only: `INSERT` only, never `UPDATE` or `DELETE`
- `status`: `success`, `error`, `running`, `timeout`
- `trigger_type`: `manual`, `scheduled`, `webhook`, `event`
- Logs are queried by `user_agent_id` (paginated, latest first)
- Used for: activity feed, troubleshooting, analytics

---

#### `subscriptions` (Stripe Sync Record)
Mirror of Stripe subscription state. Webhook-driven updates.
```sql
CREATE TABLE subscriptions (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  user_agent_id           uuid UNIQUE REFERENCES user_agents(id) ON DELETE CASCADE,
  stripe_subscription_id  text UNIQUE NOT NULL,
  stripe_customer_id      text NOT NULL,
  stripe_price_id         text NOT NULL,
  status                  text NOT NULL,
  current_period_start    timestamp,
  current_period_end      timestamp,
  cancel_at_period_end    boolean DEFAULT false,
  canceled_at             timestamp,
  amount_usd_cents        integer NOT NULL,
  billing_interval        text DEFAULT 'month',
  metadata                jsonb DEFAULT '{}',
  last_webhook_event_id   text,
  last_webhook_at         timestamp,
  created_at              timestamp DEFAULT now(),
  updated_at              timestamp DEFAULT now()
);

-- Indexes
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe_sub_id ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_user_agent_id ON subscriptions(user_agent_id);
```

**Invariants:**
- One subscription per `user_agent` (1:1 relationship via unique constraint)
- Status mirrors Stripe: `active`, `past_due`, `canceled`, `unpaid`, `trialing`
- Webhook events update `status`, `current_period_end`, `canceled_at`
- `last_webhook_event_id` prevents duplicate processing (idempotency key)
- Only active subscriptions grant access to agent (check in permission middleware)

---

#### `agent_schedules` (Optional, for Scheduled Runs)
If an agent has a recurring schedule (e.g., daily briefing at 8am).
```sql
CREATE TABLE agent_schedules (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_agent_id       uuid UNIQUE NOT NULL REFERENCES user_agents(id) ON DELETE CASCADE,
  cron_expression     text NOT NULL,
  timezone            text DEFAULT 'UTC',
  last_run_at         timestamp,
  next_run_at         timestamp,
  is_enabled          boolean DEFAULT true,
  created_at          timestamp DEFAULT now(),
  updated_at          timestamp DEFAULT now()
);

-- Indexes
CREATE INDEX idx_agent_schedules_enabled ON agent_schedules(is_enabled);
CREATE INDEX idx_agent_schedules_next_run ON agent_schedules(next_run_at);
```

**Usage:** Backend polls this for upcoming scheduled tasks, triggers them via job queue (APScheduler).

---

### Database Initialization

**Supabase setup steps:**
1. Create Supabase project (region: closest to Dubai or EU)
2. Enable Auth (email/password, no magic links yet)
3. Create tables above with exact schema
4. Create Postgres trigger for auto-profile creation on signup:
   ```sql
   CREATE TRIGGER on_auth_user_created
   AFTER INSERT ON auth.users
   FOR EACH ROW
   EXECUTE FUNCTION public.handle_new_user();
   ```
5. Enable Row Level Security (RLS) on all tables (see auth flow section)
6. Create service role key for backend (never expose publicly)
7. Enable Supabase Realtime on `user_agents` table

---

## 2. API CONTRACT

### Base URL
- **Development:** `http://localhost:8000`
- **Production:** `https://api.stratus.ai` (or domain TBD)

### Authentication Header
All endpoints except `/auth/*` and `/health` require:
```
Authorization: Bearer <supabase_access_token>
```

Supabase access token is a JWT issued by Supabase Auth. Backend validates it via Supabase's `verify_id_token()` function.

### Standard Response Envelope
**Success (2xx):**
```json
{
  "success": true,
  "data": {...},
  "error": null,
  "error_message": null,
  "meta": {}
}
```

**Error (4xx/5xx):**
```json
{
  "success": false,
  "data": null,
  "error": "ERROR_CODE",
  "error_message": "Human-readable error description",
  "meta": {}
}
```

---

### Domain 1: Health & System

#### `GET /health`
Health check endpoint. No auth required.
```
Response: 200 OK
{
  "success": true,
  "data": { "status": "healthy", "timestamp": "2026-03-17T10:00:00Z" },
  "error": null,
  "error_message": null
}
```

---

### Domain 2: Auth (Profile Only)

**Note:** Supabase Auth handles login/register/password reset. These endpoints manage profile data only.

#### `GET /auth/profile`
Fetch current user's profile. **Auth required.**
```
Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "company_name": "Acme Inc",
    "avatar_url": "https://...",
    "timezone": "UTC",
    "is_admin": false,
    "created_at": "2026-03-17T10:00:00Z"
  },
  "error": null,
  "error_message": null
}
```

---

#### `PATCH /auth/profile`
Update profile. **Auth required.** User can only update their own profile.
```
Request:
{
  "full_name": "Jane Doe",
  "company_name": "Acme International",
  "timezone": "Asia/Dubai",
  "notification_email": "notifications@example.com"
}

Response: 200 OK
{
  "success": true,
  "data": { ...updated profile... },
  "error": null,
  "error_message": null
}
```

---

### Domain 3: Marketplace (Agent Templates)

#### `GET /marketplace/agents`
List all published agent templates. **No auth required** (browsable).
```
Query params:
  - category?: string (e.g., "linkedin", "crm", "analytics")
  - featured?: boolean (true = featured only)
  - page?: integer (default 1)
  - limit?: integer (default 10, max 50)
  - search?: string (search in name + description)

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "LinkedIn Post Agent",
      "slug": "linkedin-post-agent",
      "description": "Generates and schedules LinkedIn posts",
      "icon_url": "https://...",
      "category": "linkedin",
      "role": "Content Creator",
      "features": ["auto-generate", "schedule", "analytics"],
      "industries": ["tech", "saas"],
      "price_usd_cents": 2999,
      "setup_fee_cents": 0,
      "billing_interval": "month",
      "is_featured": true,
      "created_at": "2026-03-17T10:00:00Z"
    },
    ...
  ],
  "error": null,
  "error_message": null,
  "meta": {
    "total": 42,
    "page": 1,
    "limit": 10,
    "pages": 5
  }
}
```

---

#### `GET /marketplace/agents/{slug}`
Get a single agent template by slug. **No auth required.**
```
Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "LinkedIn Post Agent",
    "slug": "linkedin-post-agent",
    "description": "...",
    "long_description": "...",
    "icon_url": "...",
    "category": "linkedin",
    "role": "Content Creator",
    "features": ["auto-generate", "schedule", "analytics"],
    "industries": ["tech", "saas"],
    "price_usd_cents": 2999,
    "setup_fee_cents": 0,
    "config_schema": { ...JSON Schema... },
    "created_at": "2026-03-17T10:00:00Z"
  },
  "error": null,
  "error_message": null
}
```

---

### Domain 4: Agents (User's Hired Instances)

#### `GET /agents`
List all agents hired by the current user. **Auth required.**
```
Query params:
  - status?: string (active, inactive, error, paused)
  - page?: integer (default 1)
  - limit?: integer (default 20)

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "My LinkedIn Bot",
      "agent_template_id": "uuid",
      "agent_template": {
        "id": "uuid",
        "name": "LinkedIn Post Agent",
        "slug": "linkedin-post-agent",
        "icon_url": "...",
        "category": "linkedin"
      },
      "status": "active",
      "is_active": true,
      "config": { "platform": "linkedin", "account_id": "..." },
      "connected_platform": "linkedin",
      "connected_platform_id": "...",
      "stripe_subscription_status": "active",
      "last_run_at": "2026-03-17T08:30:00Z",
      "next_run_at": "2026-03-18T08:00:00Z",
      "run_count": 42,
      "created_at": "2026-03-17T10:00:00Z"
    },
    ...
  ],
  "error": null,
  "error_message": null,
  "meta": {
    "total": 5,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

---

#### `POST /agents`
Hire a new agent. Creates a user_agent record and initiates Stripe checkout. **Auth required.**
```
Request:
{
  "agent_template_id": "uuid",
  "name": "My LinkedIn Bot",
  "config": {
    "platform": "linkedin",
    "account_id": "12345"
  }
}

Response: 201 CREATED
{
  "success": true,
  "data": {
    "id": "uuid",
    "user_agent_id": "uuid",
    "name": "My LinkedIn Bot",
    "agent_template_id": "uuid",
    "status": "inactive",
    "is_active": false,
    "stripe_checkout_session_id": "cs_...",
    "stripe_checkout_url": "https://checkout.stripe.com/...",
    "created_at": "2026-03-17T10:00:00Z"
  },
  "error": null,
  "error_message": null
}
```

**Validation:**
- `agent_template_id` must exist and be published
- `config` must pass JSON Schema validation against template's `config_schema`
- User must not already have an active instance of this template (or allow duplicates — decide before Phase 5)

**What happens:**
1. Backend creates `user_agent` with `status = 'inactive'`
2. Backend creates `subscriptions` record with Stripe (via Stripe API)
3. Backend creates Stripe checkout session
4. Returns checkout URL to frontend
5. Frontend redirects user to Stripe checkout
6. On payment success, webhook updates subscription status → activates agent

---

#### `GET /agents/{agent_id}`
Get a single agent instance detail. **Auth required.** User can only access their own agents.
```
Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "My LinkedIn Bot",
    "agent_template_id": "uuid",
    "agent_template": { ...full template data... },
    "status": "active",
    "is_active": true,
    "config": { ...user config... },
    "stripe_subscription_id": "sub_...",
    "stripe_subscription_status": "active",
    "last_run_at": "2026-03-17T08:30:00Z",
    "next_run_at": "2026-03-18T08:00:00Z",
    "run_count": 42,
    "created_at": "2026-03-17T10:00:00Z",
    "updated_at": "2026-03-17T14:00:00Z"
  },
  "error": null,
  "error_message": null
}
```

---

#### `PATCH /agents/{agent_id}`
Update an agent instance (name, config, status). **Auth required.** User can only update their own agents.
```
Request:
{
  "name": "My New Bot Name",
  "config": {
    "platform": "linkedin",
    "account_id": "67890",
    "post_frequency": "daily"
  },
  "status": "paused"
}

Response: 200 OK
{
  "success": true,
  "data": { ...updated agent... },
  "error": null,
  "error_message": null
}
```

**Validation:**
- `config` must pass JSON Schema validation
- `status` must be one of: `inactive`, `active`, `paused`, `error`
- Cannot set `status = 'active'` if subscription is not active

---

#### `DELETE /agents/{agent_id}`
Delete (soft delete) an agent instance. **Auth required.** Cascade soft-deletes related logs (or archive them).
```
Response: 200 OK
{
  "success": true,
  "data": { "id": "uuid", "deleted_at": "2026-03-17T14:30:00Z" },
  "error": null,
  "error_message": null
}
```

---

#### `GET /agents/{agent_id}/logs`
Fetch paginated activity logs for an agent instance. **Auth required.** User can only access their own agents' logs.
```
Query params:
  - page?: integer (default 1)
  - limit?: integer (default 20, max 100)
  - status?: string (success, error, running, timeout)
  - since?: timestamp (ISO 8601, fetch logs after this time)

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "user_agent_id": "uuid",
      "status": "success",
      "trigger_type": "scheduled",
      "input_data": { "keyword": "AI agents" },
      "output_data": { "posts_generated": 3 },
      "error_message": null,
      "duration_ms": 2150,
      "started_at": "2026-03-17T08:30:00Z",
      "completed_at": "2026-03-17T08:30:02.150Z",
      "created_at": "2026-03-17T08:30:02.150Z"
    },
    ...
  ],
  "error": null,
  "error_message": null,
  "meta": {
    "total": 87,
    "page": 1,
    "limit": 20,
    "pages": 5
  }
}
```

---

#### `POST /agents/{agent_id}/run`
Manually trigger an agent run (for manual execution, testing). **Auth required.** User can only trigger their own agents.
```
Request:
{
  "input_data": {
    "keyword": "AI agents",
    "tone": "professional"
  }
}

Response: 202 ACCEPTED
{
  "success": true,
  "data": {
    "id": "uuid",
    "user_agent_id": "uuid",
    "status": "running",
    "trigger_type": "manual",
    "input_data": { ...provided... },
    "started_at": "2026-03-17T14:30:00Z"
  },
  "error": null,
  "error_message": null
}
```

**What happens:**
1. Validates agent is active and subscription is active
2. Creates `agent_log` record with `status = 'running'`
3. Enqueues job in background queue (Celery or APScheduler)
4. Returns 202 ACCEPTED immediately
5. Job runs asynchronously, updates `agent_log` when complete

---

#### `GET /agents/{agent_id}/schedule`
Get the schedule for an agent (if it has one). **Auth required.**
```
Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "user_agent_id": "uuid",
    "cron_expression": "0 8 * * *",
    "timezone": "Asia/Dubai",
    "is_enabled": true,
    "last_run_at": "2026-03-17T08:00:00Z",
    "next_run_at": "2026-03-18T08:00:00Z"
  },
  "error": null,
  "error_message": null
}
```

Returns 404 if no schedule exists.

---

#### `POST /agents/{agent_id}/schedule`
Create or update a schedule for an agent. **Auth required.**
```
Request:
{
  "cron_expression": "0 8 * * *",
  "timezone": "Asia/Dubai",
  "is_enabled": true
}

Response: 201 CREATED or 200 OK
{
  "success": true,
  "data": { ...schedule... },
  "error": null,
  "error_message": null
}
```

**Cron validation:** Use `croniter` library to validate expression.

---

#### `DELETE /agents/{agent_id}/schedule`
Remove the schedule from an agent. **Auth required.**
```
Response: 200 OK
{
  "success": true,
  "data": { "id": "uuid", "deleted": true },
  "error": null,
  "error_message": null
}
```

---

### Domain 5: Subscriptions & Billing

#### `GET /subscriptions`
List all active subscriptions for the current user. **Auth required.**
```
Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "user_agent_id": "uuid",
      "user_agent": {
        "id": "uuid",
        "name": "My LinkedIn Bot",
        "agent_template": { "name": "LinkedIn Post Agent", ... }
      },
      "stripe_subscription_id": "sub_...",
      "status": "active",
      "amount_usd_cents": 2999,
      "billing_interval": "month",
      "current_period_start": "2026-03-17T00:00:00Z",
      "current_period_end": "2026-04-17T00:00:00Z",
      "cancel_at_period_end": false,
      "created_at": "2026-03-17T10:00:00Z"
    },
    ...
  ],
  "error": null,
  "error_message": null,
  "meta": {
    "total": 3,
    "total_monthly_usd": 89.97
  }
}
```

---

#### `POST /subscriptions/{subscription_id}/cancel`
Cancel a subscription (takes effect at period end, can be uncanceled). **Auth required.**
```
Request:
{
  "reason": "Not using this agent anymore",
  "feedback": "..."
}

Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "active",
    "cancel_at_period_end": true,
    "current_period_end": "2026-04-17T00:00:00Z",
    "canceled_at": null,
    "message": "Subscription will cancel on 2026-04-17"
  },
  "error": null,
  "error_message": null
}
```

**What happens:**
1. Calls Stripe API to set `cancel_at_period_end = true`
2. Updates local `subscriptions` record
3. Agent remains active until period end
4. On period end, webhook fires, sets `status = 'canceled'`, disables agent

---

#### `POST /subscriptions/{subscription_id}/reactivate`
Reactivate a canceled subscription (if within grace period, TBD). **Auth required.**
```
Response: 200 OK
{
  "success": true,
  "data": { "status": "active", "cancel_at_period_end": false },
  "error": null,
  "error_message": null
}
```

---

### Domain 6: Stripe Webhooks

#### `POST /webhooks/stripe`
Stripe sends event notifications here. **No auth required** (validated by Stripe signature).
```
Request Headers:
  Stripe-Signature: <signature>

Request Body:
{
  "id": "evt_...",
  "type": "customer.subscription.updated",
  "data": { "object": { ...subscription data... } }
}

Response: 200 OK
{
  "success": true,
  "data": { "received": true },
  "error": null,
  "error_message": null
}
```

**Events to handle:**

1. **`customer.subscription.created`**
   - Create/update `subscriptions` record
   - Set `user_agent.stripe_subscription_id` and `stripe_subscription_status`
   - Set `user_agent.is_active = true` if status = 'active'

2. **`customer.subscription.updated`**
   - Update `subscriptions.status`, `current_period_end`, etc.
   - Update `user_agent.stripe_subscription_status`
   - If status changed to 'canceled' → set `user_agent.is_active = false`
   - If status changed to 'past_due' → alert user (optional)

3. **`customer.subscription.deleted`**
   - Set `subscriptions.status = 'canceled'`
   - Set `user_agent.is_active = false`
   - Delete agent is optional (soft delete or archive)

4. **`invoice.payment_succeeded`**
   - Log payment event (optional, for accounting)
   - Update `subscriptions.last_webhook_at`

5. **`invoice.payment_failed`**
   - Notify user (email or in-app alert)
   - User has grace period to retry payment

**Webhook validation:**
```python
import stripe

def verify_stripe_signature(body: bytes, sig_header: str) -> dict:
    try:
        return stripe.Webhook.construct_event(
            body,
            sig_header,
            STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
```

**Idempotency:** Use `event.id` as idempotency key. Store in `subscriptions.last_webhook_event_id`. Skip if already processed.

---

### Domain 7: Admin Endpoints

All admin endpoints require `profiles.is_admin = true`. Check in middleware.

#### `GET /admin/agents`
List all agent templates (published and unpublished). **Admin only.**
```
Query params:
  - published?: boolean
  - page?: integer
  - limit?: integer

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "LinkedIn Post Agent",
      "slug": "...",
      "is_published": true,
      "is_featured": false,
      "price_usd_cents": 2999,
      "run_count": 542,
      "user_count": 23,
      "created_at": "2026-03-17T10:00:00Z"
    },
    ...
  ],
  "error": null,
  "error_message": null,
  "meta": { "total": 12, ... }
}
```

---

#### `POST /admin/agents`
Create a new agent template. **Admin only.**
```
Request:
{
  "name": "LinkedIn Post Agent",
  "slug": "linkedin-post-agent",
  "description": "Generates and schedules LinkedIn posts",
  "long_description": "...",
  "icon_url": "https://...",
  "category": "linkedin",
  "role": "Content Creator",
  "features": ["auto-generate", "schedule", "analytics"],
  "industries": ["tech", "saas"],
  "price_usd_cents": 2999,
  "setup_fee_cents": 0,
  "config_schema": { ...JSON Schema... },
  "is_published": false,
  "is_featured": false
}

Response: 201 CREATED
{
  "success": true,
  "data": { ...agent template... },
  "error": null,
  "error_message": null
}
```

---

#### `PATCH /admin/agents/{template_id}`
Update an agent template. **Admin only.**
```
Request:
{
  "name": "...",
  "price_usd_cents": 3999,
  "is_published": true,
  "is_featured": true
}

Response: 200 OK
{
  "success": true,
  "data": { ...updated template... },
  "error": null,
  "error_message": null
}
```

---

#### `GET /admin/clients`
List all users with their subscription metrics. **Admin only.**
```
Query params:
  - page?: integer
  - limit?: integer

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "company_name": "Acme Inc",
      "agent_count": 5,
      "active_subscription_count": 4,
      "total_monthly_usd": 89.97,
      "created_at": "2026-03-17T10:00:00Z",
      "last_agent_run": "2026-03-17T14:00:00Z"
    },
    ...
  ],
  "error": null,
  "error_message": null,
  "meta": { "total": 342, ... }
}
```

---

#### `GET /admin/analytics`
System-wide analytics. **Admin only.**
```
Query params:
  - period?: string (week, month, year)

Response: 200 OK
{
  "success": true,
  "data": {
    "total_users": 342,
    "total_agents_hired": 1,250,
    "total_subscriptions_active": 1,050,
    "total_monthly_recurring_revenue_usd": 31490,
    "total_agent_runs_this_month": 45230,
    "avg_subscription_duration_days": 42,
    "churn_rate": 0.08
  },
  "error": null,
  "error_message": null
}
```

---

## 3. AUTH FLOW

### Overview
1. **Signup/Login:** Handled by Supabase Auth (frontend calls Supabase directly)
2. **Profile:** User extends auth record with `profiles` table
3. **Session:** Supabase issues JWT (access + refresh tokens)
4. **API calls:** Frontend sends JWT in Authorization header
5. **Backend validation:** FastAPI verifies JWT and checks RLS

### Step-by-Step Flow

#### Signup (Web/Mobile)
```
User enters email + password
     ↓
Frontend calls supabase.auth.signUp({ email, password })
     ↓
Supabase creates auth.users record
     ↓
Supabase trigger fires: handle_new_user()
     ↓
Trigger inserts into profiles (id, email)
     ↓
Supabase returns access_token + refresh_token to frontend
     ↓
Frontend stores tokens in:
  - Web: localStorage or secure sessionStorage
  - Mobile: Expo SecureStore
     ↓
Frontend redirects to /dashboard
     ↓
All subsequent requests include: Authorization: Bearer <access_token>
```

**Trigger SQL:**
```sql
CREATE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email)
  VALUES (new.id, new.email);
  RETURN new;
END;
$$;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user();
```

---

#### Login (Web/Mobile)
```
User enters email + password
     ↓
Frontend calls supabase.auth.signInWithPassword({ email, password })
     ↓
Supabase validates password
     ↓
If valid: returns access_token + refresh_token
If invalid: returns error
     ↓
Frontend stores tokens (same as signup)
```

---

#### API Request Validation

**Frontend sends:**
```
GET /agents
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Backend middleware (FastAPI):**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    
    try:
        # Verify token with Supabase
        payload = supabase.auth.verify_id_token(token)
        user_id = payload['sub']  # Supabase user ID (UUID)
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

async def get_current_user(user_id: str = Depends(verify_token)):
    # Fetch user profile from database
    profile = await db.fetch_one(
        "SELECT * FROM profiles WHERE id = %s",
        (user_id,)
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return profile
```

**Usage in endpoints:**
```python
@router.get("/agents")
async def list_agents(current_user = Depends(get_current_user)):
    # current_user is the profile object
    agents = await db.fetch(
        "SELECT * FROM user_agents WHERE user_id = %s",
        (current_user['id'],)
    )
    return {"success": True, "data": agents}
```

---

#### Row Level Security (RLS)

Supabase RLS ensures users can only access their own data at the database level. Backend enforces it too.

**RLS policies on `user_agents`:**
```sql
-- Users can see only their own agents
CREATE POLICY "Users can view own agents"
ON public.user_agents
FOR SELECT
USING (auth.uid() = user_id);

-- Users can insert only for themselves
CREATE POLICY "Users can insert own agents"
ON public.user_agents
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users can update only their own agents
CREATE POLICY "Users can update own agents"
ON public.user_agents
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Users can delete only their own agents
CREATE POLICY "Users can delete own agents"
ON public.user_agents
FOR DELETE
USING (auth.uid() = user_id);
```

**Enable RLS:**
```sql
ALTER TABLE public.user_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_logs ENABLE ROW LEVEL SECURITY;
```

---

#### Refresh Token Flow

Access tokens expire in 1 hour. Refresh tokens are long-lived.

**Frontend (when access token expires):**
```javascript
// Automatically handled by Supabase client library
const { data, error } = await supabase.auth.refreshSession()

if (error) {
  // Redirect to login
  navigate('/signin')
}
// New access token is in data.session.access_token
```

**Backend:** No action needed; Supabase handles refresh server-side.

---

#### Logout

**Frontend:**
```javascript
await supabase.auth.signOut()
// Clear stored tokens
localStorage.removeItem('supabase.auth.token')
// Redirect to login
navigate('/signin')
```

**Backend:** No logout endpoint needed; JWT expiration handles it.

---

### Permission Boundaries

**Data access rules:**
1. Users can only access their own agents, logs, subscriptions
2. Users can view all published agent templates
3. Only admins can:
   - Create/edit/publish agent templates
   - View all clients and analytics
   - Manage billing settings

**Enforcement:**
- RLS policies at database level (Supabase)
- Backend middleware checks `profiles.is_admin`
- Frontend hides admin UI if not admin (cosmetic)

---

## 4. STRIPE ARCHITECTURE

### Subscription Model
- **Per-agent monthly subscription:** User hires agent → pays $29.99/month (price TBD)
- **Setup fee (optional):** One-time fee when first hiring (TBD)
- **Billing interval:** Monthly (others can be added later)

### Stripe Product Setup

**In Stripe Dashboard (or via API):**

1. **Create Product:** "Stratus Agent Base"
   - Name: "Stratus Agent"
   - Type: Service
   - Recurring: Yes

2. **Create Price:** "Price per Agent"
   - Amount: 2999 (cents = $29.99)
   - Currency: USD (or AED if Stripe supports)
   - Billing period: Monthly
   - Save Stripe Price ID (e.g., `price_...`)

3. **Store in Supabase:**
   ```sql
   CREATE TABLE agent_stripe_prices (
     id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
     agent_template_id uuid REFERENCES agent_templates(id),
     stripe_price_id text UNIQUE NOT NULL,
     amount_usd_cents integer NOT NULL,
     billing_interval text DEFAULT 'month',
     created_at timestamp DEFAULT now()
   );
   ```

---

### Hire Flow (Checkout)

**Step 1: User clicks "Hire Agent"**
```
Frontend → POST /agents
{
  "agent_template_id": "uuid",
  "name": "My LinkedIn Bot",
  "config": { ... }
}
```

**Step 2: Backend creates `user_agent` + checkout session**
```python
@router.post("/agents")
async def hire_agent(
    agent_id: str,
    name: str,
    config: dict,
    current_user = Depends(get_current_user)
):
    # Validate agent template exists
    template = await db.fetch_one(
        "SELECT * FROM agent_templates WHERE id = %s AND is_published = true",
        (agent_id,)
    )
    if not template:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Validate config against schema
    validate_config_against_schema(config, template['config_schema'])
    
    # Create user_agent record
    user_agent = await db.fetch_one(
        """
        INSERT INTO user_agents (
            user_id, agent_template_id, name, config, status
        ) VALUES (%s, %s, %s, %s, 'inactive')
        RETURNING *
        """,
        (current_user['id'], agent_id, name, json.dumps(config))
    )
    
    # Create Stripe customer (if not exists)
    stripe_customer_id = get_or_create_stripe_customer(
        user_id=current_user['id'],
        email=current_user['email']
    )
    
    # Create Stripe checkout session
    checkout_session = stripe.checkout.Session.create(
        customer=stripe_customer_id,
        payment_method_types=['card'],
        line_items=[
            {
                'price': template['stripe_price_id'],
                'quantity': 1,
            }
        ],
        mode='subscription',
        success_url=f"{FRONTEND_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/marketplace",
        metadata={
            'user_agent_id': user_agent['id'],
            'user_id': current_user['id'],
            'agent_template_id': agent_id
        }
    )
    
    return {
        "success": True,
        "data": {
            "user_agent_id": user_agent['id'],
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
    }
```

**Step 3: Frontend redirects user to checkout**
```javascript
window.location.href = response.data.checkout_url
// Stripe handles payment
```

**Step 4: User completes payment**
```
User enters card details
     ↓
Stripe processes payment
     ↓
Stripe creates Subscription in Stripe dashboard
     ↓
Stripe fires webhook: customer.subscription.created
     ↓
Backend receives webhook (see Webhooks section)
```

---

### Webhook Handler (Subscription Created)

**When Stripe fires `customer.subscription.created`:**
```python
import stripe

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            body,
            sig_header,
            STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Extract subscription data
    subscription = event.data.object
    
    if event.type == 'customer.subscription.created':
        # Idempotency check
        existing = await db.fetch_one(
            "SELECT * FROM subscriptions WHERE stripe_subscription_id = %s",
            (subscription.id,)
        )
        if existing:
            return {"success": True}  # Already processed
        
        # Get user_agent_id from metadata or lookup by customer
        user_agent_id = subscription.metadata.get('user_agent_id')
        
        # Create subscription record
        await db.execute(
            """
            INSERT INTO subscriptions (
                user_id,
                user_agent_id,
                stripe_subscription_id,
                stripe_customer_id,
                stripe_price_id,
                status,
                current_period_start,
                current_period_end,
                amount_usd_cents,
                last_webhook_event_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                subscription.metadata['user_id'],
                user_agent_id,
                subscription.id,
                subscription.customer,
                subscription.items.data[0].price.id,
                subscription.status,
                datetime.fromtimestamp(subscription.current_period_start),
                datetime.fromtimestamp(subscription.current_period_end),
                subscription.items.data[0].price.unit_amount,
                event.id
            )
        )
        
        # Update user_agent
        await db.execute(
            """
            UPDATE user_agents
            SET stripe_subscription_id = %s,
                stripe_subscription_status = %s,
                is_active = %s,
                status = %s
            WHERE id = %s
            """,
            (
                subscription.id,
                subscription.status,
                subscription.status == 'active',
                'active' if subscription.status == 'active' else 'inactive',
                user_agent_id
            )
        )
        
        # Log success
        logger.info(f"Subscription created: {subscription.id}")
    
    elif event.type == 'customer.subscription.updated':
        # Handle status changes
        await db.execute(
            """
            UPDATE subscriptions
            SET status = %s,
                current_period_end = %s,
                cancel_at_period_end = %s,
                last_webhook_event_id = %s,
                last_webhook_at = now()
            WHERE stripe_subscription_id = %s
            """,
            (
                subscription.status,
                datetime.fromtimestamp(subscription.current_period_end),
                subscription.cancel_at_period_end,
                event.id,
                subscription.id
            )
        )
        
        # Deactivate agent if subscription is not active
        if subscription.status != 'active':
            user_agent_id = await db.fetch_val(
                "SELECT user_agent_id FROM subscriptions WHERE stripe_subscription_id = %s",
                (subscription.id,)
            )
            await db.execute(
                """
                UPDATE user_agents
                SET is_active = false, status = 'inactive'
                WHERE id = %s
                """,
                (user_agent_id,)
            )
    
    elif event.type == 'customer.subscription.deleted':
        # Subscription was canceled or expired
        await db.execute(
            """
            UPDATE subscriptions
            SET status = 'canceled',
                canceled_at = now(),
                last_webhook_event_id = %s,
                last_webhook_at = now()
            WHERE stripe_subscription_id = %s
            """,
            (event.id, subscription.id)
        )
        
        # Deactivate agent
        user_agent_id = await db.fetch_val(
            "SELECT user_agent_id FROM subscriptions WHERE stripe_subscription_id = %s",
            (subscription.id,)
        )
        await db.execute(
            """
            UPDATE user_agents
            SET is_active = false, status = 'inactive'
            WHERE id = %s
            """,
            (user_agent_id,)
        )
    
    return {"success": True, "received": True}
```

---

### Access Gate

**Before any agent action (run, update, fetch logs), check subscription:**
```python
async def verify_agent_access(
    user_agent_id: str,
    current_user = Depends(get_current_user)
):
    # Fetch agent + subscription
    agent = await db.fetch_one(
        "SELECT * FROM user_agents WHERE id = %s AND user_id = %s",
        (user_agent_id, current_user['id'])
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check subscription is active
    subscription = await db.fetch_one(
        "SELECT * FROM subscriptions WHERE user_agent_id = %s",
        (user_agent_id,)
    )
    if not subscription or subscription['status'] != 'active':
        raise HTTPException(
            status_code=403,
            detail="Subscription inactive. Please renew to use this agent."
        )
    
    return agent

# Usage in endpoint
@router.post("/agents/{agent_id}/run")
async def run_agent(
    agent_id: str,
    input_data: dict,
    agent = Depends(verify_agent_access)
):
    # Agent is verified to have active subscription
    # Proceed with execution
    ...
```

---

### Idempotency

**Goal:** Don't process the same webhook twice.

**Mechanism:**
- Store `event.id` in `subscriptions.last_webhook_event_id`
- Before processing, check if `event.id` already exists
- Skip if already processed

```python
existing_event = await db.fetch_val(
    "SELECT id FROM subscriptions WHERE last_webhook_event_id = %s",
    (event.id,)
)
if existing_event:
    return {"success": True}  # Already processed
```

---

## 5. REAL-TIME UPDATES

### Requirement
Agent status dots on dashboard/mobile must update live when agent finishes a run or changes status.

### Solution: Supabase Realtime

**Architecture:**
1. Backend publishes status changes to Supabase Realtime
2. Frontend subscribes to `user_agents` table for changes
3. When `user_agents.status` or `user_agents.last_run_at` updates, subscribers get notified
4. Frontend updates agent cards in real-time

---

### Backend Publishing (Python/FastAPI)

When an agent finishes a run or status changes:
```python
import asyncpg
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async def update_agent_status(user_agent_id: str, new_status: str):
    # Update database
    await db.execute(
        "UPDATE user_agents SET status = %s, updated_at = now() WHERE id = %s",
        (new_status, user_agent_id)
    )
    
    # Supabase Realtime automatically notifies subscribers
    # because we updated the table
```

**Enable Realtime on `user_agents`:**
```sql
ALTER PUBLICATION supabase_realtime ADD TABLE user_agents;
ALTER PUBLICATION supabase_realtime ADD TABLE agent_logs;
```

---

### Frontend Subscription (Next.js)

```typescript
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

export function useLiveAgents(userId: string) {
  const [agents, setAgents] = useState([])

  useEffect(() => {
    // Initial fetch
    const fetchAgents = async () => {
      const { data, error } = await supabase
        .from('user_agents')
        .select('*')
        .eq('user_id', userId)

      if (error) {
        console.error('Error fetching agents:', error)
      } else {
        setAgents(data)
      }
    }

    fetchAgents()

    // Subscribe to changes
    const subscription = supabase
      .channel(`user_agents:${userId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'user_agents',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setAgents([...agents, payload.new])
          } else if (payload.eventType === 'UPDATE') {
            setAgents(
              agents.map((a) =>
                a.id === payload.new.id ? payload.new : a
              )
            )
          } else if (payload.eventType === 'DELETE') {
            setAgents(agents.filter((a) => a.id !== payload.old.id))
          }
        }
      )
      .subscribe()

    return () => {
      subscription.unsubscribe()
    }
  }, [userId])

  return agents
}
```

**Usage in component:**
```typescript
export function Dashboard() {
  const { user } = useAuth()
  const agents = useLiveAgents(user.id)

  return (
    <div>
      {agents.map((agent) => (
        <AgentCard
          key={agent.id}
          agent={agent}
          isOnline={agent.status === 'active'}
        />
      ))}
    </div>
  )
}
```

---

### Mobile Subscription (Expo)

Same pattern, using `@supabase/supabase-js`:
```typescript
import { useLiveAgents } from './hooks'

export function DashboardScreen() {
  const { user } = useAuth()
  const agents = useLiveAgents(user.id)

  return (
    <ScrollView>
      {agents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
    </ScrollView>
  )
}
```

---

## 6. ERROR CODES

Standard error codes returned in API responses.

### Authentication & Authorization

| Code | Meaning | HTTP | Fix |
|------|---------|------|-----|
| `UNAUTHORIZED` | Missing or invalid token | 401 | Refresh token or login again |
| `FORBIDDEN` | Token valid but insufficient permissions | 403 | User doesn't have access |
| `ADMIN_ONLY` | Endpoint requires admin role | 403 | Only admins can access |

### Agents & Marketplace

| Code | Meaning | HTTP | Fix |
|------|---------|------|-----|
| `AGENT_NOT_FOUND` | Agent template or instance not found | 404 | Check agent ID |
| `AGENT_NOT_PUBLISHED` | Agent template is not published | 404 | Admin needs to publish it |
| `AGENT_ALREADY_HIRED` | User already has this agent | 409 | Remove existing agent or use different one |
| `CONFIG_VALIDATION_FAILED` | Config doesn't match schema | 400 | Fix config fields |
| `AGENT_INACTIVE` | Agent is not active | 403 | User needs active subscription |

### Subscriptions & Billing

| Code | Meaning | HTTP | Fix |
|------|---------|------|-----|
| `STRIPE_ERROR` | Stripe API error | 500 | Try again later, contact support |
| `SUBSCRIPTION_NOT_FOUND` | Subscription doesn't exist | 404 | Agent might not be hired |
| `SUBSCRIPTION_INACTIVE` | Subscription is not active | 403 | Renew subscription to use agent |
| `PAYMENT_FAILED` | Payment was declined | 402 | Update payment method |
| `INVALID_CHECKOUT_SESSION` | Checkout session expired or invalid | 400 | Start new checkout |

### Data & Validation

| Code | Meaning | HTTP | Fix |
|------|---------|------|-----|
| `VALIDATION_ERROR` | Request body validation failed | 400 | Check required fields |
| `INVALID_SCHEMA` | JSON doesn't match expected schema | 400 | Fix JSON structure |
| `DUPLICATE_ENTRY` | Unique constraint violated | 409 | Remove duplicate or use different value |
| `NOT_FOUND` | Resource doesn't exist | 404 | Check resource ID |

### Internal & System

| Code | Meaning | HTTP | Fix |
|------|---------|------|-----|
| `INTERNAL_ERROR` | Unexpected server error | 500 | Try again, contact support |
| `RATE_LIMITED` | Too many requests | 429 | Wait before retrying |
| `SERVICE_UNAVAILABLE` | Service is down | 503 | Try again later |

### Example Error Response

```json
{
  "success": false,
  "data": null,
  "error": "SUBSCRIPTION_INACTIVE",
  "error_message": "Your subscription for this agent has expired. Visit billing to renew.",
  "meta": {
    "error_code": "SUBSCRIPTION_INACTIVE",
    "timestamp": "2026-03-17T14:30:00Z"
  }
}
```

---

## 7. FOLDER STRUCTURE

Recommended FastAPI project structure for Backend Engineer.

```
stratus-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app initialization
│   ├── config.py                        # Environment variables, settings
│   ├── dependencies.py                  # Shared dependencies (auth, db)
│   ├── exceptions.py                    # Custom exception classes
│   ├── middleware.py                    # Custom middleware (auth, CORS, etc.)
│   ├── utils.py                         # Utility functions
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py                # Supabase connection setup
│   │   ├── migrations.sql               # Schema definitions (from section 1)
│   │   └── seed.py                      # Seed test data
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── users.py                     # Profile schema
│   │   ├── agents.py                    # Agent template + user agent schemas
│   │   ├── subscriptions.py             # Subscription schemas
│   │   ├── logs.py                      # Agent log schemas
│   │   └── common.py                    # Shared schemas (enums, responses)
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                      # Base repository class
│   │   ├── users.py                     # User queries
│   │   ├── agents.py                    # Agent queries
│   │   ├── subscriptions.py             # Subscription queries
│   │   ├── logs.py                      # Log queries
│   │   └── marketplace.py               # Marketplace queries
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py              # Auth logic
│   │   ├── agent_service.py             # Agent business logic
│   │   ├── stripe_service.py            # Stripe integration
│   │   ├── subscription_service.py      # Subscription logic
│   │   └── notification_service.py      # Email/push notifications (future)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py                    # GET /health
│   │   ├── auth.py                      # /auth endpoints
│   │   ├── agents.py                    # /agents endpoints
│   │   ├── marketplace.py               # /marketplace endpoints
│   │   ├── subscriptions.py             # /subscriptions endpoints
│   │   ├── webhooks.py                  # /webhooks endpoints
│   │   └── admin.py                     # /admin endpoints
│   │
│   └── workers/
│       ├── __init__.py
│       ├── tasks.py                     # Celery/APScheduler tasks
│       └── scheduler.py                 # Scheduled job setup
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   ├── test_auth.py
│   ├── test_agents.py
│   ├── test_marketplace.py
│   ├── test_subscriptions.py
│   ├── test_webhooks.py
│   └── test_admin.py
│
├── .env.example                         # Example env vars
├── .env                                 # (gitignored)
├── pyproject.toml                       # Poetry/pip dependencies
├── poetry.lock                          # Lock file
├── requirements.txt                     # Dependencies (alt to pyproject.toml)
├── Dockerfile                           # Production image
├── docker-compose.yml                   # Local dev setup
└── README.md                            # Setup instructions
```

---

### Key Files Detail

#### `app/config.py`
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Anon key
    SUPABASE_SERVICE_ROLE_KEY: str  # Service role (never expose)
    
    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # Backend
    API_PORT: int = 8000
    ENVIRONMENT: str = 'development'
    DEBUG: bool = False
    
    # CORS
    FRONTEND_URL: str = 'http://localhost:3000'
    ALLOWED_ORIGINS: list = ['http://localhost:3000', 'https://stratus.ai']
    
    # JWT
    JWT_SECRET: Optional[str] = None  # Use Supabase secrets, don't store here
    
    class Config:
        env_file = '.env'
        case_sensitive = True

settings = Settings()
```

#### `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, auth, agents, marketplace, subscriptions, webhooks, admin
from app.config import settings

app = FastAPI(
    title='Stratus API',
    version='1.0.0',
    description='AI automation agency platform'
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Routes
app.include_router(health.router)
app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(agents.router, prefix='/agents', tags=['agents'])
app.include_router(marketplace.router, prefix='/marketplace', tags=['marketplace'])
app.include_router(subscriptions.router, prefix='/subscriptions', tags=['subscriptions'])
app.include_router(webhooks.router, prefix='/webhooks', tags=['webhooks'])
app.include_router(admin.router, prefix='/admin', tags=['admin'])

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=settings.API_PORT)
```

#### `app/schemas/common.py`
```python
from pydantic import BaseModel
from typing import Any, Optional, Dict

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
    error: Optional[str] = None
    error_message: Optional[str] = None
    meta: Dict = {}

class ErrorResponse(BaseModel):
    success: bool = False
    data: Optional[Any] = None
    error: str
    error_message: str
    meta: Dict = {}
```

---

### Dependencies & Environment

**`pyproject.toml`:**
```toml
[tool.poetry]
name = "stratus-backend"
version = "1.0.0"
description = "Stratus API"
authors = ["Eyad Ismael <eyad@stratus.ai>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
supabase = "^2.0.0"
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"
stripe = "^7.0.0"
python-jose = "^3.3.0"
passlib = "^1.7.0"
httpx = "^0.25.0"
asyncpg = "^0.29.0"
python-multipart = "^0.0.6"
apscheduler = "^3.10.0"
redis = "^5.0.0"
python-json-logger = "^2.0.0"

[tool.poetry.dev-dependencies]
pytest = "^7.0"
pytest-asyncio = "^0.21.0"
httpx = "^0.25.0"
```

---

## SUMMARY FOR BACKEND ENGINEER

You have:
1. **Schema:** 7 tables with exact column specs, constraints, indexes, and RLS policies
2. **API:** 30+ endpoints with request/response shapes (all match standard envelope)
3. **Auth:** Supabase Auth integration guide with middleware examples
4. **Stripe:** Per-agent subscription flow with webhook handler and idempotency
5. **Real-time:** Supabase Realtime setup for live status updates
6. **Error codes:** Standard error responses for all failure cases
7. **Folder structure:** Organized by domain (repositories, services, schemas, API routes)

**Startup tasks (Phase 1):**
1. Set up Supabase project, run schema migrations
2. Scaffold FastAPI with folder structure above
3. Implement auth middleware + dependencies
4. Build all repositories (CRUD + queries)
5. Build all services (business logic)
6. Build all API routes (30+ endpoints)
7. Build Stripe webhook handler
8. Build Supabase Realtime setup
9. Write tests for all endpoints (80%+ coverage)

**Testing checklist:**
- Unit: Services, repositories, helpers
- Integration: API endpoints with database
- E2E: Full auth → hire → subscribe → run flow

This is your source of truth. Build it.

---

**Document Complete.**  
**Status:** Ready for Phase 1.2 (Backend build)  
**Next:** Creative Artist designs UI (Phase 0.2)