"""Agent schemas — matches web/types/index.ts AgentTemplate + UserAgent."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ─── Agent Templates (Marketplace) ────────────────────────────────────


class AgentTemplateResponse(BaseModel):
    """Matches frontend AgentTemplate interface."""

    id: str
    name: str
    slug: str
    description: str
    long_description: str | None = None
    icon_url: str | None = None
    category: str
    role: str
    features: list[str] = []
    industries: list[str] = []
    price_usd_cents: int
    setup_fee_cents: int = 0
    billing_interval: str = "month"
    is_featured: bool = False
    is_published: bool = False
    config_schema: dict[str, Any] | None = None
    created_at: str


class AgentTemplateListParams(BaseModel):
    """Matches frontend MarketplaceListParams."""

    category: str | None = None
    featured: bool | None = None
    page: int = 1
    limit: int = 10
    search: str | None = None


# ─── Agent Template Pick (nested in UserAgent) ────────────────────────


class AgentTemplatePick(BaseModel):
    """Matches frontend Pick<AgentTemplate, ...> in UserAgent."""

    id: str
    name: str
    slug: str
    icon_url: str | None = None
    category: str
    role: str


# ─── User Agents (Hired Instances) ────────────────────────────────────


class UserAgentResponse(BaseModel):
    """Matches frontend UserAgent interface."""

    id: str
    name: str
    agent_template_id: str
    agent_template: AgentTemplatePick
    status: str = "inactive"
    is_active: bool = False
    config: dict[str, Any] = {}
    connected_platform: str | None = None
    connected_platform_id: str | None = None
    stripe_subscription_status: str = "inactive"
    last_run_at: str | None = None
    next_run_at: str | None = None
    run_count: int = 0
    created_at: str
    updated_at: str


class HireAgentRequest(BaseModel):
    """Matches frontend HireAgentPayload."""

    template_id: str
    name: str | None = None
    config: dict[str, Any] | None = None


class UpdateAgentRequest(BaseModel):
    """Matches frontend UpdateAgentPayload."""

    name: str | None = None
    status: str | None = None
    config: dict[str, Any] | None = None


class HireAgentResponse(BaseModel):
    """Response from POST /agents — includes checkout URL."""

    user_agent: dict
    checkout_url: str


# ─── Admin Agent Template ─────────────────────────────────────────────


class AdminAgentTemplateResponse(AgentTemplateResponse):
    """Extended template info for admin views."""

    run_count: int = 0
    user_count: int = 0


class CreateAgentTemplateRequest(BaseModel):
    """Admin: create new agent template."""

    name: str
    slug: str
    description: str
    long_description: str | None = None
    icon_url: str | None = None
    category: str
    role: str
    features: list[str] = []
    industries: list[str] = []
    price_usd_cents: int
    setup_fee_cents: int = 0
    config_schema: dict[str, Any] | None = None
    is_published: bool = False
    is_featured: bool = False


class UpdateAgentTemplateRequest(BaseModel):
    """Admin: update agent template."""

    name: str | None = None
    description: str | None = None
    long_description: str | None = None
    icon_url: str | None = None
    category: str | None = None
    role: str | None = None
    features: list[str] | None = None
    industries: list[str] | None = None
    price_usd_cents: int | None = None
    setup_fee_cents: int | None = None
    config_schema: dict[str, Any] | None = None
    is_published: bool | None = None
    is_featured: bool | None = None
