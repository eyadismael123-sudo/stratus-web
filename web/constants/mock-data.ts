/**
 * Stratus Mock Data
 * Seed data for all pages until backend is connected.
 * Follows types/index.ts interfaces exactly.
 * Category taxonomy locked 2026-03-21.
 */

import type {
  AgentTemplate,
  UserAgent,
  AgentLog,
  AgentSchedule,
  Subscription,
  AdminStats,
  AdminClient,
  Profile,
} from "@/types";

// ─── Agent Templates (Marketplace) ────────────────────────────────────────────

export const MOCK_AGENT_TEMPLATES: AgentTemplate[] = [
  {
    id: "tpl_linkedin_post",
    name: "Frame",
    slug: "linkedin-post-agent",
    description:
      "Writes thought leadership in your voice. Daily.",
    long_description:
      "Writes thought leadership in your voice. Daily. Designed for the high-impact executives of MENA.",
    icon_url: null,
    category: "Personal",
    role: "LinkedIn Post Agent",
    features: [
      "Daily morning briefing with 3 post ideas",
      "2 post variations per topic",
      "Telegram delivery + refinement buttons",
      "LinkedIn pre-fill link — one-tap publish",
      "Grok-powered real-time trend research",
    ],
    industries: ["Any industry", "Pharma", "Tech", "Finance", "Consulting"],
    price_usd_cents: 9900,
    setup_fee_cents: 0,
    billing_interval: "month",
    is_featured: true,
    is_published: true,
    created_at: "2026-03-01T00:00:00Z",
  },
];

// ─── User Agents (Dashboard — "Your Team") ────────────────────────────────────

export const MOCK_USER_AGENTS: UserAgent[] = [
  {
    id: "ua_001",
    name: "LinkedIn Post Agent",
    agent_template_id: "tpl_linkedin_post",
    agent_template: {
      id: "tpl_linkedin_post",
      name: "LinkedIn Post Agent",
      slug: "linkedin-post-agent",
      icon_url: null,
      category: "Personal",
      role: "LinkedIn Ghostwriter",
    },
    status: "active",
    is_active: true,
    config: {
      linkedin_profile_url: "https://linkedin.com/in/eyad-ismael",
      voice_profile: "Professional yet approachable, uses medical analogies",
      post_time: "09:00",
      timezone: "Asia/Dubai",
    },
    connected_platform: "linkedin",
    connected_platform_id: "eyad-ismael",
    stripe_subscription_status: "active",
    last_run_at: "2026-03-21T08:00:00Z",
    next_run_at: "2026-03-22T08:00:00Z",
    run_count: 47,
    created_at: "2026-02-02T10:00:00Z",
    updated_at: "2026-03-21T08:00:00Z",
  },
  {
    id: "ua_002",
    name: "Car Market Intel",
    agent_template_id: "tpl_car_intel",
    agent_template: {
      id: "tpl_car_intel",
      name: "Car Market Intel",
      slug: "car-market-intel",
      icon_url: null,
      category: "Business",
      role: "Market Intelligence Agent",
    },
    status: "active",
    is_active: true,
    config: {
      target_makes: ["Toyota", "Nissan", "BMW", "Mercedes"],
      price_range_aed: { min: 30000, max: 150000 },
      alert_time: "07:30",
    },
    connected_platform: "telegram",
    connected_platform_id: "uae_cars_intel_bot",
    stripe_subscription_status: "active",
    last_run_at: "2026-03-21T07:30:00Z",
    next_run_at: "2026-03-22T07:30:00Z",
    run_count: 23,
    created_at: "2026-02-15T10:00:00Z",
    updated_at: "2026-03-21T07:30:00Z",
  },
  {
    id: "ua_003",
    name: "AI Receptionist",
    agent_template_id: "tpl_ai_receptionist",
    agent_template: {
      id: "tpl_ai_receptionist",
      name: "AI Receptionist",
      slug: "ai-receptionist",
      icon_url: null,
      category: "Business",
      role: "Customer Intake Agent",
    },
    status: "paused",
    is_active: false,
    config: {
      business_name: "Stratus Agency",
      whatsapp_number: "+971501234567",
      faq_topics: ["pricing", "services", "onboarding"],
    },
    connected_platform: "whatsapp",
    connected_platform_id: "+971501234567",
    stripe_subscription_status: "active",
    last_run_at: "2026-03-20T18:22:00Z",
    next_run_at: null,
    run_count: 89,
    created_at: "2026-01-20T10:00:00Z",
    updated_at: "2026-03-20T18:22:00Z",
  },
];

