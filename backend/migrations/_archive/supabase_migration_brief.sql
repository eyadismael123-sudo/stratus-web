-- ============================================================
-- Brief (Doctor Research Agent) — DB Migration
-- Run in Supabase SQL editor
-- ============================================================

-- ── clients ──────────────────────────────────────────────────
-- One row per client. WhatsApp number is the primary identifier.
CREATE TABLE IF NOT EXISTS clients (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    whatsapp_number TEXT UNIQUE NOT NULL,  -- E.164 format, e.g. "971501234567"
    timezone    TEXT NOT NULL DEFAULT 'Asia/Dubai',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clients_whatsapp ON clients (whatsapp_number);
CREATE INDEX IF NOT EXISTS idx_clients_active    ON clients (is_active);

-- ── client_agents ─────────────────────────────────────────────
-- Which agents each client has hired. Many-to-many.
CREATE TABLE IF NOT EXISTS client_agents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    agent_slug  TEXT NOT NULL,           -- e.g. "brief"
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    hired_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_client_agents_unique
    ON client_agents (client_id, agent_slug);
CREATE INDEX IF NOT EXISTS idx_client_agents_slug
    ON client_agents (agent_slug, is_active);

-- ── agent_logs ────────────────────────────────────────────────
-- Raw message log — every inbound and outbound message.
CREATE TABLE IF NOT EXISTS agent_logs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id    UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    agent_slug   TEXT NOT NULL,
    direction    TEXT NOT NULL CHECK (direction IN ('in', 'out')),
    message_type TEXT NOT NULL DEFAULT 'text',   -- text | voice | image
    raw_content  TEXT,
    response     TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_client
    ON agent_logs (client_id, agent_slug, created_at DESC);

-- ── agent_memory ──────────────────────────────────────────────
-- Layer 2: per-client per-agent JSONB memory.
-- Upserted by Haiku after every interaction.
CREATE TABLE IF NOT EXISTS agent_memory (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    agent_slug  TEXT NOT NULL,
    memory      JSONB NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_memory_unique
    ON agent_memory (client_id, agent_slug);

-- ── user_profiles ─────────────────────────────────────────────
-- Layer 3: cross-agent master profile synthesised by Sonnet.
CREATE TABLE IF NOT EXISTS user_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID UNIQUE NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    profile     JSONB NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── onboarding_sessions ───────────────────────────────────────
-- State machine for multi-step onboarding per client+agent.
CREATE TABLE IF NOT EXISTS onboarding_sessions (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id      UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    agent_slug     TEXT NOT NULL,
    step           INTEGER NOT NULL DEFAULT 0,
    collected_data JSONB NOT NULL DEFAULT '{}',
    is_complete    BOOLEAN NOT NULL DEFAULT FALSE,
    started_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_onboarding_unique
    ON onboarding_sessions (client_id, agent_slug);

-- ── RLS policies ──────────────────────────────────────────────
-- The backend uses the service role key (bypasses RLS).
-- Enable RLS on all tables so anon/user keys can't touch raw data.

ALTER TABLE clients             ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_agents       ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs          ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_memory        ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles       ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_sessions ENABLE ROW LEVEL SECURITY;

-- No public policies — service role bypasses RLS entirely.
-- Add client-facing policies here if you ever expose these via Supabase JS SDK.
