"""Async pipeline runner for /v1 print3d jobs.

Analogous to _run_pipeline in web.py but job-id-keyed and Supabase-backed
rather than session-keyed and in-memory.
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from app.agents.print3d.core import _build_generation_prompt, _download, build_visual_research, find_reference_image
from app.agents.print3d.email import send_order_email
from app.agents.print3d.glb_to_3mf import convert as glb_to_3mf_convert
from app.agents.print3d.meshy import generate_from_image, generate_from_text
from app.agents.print3d.quoter import calculate_quote
from app.agents.print3d.slicer import slice_3mf
from app.repositories.print3d_jobs import get_job, update_job

logger = logging.getLogger(__name__)

MESHY_API_KEY = os.environ.get("MESHY_API_KEY", "")


def _job_dir() -> Path:
    d = Path(tempfile.gettempdir()) / "print3d_v1"
    d.mkdir(exist_ok=True)
    return d


def glb_path(job_id: str) -> Path:
    return _job_dir() / f"{job_id}.glb"


def tmf_path(job_id: str) -> Path:
    return _job_dir() / f"{job_id}.3mf"


def _patch(job_id: str, data: dict) -> None:
    try:
        update_job(job_id, data)
    except Exception:
        logger.exception("Failed to patch job %s", job_id)


async def run_pipeline(job_id: str) -> None:
    """Run the full generation pipeline for a job. Updates Supabase as it progresses."""
    _patch(job_id, {"status": "running", "progress": 5})

    try:
        job = get_job(job_id)
        if not job:
            logger.error("Job %s not found at pipeline start", job_id)
            return

        brief: dict       = job.get("brief") or {}
        image_url: str    = brief.get("_image_url", "")
        texture_prompt    = brief.get("_texture_prompt", "")
        material: str     = brief.get("material", "PLA")
        dimensions: str   = brief.get("dimensions", "")

        # 1. Generate 3D model
        if image_url:
            # Customer uploaded a photo — use it directly
            _, style_prompt = await asyncio.gather(
                asyncio.to_thread(_build_generation_prompt, brief),
                build_visual_research(brief),
            )
            model = await generate_from_image(
                image_url=image_url,
                api_key=MESHY_API_KEY,
                texture_prompt=style_prompt or texture_prompt,
            )
        else:
            # No customer photo — search the web for a reference image
            prompt, style_prompt, ref_image_url = await asyncio.gather(
                asyncio.to_thread(_build_generation_prompt, brief),
                build_visual_research(brief),
                find_reference_image(brief.get("object", ""), brief.get("notes", "")),
            )
            if ref_image_url:
                logger.info("Using reference image for '%s': %s", brief.get("object", ""), ref_image_url[:80])
                model = await generate_from_image(
                    image_url=ref_image_url,
                    api_key=MESHY_API_KEY,
                    texture_prompt=style_prompt,
                )
            else:
                logger.info("No reference image found — using text-to-3D")
                model = await generate_from_text(prompt, MESHY_API_KEY, style_prompt=style_prompt)

        _patch(job_id, {"meshy_task_id": model.get("task_id", ""), "progress": 40})

        # 2. Download GLB while the signed URL is fresh
        glb = glb_path(job_id)
        glb_url = model.get("glb_url", "")
        if not glb_url:
            raise RuntimeError("Meshy returned no GLB URL")
        glb_bytes = await _download(glb_url)
        if not glb_bytes:
            raise RuntimeError("Failed to download GLB")
        glb.write_bytes(glb_bytes)
        _patch(job_id, {"glb_path": str(glb), "progress": 45})
        logger.info("GLB saved: %s (%d bytes)", glb, len(glb_bytes))

        # 3. Convert GLB → 3MF (before slicing — OrcaSlicer slices the 3MF directly)
        tmf = tmf_path(job_id)
        await asyncio.to_thread(glb_to_3mf_convert, str(glb), str(tmf))
        _patch(job_id, {"stl_path": str(tmf), "progress": 65})
        logger.info("3MF ready: %s", tmf)

        # 4. Slice the 3MF + quote
        slice_result = await asyncio.to_thread(slice_3mf, str(tmf))
        quote = calculate_quote(slice_result.grams, slice_result.print_hours)

        _patch(
            job_id,
            {
                "slice_result": {
                    "grams":       slice_result.grams,
                    "print_hours": slice_result.print_hours,
                },
                "quote_result": {
                    "filament_cost_egp": quote.filament_cost_egp,
                    "machine_cost_egp":  quote.machine_cost_egp,
                    "markup_egp":        quote.markup_egp,
                    "total_egp":         quote.total_egp,
                    "grams":             quote.grams,
                    "print_hours":       quote.print_hours,
                },
                "status":   "complete",
                "progress": 100,
            },
        )

    except TimeoutError as exc:
        logger.error("Meshy timeout for job %s: %s", job_id, exc)
        _patch(job_id, {"status": "failed", "error": {"code": "MESHY_TIMEOUT", "message": str(exc)}})
    except Exception as exc:
        logger.exception("Pipeline failed for job %s", job_id)
        _patch(job_id, {"status": "failed", "error": {"code": "PIPELINE_ERROR", "message": str(exc)}})
