"""3D Print Agent — localhost web chatbox.

Run:
  cd backend
  python -m app.agents.print3d.web
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import random
import tempfile
import uuid
from pathlib import Path

import uvicorn
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, Response

load_dotenv()

from app.agents.print3d.core import (
    ANTHROPIC_API_KEY,
    ConversationState,
    _build_generation_prompt,
    _download,
    _upload_to_public_url,
    run_vision,
)
from app.agents.print3d.meshy import generate_from_image, generate_from_text
from app.agents.print3d.quoter import calculate_quote
from app.agents.print3d.slicer import get_viewer_stl_path, slice_model
from app.agents.print3d.glb_to_3mf import convert as glb_to_3mf_convert
from app.agents.print3d.email import send_order_email

logger = logging.getLogger(__name__)

MESHY_API_KEY = os.environ["MESHY_API_KEY"]
_anthropic    = Anthropic(api_key=ANTHROPIC_API_KEY)

app       = FastAPI()
_sessions: dict[str, ConversationState] = {}
_pending:  dict[str, dict | None]       = {}


# ── Session helpers ───────────────────────────────────────────────────────────

def _get_session(sid: str) -> ConversationState:
    if sid not in _sessions:
        _sessions[sid] = ConversationState()
    return _sessions[sid]


def _glb_path(sid: str) -> Path:
    return Path(tempfile.gettempdir()) / f"print3d_{sid[:8]}.glb"


def _3mf_path(sid: str, order_id: int) -> Path:
    return Path(tempfile.gettempdir()) / f"print3d_{sid[:8]}_order_{order_id}.3mf"


def _reset(sid: str) -> None:
    _sessions.pop(sid, None)
    _pending.pop(sid, None)


def _sid(request: Request) -> str:
    return request.cookies.get("sid") or "anonymous"


# ── Claude orchestrator ───────────────────────────────────────────────────────

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
- If a model was already generated and the user asks to change something (remove a part, change style, adjust size), call generate_model again
- Keep the same object/dimensions/style from before — only change what the user asked for
- Put the edit instruction in the notes field, e.g. notes="no handle string, keep everything else the same"
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


async def _run_orchestrator(sid: str) -> dict:
    """One Claude turn with tool-use. Assumes latest user message is already in session history."""
    state = _get_session(sid)

    if state.step == "generating":
        return {"type": "generating", "text": "Still generating your model..."}

    response = await asyncio.to_thread(
        _anthropic.messages.create,
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=_SYSTEM,
        tools=_TOOLS,
        tool_choice={"type": "any"},
        messages=state.history,
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)

    if tool_block:
        if tool_block.name == "ask_user":
            text = tool_block.input.get("question", "Could you describe what you'd like to print?")
            state.history.append({"role": "assistant", "content": text})
            return {"type": "message", "text": text}

        if tool_block.name == "request_photo":
            text = tool_block.input.get("prompt", "Could you send a photo?")
            state.history.append({"role": "assistant", "content": text})
            return {"type": "message", "text": text}

        if tool_block.name == "generate_model":
            inp  = tool_block.input
            prev = state.brief
            image_bytes    = prev.get("_image_bytes")
            texture_prompt = prev.get("_texture_prompt", "")
            state.brief = {
                "object":          inp.get("object") or prev.get("object", "custom object"),
                "dimensions":      inp.get("dimensions") or prev.get("dimensions", ""),
                "style":           inp.get("style") or prev.get("style", "realistic"),
                "material":        inp.get("material") or prev.get("material", "PLA"),
                "color":           inp.get("color") or prev.get("color", "matte white"),
                "notes":           inp.get("notes", ""),
                "_image_bytes":    image_bytes,
                "_texture_prompt": texture_prompt,
            }
            state.history.append({"role": "assistant", "content": "Generating your 3D model now..."})
            state.step = "generating"
            asyncio.create_task(_run_pipeline(sid))
            return {"type": "generating", "text": "Generating your model... (~2 min)"}

    text_block = next((b for b in response.content if hasattr(b, "text") and b.text), None)
    if text_block:
        state.history.append({"role": "assistant", "content": text_block.text})
        return {"type": "message", "text": text_block.text}

    return {"type": "message", "text": "What would you like to 3D print?"}


# ── HTML chatbox ──────────────────────────────────────────────────────────────

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>3D Print Bot</title>
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #111; color: #f0ebe0; font-family: system-ui, sans-serif; height: 100vh; display: flex; flex-direction: column; }
  header { background: #1a1a1a; padding: 16px 24px; border-bottom: 1px solid #2a2a2a; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 16px; font-weight: 600; color: #f0ebe0; }
  header span { font-size: 12px; color: #666; }
  #messages { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 12px; }
  .msg { max-width: 70%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; white-space: pre-wrap; }
  .msg.user { align-self: flex-end; background: #1B4332; color: #f0ebe0; border-bottom-right-radius: 4px; }
  .msg.bot  { align-self: flex-start; background: #1e1e1e; color: #f0ebe0; border-bottom-left-radius: 4px; border: 1px solid #2a2a2a; }
  .msg.bot.loading { color: #666; font-style: italic; }
  .quote-card { align-self: flex-start; background: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 16px; border-bottom-left-radius: 4px; overflow: hidden; max-width: 320px; }
  .quote-card img { width: 100%; display: block; }
  .quote-body { padding: 14px 16px; }
  .quote-body p { font-size: 13px; color: #aaa; margin-bottom: 12px; white-space: pre-wrap; }
  .quote-actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .btn { padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 13px; font-weight: 600; }
  .btn-confirm { background: #1B4332; color: #f0ebe0; }
  .btn-confirm:hover { background: #2d6a4f; }
  .btn-cancel  { background: #2a2a2a; color: #aaa; }
  .btn-cancel:hover  { background: #333; }
  .btn-3d { background: #2a2a2a; color: #aaa; }
  .btn-3d:hover { background: #333; }
  #input-area { background: #1a1a1a; border-top: 1px solid #2a2a2a; padding: 12px 24px 16px; display: flex; flex-direction: column; gap: 8px; }
  #staged-photos { display: none; flex-wrap: wrap; gap: 8px; }
  .staged-thumb { position: relative; }
  .staged-thumb img { width: 56px; height: 56px; object-fit: cover; border-radius: 8px; display: block; }
  .remove-thumb { position: absolute; top: -5px; right: -5px; background: #444; border: none; color: #ccc; width: 18px; height: 18px; border-radius: 50%; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; line-height: 1; }
  #input-row { display: flex; gap: 10px; align-items: flex-end; }
  #msg-input { flex: 1; background: #2a2a2a; border: 1px solid #333; border-radius: 12px; padding: 10px 14px; color: #f0ebe0; font-size: 14px; resize: none; max-height: 120px; outline: none; font-family: inherit; }
  #msg-input:focus { border-color: #1B4332; }
  #photo-btn { background: #2a2a2a; border: 1px solid #333; color: #aaa; border-radius: 10px; width: 40px; height: 40px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  #photo-btn:hover { background: #333; }
  #send-btn { background: #1B4332; border: none; color: #f0ebe0; border-radius: 10px; width: 40px; height: 40px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  #send-btn:hover { background: #2d6a4f; }
  #file-input { display: none; }
  .photo-preview { max-width: 200px; border-radius: 8px; display: block; }
</style>
</head>
<body>
<header>
  <div style="width:32px;height:32px;background:#1B4332;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">🖨</div>
  <div>
    <h1>3D Print Bot</h1>
    <span>Type, upload a photo, or describe what you want printed</span>
  </div>
</header>

<div id="messages">
  <div class="msg bot">مرحبا! / Welcome 👋<br><br>Tell me what you'd like to 3D print — text or a photo.<br>أخبرني ما تريد طباعته — نص أو صورة</div>
</div>

<div id="input-area">
  <div id="staged-photos"></div>
  <div id="input-row">
    <button id="photo-btn" onclick="document.getElementById('file-input').click()" title="Upload photo">📎</button>
    <input type="file" id="file-input" accept="image/*" multiple onchange="for(const f of this.files) stagePhoto(f); this.value=''">
    <textarea id="msg-input" placeholder="Type a message or attach photos..." rows="1"
      onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendAll()}"
      oninput="this.style.height='auto';this.style.height=this.scrollHeight+'px'"></textarea>
    <button id="send-btn" onclick="sendAll()">↑</button>
  </div>
</div>

<script>
const messages = document.getElementById('messages');
const stagedContainer = document.getElementById('staged-photos');
let stagedFiles = [];

function addMsg(text, who) {
  const div = document.createElement('div');
  div.className = 'msg ' + who;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function addLoading() {
  const div = document.createElement('div');
  div.className = 'msg bot loading';
  div.textContent = 'Thinking...';
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function addQuote(data) {
  const card = document.createElement('div');
  card.className = 'quote-card';

  if (data.preview_b64) {
    const img = document.createElement('img');
    img.src = 'data:image/jpeg;base64,' + data.preview_b64;
    card.appendChild(img);
  }

  const body = document.createElement('div');
  body.className = 'quote-body';

  const p = document.createElement('p');
  p.textContent = data.caption;
  body.appendChild(p);

  const actions = document.createElement('div');
  actions.className = 'quote-actions';

  const confirm = document.createElement('button');
  confirm.className = 'btn btn-confirm';
  confirm.textContent = '✅ Confirm — EGP ' + data.total_egp;
  confirm.onclick = () => sendAction('confirm', card);

  const cancel = document.createElement('button');
  cancel.className = 'btn btn-cancel';
  cancel.textContent = '❌ Cancel';
  cancel.onclick = () => sendAction('cancel', card);

  actions.appendChild(confirm);
  actions.appendChild(cancel);

  if (data.has_glb) {
    const view3d = document.createElement('button');
    view3d.className = 'btn btn-3d';
    view3d.textContent = '🔭 View 3D';
    view3d.onclick = () => window.open('/viewer', '_blank');
    actions.appendChild(view3d);
  }
  body.appendChild(actions);
  card.appendChild(body);
  messages.appendChild(card);
  messages.scrollTop = messages.scrollHeight;
}

// ── Staged photo queue ────────────────────────────────────────────────────────

async function stagePhoto(file) {
  if (!file || !file.type.startsWith('image/')) return;
  const dataUrl = await new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.readAsDataURL(file);
  });
  stagedFiles.push({ file, dataUrl });
  renderStagedPhotos();
}

function renderStagedPhotos() {
  stagedContainer.innerHTML = '';
  stagedContainer.style.display = stagedFiles.length ? 'flex' : 'none';
  stagedFiles.forEach((item, idx) => {
    const wrap = document.createElement('div');
    wrap.className = 'staged-thumb';
    const img = document.createElement('img');
    img.src = item.dataUrl;
    const rm = document.createElement('button');
    rm.className = 'remove-thumb';
    rm.textContent = '×';
    rm.onclick = () => removeStagedPhoto(idx);
    wrap.appendChild(img);
    wrap.appendChild(rm);
    stagedContainer.appendChild(wrap);
  });
}

function removeStagedPhoto(idx) {
  stagedFiles.splice(idx, 1);
  renderStagedPhotos();
}

// ── Send ──────────────────────────────────────────────────────────────────────

async function sendAll() {
  const input = document.getElementById('msg-input');
  const text = input.value.trim();
  const photos = stagedFiles.slice();

  if (!text && photos.length === 0) return;

  input.value = '';
  input.style.height = 'auto';
  stagedFiles = [];
  renderStagedPhotos();

  if (photos.length > 0) {
    const wrapper = document.createElement('div');
    wrapper.className = 'msg user';
    wrapper.style.display = 'flex';
    wrapper.style.flexWrap = 'wrap';
    wrapper.style.gap = '6px';
    photos.forEach(({ dataUrl }) => {
      const img = document.createElement('img');
      img.src = dataUrl;
      img.className = 'photo-preview';
      wrapper.appendChild(img);
    });
    if (text) {
      const span = document.createElement('div');
      span.style.width = '100%';
      span.textContent = text;
      wrapper.appendChild(span);
    }
    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;

    const loader = addLoading();
    loader.textContent = 'Analysing photo...';

    const formData = new FormData();
    photos.forEach(({ file }) => formData.append('files', file));
    formData.append('caption', text);

    try {
      const res = await fetch('/chat/photo', { method: 'POST', body: formData });
      if (!res.ok) throw new Error('Server error ' + res.status);
      const data = await res.json();
      loader.remove();
      handleResponse(data);
    } catch(e) {
      loader.textContent = '⚠️ Error: ' + e.message;
      loader.style.color = '#e57373';
    }
  } else {
    addMsg(text, 'user');
    const loader = addLoading();
    try {
      const res = await fetch('/chat/message', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text}),
      });
      if (!res.ok) throw new Error('Server error ' + res.status);
      const data = await res.json();
      loader.remove();
      handleResponse(data);
    } catch(e) {
      loader.textContent = '⚠️ Error: ' + e.message;
      loader.style.color = '#e57373';
    }
  }
}

// ── Paste ─────────────────────────────────────────────────────────────────────
document.addEventListener('paste', (e) => {
  const items = e.clipboardData && e.clipboardData.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault();
      stagePhoto(item.getAsFile());
      return;
    }
  }
});

// ── Drag and drop ─────────────────────────────────────────────────────────────
document.body.addEventListener('dragover', (e) => {
  e.preventDefault();
  document.body.style.outline = '2px dashed #1B4332';
});
document.body.addEventListener('dragleave', () => {
  document.body.style.outline = '';
});
document.body.addEventListener('drop', (e) => {
  e.preventDefault();
  document.body.style.outline = '';
  const files = e.dataTransfer && e.dataTransfer.files;
  if (!files) return;
  for (const file of files) {
    if (file.type.startsWith('image/')) stagePhoto(file);
  }
});

async function sendAction(action, card) {
  card.querySelector('.quote-actions').innerHTML = '<span style="color:#666;font-size:13px">Processing...</span>';
  try {
    const res = await fetch('/chat/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action}),
    });
    const data = await res.json();
    card.querySelector('.quote-actions').remove();
    handleResponse(data);
  } catch(e) {
    addMsg('⚠️ Error: ' + e.message, 'bot');
  }
}

function handleResponse(data) {
  if (data.type === 'message') {
    addMsg(data.text, 'bot');
  } else if (data.type === 'generating') {
    const loader = addLoading();
    loader.textContent = data.text || 'Generating your model... (~2 min)';
    pollGeneration(loader);
  } else if (data.type === 'quote') {
    addQuote(data);
  } else if (data.type === 'error') {
    addMsg('⚠️ ' + data.text, 'bot');
  }
}

async function pollGeneration(loader) {
  while (true) {
    await new Promise(r => setTimeout(r, 3000));
    try {
      const res = await fetch('/chat/status');
      const data = await res.json();
      if (data.type === 'generating') {
        loader.textContent = data.text || 'Still generating...';
      } else {
        loader.remove();
        handleResponse(data);
        return;
      }
    } catch(e) {
      loader.textContent = '⚠️ Lost connection';
      return;
    }
  }
}
</script>
</body>
</html>"""


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    sid = request.cookies.get("sid")
    response = HTMLResponse(content=_HTML)
    if not sid:
        sid = str(uuid.uuid4())
        response.set_cookie("sid", sid, httponly=True, samesite="lax")
    return response


