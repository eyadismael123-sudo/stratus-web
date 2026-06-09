"""POST /v1/chat — stateless conversation turn."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from uuid import UUID

from anthropic import Anthropic
from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from fastapi.responses import JSONResponse

from app.agents.print3d.core import (
    ANTHROPIC_API_KEY,
    _upload_to_public_url,
    run_vision,
)
from app.agents.print3d.jobs import run_pipeline
from app.api.v1.auth import require_api_key, require_app_stage
from app.api.v1.errors import bad_request, internal, rate_limited
from app.api.v1.schemas import ChatGenerationStartedResponse, ChatMessageResponse
from app.config import settings
from app.repositories.print3d_jobs import (
    create_job,
    get_idempotency,
    save_idempotency,
    update_job,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["v1"])

_anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

# Sliding 60s window per customer_id
_rl_windows: dict[str, list[float]] = defaultdict(list)
_rl_lock = asyncio.Lock()

_MAX_HISTORY = 12  # ~6 turns — prevents context drift on long conversations


def _trim_history(history: list[dict]) -> list[dict]:
    """Keep only the last N messages before each Claude call."""
    return history[-_MAX_HISTORY:] if len(history) > _MAX_HISTORY else history

_SYSTEM = """\
You are a 3D print order assistant. Your job is to understand what the customer wants and generate their model.

REQUIRED before generating: object description + dimensions (size).
DEFAULTS — apply silently, NEVER ask: color=matte white, material=PLA, style=infer from object.

RULES:
- Lead the conversation — ask proactively, don't wait for the customer to volunteer everything
- ONE question per turn maximum
- If a photo was analysed, its details are already in the conversation — use them
- Respond in the customer's language (Arabic or English)
- If customer says "just do it" and you have object + any size reference, infer the rest and generate
- NEVER ask about colour, material, or style — use defaults
- If customer provides a real-world size reference (e.g. "fist-sized", "tennis ball"), infer dimensions from it

TOOLS:
- ask_user: need more info (almost always to get dimensions)
- request_photo: reference photo would help clarify the object
- generate_model: you have object + dimensions — generate now

