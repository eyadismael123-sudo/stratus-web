"""Admin endpoints — template management, client overview, analytics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.db.connection import get_service_client
from app.dependencies import require_admin
from app.schemas.agents import (
    AdminAgentTemplateResponse,
    CreateAgentTemplateRequest,
    UpdateAgentTemplateRequest,
)
from app.schemas.common import PaginationMeta, SuccessResponse
from app.services import agent_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/agents", response_model=SuccessResponse[list[AdminAgentTemplateResponse]])
def list_templates(
    published: bool | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """List all agent templates (published + unpublished)."""
    templates, total = agent_service.list_all_templates(
        published=published, page=page, limit=limit
    )
    meta = PaginationMeta(
        total=total, page=page, limit=limit, pages=(total + limit - 1) // limit if total else 0
    )
    return {"success": True, "data": templates, "meta": meta.model_dump()}


@router.post("/agents", response_model=SuccessResponse[AdminAgentTemplateResponse])
def create_template(body: CreateAgentTemplateRequest):
    """Create a new agent template."""
    data = body.model_dump(exclude_unset=True)
    template = agent_service.create_template(data)
    return {"success": True, "data": template}


@router.patch("/agents/{template_id}", response_model=SuccessResponse[AdminAgentTemplateResponse])
def update_template(template_id: str, body: UpdateAgentTemplateRequest):
    """Update an agent template."""
    updates = body.model_dump(exclude_unset=True)
    updated = agent_service.update_template(template_id, updates)
    return {"success": True, "data": updated}


@router.get("/clients")
def list_clients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List all users with subscription metrics."""
    db = get_service_client()

    offset = (page - 1) * limit
    result = (
        db.table("profiles")
        .select("*, subscriptions(id, status, user_agent_id)", count="exact")
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    total = result.count if result.count is not None else 0
    meta = PaginationMeta(
        total=total, page=page, limit=limit, pages=(total + limit - 1) // limit if total else 0
    )
    return {"success": True, "data": result.data or [], "meta": meta.model_dump()}


@router.get("/analytics")
def get_analytics():
    """System-wide stats: MRR, active agents, total clients."""
    db = get_service_client()

    # Active subscriptions count
    active_subs = (
        db.table("subscriptions")
        .select("id", count="exact")
        .eq("status", "active")
        .execute()
    )
    active_count = active_subs.count if active_subs.count is not None else 0

    # Total clients
    total_clients = (
        db.table("profiles")
        .select("id", count="exact")
        .is_("deleted_at", "null")
        .execute()
    )
    client_count = total_clients.count if total_clients.count is not None else 0

    # Total agents hired
    total_agents = (
        db.table("user_agents")
        .select("id", count="exact")
        .is_("deleted_at", "null")
        .execute()
    )
    agent_count = total_agents.count if total_agents.count is not None else 0

    # MRR = active subscriptions * $50
    mrr_cents = active_count * 5000

    return {
        "success": True,
        "data": {
            "mrr_cents": mrr_cents,
            "mrr_usd": mrr_cents / 100,
            "active_subscriptions": active_count,
            "total_clients": client_count,
            "total_agents_hired": agent_count,
        },
    }