@app.post("/chat/message")
async def chat_message(body: dict, request: Request):
    sid  = _sid(request)
    text = (body.get("text") or "").strip()
    if not text:
        return {"type": "message", "text": "Say something!"}
    _get_session(sid).history.append({"role": "user", "content": text})
    return await _run_orchestrator(sid)


@app.post("/chat/photo")
async def chat_photo(request: Request, files: list[UploadFile] = File(...), caption: str = Form("")):
    sid    = _sid(request)
    state  = _get_session(sid)
    images = [await f.read() for f in files]

    try:
        vision = await run_vision(images, caption)
    except Exception as e:
        logger.exception("Vision failed")
        return {"type": "error", "text": f"Couldn't read that image — {e}"}

    if vision.get("refused"):
        return {"type": "message", "text": vision.get("reason", "We can't process that request.")}

    best_idx = int(vision.get("best_image_index", 0))
    best_idx = max(0, min(best_idx, len(images) - 1))
    state.brief = {
        "_image_bytes":    images[best_idx],
        "_texture_prompt": vision.get("texture_prompt", ""),
    }

    obj   = vision.get("object_id", "object")
    dims  = vision.get("dimensions_hint", "")
    notes = vision.get("printability_notes", "")
    parts = [f"[Photo received — {obj}]"]
    if caption:
        parts.append(f"Caption: {caption}")
    if dims:
        parts.append(f"Size context from photo: {dims}")
    if notes:
        parts.append(f"Printability notes: {notes}")

    state.history.append({"role": "user", "content": "\n".join(parts)})
    return await _run_orchestrator(sid)


