"""POST /v1/download — mint a 24-hour signed download URL for a completed job."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.auth import require_api_key, require_app_stage
from app.api.v1.errors import bad_request, not_found
from app.api.v1.schemas import DownloadRequest, DownloadResponse
from app.api.v1.signed_urls import sign_url
from app.config import settings
from app.repositories.print3d_jobs import get_job

router = APIRouter(tags=["v1"])

_DOWNLOAD_TTL_MINUTES = 60 * 24  # 24-hour links


@router.post("/download")
async def download(
    body:     DownloadRequest,
    _api_key: str = Depends(require_api_key),
    _stage:   str = Depends(require_app_stage),
) -> JSONResponse:
    job = get_job(body.job_id)
    if not job:
        raise not_found("job")

    if job.get("customer_id") != body.customer_id:
        raise bad_request("customer_id mismatch", None)

    if job.get("status") != "complete":
        raise bad_request("Job is not complete", {"status": job.get("status")})

    if not job.get("glb_path"):
        raise bad_request("Model file not available", None)

    signed_path  = sign_url(f"/v1/models/{body.job_id}.glb", body.job_id, ttl_minutes=_DOWNLOAD_TTL_MINUTES)
    download_url = f"{settings.api_base_url}{signed_path}"
    expires_at   = (datetime.now(timezone.utc) + timedelta(minutes=_DOWNLOAD_TTL_MINUTES)).isoformat()

    resp = DownloadResponse(download_url=download_url, expires_at=expires_at)
    return JSONResponse(resp.model_dump(by_alias=True))
