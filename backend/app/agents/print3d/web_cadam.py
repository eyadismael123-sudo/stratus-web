"""3D Print Bot — CADAM-style comparison build.

Uses Claude vision + reasoning to generate parametric OpenSCAD code instead
of a Meshy mesh blob. Key difference: output is editable CAD with live sliders,
not a frozen mesh.

Run on port 8002:
  cd backend
  python -m app.agents.print3d.web_cadam
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

import uvicorn
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response

load_dotenv()

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
_anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

app = FastAPI()


# ── Media-type detector (same as core.py) ────────────────────────────────────

def _detect_media_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF8"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


# ── OpenSCAD generation prompt ────────────────────────────────────────────────

_SCAD_PROMPT = """\
You are a parametric CAD expert. Given a description or photo of a physical object,
generate clean OpenSCAD code that models it well enough to 3D print.

RULES:
1. ALL key dimensions must be named variables at the very top, each with an
   OpenSCAD Customizer range comment:
     width = 80;  // [10:200]
   The range must be realistic (min ≥ 1, max ≤ 500, sensible defaults).
2. No hardcoded numbers inside the geometry — reference the top-level variables.
3. Use standard primitives: cube, cylinder, sphere, difference, union,
   translate, rotate, scale, linear_extrude, hull.
4. Aim for a printable model — avoid zero-thickness walls, keep minimum feature
   size ≥ 1 mm.
5. Add a short comment above each section explaining what it builds.
6. Keep the code concise (under 80 lines if possible).

Return ONLY valid JSON (no markdown, no prose):
{
  "description": "one-line plain-English description of the modelled object",
  "openscad_code": "full OpenSCAD code as a single string with \\n newlines",
  "parameters": [
    {
      "name": "variable_name_in_code",
      "label": "Human label (mm)",
      "value": 80,
      "min": 10,
      "max": 200,
      "step": 1
    }
  ],
  "print_notes": "e.g. no supports needed, 0.2 mm layer height recommended"
}