@app.get("/chat/status")
async def chat_status(request: Request):
    sid    = _sid(request)
    result = _pending.get(sid)
    if result is not None:
        return result
    return {"type": "generating", "text": "Still generating..."}


@app.post("/chat/action")
async def chat_action(body: dict, request: Request):
    sid    = _sid(request)
    action = body.get("action")
    if action == "confirm":
        return await _confirm_order(sid)
    if action == "cancel":
        _reset(sid)
        return {"type": "message", "text": "Cancelled. Send a new request whenever you're ready."}
    return {"type": "message", "text": "Unknown action."}


@app.post("/chat/end")
async def chat_end(request: Request):
    """Called by the frontend on tab close or page unload — cleans up the session immediately."""
    _reset(_sid(request))
    return {"ok": True}


# ── Pipeline ──────────────────────────────────────────────────────────────────

async def _run_pipeline(sid: str) -> None:
    _pending[sid] = None
    state         = _get_session(sid)
    state.step    = "generating"

    try:
        image_bytes    = state.brief.get("_image_bytes")
        texture_prompt = state.brief.get("_texture_prompt", "")

        # 1. Generate 3D model
        if image_bytes:
            public_url = await _upload_to_public_url(image_bytes)
            if public_url:
                model = await generate_from_image(
                    image_url=public_url,
                    api_key=MESHY_API_KEY,
                    texture_prompt=texture_prompt,
                )
            else:
                logger.warning("Image upload failed — falling back to text-to-3d")
                prompt = await asyncio.to_thread(_build_generation_prompt, state.brief)
                model  = await generate_from_text(prompt, MESHY_API_KEY)
        else:
            prompt = await asyncio.to_thread(_build_generation_prompt, state.brief)
            model  = await generate_from_text(prompt, MESHY_API_KEY)

        state.model_result = model

        # 2. Download GLB while the signed URL is fresh
        has_glb = False
        glb_url = model.get("glb_url", "")
        if glb_url:
            glb_bytes = await _download(glb_url)
            if glb_bytes:
                path = _glb_path(sid)
                path.write_bytes(glb_bytes)
                state.model_result["glb_path"] = str(path)
                has_glb = True
                logger.info("GLB persisted to %s (%d bytes)", path, len(glb_bytes))

        # 3. Slice + quote
        slice_result = await asyncio.to_thread(
            slice_model,
            model["model_url"],
            state.brief.get("material", "PLA"),
            state.brief.get("dimensions", ""),
        )
        quote             = calculate_quote(slice_result.grams, slice_result.print_hours)
        state.quote_result = quote

        # 4. Preview thumbnail → base64
        preview_b64 = ""
        if model.get("preview_url"):
            preview_bytes = await _download(model["preview_url"])
            if preview_bytes:
                preview_b64 = base64.standard_b64encode(preview_bytes).decode()

        caption = (
            f"{state.brief.get('object', 'Your model')}\n"
            f"Material: {state.brief.get('material', 'PLA')}\n"
            f"Size: {state.brief.get('dimensions', '~15cm')}\n\n"
            f"Print time: ~{quote.print_hours:.1f} hrs\n"
            f"Weight: {quote.grams:.0f}g\n"
            f"Total: EGP {quote.total_egp:.0f}"
        )

        state.step    = "confirming"
        _pending[sid] = {
            "type":        "quote",
            "preview_b64": preview_b64,
            "has_glb":     has_glb,
            "caption":     caption,
            "total_egp":   round(quote.total_egp),
        }

    except Exception as e:
        logger.exception("Pipeline failed")
        state.step    = "idle"
        _pending[sid] = {"type": "error", "text": str(e)}


