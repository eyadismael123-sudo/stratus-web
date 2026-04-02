"""Marketplace endpoints — public agent browsing."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.agents import AgentTemplateResponse
from app.schemas.common import PaginationMeta, SuccessResponse
from app.services import agent_service

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/agents", response_model=SuccessResponse[list[AgentTemplateResponse]])
def list_agents(
    category: str | None = Query(None),
    featured: bool | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """List published agents in the marketplace (public, no auth)."""
    agents, total = agent_service.list_marketplace_agents(
        category=category, featured=featured, search=search, page=page, limit=limit
    )
    meta = PaginationMeta(
        total=total, page=page, limit=limit, pages=(total + limit - 1) // limit if total else 0
    )
    return {"success": True, "data": agents, "meta": meta.model_dump()}


@router.get("/agents/{slug}", response_model=SuccessResponse[AgentTemplateResponse])
def get_agent(slug: str):
    """Get a single marketplace agent by slug (public, no auth)."""
    agent = agent_service.get_marketplace_agent(slug)
    return {"success": True, "data": agent}