// ─── Agent Logs (for Agent Detail page) ───────────────────────────────────────

export const MOCK_AGENT_LOGS: AgentLog[] = [
  {
    id: "log_001",
    user_agent_id: "ua_001",
    agent_template_id: "tpl_linkedin_post",
    status: "success",
    trigger_type: "scheduled",
    input_data: { topic: "AI in healthcare diagnostics", sources_scanned: 12 },
    output_data: {
      post_variation_a:
        "After 3 months of AI-assisted diagnostics, here is what no one tells you about accuracy...",
      post_variation_b:
        "The radiologist vs. AI debate misses the point entirely. Here is what actually matters...",
      briefing_sent: true,
      linkedin_prefill_url: "https://linkedin.com/sharing/...",
    },
    error_message: null,
    duration_ms: 4821,
    started_at: "2026-03-21T08:00:00Z",
    completed_at: "2026-03-21T08:00:05Z",
    created_at: "2026-03-21T08:00:00Z",
  },
  {
    id: "log_002",
    user_agent_id: "ua_001",
    agent_template_id: "tpl_linkedin_post",
    status: "success",
    trigger_type: "scheduled",
    input_data: { topic: "Medical student productivity", sources_scanned: 9 },
    output_data: {
      post_variation_a:
        "I studied 400 pages this week with 3 AI tools. Here is what actually worked...",
      post_variation_b:
        "Most medical students use AI wrong. After testing 6 tools, here is the honest breakdown...",
      briefing_sent: true,
    },
    error_message: null,
    duration_ms: 3944,
    started_at: "2026-03-20T08:00:00Z",
    completed_at: "2026-03-20T08:00:04Z",
    created_at: "2026-03-20T08:00:00Z",
  },
  {
    id: "log_003",
    user_agent_id: "ua_001",
    agent_template_id: "tpl_linkedin_post",
    status: "error",
    trigger_type: "scheduled",
    input_data: { topic: "Dubai startup scene 2026" },
    output_data: null,
    error_message: "Grok API rate limit exceeded. Retrying in 15 minutes.",
    duration_ms: 1200,
    started_at: "2026-03-19T08:00:00Z",
    completed_at: "2026-03-19T08:00:01Z",
    created_at: "2026-03-19T08:00:00Z",
  },
  {
    id: "log_004",
    user_agent_id: "ua_001",
    agent_template_id: "tpl_linkedin_post",
    status: "success",
    trigger_type: "manual",
    input_data: { topic: "AbbVie pharma innovation", sources_scanned: 7 },
    output_data: {
      post_variation_a:
        "AbbVie just changed how they approach Phase 3 trials. Here is what it means for the industry...",
      post_variation_b:
        "3 things pharma companies get wrong about AI integration. AbbVie is actually getting them right...",
      briefing_sent: true,
    },
    error_message: null,
    duration_ms: 5103,
    started_at: "2026-03-18T14:32:00Z",
    completed_at: "2026-03-18T14:32:05Z",
    created_at: "2026-03-18T14:32:00Z",
  },
  {
    id: "log_005",
    user_agent_id: "ua_001",
    agent_template_id: "tpl_linkedin_post",
    status: "success",
    trigger_type: "scheduled",
    input_data: { topic: "Remote work and productivity research", sources_scanned: 11 },
    output_data: {
      post_variation_a:
        "Stanford just published 2 years of remote work data. The results surprised everyone including me...",
      post_variation_b:
        "Remote work is not dying. Here is what the data actually says (versus what your CEO is reading)...",
      briefing_sent: true,
    },
    error_message: null,
    duration_ms: 4456,
    started_at: "2026-03-17T08:00:00Z",
    completed_at: "2026-03-17T08:00:04Z",
    created_at: "2026-03-17T08:00:00Z",
  },
  {
    id: "log_006",
    user_agent_id: "ua_001",
    agent_template_id: "tpl_linkedin_post",
    status: "success",
    trigger_type: "scheduled",
    input_data: { topic: "AI agent startups Series A 2026", sources_scanned: 15 },
    output_data: {
      post_variation_a:
        "$47M raised by AI agent startups this week alone. Here is what they all have in common...",
      post_variation_b:
        "Investors are now asking one question before writing any AI cheque. Here is what it is...",
      briefing_sent: true,
    },
    error_message: null,
    duration_ms: 5889,
    started_at: "2026-03-16T08:00:00Z",
    completed_at: "2026-03-16T08:00:06Z",
    created_at: "2026-03-16T08:00:00Z",
  },
  {
    id: "log_007",
    user_agent_id: "ua_001",
    agent_template_id: "tpl_linkedin_post",
    status: "success",
    trigger_type: "scheduled",
    input_data: { topic: "Healthcare digitization UAE", sources_scanned: 8 },
    output_data: {
      post_variation_a:
        "UAE just mandated digital health records across all private hospitals by Q3 2026. Here is what changes...",
      post_variation_b:
        "I asked 5 Dubai clinic managers what scares them about digital health records. Their answers were honest...",
      briefing_sent: true,
    },
    error_message: null,
    duration_ms: 4102,
    started_at: "2026-03-15T08:00:00Z",
    completed_at: "2026-03-15T08:00:04Z",
    created_at: "2026-03-15T08:00:00Z",
  },
];

