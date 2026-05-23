-- Structured LinkedIn memory table — replaces JSON blob in wa_agent_memory for linkedin agent.
-- Each client gets one row. voice_profile stays JSONB (complex nested object).
-- style_notes is a text array so individual notes can be appended cleanly.

CREATE TABLE IF NOT EXISTS linkedin_memory (
    client_id   UUID PRIMARY KEY REFERENCES clients(id) ON DELETE CASCADE,
    field       TEXT,
    audience    TEXT,
    region      TEXT,
    post_time   TEXT        NOT NULL DEFAULT '09:00',
    post_frequency TEXT     NOT NULL DEFAULT 'daily',
    voice_profile  JSONB    NOT NULL DEFAULT '{}',
    style_notes    TEXT[]   NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Migrate any existing linkedin rows from wa_agent_memory into the new table.
INSERT INTO linkedin_memory (
    client_id,
    field,
    audience,
    region,
    post_time,
    post_frequency,
    voice_profile,
    style_notes,
    updated_at
)
SELECT
    client_id,
    memory_json->>'field',
    memory_json->>'audience',
    memory_json->>'region',
    COALESCE(memory_json->>'post_time', '09:00'),
    COALESCE(memory_json->>'post_frequency', 'daily'),
    COALESCE(memory_json->'voice_profile', '{}'),
    ARRAY(SELECT jsonb_array_elements_text(COALESCE(memory_json->'style_notes', '[]'))),
    COALESCE(updated_at, now())
FROM wa_agent_memory
WHERE agent_slug = 'linkedin'
ON CONFLICT (client_id) DO NOTHING;
