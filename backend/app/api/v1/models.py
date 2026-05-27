"""GET /v1/models/{job_id}.glb — signed URL endpoint for 3D model preview.

CORS is opened for *.myshopify.com and the cousin's domain on this endpoint only.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.v1.errors import not_found
from app.api.v1.signed_urls import verify_signed_url
from app.repositories.print3d_jobs import get_job

router = APIRouter()


@router.get(
    "/models/{job_id}.glb",
    tags=["v1"],
    responses={
        200: {"content": {"model/gltf-binary": {}}},
        401: {"description": "Invalid or expired signature"},
        404: {"description": "Model not found"},
    },
)
async def serve_model(
    job_id: str,
    exp: str = Query(...),
    sig: str = Query(...),
) -> Response:
    verify_signed_url(f"/v1/models/{job_id}.glb", job_id, exp, sig)

    job = get_job(job_id)
    if not job or not job.get("glb_path"):
        raise not_found("Model")

    glb_path = Path(job["glb_path"])
    if not glb_path.exists():
        raise not_found("Model file")

    return Response(
        content=glb_path.read_bytes(),
        media_type="model/gltf-binary",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "private, no-store",
        },
    )
