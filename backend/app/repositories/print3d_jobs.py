"""print3d_jobs repository — Supabase CRUD for /v1 generation jobs and idempotency keys."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_service_client


# ── Jobs ──────────────────────────────────────────────────────────────────────

def create_job(customer_id: str) -> dict[str, Any]:
    db = get_service_client()
    result = (
        db.table("print3d_jobs")
        .insert({"customer_id": customer_id, "status": "queued", "progress": 0})
        .execute()
    )
    if not result.data:
        raise RuntimeError("Failed to create print3d job")
    return result.data[0]


def get_job(job_id: str) -> dict[str, Any] | None:
    db = get_service_client()
    try:
        result = (
            db.table("print3d_jobs")
            .select("*")
            .eq("id", job_id)
            .maybe_single()
            .execute()
        )
        return result.data
    except Exception as exc:
        if "204" in str(exc) or "Missing response" in str(exc):
            return None
        raise


def update_job(job_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    db = get_service_client()
    result = (
        db.table("print3d_jobs")
        .update(patch)
        .eq("id", job_id)
        .execute()
    )
    if not result.data:
        raise RuntimeError(f"Failed to update print3d job {job_id}")
    return result.data[0]


# ── Idempotency keys ──────────────────────────────────────────────────────────

def get_idempotency(key: str, customer_id: str) -> dict[str, Any] | None:
    db = get_service_client()
    result = (
        db.table("print3d_idempotency_keys")
        .select("*")
        .eq("key", key)
        .eq("customer_id", customer_id)
        .maybe_single()
        .execute()
    )
    if result.data is None:
        return None
    row = result.data
    # Treat expired keys as absent
    from datetime import datetime, timezone
    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if expires_at < datetime.now(tz=timezone.utc):
        return None
    return row


def save_idempotency(key: str, customer_id: str, response_body: dict[str, Any]) -> None:
    db = get_service_client()
    db.table("print3d_idempotency_keys").upsert(
        {"key": key, "customer_id": customer_id, "response_body": response_body},
        on_conflict="key,customer_id",
    ).execute()