async def _confirm_order(sid: str) -> dict:
    state = _get_session(sid)
    if state.step != "confirming" or state.quote_result is None:
        return {"type": "message", "text": "Session expired — send a new request."}

    order_id = random.randint(1000, 9999)
    quote    = state.quote_result
    glb_path = str(_glb_path(sid))
    brief    = dict(state.brief) if state.brief else {}

    _reset(sid)
    asyncio.create_task(_finalize_order(sid, order_id, brief, quote.total_egp, glb_path))

    return {
        "type": "message",
        "text": (
            f"✅ Order #{order_id} confirmed!\n\n"
            f"Total: EGP {quote.total_egp:.0f}\n"
            f"We'll start printing and reach out for delivery."
        ),
    }


async def _finalize_order(
    sid: str,
    order_id: int,
    brief: dict,
    total_egp: float,
    glb_path: str,
) -> None:
    output_path = _3mf_path(sid, order_id)
    try:
        if Path(glb_path).exists():
            logger.info("Converting GLB → 3MF for order %d…", order_id)
            await asyncio.to_thread(glb_to_3mf_convert, glb_path, str(output_path))
            logger.info("3MF ready: %s", output_path)
        else:
            logger.warning("GLB missing for order %d — will email brief only", order_id)
            output_path = None  # type: ignore[assignment]
    except Exception:
        logger.exception("GLB→3MF conversion failed for order %d", order_id)
        output_path = None  # type: ignore[assignment]

    try:
        model_url = ""  # already dropped from customer view; kept for cousin fallback
        await asyncio.to_thread(
            send_order_email, order_id, brief, total_egp, glb_path, output_path, model_url
        )
    except Exception:
        logger.exception("Failed to send order email for order %d", order_id)


