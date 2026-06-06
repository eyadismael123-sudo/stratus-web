"""GET /v1/generate/{jobId} — poll job status."""
from __future__ import annotations

import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response

from app.api.v1.auth import require_api_key, require_app_stage
from app.api.v1.errors import not_found
from app.api.v1.schemas import (
    GenerateStatusResponse,
    JobStatus,
    PricingBreakdown,
    PricingLineItem,
    PricingOption,
)
from app.api.v1.signed_urls import sign_url
from app.config import settings
from app.repositories.print3d_jobs import get_job

logger = logging.getLogger(__name__)
router = APIRouter(tags=["v1"])

_BUCKET   = "print3d-uploads"
_GLB_PATH = "models/{job_id}.glb"


async def _https_model_url(job_id: str, glb_path_str: str | None) -> str:
    """Upload GLB to Supabase Storage (HTTPS) and return its public URL.
    Falls back to the signed VPS URL if Supabase is unavailable or the file is missing."""
    glb = Path(glb_path_str) if glb_path_str else None
    if glb and glb.exists() and settings.supabase_url and settings.supabase_service_role_key:
        filename   = _GLB_PATH.format(job_id=job_id)
        public_url = f"{settings.supabase_url}/storage/v1/object/public/{_BUCKET}/{filename}"
        try:
            async with httpx.AsyncClient() as client:
                # Skip upload if already present
                head = await client.head(public_url, timeout=5.0)
                if head.status_code == 200:
                    return public_url
                up = await client.post(
                    f"{settings.supabase_url}/storage/v1/object/{_BUCKET}/{filename}",
                    headers={
                        "Authorization": f"Bearer {settings.supabase_service_role_key}",
                        "Content-Type":  "model/gltf-binary",
                    },
                    content=glb.read_bytes(),
                    timeout=30.0,
                )
                if up.status_code in (200, 201):
                    return public_url
        except Exception as exc:
            logger.warning("Supabase GLB upload failed: %s", exc)

    signed = sign_url(f"/v1/models/{job_id}.glb", job_id)
    return f"{settings.api_base_url}{signed}"


@router.head("/generate/{job_id}")
async def generate_status_head(
    job_id:   str,
    _api_key: str = Depends(require_api_key),
    _stage:   str = Depends(require_app_stage),
) -> Response:
    job = get_job(job_id)
    return Response(status_code=200 if job else 404)


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
        model_url = await _https_model_url(job_id, job.get("glb_path"))
        format_   = "glb"

        q = job.get("quote_result") or {}
        if q:
            total = q.get("total_egp", 0)
            pricing = PricingBreakdown(
                print_cost=PricingOption(
                    amount=total,
                    breakdown=[
                        PricingLineItem(label="Filament",     amount=q.get("filament_cost_egp", 0)),
                        PricingLineItem(label="Machine time", amount=q.get("machine_cost_egp", 0)),
                        PricingLineItem(label="Service fee",  amount=q.get("markup_egp", 0)),
                    ],
                ),
                download_cost=PricingOption(amount=0, breakdown=[]),
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
