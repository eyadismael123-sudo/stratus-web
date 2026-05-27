"""Tripo3D API client for 3D model generation.

Free tier: 300 credits/month (~100+ generations).
Two endpoints:
  text_to_model  — text prompt → model + preview image
  image_to_model — customer photo URL → model + preview image

Both are async jobs: submit → poll until success/failed/timed out.
API docs: https://platform.tripo3d.ai/docs
"""
from __future__ import annotations

import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)

TRIPO_BASE = "https://platform.tripo3d.ai/api/v2"
POLL_INTERVAL_S = 5
POLL_TIMEOUT_S = 180


async def generate_from_text(prompt: str, api_key: str) -> dict:
    """Submit a text-to-3D job and block until complete.

    Returns:
        {
            "task_id": str,
            "model_url": str,   # GLB format — OrcaSlicer-compatible
            "preview_url": str, # rendered thumbnail shown to customer
        }
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TRIPO_BASE}/openapi/task",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "type": "text_to_model",
                "model_version": "v2.0-20240919",
                "prompt": prompt,
                "negative_prompt": "low quality, blurry, deformed",
                "face_limit": 10000,
                "texture": True,
                "pbr": False,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("code", 0) != 0:
            raise RuntimeError(f"Tripo API error: {body.get('message', 'unknown')}")
        task_id: str = body["data"]["task_id"]

    logger.info("Tripo text_to_model submitted — task_id=%s", task_id)
    return await _poll_until_done(task_id, api_key)


async def generate_from_image(image_url: str, api_key: str) -> dict:
    """Submit an image-to-3D job and block until complete.

    Args:
        image_url: Telegram CDN URL for the customer's photo
        api_key:   Tripo API key
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TRIPO_BASE}/openapi/task",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "type": "image_to_model",
                "file": {
                    "type": "jpg",
                    "url": image_url,
                },
                "face_limit": 10000,
                "texture": True,
                "pbr": False,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("code", 0) != 0:
            raise RuntimeError(f"Tripo API error: {body.get('message', 'unknown')}")
        task_id: str = body["data"]["task_id"]

    logger.info("Tripo image_to_model submitted — task_id=%s", task_id)
    return await _poll_until_done(task_id, api_key)


async def _poll_until_done(task_id: str, api_key: str) -> dict:
    """Poll the Tripo task endpoint until it succeeds, fails, or times out."""
    deadline = time.monotonic() + POLL_TIMEOUT_S

    async with httpx.AsyncClient() as client:
        while time.monotonic() < deadline:
            resp = await client.get(
                f"{TRIPO_BASE}/openapi/task/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15.0,
            )
            resp.raise_for_status()
            body = resp.json()
            data = body.get("data", {})
            status: str = data.get("status", "queued")

            if status == "success":
                output = data.get("output", {})
                return {
                    "task_id": task_id,
                    "model_url": output.get("model", ""),
                    "preview_url": output.get("rendered_image", ""),
                }

            if status == "failed":
                raise RuntimeError(
                    f"Tripo task {task_id} failed — check dashboard for details"
                )

            progress = data.get("progress", 0)
            logger.info(
                "Tripo task_id=%s  status=%-10s  progress=%s%%",
                task_id, status, progress,
            )
            await asyncio.sleep(POLL_INTERVAL_S)

    raise TimeoutError(
        f"Tripo task {task_id} did not complete within {POLL_TIMEOUT_S}s"
    )
