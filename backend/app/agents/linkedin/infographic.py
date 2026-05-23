"""LinkedIn Infographic Generator.

Extracts key points from a post using Claude Haiku, renders a chic dark
HTML slide (1080x1080), and screenshots it with Playwright.

Returns raw PNG bytes — the caller sends them via Telegram sendPhoto.
"""

from __future__ import annotations

import asyncio
import json
import logging

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_SANS = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def _extract_key_points(topic: str, post_text: str) -> dict:
    """Use Haiku to pull a headline + 3-4 punchy key points from the post."""
    if not settings.anthropic_api_key:
        return {"headline": topic, "points": [post_text[:120]]}

    prompt = (
        f'Topic: "{topic}"\n\nPost:\n{post_text}\n\n'
        "Create a JSON object for a chic infographic slide with:\n"
        '  "headline": one punchy, bold statement (max 10 words) that captures the post\'s core insight\n'
        '  "label": 2-3 word category label (e.g. "LEADERSHIP", "INDUSTRY INSIGHT", "CAREER GROWTH")\n'
        '  "points": array of 3-4 short punchy insights from the post (max 15 words each)\n\n'
        "Rules: no generic platitudes, make each point feel specific and credible. "
        "Return ONLY valid JSON, no markdown."
    )

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
            return {
                "headline": str(data.get("headline", topic))[:80],
                "label": str(data.get("label", "INSIGHT"))[:30].upper(),
                "points": [str(p)[:120] for p in data.get("points", [])[:4]],
            }
    except Exception:
        logger.exception("Infographic key point extraction failed")

    return {"headline": topic, "label": "INSIGHT", "points": []}


def _render_html(content: dict, author_name: str, author_field: str) -> str:
    """Build the 1080x1080 HTML slide."""
    headline = content.get("headline", "")
    label = content.get("label", "INSIGHT")
    points = content.get("points", [])

    # Escape HTML special chars
    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    points_html = "".join(
        f'<div class="point"><span class="num">0{i}</span>'
        f'<span class="pt">{esc(p)}</span></div>'
        for i, p in enumerate(points, 1)
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@400;500;600&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  width:1080px;height:1080px;
  background:#0a0a10;
  font-family:'Inter',{_SANS};
  color:#f0f0f0;
  display:flex;flex-direction:column;
  padding:88px 88px 72px;
  position:relative;overflow:hidden;
}}
.glow{{
  position:absolute;top:-280px;right:-280px;
  width:700px;height:700px;
  background:radial-gradient(circle,rgba(255,214,10,.07) 0%,transparent 65%);
  pointer-events:none;
}}
.glow2{{
  position:absolute;bottom:-200px;left:-200px;
  width:500px;height:500px;
  background:radial-gradient(circle,rgba(80,80,180,.06) 0%,transparent 65%);
  pointer-events:none;
}}
.label{{
  font-size:13px;font-weight:600;letter-spacing:3px;
  text-transform:uppercase;color:#FFD60A;
  margin-bottom:28px;
}}
.headline{{
  font-family:'Playfair Display',Georgia,serif;
  font-size:54px;line-height:1.12;color:#ffffff;
  margin-bottom:44px;max-width:820px;
}}
.bar{{
  width:56px;height:3px;background:#FFD60A;
  margin-bottom:48px;border-radius:2px;
}}
.points{{flex:1;display:flex;flex-direction:column;gap:28px;justify-content:center}}
.point{{display:flex;align-items:flex-start;gap:22px}}
.num{{
  font-size:12px;font-weight:700;color:#FFD60A;
  min-width:26px;padding-top:5px;letter-spacing:1px;
}}
.pt{{
  font-size:21px;line-height:1.55;
  color:rgba(240,240,240,.88);font-weight:400;
}}
.footer{{
  display:flex;justify-content:space-between;align-items:flex-end;
  margin-top:48px;padding-top:24px;
  border-top:1px solid rgba(255,255,255,.08);
}}
.author-name{{font-size:15px;font-weight:600;color:#f0f0f0}}
.author-field{{font-size:13px;color:rgba(255,255,255,.38);margin-top:4px}}
.wm{{font-size:11px;color:rgba(255,255,255,.16);letter-spacing:2px;text-transform:uppercase}}
</style>
</head>
<body>
  <div class="glow"></div>
  <div class="glow2"></div>
  <div class="label">{esc(label)}</div>
  <div class="headline">{esc(headline)}</div>
  <div class="bar"></div>
  <div class="points">{points_html}</div>
  <div class="footer">
    <div>
      <div class="author-name">{esc(author_name)}</div>
      <div class="author-field">{esc(author_field)}</div>
    </div>
    <div class="wm">Stratus</div>
  </div>
</body>
</html>"""


def _screenshot_sync(html: str) -> bytes:
    """Render HTML and return PNG bytes (runs synchronously — call via asyncio.to_thread)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(600)  # let Google Fonts settle
        img = page.screenshot(type="png")
        browser.close()
        return img


async def generate_infographic(
    topic: str,
    post_text: str,
    author_name: str,
    author_field: str,
) -> bytes | None:
    """Main entry point — returns PNG bytes or None on failure."""
    try:
        content = await asyncio.to_thread(_extract_key_points, topic, post_text)
        html = _render_html(content, author_name, author_field)
        img_bytes = await asyncio.to_thread(_screenshot_sync, html)
        return img_bytes
    except Exception:
        logger.exception("generate_infographic failed for topic=%r", topic)
        return None
