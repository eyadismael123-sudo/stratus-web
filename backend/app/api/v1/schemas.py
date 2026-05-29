"""Pydantic request/response models for /v1/* endpoints.

Matches the Shopify partner API contract exactly.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── /v1/health ────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    uptime_seconds: float


# ── /v1/chat ──────────────────────────────────────────────────────────────────

class ChatMessageResponse(BaseModel):
    type: str = "message"
    content: str


class ChatGenerationStartedResponse(BaseModel):
    type: str = "generation_started"
    job_id: str = Field(alias="jobId")
    estimated_seconds: int = Field(alias="estimatedSeconds")

    model_config = {"populate_by_name": True}


# ── /v1/generate/{jobId} ──────────────────────────────────────────────────────

class JobStatus(str, Enum):
    queued     = "queued"
    running    = "running"
    complete   = "complete"
    failed     = "failed"


class PricingLineItem(BaseModel):
    label: str
    amount_egp: float = Field(alias="amountEgp")

    model_config = {"populate_by_name": True}


class PricingBreakdown(BaseModel):
    filament:    PricingLineItem
    machine:     PricingLineItem
    markup:      PricingLineItem
    total_egp:   float = Field(alias="totalEgp")

    model_config = {"populate_by_name": True}


class GenerateStatusResponse(BaseModel):
    status:            JobStatus
    progress:          int                   # 0–100
    model_url:         str | None = Field(None, alias="modelUrl")
    format:            str | None = None
    pricing:           PricingBreakdown | None = None
    estimated_seconds: int | None = Field(None, alias="estimatedSeconds")
    error:             dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


# ── /v1/download ──────────────────────────────────────────────────────────────

class DownloadRequest(BaseModel):
    job_id:      str = Field(alias="jobId")
    customer_id: str = Field(alias="customerId")

    model_config = {"populate_by_name": True}


class DownloadResponse(BaseModel):
    download_url: str = Field(alias="downloadUrl")
    expires_at:   str = Field(alias="expiresAt")

    model_config = {"populate_by_name": True}


# ── /v1/webhooks/order-paid ───────────────────────────────────────────────────

class OrderPaidWebhook(BaseModel):
    job_id:      str = Field(alias="jobId")
    customer_id: str = Field(alias="customerId")
    order_id:    str = Field(alias="orderId")
    amount_paid: float | None = Field(None, alias="amountPaid")

    model_config = {"populate_by_name": True}
