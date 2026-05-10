-- LinkedIn Ghostwriter: 4 new tables
-- Run this in the Supabase SQL editor

-- 1. OAuth tokens per client
CREATE TABLE IF NOT EXISTS linkedin_accounts (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    linkedin_user_id  TEXT NOT NULL,
    access_token      TEXT NOT NULL,
    refresh_token     TEXT,
    token_expires_at  TIMESTAMPTZ,
    linkedin_name     TEXT,
    linkedin_email    TEXT,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(client_id)
);

-- 2. Extracted voice profiles (one per client)
CREATE TABLE IF NOT EXISTS voice_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    raw_profile     JSONB NOT NULL DEFAULT '{}',
    posts_analyzed  INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(client_id)
);

-- 3. Post sessions (one session = one daily prompt cycle)
CREATE TABLE IF NOT EXISTS linkedin_post_sessions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    topic             TEXT,
    grok_suggestions  JSONB,
    version_a         TEXT,
    version_b         TEXT,
    selected_version  TEXT CHECK (selected_version IN ('A', 'B')),
    state             TEXT NOT NULL DEFAULT 'IDLE'
                        CHECK (state IN ('IDLE', 'TOPIC_SENT', 'VERSIONS_SENT', 'COMPLETED', 'EXPIRED')),
    linkedin_post_id  TEXT,
    posted_at         TIMESTAMPTZ,
    expires_at        TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_linkedin_post_sessions_client_state
    ON linkedin_post_sessions(client_id, state);

-- 4. Published post history (append-only, never update rows)
CREATE TABLE IF NOT EXISTS linkedin_posts (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    session_id        UUID REFERENCES linkedin_post_sessions(id),
    topic             TEXT NOT NULL,
    content           TEXT NOT NULL,
    linkedin_post_id  TEXT,
    posted_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_linkedin_posts_client_posted
    ON linkedin_posts(client_id, posted_at DESC);