# ── Static model routes ───────────────────────────────────────────────────────

@app.post("/proxy/glb")
async def proxy_glb(body: dict):
    url = (body.get("url") or "").strip()
    if not url:
        return Response(status_code=400)
    data = await _download(url)
    if not data:
        return Response(status_code=502)
    return Response(content=data, media_type="model/gltf-binary")


@app.get("/model.stl")
async def serve_stl():
    stl = get_viewer_stl_path()
    if not stl.exists():
        return Response(status_code=404)
    return Response(
        content=stl.read_bytes(),
        media_type="model/stl",
        headers={"Content-Disposition": "inline; filename=model.stl"},
    )


@app.get("/model.glb")
async def serve_glb(request: Request):
    sid  = _sid(request)
    path = _glb_path(sid)
    if not path.exists():
        return Response(status_code=404)
    return Response(
        content=path.read_bytes(),
        media_type="model/gltf-binary",
        headers={"Content-Disposition": "inline; filename=model.glb"},
    )


# ── 3D viewer (model-viewer — handles GLB natively, no Three.js fuss) ────────

_VIEWER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>3D Model Viewer</title>
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #111; height: 100vh; overflow: hidden; }
  model-viewer { width: 100vw; height: 100vh; --poster-color: #111; }
  #info { position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
          background: rgba(0,0,0,.65); padding: 6px 18px; border-radius: 20px;
          font-size: 12px; color: #aaa; font-family: system-ui; pointer-events: none;
          white-space: nowrap; }
</style>
</head>
<body>
<div id="info">Drag to rotate &nbsp;·&nbsp; Scroll to zoom &nbsp;·&nbsp; Right-drag to pan</div>
<model-viewer
  src="/model.glb"
  camera-controls
  auto-rotate
  shadow-intensity="1"
  environment-image="neutral"
  exposure="1.0"
  alt="3D printed model"
></model-viewer>
</body>
</html>"""


@app.get("/viewer", response_class=HTMLResponse)
async def viewer():
    return _VIEWER_HTML


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s  %(levelname)s  %(message)s",
        level=logging.INFO,
    )
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
