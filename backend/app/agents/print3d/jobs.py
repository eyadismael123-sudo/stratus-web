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

from app.agents.print3d.core import _build_generation_prompt, _download, _is_figurine, build_visual_research, find_reference_images
from app.agents.print3d.email import send_order_email
from app.agents.print3d.glb_to_3mf import convert as glb_to_3mf_convert
from app.agents.print3d.meshy import generate_from_image, generate_from_multi_image, generate_from_text
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
        is_figurine = _is_figurine(brief)
        if image_url:
            # Customer uploaded a photo.
            # Vision already extracted accurate colors from the image — use it as primary.
            # Run web reference search + web style research in parallel as supplements.
            ref_image_urls, web_style = await asyncio.gather(
                find_reference_images(brief.get("object", ""), brief.get("notes", "")),
                build_visual_research(brief),
            )
            # Vision-extracted texture_prompt always preferred over web-searched description —
            # vision actually saw the uploaded image; web search infers from text only.
            final_texture = texture_prompt or web_style

            # Lead with the uploaded photo; web refs provide geometry cues for unseen sides
            all_images = [image_url] + list(ref_image_urls)

            if len(all_images) > 1:
                logger.info(
                    "Uploaded image + %d web reference(s) for '%s'",
                    len(all_images) - 1, brief.get("object", ""),
                )
                model = await generate_from_multi_image(
                    image_urls=all_images[:4],
                    api_key=MESHY_API_KEY,
                    texture_prompt=final_texture,
                )
            else:
                model = await generate_from_image(
                    image_url=image_url,
                    api_key=MESHY_API_KEY,
                    texture_prompt=final_texture,
                )
        else:
            # No customer photo — always search for reference images
            prompt, style_prompt, ref_image_urls = await asyncio.gather(
                asyncio.to_thread(_build_generation_prompt, brief),
                build_visual_research(brief),
                find_reference_images(brief.get("object", ""), brief.get("notes", "")),
            )
            if ref_image_urls:
                logger.info(
                    "Using %d reference image(s) for '%s': %s",
                    len(ref_image_urls), brief.get("object", ""),
                    " | ".join(u[:60] for u in ref_image_urls),
                )
                model = await generate_from_multi_image(
                    image_urls=ref_image_urls,
                    api_key=MESHY_API_KEY,
                    texture_prompt=style_prompt,
                )
            elif is_figurine:
                # Figurines must NEVER use text-to-3D — face/pose accuracy requires a real photo.
                # Raise so the job surfaces as failed rather than producing a useless generic model.
                raise RuntimeError(
                    "No reference image found for figurine. Cannot generate accurate face/pose "
                    "via text-to-3D. Please upload a photo or try a different search term."
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

        # 5. Email cousin the .3mf + .glb (non-blocking, failure must not crash the job)
        try:
            await asyncio.to_thread(
                send_order_email,
                job_id,
                brief,
                quote.total_egp,
                str(glb),
                str(tmf),
                model.get("model_urls", {}).get("glb", ""),
            )
        except Exception:
            logger.exception("Order email failed for job %s (job still complete)", job_id)

    except TimeoutError as exc:
        logger.error("Meshy timeout for job %s: %s", job_id, exc)
        _patch(job_id, {"status": "failed", "error": {"code": "MESHY_TIMEOUT", "message": str(exc)}})
    except Exception as exc:
        logger.exception("Pipeline failed for job %s", job_id)
        _patch(job_id, {"status": "failed", "error": {"code": "PIPELINE_ERROR", "message": str(exc)}})
