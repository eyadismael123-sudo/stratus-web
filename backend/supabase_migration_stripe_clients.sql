-- Stripe billing fields for Telegram-native clients (LinkedIn Agent MVP)
-- Run in Supabase SQL Editor

-- Stripe customer ID on the client (one per client, spans multiple agents)
ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT UNIQUE;

-- Per-agent subscription tracking on client_agents
ALTER TABLE client_agents
    ADD COLUMN IF NOT EXISTS stripe_subscription_id   TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS stripe_subscription_status TEXT NOT NULL DEFAULT 'inactive';

CREATE INDEX IF NOT EXISTS idx_client_agents_stripe_sub
    ON client_agents (stripe_subscription_id)
    WHERE stripe_subscription_id IS NOT NULL;
