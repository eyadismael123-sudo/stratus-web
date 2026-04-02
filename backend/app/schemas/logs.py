"""Agent log and schedule schemas — matches web/types/index.ts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AgentLogResponse(BaseModel):
    """Matches frontend AgentLog interface."""

    id: str
    user_agent_id: str
    agent_template_id: str
    status: str
    trigger_type: str | None = None
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    started_at: str
    completed_at: str | None = None
    created_at: str


class ManualRunRequest(BaseModel):
    """Request body for POST /agents/{id}/run."""

    input_data: dict[str, Any] | None = None


class AgentScheduleResponse(BaseModel):
    """Matches frontend AgentSchedule interface."""

    id: str
    user_agent_id: str
    cron_expression: str
    timezone: str = "UTC"
    last_run_at: str | None = None
    next_run_at: str | None = None
    is_enabled: bool = True
    created_at: str


class CreateScheduleRequest(BaseModel):
    """Request body for POST /agents/{id}/schedule."""

    cron_expression: str
    timezone: str = "UTC"
    is_enabled: bool = True
