"""Meshy.ai API client for 3D model generation.

Two endpoints:
  text_to_3d  — enriched text prompt → model + preview image
  image_to_3d — customer photo → model + preview image

Both are async jobs: submit → poll until SUCCEEDED/FAILED/timed out.
"""
from __future__ import annotations

import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)

MESHY_BASE = "https://api.meshy.ai"
POLL_INTERVAL_S = 5      # seconds between status checks
POLL_TIMEOUT_S = 480     # max wait before giving up (image-to-3d can take ~5-6 min)


async def generate_from_text(prompt: str, api_key: str, style_prompt: str = "") -> dict:
    """Submit a text-to-3D job (preview → refine) and block until complete.

    Two-step: preview builds geometry, refine adds PBR colour/textures.
    style_prompt should describe the object's real-world colours (skin tone,
    clothing colours, markings, etc.) so Meshy applies the right textures.
    """
    # Step 1 — preview (geometry only, ~1 min)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MESHY_BASE}/openapi/v2/text-to-3d",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"mode": "preview", "prompt": prompt, "art_style": "realistic"},
            timeout=30.0,
        )
        resp.raise_for_status()
        preview_task_id = resp.json()["result"]

    logger.info("Meshy text_to_3d preview submitted — task_id=%s", preview_task_id)
    await _poll_until_done(preview_task_id, "v2/text-to-3d", api_key)

    # Step 2 — refine (adds PBR textures/colours, ~2 min)
    refine_payload: dict = {
        "mode": "refine",
        "preview_task_id": preview_task_id,
        "texture_richness": "high",
    }
    if style_prompt.strip():
        refine_payload["style_prompt"] = style_prompt.strip()[:600]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MESHY_BASE}/openapi/v2/text-to-3d",
            headers={"Authorization": f"Bearer {api_key}"},
            json=refine_payload,
            timeout=30.0,
        )
        resp.raise_for_status()
        refine_task_id = resp.json()["result"]

    logger.info("Meshy text_to_3d refine submitted — task_id=%s  style=%s", refine_task_id, bool(style_prompt))
    return await _poll_until_done(refine_task_id, "v2/text-to-3d", api_key)


async def generate_from_image(image_url: str, api_key: str, texture_prompt: str = "") -> dict:
    """Submit an image-to-3D job and block until complete.

    Geometry comes from the actual photo pixels (Meshy's vision model).
    texture_prompt lets Sonnet's world knowledge guide colours + unseen surfaces.

    Args:
        image_url:      Public URL to the customer's photo
        api_key:        Meshy API key
        texture_prompt: Optional Sonnet-written surface description (max 600 chars)
    """
    # texture_prompt triggers a slow second texturing pass — Meshy reads colour
    # from the photo itself, so skipping it keeps generation under 2 min.
    payload: dict = {"image_url": image_url}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MESHY_BASE}/openapi/v1/image-to-3d",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=30.0,
        )
        resp.raise_for_status()
        task_id = resp.json()["result"]

    logger.info("Meshy image_to_3d submitted — task_id=%s", task_id)
    return await _poll_until_done(task_id, "v1/image-to-3d", api_key)


async def _poll_until_done(task_id: str, endpoint: str, api_key: str) -> dict:
    """Poll the Meshy task endpoint until it succeeds, fails, or times out."""
    deadline = time.monotonic() + POLL_TIMEOUT_S

    async with httpx.AsyncClient() as client:
        while time.monotonic() < deadline:
            resp = await client.get(
                f"{MESHY_BASE}/openapi/{endpoint}/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "PENDING")

            if status == "SUCCEEDED":
                model_urls = data.get("model_urls", {})
                result = {
                    "task_id": task_id,
                    "model_url": model_urls.get("obj", ""),
                    "glb_url": model_urls.get("glb", ""),
                    "preview_url": data.get("thumbnail_url", ""),
                }
                logger.info(
                    "Meshy SUCCEEDED — obj=%s glb=%s preview=%s",
                    bool(result["model_url"]),
                    bool(result["glb_url"]),
                    bool(result["preview_url"]),
                )
                return result

            if status in ("FAILED", "EXPIRED"):
                error = data.get("task_error", {}).get("message", "unknown error")
                raise RuntimeError(
                    f"Meshy task {task_id} ended with status={status}: {error}"
                )

            progress = data.get("progress", 0)
            logger.info(
                "Meshy task_id=%s  status=%-10s  progress=%s%%",
                task_id, status, progress,
            )
            await asyncio.sleep(POLL_INTERVAL_S)

    raise TimeoutError(
        f"Meshy task {task_id} did not complete within {POLL_TIMEOUT_S}s"
    )