EDITING EXISTING MODELS:
- If a model was already generated and the user asks to change something, call generate_model again
- Keep the same object/dimensions/style from before — only change what the user asked for
- Put the edit instruction in the notes field
- The original photo (if any) will be reused automatically"""

_TOOLS = [
    {
        "name": "ask_user",
        "description": "Ask the user one clarifying question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to ask."},
            },
            "required": ["question"],
        },
    },
    {
        "name": "request_photo",
        "description": "Ask the user to upload a reference photo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Message prompting for the photo."},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "generate_model",
        "description": "Start 3D model generation. Use only when object AND dimensions are known.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object":     {"type": "string", "description": "What to print."},
                "dimensions": {"type": "string", "description": "Size in cm, e.g. '10cm tall x 5cm wide'."},
                "style":      {"type": "string", "description": "Visual style (realistic, minimalist, etc.)."},
                "material":   {"type": "string", "description": "Print material."},
                "color":      {"type": "string", "description": "Color and finish."},
                "notes":      {"type": "string", "description": "Any extra detail."},
            },
            "required": ["object", "dimensions"],
        },
    },
]


async def _check_rate_limit(customer_id: str) -> tuple[int, int, int]:
    """Sliding 60s window. Returns (limit, remaining, reset_epoch). Raises 429 if exceeded."""
    limit        = settings.rate_limit_per_minute
    now          = time.time()
    window_start = now - 60.0

    async with _rl_lock:
        _rl_windows[customer_id] = [t for t in _rl_windows[customer_id] if t > window_start]
        count = len(_rl_windows[customer_id])

        if count >= limit:
            oldest      = min(_rl_windows[customer_id])
            retry_after = int(oldest + 60 - now) + 1
            raise rate_limited(retry_after)

        _rl_windows[customer_id].append(now)
        remaining = limit - count - 1
        reset     = int(window_start + 60)

    return limit, remaining, reset


def _add_rl_headers(response: Response, limit: int, remaining: int, reset: int) -> None:
    response.headers["X-RateLimit-Limit"]     = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"]     = str(reset)


async def _run_orchestrator(history: list[dict], image_url: str) -> dict:
    """One Claude haiku turn. Returns {type: 'message'|'generate', content|brief}."""
    response = await asyncio.to_thread(
        _anthropic.messages.create,
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=_SYSTEM,
        tools=_TOOLS,
        tool_choice={"type": "any"},
        messages=_trim_history(history),
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)

    if tool_block:
        if tool_block.name in ("ask_user", "request_photo"):
            key  = "question" if tool_block.name == "ask_user" else "prompt"
            text = tool_block.input.get(key, "Could you describe what you'd like to print?")
            return {"type": "message", "content": text}

        if tool_block.name == "generate_model":
            inp   = tool_block.input
            brief = {
                "object":          inp.get("object", "custom object"),
                "dimensions":      inp.get("dimensions", ""),
                "style":           inp.get("style", "realistic"),
                "material":        inp.get("material", "PLA"),
                "color":           inp.get("color", "matte white"),
                "notes":           inp.get("notes", ""),
                "_image_url":      image_url,
                "_texture_prompt": "",
            }
            return {"type": "generate", "brief": brief}

    # Fallback to text block
    text_block = next((b for b in response.content if hasattr(b, "text") and b.text), None)
    text = text_block.text if text_block else "Could you describe what you'd like to print?"
    return {"type": "message", "content": text}


def _validate_customer_id(customer_id: str) -> None:
    try:
        UUID(customer_id)
    except ValueError:
        raise bad_request("Invalid customer_id", {"expected": "UUID"})


@router.post("/chat")
async def chat(
    request:     Request,
    response:    Response,
    message:     str              = Form(""),
    customer_id: str              = Form(...),
    history:     str              = Form("[]"),
    image_0:     UploadFile | None = File(None),
    image_1:     UploadFile | None = File(None),
    image_2:     UploadFile | None = File(None),
    _api_key:    str              = Depends(require_api_key),
    _stage:      str              = Depends(require_app_stage),
):
    # 0. Validate customer_id before touching anything
    _validate_customer_id(customer_id)

    # 1. Idempotency
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        cached = get_idempotency(idempotency_key, customer_id)
        if cached:
            return JSONResponse(cached["response_body"])

    # 2. Rate limit
    limit, remaining, reset = await _check_rate_limit(customer_id)
    _add_rl_headers(response, limit, remaining, reset)

    # 3. Parse history
    try:
        history_list: list[dict] = json.loads(history)
    except (json.JSONDecodeError, ValueError):
        raise bad_request("Invalid history JSON", None)

    # 4. Collect uploaded images
    image_bytes_list: list[bytes] = []
    for upload in (image_0, image_1, image_2):
        if upload is not None:
            image_bytes_list.append(await upload.read())

    # 5. Vision processing
    image_url      = ""
    texture_prompt = ""

    if image_bytes_list:
        vision = await run_vision(image_bytes_list, message or "")
        if not vision.get("refused"):
            obj            = vision.get("object_id", "object")
            dims           = vision.get("dimensions_hint", "")
            notes          = vision.get("printability_notes", "")
            texture_prompt = vision.get("texture_prompt", "")
            vision_msg = (
                f"[Photo received — {obj}]\n"
                f"Caption: {message or '(no caption)'}\n"
                f"Dimensions hint: {dims}\n"
                f"Notes: {notes}"
            )
            history_list.append({"role": "user", "content": vision_msg})
            uploaded = await _upload_to_public_url(image_bytes_list[0])
            if uploaded:
                image_url = uploaded
        else:
            history_list.append({"role": "user", "content": message or "(photo received)"})
    elif message:
        history_list.append({"role": "user", "content": message})

    # 6. Orchestrator
    try:
        result = await _run_orchestrator(history_list, image_url)
    except Exception:
        logger.exception("Orchestrator error for customer %s", customer_id)
        raise internal("Orchestrator error")

    # 7. Build response
    if result["type"] == "generate":
        brief = result["brief"]
        if texture_prompt:
            brief["_texture_prompt"] = texture_prompt
        job = create_job(customer_id)
        update_job(job["id"], {"brief": brief})
        asyncio.create_task(run_pipeline(job["id"]))
        out      = ChatGenerationStartedResponse(job_id=job["id"], estimated_seconds=120)
        resp_body = out.model_dump(by_alias=True)
    else:
        out      = ChatMessageResponse(content=result["content"])
        resp_body = out.model_dump()

    # 8. Cache idempotency
    if idempotency_key:
        save_idempotency(idempotency_key, customer_id, resp_body)

    return JSONResponse(resp_body)