// ─── Agent Schedule ────────────────────────────────────────────────────────────

export const MOCK_AGENT_SCHEDULE: AgentSchedule = {
  id: "sched_001",
  user_agent_id: "ua_001",
  cron_expression: "0 8 * * *",
  timezone: "Asia/Dubai",
  last_run_at: "2026-03-21T08:00:00Z",
  next_run_at: "2026-03-22T08:00:00Z",
  is_enabled: true,
  created_at: "2026-02-02T10:00:00Z",
};

// Schedule grid data: runs per day of week (Mon=0 ... Sun=6)
// Used for the ScheduleGrid component
export const MOCK_SCHEDULE_GRID: Record<string, number[]> = {
  // week of 2026-03-16 → 2026-03-22 (Mon–Sun)
  "2026-03-16": [1], // Monday — 1 run
  "2026-03-17": [1], // Tuesday — 1 run
  "2026-03-18": [2], // Wednesday — 2 runs (manual + scheduled)
  "2026-03-19": [0], // Thursday — 0 (error, no output)
  "2026-03-20": [1], // Friday — 1 run
  "2026-03-21": [1], // Saturday — 1 run
  "2026-03-22": [0], // Sunday — pending
};

// ─── Subscriptions (Billing page) ─────────────────────────────────────────────

export const MOCK_SUBSCRIPTIONS: Subscription[] = [
  {
    id: "sub_001",
    user_id: "user_eyad",
    user_agent_id: "ua_001",
    stripe_subscription_id: "sub_stripe_001",
    stripe_customer_id: "cus_stripe_eyad",
    stripe_price_id: "price_linkedin_monthly",
    status: "active",
    current_period_start: "2026-03-01T00:00:00Z",
    current_period_end: "2026-04-01T00:00:00Z",
    cancel_at_period_end: false,
    canceled_at: null,
    amount_usd_cents: 5000,
    billing_interval: "month",
    created_at: "2026-02-02T10:00:00Z",
  },
  {
    id: "sub_002",
    user_id: "user_eyad",
    user_agent_id: "ua_002",
    stripe_subscription_id: "sub_stripe_002",
    stripe_customer_id: "cus_stripe_eyad",
    stripe_price_id: "price_car_intel_monthly",
    status: "active",
    current_period_start: "2026-03-15T00:00:00Z",
    current_period_end: "2026-04-15T00:00:00Z",
    cancel_at_period_end: false,
    canceled_at: null,
    amount_usd_cents: 6000,
    billing_interval: "month",
    created_at: "2026-02-15T10:00:00Z",
  },
  {
    id: "sub_003",
    user_id: "user_eyad",
    user_agent_id: "ua_003",
    stripe_subscription_id: "sub_stripe_003",
    stripe_customer_id: "cus_stripe_eyad",
    stripe_price_id: "price_receptionist_monthly",
    status: "active",
    current_period_start: "2026-01-20T00:00:00Z",
    current_period_end: "2026-04-20T00:00:00Z",
    cancel_at_period_end: true,
    canceled_at: "2026-03-20T18:22:00Z",
    amount_usd_cents: 7000,
    billing_interval: "month",
    created_at: "2026-01-20T10:00:00Z",
  },
];

