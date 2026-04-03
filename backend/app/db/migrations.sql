-- Stratus Platform — Database Migration
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)

-- ─── Profiles ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS profiles (
  id                   uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email                text UNIQUE NOT NULL,
  full_name            text,
  company_name         text,
  avatar_url           text,
  is_admin             boolean DEFAULT false,
  timezone             text DEFAULT 'UTC',
  notification_email   text,
  created_at           timestamptz DEFAULT now(),
  updated_at           timestamptz DEFAULT now(),
  deleted_at           timestamptz NULL
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_is_admin ON profiles(is_admin);

-- ─── Agent Templates (Marketplace Listings) ─────────────────────────
CREATE TABLE IF NOT EXISTS agent_templates (
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
  platforms          text[] DEFAULT '{}',
  requirements       text[] DEFAULT '{}',
  price_usd_cents    integer NOT NULL,
  setup_fee_cents    integer DEFAULT 0,
  setup_time_minutes integer DEFAULT 10,
  billing_interval   text DEFAULT 'month',
  max_users          integer,
  api_endpoint       text,
  webhook_url        text,
  config_schema      jsonb,
  is_published       boolean DEFAULT false,
  is_featured        boolean DEFAULT false,
  created_at         timestamptz DEFAULT now(),
  updated_at         timestamptz DEFAULT now(),
  deleted_at         timestamptz NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_templates_slug ON agent_templates(slug);
CREATE INDEX IF NOT EXISTS idx_agent_templates_published ON agent_templates(is_published);
CREATE INDEX IF NOT EXISTS idx_agent_templates_featured ON agent_templates(is_featured);
CREATE INDEX IF NOT EXISTS idx_agent_templates_category ON agent_templates(category);

-- ─── User Agents (Hired Instances) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS user_agents (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  agent_template_id       uuid NOT NULL REFERENCES agent_templates(id),
  name                    text NOT NULL,
  status                  text DEFAULT 'inactive',
  config                  jsonb DEFAULT '{}',
  stripe_subscription_id  text UNIQUE,
  stripe_subscription_status text DEFAULT 'inactive',
  last_run_at             timestamptz,
  next_run_at             timestamptz,
  run_count               integer DEFAULT 0,
  connected_platform      text,
  connected_platform_id   text,
  is_active               boolean DEFAULT false,
  created_at              timestamptz DEFAULT now(),
  updated_at              timestamptz DEFAULT now(),
  deleted_at              timestamptz NULL
);

CREATE INDEX IF NOT EXISTS idx_user_agents_user_id ON user_agents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_agents_template_id ON user_agents(agent_template_id);
CREATE INDEX IF NOT EXISTS idx_user_agents_status ON user_agents(status);
CREATE INDEX IF NOT EXISTS idx_user_agents_is_active ON user_agents(is_active);

-- ─── Agent Logs (Immutable Run History) ─────────────────────────────
CREATE TABLE IF NOT EXISTS agent_logs (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_agent_id       uuid NOT NULL REFERENCES user_agents(id) ON DELETE CASCADE,
  agent_template_id   uuid NOT NULL REFERENCES agent_templates(id),
  status              text NOT NULL,
  trigger_type        text,
  input_data          jsonb,
  output_data         jsonb,
  error_message       text,
  duration_ms         integer,
  started_at          timestamptz DEFAULT now(),
  completed_at        timestamptz,
  created_at          timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_user_agent_id ON agent_logs(user_agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_status ON agent_logs(status);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created_at ON agent_logs(created_at);

-- ─── Subscriptions (Stripe Sync) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS subscriptions (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  user_agent_id           uuid UNIQUE REFERENCES user_agents(id) ON DELETE CASCADE,
  stripe_subscription_id  text UNIQUE NOT NULL,
  stripe_customer_id      text NOT NULL,
  status                  text NOT NULL,
  current_period_start    timestamptz,
  current_period_end      timestamptz,
  cancel_at_period_end    boolean DEFAULT false,
  canceled_at             timestamptz,
  cancellation_reason     text,
  amount_usd_cents        integer DEFAULT 5000,
  billing_interval        text DEFAULT 'month',
  metadata                jsonb DEFAULT '{}',
  last_webhook_event_id   text,
  last_webhook_at         timestamptz,
  created_at              timestamptz DEFAULT now(),
  updated_at              timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_sub_id ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- ─── Agent Schedules ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_schedules (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_agent_id       uuid UNIQUE NOT NULL REFERENCES user_agents(id) ON DELETE CASCADE,
  cron_expression     text NOT NULL,
  timezone            text DEFAULT 'UTC',
  last_run_at         timestamptz,
  next_run_at         timestamptz,
  is_enabled          boolean DEFAULT true,
  created_at          timestamptz DEFAULT now(),
  updated_at          timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_schedules_enabled ON agent_schedules(is_enabled);
CREATE INDEX IF NOT EXISTS idx_agent_schedules_next_run ON agent_schedules(next_run_at);

-- ─── Memory Columns on User Agents ─────────────────────────────────
ALTER TABLE user_agents ADD COLUMN IF NOT EXISTS memory_summary      text;
ALTER TABLE user_agents ADD COLUMN IF NOT EXISTS memory_updated_at   timestamptz;

-- ─── Agent Signals (Phase 1.4 — Schema Only) ───────────────────────
CREATE TABLE IF NOT EXISTS agent_signals (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id       uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  source_agent    uuid NOT NULL REFERENCES user_agents(id) ON DELETE CASCADE,
  signal_type     text NOT NULL CHECK (signal_type IN ('trend', 'news', 'opportunity', 'alert')),
  content         text NOT NULL,
  industries      text[] DEFAULT '{}',
  consumed_by     uuid[] DEFAULT '{}',
  expires_at      timestamptz DEFAULT (now() + interval '7 days'),
  created_at      timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_signals_client     ON agent_signals(client_id);
CREATE INDEX IF NOT EXISTS idx_signals_industries ON agent_signals USING GIN(industries);
CREATE INDEX IF NOT EXISTS idx_signals_type       ON agent_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_expires    ON agent_signals(expires_at);

-- ─── Client-Facing Chat ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id   uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  agent_id    uuid REFERENCES user_agents(id),  -- NULL = Chief of Staff
  created_at  timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversations_client ON conversations(client_id);

CREATE TABLE IF NOT EXISTS messages (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id  uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role             text NOT NULL CHECK (role IN ('user', 'assistant')),
  content          text NOT NULL,
  tokens_used      integer,
  created_at       timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);

-- ─── Auto-create profile on signup (Supabase trigger) ───────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing trigger if any, then create
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ─── Row Level Security ─────────────────────────────────────────────
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_signals ENABLE ROW LEVEL SECURITY;

-- Profiles: users can read their own profile
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Agent templates: anyone can read published templates
CREATE POLICY "Anyone can view published templates" ON agent_templates
  FOR SELECT USING (is_published = true);

-- User agents: users can only see their own
CREATE POLICY "Users can view own agents" ON user_agents
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own agents" ON user_agents
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own agents" ON user_agents
  FOR UPDATE USING (auth.uid() = user_id);

-- Agent logs: users can only see logs for their agents
CREATE POLICY "Users can view own agent logs" ON agent_logs
  FOR SELECT USING (
    user_agent_id IN (SELECT id FROM user_agents WHERE user_id = auth.uid())
  );

-- Subscriptions: users can only see their own
CREATE POLICY "Users can view own subscriptions" ON subscriptions
  FOR SELECT USING (auth.uid() = user_id);

-- Schedules: users can manage their own agent schedules
CREATE POLICY "Users can view own schedules" ON agent_schedules
  FOR SELECT USING (
    user_agent_id IN (SELECT id FROM user_agents WHERE user_id = auth.uid())
  );

-- Conversations + Messages: users can only see their own
ALTER TABLE agent_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own signals" ON agent_signals
  FOR SELECT USING (auth.uid() = client_id);

CREATE POLICY "Users can view own conversations" ON conversations
  FOR SELECT USING (auth.uid() = client_id);
CREATE POLICY "Users can insert own conversations" ON conversations
  FOR INSERT WITH CHECK (auth.uid() = client_id);

CREATE POLICY "Users can view own messages" ON messages
  FOR SELECT USING (
    conversation_id IN (SELECT id FROM conversations WHERE client_id = auth.uid())
  );
CREATE POLICY "Users can insert own messages" ON messages
  FOR INSERT WITH CHECK (
    conversation_id IN (SELECT id FROM conversations WHERE client_id = auth.uid())
  );

-- Service role bypasses RLS — used by backend for admin operations
