/**
 * Stratus TypeScript Types
 * Derived from API contracts in /ARCHITECTURE.md
 * These match the FastAPI response shapes exactly.
 */

// ─── API Response Envelope ────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  error_message: string | null;
  meta?: PaginationMeta;
}

export interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ─── Auth / Profile ───────────────────────────────────────────────────

export interface Profile {
  id: string;
  email: string;
  full_name: string | null;
  company_name: string | null;
  avatar_url: string | null;
  timezone: string;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

export interface UpdateProfilePayload {
  full_name?: string;
  company_name?: string;
  timezone?: string;
  notification_email?: string;
}

// ─── Agent Templates (Marketplace) ────────────────────────────────────

export interface AgentTemplate {
  id: string;
  name: string;
  slug: string;
  description: string;
  long_description?: string;
  icon_url: string | null;
  category: string;
  role: string;
  features: string[];
  industries: string[];
  price_usd_cents: number;
  setup_fee_cents: number;
  billing_interval: "month" | "year";
  is_featured: boolean;
  is_published: boolean;
  config_schema?: Record<string, unknown>;
  created_at: string;
}

export interface MarketplaceListParams {
  category?: string;
  featured?: boolean;
  page?: number;
  limit?: number;
  search?: string;
}

// ─── User Agents (Hired Instances) ────────────────────────────────────

export type AgentStatus = "inactive" | "active" | "error" | "paused";
export type StripeSubscriptionStatus =
  | "active"
  | "past_due"
  | "canceled"
  | "unpaid"
  | "trialing"
  | "inactive";
export type ConnectedPlatform = "linkedin" | "telegram" | "whatsapp" | "email";

export interface UserAgent {
  id: string;
  name: string;
  agent_template_id: string;
  agent_template: Pick<
    AgentTemplate,
    "id" | "name" | "slug" | "icon_url" | "category" | "role"
  >;
  status: AgentStatus;
  is_active: boolean;
  config: Record<string, unknown>;
  connected_platform: ConnectedPlatform | null;
  connected_platform_id: string | null;
  stripe_subscription_status: StripeSubscriptionStatus;
  last_run_at: string | null;
  next_run_at: string | null;
  run_count: number;
  created_at: string;
  updated_at: string;
}

export interface HireAgentPayload {
  agent_template_id: string;
  name: string;
  config?: Record<string, unknown>;
}

export interface UpdateAgentPayload {
  name?: string;
  status?: AgentStatus;
  config?: Record<string, unknown>;
}

// ─── Agent Logs ───────────────────────────────────────────────────────

export type LogStatus = "success" | "error" | "running" | "timeout";
export type TriggerType = "manual" | "scheduled" | "webhook" | "event";

export interface AgentLog {
  id: string;
  user_agent_id: string;
  agent_template_id: string;
  status: LogStatus;
  trigger_type: TriggerType;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  error_message: string | null;
  duration_ms: number | null;
  started_at: string;
  completed_at: string | null;
  created_at: string;
}

// ─── Agent Schedules ─────────────────────────────────────────────────

export interface AgentSchedule {
  id: string;
  user_agent_id: string;
  cron_expression: string;
  timezone: string;
  last_run_at: string | null;
  next_run_at: string | null;
  is_enabled: boolean;
  created_at: string;
}

// ─── Subscriptions / Billing ──────────────────────────────────────────

export type SubscriptionStatus =
  | "active"
  | "past_due"
  | "canceled"
  | "unpaid"
  | "trialing";

export interface Subscription {
  id: string;
  user_id: string;
  user_agent_id: string;
  stripe_subscription_id: string;
  stripe_customer_id: string;
  stripe_price_id: string;
  status: SubscriptionStatus;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  amount_usd_cents: number;
  billing_interval: "month" | "year";
  created_at: string;
}

// ─── Stripe Checkout ─────────────────────────────────────────────────

export interface CheckoutSession {
  checkout_url: string;
  session_id: string;
}

// ─── Admin ───────────────────────────────────────────────────────────

export interface AdminStats {
  total_agents_running: number;
  total_clients: number;
  total_revenue_cents: number;
  churn_rate: number;
  mrr_cents: number;
}

export interface AdminClient extends Profile {
  agents_hired: UserAgent[];
  lifetime_value_cents: number;
  last_activity_at: string | null;
  churn_risk: "low" | "medium" | "high";
}

// ─── UI-only helpers ─────────────────────────────────────────────────

/** Agent category taxonomy (locked 2026-03-21) */
export type AgentCategory = "Personal" | "Business" | "Health" | "All";

export interface AgentCardProps {
  agent: UserAgent;
  onClick?: () => void;
}

export interface NavItem {
  label: string;
  href: string;
  icon?: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
}