// Invoice mock rows (not in types — kept as plain object for billing table)
export interface MockInvoice {
  id: string;
  date: string;
  description: string;
  amount_usd_cents: number;
  status: "paid" | "pending" | "failed";
  stripe_invoice_id: string;
  pdf_url: string | null;
}

export const MOCK_INVOICES: MockInvoice[] = [
  {
    id: "inv_001",
    date: "2026-03-01T00:00:00Z",
    description: "LinkedIn Post Agent — March 2026",
    amount_usd_cents: 5000,
    status: "paid",
    stripe_invoice_id: "in_stripe_001",
    pdf_url: null,
  },
  {
    id: "inv_002",
    date: "2026-03-15T00:00:00Z",
    description: "Car Market Intel — March 2026",
    amount_usd_cents: 6000,
    status: "paid",
    stripe_invoice_id: "in_stripe_002",
    pdf_url: null,
  },
  {
    id: "inv_003",
    date: "2026-02-01T00:00:00Z",
    description: "LinkedIn Post Agent — February 2026",
    amount_usd_cents: 5000,
    status: "paid",
    stripe_invoice_id: "in_stripe_003",
    pdf_url: null,
  },
  {
    id: "inv_004",
    date: "2026-01-20T00:00:00Z",
    description: "AI Receptionist — January 2026",
    amount_usd_cents: 7000,
    status: "paid",
    stripe_invoice_id: "in_stripe_004",
    pdf_url: null,
  },
  {
    id: "inv_005",
    date: "2026-02-15T00:00:00Z",
    description: "Car Market Intel — February 2026",
    amount_usd_cents: 6000,
    status: "paid",
    stripe_invoice_id: "in_stripe_005",
    pdf_url: null,
  },
  {
    id: "inv_006",
    date: "2026-01-01T00:00:00Z",
    description: "LinkedIn Post Agent — January 2026",
    amount_usd_cents: 5000,
    status: "paid",
    stripe_invoice_id: "in_stripe_006",
    pdf_url: null,
  },
];

// ─── Admin Stats (Admin War Room) ─────────────────────────────────────────────

export const MOCK_ADMIN_STATS: AdminStats = {
  total_agents_running: 7,
  total_clients: 4,
  total_revenue_cents: 183000,
  churn_rate: 0.08,
  mrr_cents: 45500,
};

// ─── Admin Clients ─────────────────────────────────────────────────────────────

const BASE_PROFILE: Omit<Profile, "id" | "email" | "full_name" | "company_name" | "avatar_url" | "is_admin" | "created_at" | "updated_at"> = {
  timezone: "Asia/Dubai",
};

export const MOCK_ADMIN_CLIENTS: AdminClient[] = [
  {
    id: "user_client_001",
    email: "rashid@abbvie.com",
    full_name: "Rashid Ismael",
    company_name: "AbbVie Pharma",
    avatar_url: null,
    is_admin: false,
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-03-21T08:00:00Z",
    ...BASE_PROFILE,
    agents_hired: [MOCK_USER_AGENTS[0]],
    lifetime_value_cents: 25000,
    last_activity_at: "2026-03-21T08:00:00Z",
    churn_risk: "low",
  },
  {
    id: "user_client_002",
    email: "hassan@uaecars.ae",
    full_name: "Hassan Al Maktoum",
    company_name: "UAE Cars Trading",
    avatar_url: null,
    is_admin: false,
    created_at: "2026-02-15T10:00:00Z",
    updated_at: "2026-03-21T07:30:00Z",
    ...BASE_PROFILE,
    agents_hired: [MOCK_USER_AGENTS[1]],
    lifetime_value_cents: 12000,
    last_activity_at: "2026-03-21T07:30:00Z",
    churn_risk: "low",
  },
  {
    id: "user_client_003",
    email: "layla@difc-law.com",
    full_name: "Layla Khalid",
    company_name: "DIFC Legal Partners",
    avatar_url: null,
    is_admin: false,
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-03-18T12:00:00Z",
    ...BASE_PROFILE,
    agents_hired: [],
    lifetime_value_cents: 35000,
    last_activity_at: "2026-03-18T12:00:00Z",
    churn_risk: "medium",
  },
  {
    id: "user_client_004",
    email: "omar@luxeclinic.ae",
    full_name: "Dr. Omar Yusuf",
    company_name: "Luxe Medical Centre",
    avatar_url: null,
    is_admin: false,
    created_at: "2026-01-05T10:00:00Z",
    updated_at: "2026-03-10T09:00:00Z",
    ...BASE_PROFILE,
    agents_hired: [],
    lifetime_value_cents: 48000,
    last_activity_at: "2026-03-10T09:00:00Z",
    churn_risk: "high",
  },
];

