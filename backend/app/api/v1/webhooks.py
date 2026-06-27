"""POST /v1/webhooks/order-paid — Shopify order.paid webhook from cousin's app server."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from pathlib import Path

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from app.agents.print3d.email import send_order_email
from app.agents.print3d.glb_to_3mf import convert as glb_to_3mf_convert
from app.agents.print3d.jobs import glb_path, tmf_path
from app.api.v1.errors import bad_request, unauthorized
from app.api.v1.schemas import OrderPaidWebhook
from app.config import settings
from app.repositories.print3d_jobs import get_job, update_job

logger = logging.getLogger(__name__)
router = APIRouter(tags=["v1"])

# Per-job lock prevents duplicate webhook retries from corrupting the same 3MF file
_finalize_locks: dict[str, asyncio.Lock] = {}


def _get_finalize_lock(job_id: str) -> asyncio.Lock:
    if job_id not in _finalize_locks:
        _finalize_locks[job_id] = asyncio.Lock()
    return _finalize_locks[job_id]


def _verify_layered_hmac(body: bytes, hmac_header: str | None) -> bool:
    secret = settings.shopify_webhook_secret
    if not secret:
        # Fail closed — never accept webhooks without a configured secret
        logger.error("shopify_webhook_secret not configured — rejecting webhook")
        return False
    if not hmac_header:
        return False
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, hmac_header)


@router.post("/webhooks/order-paid")
async def order_paid(
    request: Request,
    x_layered_signature: str | None = Header(None),
) -> JSONResponse:
    # Read raw bytes first — HMAC must be verified before any parsing
    body = await request.body()

    if not _verify_layered_hmac(body, x_layered_signature):
        raise unauthorized("Invalid webhook signature")

    try:
        payload = OrderPaidWebhook.model_validate_json(body)
    except Exception as exc:
        raise bad_request("Invalid webhook payload", {"detail": str(exc)})

    job = get_job(payload.job_id)
    if not job:
        raise bad_request("Job not found", {"job_id": payload.job_id})

    if job.get("customer_id") != payload.customer_id:
        raise unauthorized("customer_id mismatch")

    asyncio.create_task(_finalize_order(payload, job))
    return JSONResponse({"ok": True})


async def _finalize_order(payload: OrderPaidWebhook, job: dict) -> None:
    job_id = payload.job_id

    async with _get_finalize_lock(job_id):
        glb       = glb_path(job_id)
        tmf       = tmf_path(job_id)
        brief     = job.get("brief") or {}
        quote     = job.get("quote_result") or {}
        total_egp = float(quote.get("total_egp", 0))

        # Convert GLB → 3MF
        tmf_str: str | None = None
        if glb.exists():
            try:
                await asyncio.to_thread(glb_to_3mf_convert, str(glb), str(tmf))
                tmf_str = str(tmf)
                update_job(job_id, {"stl_path": tmf_str})
                logger.info("3MF ready: %s", tmf)
            except Exception:
                logger.exception("GLB→3MF failed for job %s", job_id)
        else:
            logger.warning("GLB missing for job %s — emailing brief only", job_id)

        # Email based on order type
        try:
            await asyncio.to_thread(
                send_order_email,
                payload.order_id,
                brief,
                total_egp,
                str(glb) if glb.exists() else "",
                tmf_str or "",
                "",
                payload.order_type,
                payload.customer_email,
                payload.merchant_email,
            )
        except Exception:
            logger.exception("Email failed for order %s", payload.order_id)
