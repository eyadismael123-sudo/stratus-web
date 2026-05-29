"""GET /v1/generate/{jobId} — poll job status."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.auth import require_api_key, require_app_stage
from app.api.v1.errors import not_found
from app.api.v1.schemas import (
    GenerateStatusResponse,
    JobStatus,
    PricingBreakdown,
    PricingLineItem,
)
from app.api.v1.signed_urls import sign_url
from app.config import settings
from app.repositories.print3d_jobs import get_job

router = APIRouter(tags=["v1"])


@router.get("/generate/{job_id}")
async def generate_status(
    job_id:   str,
    _api_key: str = Depends(require_api_key),
    _stage:   str = Depends(require_app_stage),
) -> JSONResponse:
    job = get_job(job_id)
    if not job:
        raise not_found("job")

    status   = JobStatus(job["status"])
    progress = int(job.get("progress") or 0)

    model_url = None
    format_   = None
    pricing   = None
    estimated = None
    error     = None

    if status == JobStatus.complete:
        signed_path = sign_url(f"/v1/models/{job_id}.glb", job_id)
        model_url   = f"{settings.api_base_url}{signed_path}"
        format_     = "glb"

        q = job.get("quote_result") or {}
        if q:
            pricing = PricingBreakdown(
                filament=PricingLineItem(label="Filament",     amount_egp=q.get("filament_cost_egp", 0)),
                machine=PricingLineItem(label="Machine time",  amount_egp=q.get("machine_cost_egp", 0)),
                markup=PricingLineItem(label="Service fee",    amount_egp=q.get("markup_egp", 0)),
                total_egp=q.get("total_egp", 0),
            )

    elif status in (JobStatus.queued, JobStatus.running):
        estimated = max(30, 120 - progress)

    elif status == JobStatus.failed:
        error = job.get("error") or {"code": "UNKNOWN", "message": "Pipeline failed"}

    resp = GenerateStatusResponse(
        status=status,
        progress=progress,
        model_url=model_url,
        format=format_,
        pricing=pricing,
        estimated_seconds=estimated,
        error=error,
    )
    return JSONResponse(resp.model_dump(by_alias=True, exclude_none=True))
