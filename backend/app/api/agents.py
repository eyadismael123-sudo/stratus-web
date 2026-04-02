"""Agent endpoints — CRUD for user's hired agents, logs, schedules."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user
from app.schemas.agents import (
    HireAgentRequest,
    HireAgentResponse,
    UpdateAgentRequest,
    UserAgentResponse,
)
from app.schemas.common import PaginationMeta, SuccessResponse
from app.schemas.logs import (
    AgentLogResponse,
    AgentScheduleResponse,
    CreateScheduleRequest,
    ManualRunRequest,
)
from app.services import agent_service, stripe_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=SuccessResponse[list[UserAgentResponse]])
def list_agents(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """List the current user's hired agents."""
    agents, total = agent_service.list_user_agents(
        user_id=current_user["id"], status=status, page=page, limit=limit
    )
    meta = PaginationMeta(
        total=total, page=page, limit=limit, pages=(total + limit - 1) // limit if total else 0
    )
    return {"success": True, "data": agents, "meta": meta.model_dump()}


@router.post("", response_model=SuccessResponse[HireAgentResponse])
def hire_agent(
    body: HireAgentRequest,
    current_user: dict = Depends(get_current_user),
):
    """Hire an agent — creates user_agent + Stripe checkout session."""
    user_agent = agent_service.create_user_agent(
        user_id=current_user["id"],
        template_id=body.template_id,
        name=body.name,
    )

    checkout_url = stripe_service.create_checkout_session(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_agent_id=user_agent["id"],
        template_name=user_agent["name"],
    )

    return {
        "success": True,
        "data": {
            "user_agent": user_agent,
            "checkout_url": checkout_url,
        },
    }


@router.get("/{agent_id}", response_model=SuccessResponse[UserAgentResponse])
def get_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single hired agent."""
    agent = agent_service.get_user_agent(agent_id, current_user["id"])
    return {"success": True, "data": agent}


@router.patch("/{agent_id}", response_model=SuccessResponse[UserAgentResponse])
def update_agent(
    agent_id: str,
    body: UpdateAgentRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update a hired agent."""
    updates = body.model_dump(exclude_unset=True)
    updated = agent_service.update_user_agent(agent_id, current_user["id"], updates)
    return {"success": True, "data": updated}


@router.delete("/{agent_id}", response_model=SuccessResponse[UserAgentResponse])
def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Soft delete a hired agent."""
    deleted = agent_service.delete_user_agent(agent_id, current_user["id"])
    return {"success": True, "data": deleted}


# ─── Logs ────────────────────────────────────────────────────────────


@router.get(
    "/{agent_id}/logs", response_model=SuccessResponse[list[AgentLogResponse]]
)
def list_logs(
    agent_id: str,
    status: str | None = Query(None),
    since: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """List activity logs for a hired agent."""
    logs, total = agent_service.list_agent_logs(
        agent_id=agent_id,
        user_id=current_user["id"],
        status=status,
        since=since,
        page=page,
        limit=limit,
    )
    meta = PaginationMeta(
        total=total, page=page, limit=limit, pages=(total + limit - 1) // limit if total else 0
    )
    return {"success": True, "data": logs, "meta": meta.model_dump()}


@router.post(
    "/{agent_id}/run", response_model=SuccessResponse[AgentLogResponse]
)
def manual_run(
    agent_id: str,
    body: ManualRunRequest | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Manually trigger an agent run."""
    input_data = body.input_data if body else None
    log = agent_service.create_manual_run_log(
        agent_id, current_user["id"], input_data
    )
    return {"success": True, "data": log}


# ─── Schedules ───────────────────────────────────────────────────────


@router.get(
    "/{agent_id}/schedule",
    response_model=SuccessResponse[AgentScheduleResponse],
)
def get_schedule(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Get the schedule for a hired agent."""
    schedule = agent_service.get_schedule(agent_id, current_user["id"])
    return {"success": True, "data": schedule}


@router.post(
    "/{agent_id}/schedule",
    response_model=SuccessResponse[AgentScheduleResponse],
)
def upsert_schedule(
    agent_id: str,
    body: CreateScheduleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create or update the schedule for a hired agent."""
    data = body.model_dump(exclude_unset=True)
    schedule = agent_service.upsert_schedule(agent_id, current_user["id"], data)
    return {"success": True, "data": schedule}


@router.delete(
    "/{agent_id}/schedule",
    response_model=SuccessResponse[AgentScheduleResponse],
)
def delete_schedule(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Delete the schedule for a hired agent."""
    deleted = agent_service.delete_schedule(agent_id, current_user["id"])
    return {"success": True, "data": deleted}