If given a photo: study the object carefully — identify the geometry (box, cylinder,
curved surface, etc.) and model the dominant shape accurately.
If given text: model exactly what is described.
"""


# ── Claude call ───────────────────────────────────────────────────────────────

async def generate_scad(images: list[bytes], text: str) -> dict:
    """Call Claude to produce parametric OpenSCAD + parameter list."""
    content: list[dict] = []

    for img in images:
        mt = _detect_media_type(img)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mt,
                "data": base64.standard_b64encode(img).decode(),
            },
        })

    prompt = _SCAD_PROMPT
    if text:
        prompt += f"\n\nUser description: {text}"
    if len(images) > 1:
        prompt += f"\n\n({len(images)} photos provided — use all angles)"

    content.append({"type": "text", "text": prompt})

    resp = _anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )

    raw = resp.content[0].text.strip()

    # Strip markdown fences if Claude wraps in ```json
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)
    return data


# ── OpenSCAD render ───────────────────────────────────────────────────────────

OPENSCAD_BIN = "openscad"

def render_scad(code: str) -> tuple[bytes | None, bytes | None]:
    """Render OpenSCAD code → (stl_bytes, png_bytes). Returns Nones on failure."""
    with tempfile.TemporaryDirectory() as tmp:
        scad_path = Path(tmp) / "model.scad"
        stl_path  = Path(tmp) / "model.stl"
        png_path  = Path(tmp) / "preview.png"

        scad_path.write_text(code)

        # Render STL
        r = subprocess.run(
            [OPENSCAD_BIN, "-o", str(stl_path), str(scad_path)],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            logger.warning("OpenSCAD STL failed: %s", r.stderr[:300])
            return None, None

        # Render PNG preview
        subprocess.run(
            [OPENSCAD_BIN, "-o", str(png_path),
             "--camera=0,0,0,45,0,45,500",
             "--imgsize=600,400",
             str(scad_path)],
            capture_output=True, timeout=60,
        )

        stl_bytes = stl_path.read_bytes() if stl_path.exists() else None
        png_bytes = png_path.read_bytes() if png_path.exists() else None
        return stl_bytes, png_bytes


# ── In-memory STL store (single session) ─────────────────────────────────────
_last_stl: bytes | None = None


# ── HTML ──────────────────────────────────────────────────────────────────────

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>3D Print Bot — CADAM</title>
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #111; color: #f0ebe0; font-family: system-ui, sans-serif; height: 100vh; display: flex; flex-direction: column; }
  header { background: #1a1a1a; padding: 16px 24px; border-bottom: 1px solid #2a2a2a; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 16px; font-weight: 600; }
  header span { font-size: 12px; color: #666; }
  .badge { background: #2a1a00; color: #f59e0b; border: 1px solid #78350f; border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 700; }
  #messages { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 12px; }
  .msg { max-width: 70%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; white-space: pre-wrap; }
  .msg.user { align-self: flex-end; background: #1B4332; color: #f0ebe0; border-bottom-right-radius: 4px; }
  .msg.bot  { align-self: flex-start; background: #1e1e1e; color: #f0ebe0; border-bottom-left-radius: 4px; border: 1px solid #2a2a2a; }
  .msg.bot.loading { color: #666; font-style: italic; }
  .photo-preview { max-width: 200px; border-radius: 8px; display: block; }

  /* CADAM result card */
  .cadam-card { align-self: flex-start; background: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 16px; border-bottom-left-radius: 4px; overflow: hidden; max-width: 520px; width: 100%; }
  .cadam-header { padding: 14px 16px 0; }
  .cadam-title { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
  .cadam-notes { font-size: 12px; color: #888; margin-bottom: 12px; }
  .cadam-sliders { padding: 0 16px 12px; display: flex; flex-direction: column; gap: 10px; }
  .slider-row { display: flex; align-items: center; gap: 10px; }
  .slider-row label { font-size: 12px; color: #aaa; min-width: 140px; }
  .slider-row input[type=range] { flex: 1; accent-color: #f59e0b; }
  .slider-val { font-size: 12px; color: #f0ebe0; min-width: 40px; text-align: right; }
  .cadam-code-wrap { background: #111; border-top: 1px solid #2a2a2a; padding: 14px 16px; position: relative; }
  .cadam-code-wrap pre { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; color: #a6e22e; overflow-x: auto; white-space: pre; line-height: 1.6; max-height: 240px; }
  .cadam-preview img { width: 100%; display: block; }
  model-viewer { width: 100%; height: 300px; background: #111; display: block; }
  .cadam-actions { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid #2a2a2a; flex-wrap: wrap; }
  .btn { padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 13px; font-weight: 600; }
  .btn-amber  { background: #f59e0b; color: #111; }
  .btn-amber:hover  { background: #fbbf24; }
  .btn-dark   { background: #2a2a2a; color: #aaa; }
  .btn-dark:hover   { background: #333; }
  .btn-green  { background: #1B4332; color: #f0ebe0; }
  .btn-green:hover  { background: #2d6a4f; }

  /* Input */
  #input-area { background: #1a1a1a; border-top: 1px solid #2a2a2a; padding: 12px 24px 16px; display: flex; flex-direction: column; gap: 8px; }
  #staged-photos { display: none; flex-wrap: wrap; gap: 8px; }
  .staged-thumb { position: relative; }
  .staged-thumb img { width: 56px; height: 56px; object-fit: cover; border-radius: 8px; display: block; }
  .remove-thumb { position: absolute; top: -5px; right: -5px; background: #444; border: none; color: #ccc; width: 18px; height: 18px; border-radius: 50%; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; line-height: 1; }
  #input-row { display: flex; gap: 10px; align-items: flex-end; }
  #msg-input { flex: 1; background: #2a2a2a; border: 1px solid #333; border-radius: 12px; padding: 10px 14px; color: #f0ebe0; font-size: 14px; resize: none; max-height: 120px; outline: none; font-family: inherit; }
  #msg-input:focus { border-color: #f59e0b; }
  #photo-btn { background: #2a2a2a; border: 1px solid #333; color: #aaa; border-radius: 10px; width: 40px; height: 40px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  #photo-btn:hover { background: #333; }
  #send-btn { background: #f59e0b; border: none; color: #111; border-radius: 10px; width: 40px; height: 40px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-weight: 700; }
  #send-btn:hover { background: #fbbf24; }
  #file-input { display: none; }
</style>
</head>
<body>
<header>
  <div style="width:32px;height:32px;background:#78350f;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">📐</div>
  <div>
    <h1>3D Print Bot <span class="badge">CADAM</span></h1>
    <span>Parametric CAD output — editable dimensions, clean geometry</span>
  </div>
</header>

<div id="messages">
  <div class="msg bot">Welcome to the CADAM build 📐<br><br>Send a photo or describe an object — I'll generate parametric OpenSCAD code with live sliders instead of a mesh blob.<br><br>Compare this output to the Meshy version at <strong>:8001</strong></div>
</div>

<div id="input-area">
  <div id="staged-photos"></div>
  <div id="input-row">
    <button id="photo-btn" onclick="document.getElementById('file-input').click()" title="Upload photo">📎</button>
    <input type="file" id="file-input" accept="image/*" multiple onchange="for(const f of this.files) stagePhoto(f); this.value=''">
    <textarea id="msg-input" placeholder="Describe what you want printed, or attach a photo..." rows="1"
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

function addLoading(text) {
  const div = document.createElement('div');
  div.className = 'msg bot loading';
  div.textContent = text || 'Generating CAD...';
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

// ── CADAM result card ─────────────────────────────────────────────────────────

function addCadamCard(data) {
  let currentCode = data.openscad_code;
  const params = data.parameters || [];

  const card = document.createElement('div');
  card.className = 'cadam-card';

  // Preview image
  if (data.preview_b64) {
    const previewWrap = document.createElement('div');
    previewWrap.className = 'cadam-preview';
    const img = document.createElement('img');
    img.src = 'data:image/png;base64,' + data.preview_b64;
    previewWrap.appendChild(img);
    card.appendChild(previewWrap);
  }

  // Header
  const header = document.createElement('div');
  header.className = 'cadam-header';
  const title = document.createElement('div');
  title.className = 'cadam-title';
  title.textContent = data.description || 'Parametric model';
  const notes = document.createElement('div');
  notes.className = 'cadam-notes';
  notes.textContent = data.print_notes || '';
  header.appendChild(title);
  if (data.print_notes) header.appendChild(notes);
  card.appendChild(header);

  // Sliders
  if (params.length > 0) {
    const sliderSection = document.createElement('div');
    sliderSection.className = 'cadam-sliders';

    params.forEach(p => {
      const row = document.createElement('div');
      row.className = 'slider-row';

      const label = document.createElement('label');
      label.textContent = p.label;

      const slider = document.createElement('input');
      slider.type = 'range';
      slider.min = p.min;
      slider.max = p.max;
      slider.step = p.step || 1;
      slider.value = p.value;

      const val = document.createElement('span');
      val.className = 'slider-val';
      val.textContent = p.value;

      slider.oninput = () => {
        val.textContent = slider.value;
        // Replace the variable assignment in the code
        const regex = new RegExp(`(${p.name}\\s*=\\s*)[0-9.]+`, 'g');
        currentCode = currentCode.replace(regex, `$1${slider.value}`);
        codeEl.textContent = currentCode;
      };

      row.appendChild(label);
      row.appendChild(slider);
      row.appendChild(val);
      sliderSection.appendChild(row);
    });

    card.appendChild(sliderSection);
  }

  // Code block
  const codeWrap = document.createElement('div');
  codeWrap.className = 'cadam-code-wrap';
  const pre = document.createElement('pre');
  pre.textContent = currentCode;
  const codeEl = pre;
  codeWrap.appendChild(pre);
  card.appendChild(codeWrap);

  // Actions
  const actions = document.createElement('div');
  actions.className = 'cadam-actions';

  // View in 3D
  if (data.has_stl) {
    const view3d = document.createElement('button');
    view3d.className = 'btn btn-green';
    view3d.textContent = '🔭 View in 3D';
    view3d.onclick = () => {
      view3d.remove();
      const mv = document.createElement('model-viewer');
      mv.setAttribute('src', '/model.stl');
      mv.setAttribute('auto-rotate', '');
      mv.setAttribute('camera-controls', '');
      mv.setAttribute('shadow-intensity', '1');
      card.appendChild(mv);
      messages.scrollTop = messages.scrollHeight;
    };
    actions.appendChild(view3d);
  }

  // Re-render with current slider values
  const reRenderBtn = document.createElement('button');
  reRenderBtn.className = 'btn btn-amber';
  reRenderBtn.textContent = '🔄 Re-render';
  reRenderBtn.onclick = async () => {
    reRenderBtn.textContent = 'Rendering...';
    reRenderBtn.disabled = true;
    const res = await fetch('/render', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ code: codeEl.textContent }),
    });
    const d = await res.json();
    reRenderBtn.textContent = '🔄 Re-render';
    reRenderBtn.disabled = false;
    if (d.preview_b64) {
      const existing = card.querySelector('.cadam-preview img');
      if (existing) existing.src = 'data:image/png;base64,' + d.preview_b64;
    }
    // Refresh model-viewer STL if open
    const mv = card.querySelector('model-viewer');
    if (mv) { mv.src = ''; mv.src = '/model.stl?t=' + Date.now(); }
  };

  // Download .scad
  const dlBtn = document.createElement('button');
  dlBtn.className = 'btn btn-dark';
  dlBtn.textContent = '⬇ .scad';
  dlBtn.onclick = () => {
    const blob = new Blob([codeEl.textContent], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'model.scad';
    a.click();
  };

  // Download STL
  const stlBtn = document.createElement('button');
  stlBtn.className = 'btn btn-dark';
  stlBtn.textContent = '⬇ .stl';
  stlBtn.onclick = () => { window.open('/model.stl', '_blank'); };

  // Copy code
  const copyBtn = document.createElement('button');
  copyBtn.className = 'btn btn-dark';
  copyBtn.textContent = '📋 Copy';
  copyBtn.onclick = () => {
    navigator.clipboard.writeText(codeEl.textContent).then(() => {
      copyBtn.textContent = '✓';
      setTimeout(() => copyBtn.textContent = '📋 Copy', 1500);
    });
  };

  actions.appendChild(reRenderBtn);
  actions.appendChild(dlBtn);
  if (data.has_stl) actions.appendChild(stlBtn);
  actions.appendChild(copyBtn);
  card.appendChild(actions);

  messages.appendChild(card);
  messages.scrollTop = messages.scrollHeight;
}

// ── Staged photo queue ────────────────────────────────────────────────────────

async function stagePhoto(file) {
  if (!file || !file.type.startsWith('image/')) return;
  const dataUrl = await new Promise(resolve => {
    const reader = new FileReader();
    reader.onload = e => resolve(e.target.result);
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
    rm.onclick = () => { stagedFiles.splice(idx, 1); renderStagedPhotos(); };
    wrap.appendChild(img);
    wrap.appendChild(rm);
    stagedContainer.appendChild(wrap);
  });
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

  // Show user bubble
  if (photos.length > 0) {
    const wrapper = document.createElement('div');
    wrapper.className = 'msg user';
    wrapper.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;';
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
  } else {
    addMsg(text, 'user');
  }
  messages.scrollTop = messages.scrollHeight;

  const loader = addLoading('Generating parametric CAD...');

  const formData = new FormData();
  photos.forEach(({ file }) => formData.append('files', file));
  formData.append('text', text);

  try {
    const res = await fetch('/generate', { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Server error ' + res.status);
    const data = await res.json();
    loader.remove();
    if (data.error) {
      addMsg('⚠️ ' + data.error, 'bot');
    } else {
      addCadamCard(data);
    }
  } catch(e) {
    loader.textContent = '⚠️ ' + e.message;
    loader.style.color = '#e57373';
  }
}

// ── Paste & drag ──────────────────────────────────────────────────────────────
document.addEventListener('paste', e => {
  const items = e.clipboardData && e.clipboardData.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith('image/')) { e.preventDefault(); stagePhoto(item.getAsFile()); return; }
  }
});
document.body.addEventListener('dragover', e => { e.preventDefault(); document.body.style.outline = '2px dashed #f59e0b'; });
document.body.addEventListener('dragleave', () => { document.body.style.outline = ''; });
document.body.addEventListener('drop', e => {
  e.preventDefault(); document.body.style.outline = '';
  const files = e.dataTransfer && e.dataTransfer.files;
  if (files) for (const f of files) if (f.type.startsWith('image/')) stagePhoto(f);
});
</script>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML


@app.post("/generate")
async def generate(files: list[UploadFile] = File(default=[]), text: str = Form("")):
    global _last_stl
    images = [await f.read() for f in files]
    if not images and not text.strip():
        return {"error": "Send a photo or describe something."}
    try:
        data = await generate_scad(images, text)
    except json.JSONDecodeError as e:
        logger.exception("Claude returned invalid JSON")
        return {"error": f"JSON parse error — {e}"}
    except Exception as e:
        logger.exception("Generation failed")
        return {"error": str(e)}

    # Render preview + STL server-side
    code = data.get("openscad_code", "")
    stl_bytes, png_bytes = render_scad(code)
    _last_stl = stl_bytes

    if png_bytes:
        data["preview_b64"] = base64.standard_b64encode(png_bytes).decode()
    data["has_stl"] = stl_bytes is not None
    return data


@app.post("/render")
async def rerender(body: dict):
    """Re-render with updated code (slider changes)."""
    global _last_stl
    code = body.get("code", "")
    if not code:
        return {"error": "No code provided"}
    stl_bytes, png_bytes = render_scad(code)
    _last_stl = stl_bytes
    result: dict = {"has_stl": stl_bytes is not None}
    if png_bytes:
        result["preview_b64"] = base64.standard_b64encode(png_bytes).decode()
    return result


@app.get("/model.stl")
async def get_stl():
    if not _last_stl:
        return Response(status_code=404)
    return Response(content=_last_stl, media_type="application/octet-stream",
                    headers={"Content-Disposition": "attachment; filename=model.stl"})


@app.post("/share")
async def share(body: dict):
    code = body.get("code", "")
    encoded = urllib.parse.quote(code)
    return {"editor_url": f"https://editor.openscad.org/?code={encoded}"}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s  %(levelname)s  %(message)s",
        level=logging.INFO,
    )
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