// ─── All agent instances for admin grid ──────────────────────────────────────

export const MOCK_ALL_AGENTS: UserAgent[] = [
  ...MOCK_USER_AGENTS,
  {
    id: "ua_004",
    name: "LinkedIn Post Agent",
    agent_template_id: "tpl_linkedin_post",
    agent_template: {
      id: "tpl_linkedin_post",
      name: "LinkedIn Post Agent",
      slug: "linkedin-post-agent",
      icon_url: null,
      category: "Personal",
      role: "LinkedIn Ghostwriter",
    },
    status: "active",
    is_active: true,
    config: { client: "DIFC Legal Partners" },
    connected_platform: "linkedin",
    connected_platform_id: "layla-khalid",
    stripe_subscription_status: "active",
    last_run_at: "2026-03-21T08:00:00Z",
    next_run_at: "2026-03-22T08:00:00Z",
    run_count: 61,
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-03-21T08:00:00Z",
  },
  {
    id: "ua_005",
    name: "CV Screener",
    agent_template_id: "tpl_cv_screener",
    agent_template: {
      id: "tpl_cv_screener",
      name: "CV Screener",
      slug: "cv-screener",
      icon_url: null,
      category: "Personal",
      role: "Recruitment Screener",
    },
    status: "active",
    is_active: true,
    config: { client: "DIFC Legal Partners" },
    connected_platform: "email",
    connected_platform_id: "layla@difc-law.com",
    stripe_subscription_status: "active",
    last_run_at: "2026-03-21T09:15:00Z",
    next_run_at: "2026-03-22T09:15:00Z",
    run_count: 33,
    created_at: "2026-01-20T10:00:00Z",
    updated_at: "2026-03-21T09:15:00Z",
  },
  {
    id: "ua_006",
    name: "Doctor Morning Briefing",
    agent_template_id: "tpl_doctor_briefing",
    agent_template: {
      id: "tpl_doctor_briefing",
      name: "Doctor Morning Briefing",
      slug: "doctor-morning-briefing",
      icon_url: null,
      category: "Health",
      role: "Clinical Intelligence Agent",
    },
    status: "error",
    is_active: false,
    config: { client: "Luxe Medical Centre", specialty: "Cardiology" },
    connected_platform: "telegram",
    connected_platform_id: "dr_omar_briefing_bot",
    stripe_subscription_status: "past_due",
    last_run_at: "2026-03-10T07:30:00Z",
    next_run_at: null,
    run_count: 28,
    created_at: "2026-01-05T10:00:00Z",
    updated_at: "2026-03-10T07:30:00Z",
  },
  {
    id: "ua_007",
    name: "Clinic Operations Agent",
    agent_template_id: "tpl_clinic_ops",
    agent_template: {
      id: "tpl_clinic_ops",
      name: "Clinic Operations Agent",
      slug: "clinic-operations-agent",
      icon_url: null,
      category: "Health",
      role: "Clinic Operations Manager",
    },
    status: "active",
    is_active: true,
    config: { client: "Luxe Medical Centre" },
    connected_platform: "whatsapp",
    connected_platform_id: "+97141234567",
    stripe_subscription_status: "active",
    last_run_at: "2026-03-21T07:00:00Z",
    next_run_at: "2026-03-22T07:00:00Z",
    run_count: 74,
    created_at: "2026-01-05T10:00:00Z",
    updated_at: "2026-03-21T07:00:00Z",
  },
];
