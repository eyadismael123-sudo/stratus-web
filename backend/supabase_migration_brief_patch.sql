-- ============================================================
-- Brief DB Migration — PATCH
-- Run this if you already ran supabase_migration_brief.sql
-- and got column mismatch errors. Fixes column names +
-- adds missing columns.
-- ============================================================

-- agent_memory: rename "memory" → "memory_json"
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agent_memory' AND column_name = 'memory'
    ) THEN
        ALTER TABLE agent_memory RENAME COLUMN memory TO memory_json;
    END IF;
END $$;

-- user_profiles: rename "profile" → "profile_json"
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_profiles' AND column_name = 'profile'
    ) THEN
        ALTER TABLE user_profiles RENAME COLUMN profile TO profile_json;
    END IF;
END $$;

-- user_profiles: add last_summarized_at if missing
ALTER TABLE user_profiles
    ADD COLUMN IF NOT EXISTS last_summarized_at TIMESTAMPTZ;

-- user_profiles: add updated_at if missing
ALTER TABLE user_profiles
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- agent_logs: add processed_content if missing
ALTER TABLE agent_logs
    ADD COLUMN IF NOT EXISTS processed_content TEXT;

-- agent_logs: add tokens_used if missing
ALTER TABLE agent_logs
    ADD COLUMN IF NOT EXISTS tokens_used INTEGER NOT NULL DEFAULT 0;
