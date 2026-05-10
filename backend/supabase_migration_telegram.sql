-- Migration: Add telegram_chat_id to clients table
-- Run in Supabase SQL Editor

ALTER TABLE clients
  ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT UNIQUE;

-- Index for fast lookup by chat_id on every incoming message
CREATE INDEX IF NOT EXISTS idx_clients_telegram ON clients (telegram_chat_id);

-- Note: whatsapp_number remains on the table for existing WhatsApp agents.
-- telegram_chat_id is used exclusively by the Brief (doctor briefing) agent.
