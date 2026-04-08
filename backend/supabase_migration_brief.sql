-- ============================================================
-- Brief (Doctor Research Agent) — DB Migration
-- Run in Supabase SQL editor (fresh install)
-- NOTE: Tables are prefixed with "wa_" to avoid clashing
-- with the existing platform tables (agent_logs, user_profiles, etc.)
-- ============================================================

-- ── clients ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    whatsapp_number TEXT UNIQUE NOT NULL,  -- E.164, e.g. "971501234567"
    timezone        TEXT NOT NULL DEFAULT 'Asia/Dubai',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clients_whatsapp ON clients (whatsapp_number);
CREATE INDEX IF NOT EXISTS idx_clients_active    ON clients (is_active);

-- ── client_agents ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS client_agents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    agent_slug  TEXT NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    hired_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_client_agents_unique
    ON client_agents (client_id, agent_slug);
CREATE INDEX IF NOT EXISTS idx_client_agents_slug
    ON client_agents (agent_slug, is_active);

-- ── wa_agent_logs ─────────────────────────────────────────────
-- Raw message log for WhatsApp agents (separate from platform agent_logs)
CREATE TABLE IF NOT EXISTS wa_agent_logs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    agent_slug        TEXT NOT NULL,
    direction         TEXT NOT NULL CHECK (direction IN ('in', 'out')),
    message_type      TEXT NOT NULL DEFAULT 'text',
    raw_content       TEXT,
    processed_content TEXT,
    response          TEXT,
    tokens_used       INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wa_agent_logs_client
    ON wa_agent_logs (client_id, agent_slug, created_at DESC);

-- ── wa_agent_memory ───────────────────────────────────────────
-- Layer 2: per-client per-agent JSONB memory
CREATE TABLE IF NOT EXISTS wa_agent_memory (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    agent_slug  TEXT NOT NULL,
    memory_json JSONB NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_wa_agent_memory_unique
    ON wa_agent_memory (client_id, agent_slug);

-- ── wa_user_profiles ──────────────────────────────────────────
-- Layer 3: cross-agent master profile synthesised by Sonnet
CREATE TABLE IF NOT EXISTS wa_user_profiles (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id          UUID UNIQUE NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    profile_json       JSONB NOT NULL DEFAULT '{}',
    last_summarized_at TIMESTAMPTZ,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── onboarding_sessions ───────────────────────────────────────
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

-- ── RLS ───────────────────────────────────────────────────────
ALTER TABLE clients             ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_agents       ENABLE ROW LEVEL SECURITY;
ALTER TABLE wa_agent_logs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE wa_agent_memory     ENABLE ROW LEVEL SECURITY;
ALTER TABLE wa_user_profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_sessions ENABLE ROW LEVEL SECURITY;
