"""Shared pipeline logic — prompts, Claude helpers, upload utilities.

Imported by both agent.py (Telegram) and web.py (localhost chatbox).
No Telegram or FastAPI imports here — pure Python + httpx + anthropic.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field

import httpx
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL       = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY       = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
GROK_API_KEY       = os.getenv("GROK_API_KEY", "")
GOOGLE_API_KEY     = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID      = os.getenv("GOOGLE_CSE_ID", "")

_anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)


# ── Conversation state ────────────────────────────────────────────────────────

@dataclass
class ConversationState:
    """Per-customer state held in memory while the conversation is active."""
    step: str = "idle"         # idle | collecting | generating | confirming | done
    brief: dict = field(default_factory=dict)
    model_result: dict = field(default_factory=dict)
    quote_result: object = None
    history: list = field(default_factory=list)


# ── Claude prompts ────────────────────────────────────────────────────────────

_BRIEF_PROMPT = """\
You are a 3D print order intake assistant with the full reasoning ability of an LLM.
Your job is to understand what the customer wants and convert it into a print brief.

Return ONLY valid JSON — no prose, no markdown:
{
  "ready": true or false,
  "brief": {
    "object":     "specific description of the object",
    "function":   "decorative / functional / wearable / prototype / gift",
    "dimensions": "W×H×D in cm — your best estimate based on all available context",
    "color":      "colour + finish",
    "material":   "PLA / PETG / TPU / Resin",
    "style":      "minimalist / organic / industrial / art deco / realistic",
    "notes":      "any extra detail"
  },
  "missing_field":       "only set if truly impossible to proceed",
  "clarifying_question": "one short natural question IF needed, in the customer's language"
}

━━━ USE YOUR INTELLIGENCE ━━━

You are an LLM. Use your world knowledge to fill in the brief intelligently:

• If someone says "elephant the size of a tissue box" → object: "elephant figurine",
  dimensions: "23cm wide × 12cm tall × 12cm deep" (tissue box dimensions), style: "realistic"

• If someone says "phone stand for iPhone 12 Pro Max" → you know the phone is 7.8×16.1cm,
  so dimensions for a stand that holds it: "10cm wide × 12cm tall × 8cm deep"

• If someone says "Eiffel Tower model, 20cm tall" → object: "Eiffel Tower scale model",
  dimensions: "10cm wide × 20cm tall × 10cm deep", style: "realistic"

• If someone says "keychain of a skull" → object: "skull keychain",
  dimensions: "3cm wide × 3cm tall × 1.5cm deep", function: "functional"

• Any real-world object reference, brand, animal, landmark, food item — use your knowledge
  of its actual shape and proportions to infer dimensions if not stated.

• Common size references you should know without asking:
  - tissue box → ~23cm × 12cm × 12cm
  - tennis ball → 6.5cm diameter
  - golf ball → 4.3cm diameter
  - fist → ~10cm × 10cm × 10cm
  - AirPods case → 6cm × 4.5cm × 2cm
  - credit card → 8.5cm × 5.4cm × 0.3cm
  - any phone model → look up its real dimensions

━━━ DEFAULTS (apply silently, never ask) ━━━
  color    → ALWAYS use world knowledge — for every object without exception.
             Research what this thing actually looks like in real life:
             • Real people / characters → exact skin tone, clothing colours, markings,
               numbers, logos, hair, shoes, accessories
             • Animals → exact species colouring, patterns, gradients, markings
             • Vehicles → body colour, trim, wheels, glass, badges, interiors
             • Landmarks / buildings → stone type, weathering, window colour, ironwork
             • Everyday objects → typical material finish (ceramic glaze, brushed steel,
               matte rubber, glossy plastic), dominant colour family, accent colours
             • Fantasy / fictional → infer from lore, media, common depictions
             • Abstract / geometric → describe the surface material and finish that
               would make it look best (e.g. "polished silver metal with mirror finish")
             NEVER output "matte white" — always research and commit to real colours.
  material → "PLA"
  style    → infer from the object (animal = organic, gadget holder = minimalist, etc.)
  function → "decorative"

━━━ WHEN TO SET ready=false AND ASK ━━━
Always ask before going ready=true if:
1. SIZE is unknown — no scale reference in the message AND no universally known real-world size.
   Ask: "How big do you want it? (e.g. 10cm tall, palm-sized, desk size)"
2. The object itself is completely unclear.

If the customer gave a photo with no size hint — always ask for size first.
If they said "small" / "medium" / "large" — that is NOT enough, ask for a number.
Known sizes you can use without asking: keychain (3cm), credit card (8.5cm), AirPods case (6cm),
specific phone models (look up real dimensions), tennis ball (6.5cm), golf ball (4.3cm).
Everything else — ask.

━━━ LANGUAGE ━━━
Respond in the same language the customer used (Arabic or English).
NEVER ask more than one question per turn.
NEVER ask about colour, material, or style — use defaults."""

_VISION_PROMPT = """\
You are analysing one or more photos to prepare a 3D print brief.
The customer wants to 3D PRINT a physical object. Your job is to describe THAT object — \
not everything in the photo.

━━━ PROHIBITED CONTENT — CHECK THIS FIRST ━━━

Before doing anything else, check whether the photo contains or the request implies any of the following:

WEAPONS: firearms, guns, pistols, rifles, knives designed as weapons, swords, brass knuckles, \
tasers, grenades, explosives, silencers, or any part that is primarily a weapon component.

DRONES: unmanned aerial vehicles, quadcopters, FPV drones, drone frames, drone arms, \
propeller guards designed for drones, or any component whose primary purpose is drone assembly.

SEXUAL CONTENT: any human or humanoid figure depicted with exposed genitalia, sexual organs, \
or in an explicitly sexual pose. This includes figurines, statues, or any artistic representation.

If ANY of the above is detected, return ONLY this JSON and nothing else:
{
  "refused": true,
  "reason": "We don't print [weapons / drones / adult content]. If you think this was flagged incorrectly, please contact us."
}

Do NOT attempt to describe, reframe, or partially process prohibited content. Refuse immediately.

━━━ STEP 1: DECIDE WHAT THE CUSTOMER WANTS PRINTED ━━━

Before writing anything else, ask yourself:
"What is the physical object the customer wants to 3D print?"

This is often NOT everything visible in the photo.

CONTAINERS AND HOLDERS — the most common mistake:
When a photo shows a vessel, holder, stand, tray, or bracket WITH something inside/on it,
the customer wants the CONTAINER PRINTED, not the thing sitting inside it.

Treat the container as if it is completely empty when writing texture_prompt.
Describe the cavity as hollow geometry — never describe the object sitting inside it.

  PHOTO SHOWS                     PRINT TARGET          INTERIOR (write this, not the contents)
  ─────────────────────────────────────────────────────────────────────────────────────────────
  candle holder + candle        → candle holder        → "cylindrical opening ~2.2cm dia, 3cm deep"
  vase + flowers                → vase                 → "hollow neck opening ~4cm dia"
  phone stand + phone           → phone stand          → "angled cradle slot 65°, front lip ridge"
  pen cup + pens                → pen/pencil cup       → "open-top cavity ~7cm dia, 10cm deep"
  bowl with fruit               → bowl                 → "hemispherical hollow interior, open top"
  ring dish with ring           → ring dish            → "shallow cavity 1cm deep, raised outer rim"
  plant pot + plant             → plant pot            → "open-top cylinder, drainage hole in base"

  ✗ WRONG: "white pillar candle visible in the centre cavity, cream wax surface, wick at top"
  ✓ RIGHT:  "cylindrical cavity 2.2cm diameter 3cm deep centred on top face, smooth interior walls"

━━━ RETURN FORMAT ━━━

Return ONLY valid JSON:
{
  "object_id":        "the PRINT TARGET — the container/vessel/object itself, never its contents",
  "known_details":    ["detail clearly visible 1", "detail 2", "..."],
  "personal_details": ["plate: only if clearly legible", "custom mod: ...", "wrap colour: ..."],
  "texture_prompt":   "surface-by-surface description of the PRINT TARGET surfaces only — describe as if empty",
  "dimensions_hint":  "ONLY fill this if the customer explicitly stated a size in their caption. Otherwise empty string.",
  "size_question":    "If dimensions_hint is empty, write a short friendly size question. If they gave a size, leave empty string.",
  "printability_notes": "Features that may cause 3D printing issues (floating parts, thin overhangs, mirrored geometry). Suggest adjustments.",
  "best_image_index": 0
}

If multiple photos: set best_image_index to the clearest angle with least background clutter.

━━━ IDENTIFICATION RULES ━━━

CARS — be precise on every point:
• Generation code if known: F32 not "4 Series coupe", G80 not "M3", W176 not "A-Class"
• Body style: state exactly — 2-door coupe / 4-door gran coupe / sedan / convertible / SUV
  (a 2-door fastback coupe and a 4-door gran coupe are NOT the same)
• Trim: M Sport / M Performance / Competition / base — look for aero kit, skirt style, grille finish
• Colour: matte/satin finish = likely vinyl wrap, gloss = paint — say which
• Wheels: identify make/model if possible (OEM M4 Competition, BBS CH-R, Vossen HF-2, OZ Superturismo…)
  Always state: spoke count, spoke style (double/single/mesh/Y-pattern/split), finish, approx diameter
• Mods: carbon fibre parts (splitter, skirts, mirror caps), aftermarket exhaust, lowered suspension
• Plate: ONLY transcribe if every character is unambiguous — otherwise write "plate: [unclear]"

FIGURINES / CHARACTERS:
• Pose: exact stance (standing upright, weight on left foot, arms at sides, etc.)
• Outfit: every garment with material/texture — ribbed knit, leather, denim, satin, fur trim
• Face: facial hair style, hair length/colour, expression if clear
• Footwear: style + material (oxford leather, sneaker, boot)
• Accessories: every visible item — watch, bag, hat, jewellery
• Base: shape, diameter, texture

OTHER OBJECTS:
• Brand/product name if visible on the object
• Material inference from visual texture: brushed metal, injection-moulded plastic, cast iron, etc.
• Mechanical details: slots, ports, hinges, grilles, buttons

━━━ TEXTURE PROMPT RULES ━━━

Write surface-by-surface for ALL surfaces of the PRINT TARGET.
For surfaces the camera cannot see, use world knowledge to predict the appearance. Mark "(predicted)".
Never leave any face unspecified.

If the target is a container/holder: describe interior as empty cavity geometry, not its contents.

EXAMPLES:

Candle holder (ignore the candle inside):
"White ceramic exterior cylinder 8cm tall, smooth matte glaze, slight taper outward toward base;
top face: circular opening 2.2cm diameter, rim edge 3mm rounded bevel; interior: smooth cylindrical
cavity 3cm deep (predicted); base: flat circular disc 5cm diameter, unglazed terracotta ring on
underside (predicted)"

BMW F32 4 Series Coupe M Performance:
"Matte grey vinyl wrap exterior (satin not gloss), gloss black roof panel, M Performance carbon
fibre front splitter sharp leading edge with fine weave pattern, M Performance carbon side skirts
with visible carbon weave, OEM G8x M4 Competition wheels: 5 double-spoke Y-pattern, gloss black
finish, ~19 inch front 20 inch rear staggered, black BMW roundel centre cap, black low-profile tyres;
Shadowline gloss black window surrounds; gloss black twin-kidney grille with black mesh inserts;
full LED angel-eye headlights with corona rings; rear: twin exhaust outlets centre-mounted (predicted),
M Performance diffuser black gloss (predicted), boot lip spoiler (predicted)"

Figurine in burgundy suit:
"Burgundy leather-finish suit jacket front with notch lapels and 2-button closure, back panel
single centre vent; white button-down shirt at collar and double cuffs; white ribbed-knit balaclava
covering full head with fine horizontal ribbing; matte black cap-toe oxford shoes with leather sole
and heel stitch; cream circular base 8cm diameter smooth matte finish"

━━━ HARD RULES ━━━
- NEVER guess a plate number — only write what every character clearly shows
- NEVER confuse body styles (2-door coupe ≠ 4-door gran coupe ≠ sedan)
- dimensions_hint: figurines 15cm tall, cars 20cm long, other objects use world knowledge
- texture_prompt max 350 words — surface-by-surface, no filler
- If multiple photos: combine observations from all angles before writing
- DESCRIBE THE PRINT TARGET ONLY — exclude everything placed inside, on top of, or around it"""

_DESIGN_PROMPT = """\
You are a Meshy 3D generation specialist. Fill in the TEMPLATE below using the brief \
provided. Every slot must be completed — no slot may be left vague or skipped.

━━━ OUTPUT TEMPLATE (fill every slot, return as a single paragraph) ━━━

[STYLE] [OBJECT], [W]cm wide × [H]cm tall × [D]cm deep, [COLOR] [SURFACE TEXTURE] \
surface, [DOMINANT GEOMETRY — 1 sentence describing the main shape], \
[KEY FEATURE 1 — most important structural detail], \
[KEY FEATURE 2 — second structural detail or finish detail], \
[BASE SPEC — flat/wide/stable base description], \
walls [X]mm thick, geometry widens toward base, self-supporting silhouette

━━━ SLOT RULES ━━━

[STYLE]          → minimalist / organic / industrial / art deco / realistic
[OBJECT]         → exact name, no filler words
[W × H × D]      → explicit cm from brief — infer missing axis from object proportions
[COLOR]          → from brief colour field — translate to visual: "matte white" / "glossy black" / "frosted grey"
[SURFACE TEXTURE]→ pick ONE: smooth · ribbed · knurled · brushed · frosted · polished · textured
[DOMINANT GEOMETRY] → describe the primary shape using spatial/sculptural language only
[KEY FEATURE 1]  → most defining structural element (slot, recess, hook, grid, channel, etc.)
[KEY FEATURE 2]  → secondary feature or surface detail (chamfer, taper, rim, pattern, hole)
[BASE SPEC]      → always present — wide flat [shape] base [measurement] for stability
[WALL THICKNESS] → 2mm TPU/Resin · 2.5mm PLA decorative · 3mm PLA functional · 3.5mm PETG

━━━ FUNCTION → GEOMETRY MAPPING ━━━

When the brief includes a function, translate it into geometry in KEY FEATURE slots:

  ashtray        → shallow circular depression 3cm diameter 8mm deep centered on top face,
                   raised outer rim 10mm tall, solid flat base
  candle holder  → cylindrical cavity [match candle diameter, default 2.2cm] centered,
                   cavity depth 3cm, solid base, no lid
  vase           → hollow open-top vessel, tapered neck 4cm diameter, interior cavity
                   widens to base, walls 3mm
  pen/pencil cup → open-top cylinder cavity 7cm diameter 10cm deep, solid base
  phone stand    → angled cradle slot 65 degrees at upper third, front lip ridge 5mm
  ring dish      → shallow bowl 1cm deep, raised outer lip 5mm
  bowl           → hemispherical hollow interior open top, curved walls, solid base ring
  planter pot    → open-top cylinder, drainage hole 1cm diameter centered on base
  lamp shade     → open-top open-bottom cone, lattice or solid walls
  bookend        → L-shaped body, wide flat base flange, vertical plate face

If function is "decorative" or not in this list — skip function geometry, use form only.

━━━ HARD RULES ━━━

• GEOMETRY ONLY — Meshy understands form, not intent. Never write purpose or function.
  ✗ "a stand for watching videos"   ✓ "angled cradle slot at 65 degrees"
  ✗ "useful for storing pens"       ✓ "open-top cylindrical cavity"

• FDM CONSTRAINTS — embed naturally, never list explicitly.
  ✗ "no overhangs, thick walls"     ✓ "walls tapering outward, self-supporting silhouette"

• NEVER USE: "useful" · "for storing" · "designed to" · "elegant" · "high quality" · \
"3D printed" · "FDM" · "printable"

━━━ FEW-SHOT EXAMPLES ━━━

BRIEF:
  Object: phone stand · Dimensions: 12cm tall · Color: matte white · Material: PLA · Style: minimalist

OUTPUT:
  Minimalist phone stand, 8cm wide × 12cm tall × 5cm deep, matte white smooth surface, \
upright rectangular slab body tapering slightly toward top, angled cradle slot 65 degrees \
at upper third cut 8mm deep, front lip ridge 5mm raised to prevent sliding, wide flat \
rectangular base 8cm × 5cm for stability, walls 3mm thick, geometry widens toward base, \
self-supporting silhouette

---

BRIEF:
  Object: pen holder · Dimensions: 10cm tall × 7cm diameter · Color: black glossy · Material: PLA · Style: industrial

OUTPUT:
  Industrial pen holder, 7cm wide × 10cm tall × 7cm deep, black glossy smooth surface, \
open-top cylinder with hexagonal grid cutout pattern covering exterior wall, solid flat \
circular base 7cm diameter, angular chamfered top rim 3mm bevel, base flares 0.5cm \
beyond wall radius for stability, walls 2.5mm thick, geometry widens toward base, \
self-supporting silhouette

---

BRIEF:
  Object: cable clip · Dimensions: 3cm wide × 2cm tall · Color: grey matte · Material: TPU · Style: minimalist

OUTPUT:
  Minimalist cable clip, 3cm wide × 2cm tall × 1.5cm deep, grey matte smooth surface, \
C-shaped body with open channel 8mm diameter running full depth, rounded outer rectangular \
profile, top and bottom edges radiused 2mm, inner channel lip 1mm to retain cable, flat \
rear face 3cm × 2cm for mounting, walls 2mm thick, geometry widens toward base, \
self-supporting silhouette

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY the filled prompt — one paragraph, under 130 words, no preamble, no JSON.

BRIEF:
"""


_FIGURINE_PROMPT = """\
You are a Meshy 3D generation specialist. The object is a HUMAN FIGURINE or CHARACTER FIGURE.
Generate a geometry-first description optimised for Meshy to produce a high-quality 3D figurine.

━━━ OUTPUT TEMPLATE (fill every slot, return as a single paragraph) ━━━

[CHARACTER NAME] figurine, [H]cm tall × [W]cm wide × [D]cm deep, realistic human proportions,
[POSE — one sentence: stance, weight distribution, arm/hand position, head angle],
[FACE — hair colour, hair length/style, facial hair if any, expression],
[UPPER BODY — garment type, collar style, sleeve length],
[LOWER BODY — shorts or trousers: colour, length],
[FOOTWEAR — boot or shoe type and colour],
[ACCESSORIES — gloves, armband, equipment, ball if relevant],
solid oval base [W]cm × [D]cm, flat bottom, self-supporting

━━━ RULES ━━━
• Pose must be stable — feet flat on base, weight centred over feet
• Height = total figure height including base; base adds ~1cm to total
• Never mention walls, material, FDM, overhangs, or printing constraints
• Never use "elegant", "high quality", "beautiful", "intricate", "detailed"
• NEVER invent jersey numbers — only include a number if explicitly stated in the brief
• Under 130 words total

BRIEF:
"""

_FIGURINE_KEYWORDS = frozenset({
    "figurine", "figure", "player", "footballer", "goalkeeper", "striker",
    "athlete", "ronaldo", "messi", "neymar", "statue", "character",
    "soldier", "knight", "warrior", "hero", "villain", "mascot",
    "anime", "chibi", "person", "man", "woman", "boy", "girl",
})


def _is_figurine(brief: dict) -> bool:
    obj = brief.get("object", "").lower()
    return any(kw in obj for kw in _FIGURINE_KEYWORDS)


_VISUAL_RESEARCH_PROMPT = """\
You are a visual research specialist. Your job is to study ANY object — real, fictional,
everyday, or abstract — and produce an exhaustive colour and surface texture brief that
will guide a 3D texturing AI (Meshy) to apply exactly the right appearance.

This applies to EVERYTHING: a coffee mug, a dragon, Cristiano Ronaldo, a chess rook,
a Nike Air Max, a medieval sword, a garden snail, an abstract geometric sculpture.

Research the object thoroughly using all your knowledge and produce a detailed brief
covering every surface. Write in flowing prose, surface by surface.

━━━ WHAT TO COVER ━━━

1. COLOURS & GRADIENTS
   - Name exact colours for every region (not "red" — "deep crimson scarlet", "warm
     ivory with cream undertones", "gunmetal grey with blue-black sheen")
   - Describe gradient transitions: where does one colour fade into another?
   - Identify which colour is dominant vs accent

2. SURFACE MATERIAL & FINISH PER ZONE
   - What material is each surface made of? (glazed ceramic, brushed stainless steel,
     worn leather, smooth silicone, knitted cotton, reptile scales, polished obsidian)
   - Finish type: matte / satin / semi-gloss / high-gloss / metallic / translucent /
     subsurface-scattering (skin, wax, marble)
   - Physical texture: smooth, pored, grainy, fibrous, faceted, pitted, burnished

3. FINE SURFACE DETAILS
   - Text, numbers, logos: exact colour + placement + size relative to object
   - Patterns: describe stripe width, repeat, colour order, orientation
   - Seams, stitching, rivets, panel lines: colour and material
   - Wear, aging, imperfections if appropriate: scratches, patina, dirt accumulation zones

4. SPECULAR & LIGHTING BEHAVIOUR
   - Highly reflective zones (chrome trim, patent leather, wet surfaces, polished metal)
   - Diffuse/flat zones (unglazed pottery, fabric, rubber, raw concrete)
   - Translucent or glowing zones (LED elements, glass, gemstones, amber)

━━━ CRITICAL RULES ━━━
- Cover front, back, top, bottom, sides — every face
- Never say "colourful" or "vibrant" without naming the colour
- If uncertain, reason from world knowledge and commit — do not skip surfaces
- For fictional/fantasy objects, draw from the most widely recognised depiction
- Under 550 words total — dense and specific, no filler

━━━ SPORTS FIGURES — READ THIS FIRST ━━━
Position and role determine kit colour — NEVER assume the iconic team colours apply
to every player. Research the EXACT kit worn by the EXACT position:
- Goalkeepers always wear a DIFFERENT coloured jersey from outfield players.
  Their kit is specifically chosen to contrast with both teams and the referee.
  Research what colour that specific goalkeeper wore in that specific tournament/season —
  do NOT guess or borrow the outfield kit colours.
- Look up the exact tournament/season kit for that player's specific role.
- If a captain: note the armband colour and placement.
- Describe the correct gloves for a goalkeeper (larger, padded, latex grip palm).

Object to research:
"""


async def _web_search_visual_context(subject: str, notes: str) -> str:
    """Search the web via DuckDuckGo for accurate visual details of the subject."""
    search_query = subject
    if notes:
        search_query += f" {notes}"
    search_query += " appearance colors kit"

    try:
        from ddgs import DDGS

        def _ddg_search() -> list[dict]:
            return list(DDGS().text(search_query, max_results=5))

        results = await asyncio.to_thread(_ddg_search)
        if not results:
            return ""

        snippets = "\n\n".join(
            f"[{r.get('title', '')}]\n{r.get('body', '')}"
            for r in results
        )
        logger.info("DDG web search got %d results for: %s", len(results), search_query[:80])
        return snippets
    except Exception as exc:
        logger.warning("DDG web search failed: %s", exc)
        return ""


async def _collect_candidate_images(subject: str, notes: str) -> list[str]:
    """Gather up to 10 candidate image URLs from all sources."""
    import re

    query = f"{subject} {notes}".strip()
    clean_subject = subject.split(",")[0].strip()
    candidates: list[str] = []

    # ── Google Custom Search ──────────────────────────────────────────────────
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": GOOGLE_API_KEY,
                        "cx": GOOGLE_CSE_ID,
                        "q": query,
                        "searchType": "image",
                        "num": 8,
                        "imgSize": "large",
                        "imgType": "photo",
                        "safe": "off",
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    for item in resp.json().get("items", []):
                        url = item.get("link", "")
                        if url and url.startswith("http"):
                            candidates.append(url)
                else:
                    logger.warning("Google CSE returned %s: %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning("Google image search failed: %s", exc)

    # ── Wikimedia Commons ─────────────────────────────────────────────────────
    if len(candidates) < 5:
        # Build ordered queries: most specific first (with color), then progressively broader
        commons_queries = [clean_subject]
        # Include color from notes if present (e.g. "Glacier Silver") for better matches
        import re as _re
        color_match = _re.search(
            r'\b(glacier silver|space grey|space gray|alpine white|black sapphire|'
            r'mineral white|carbon black|estoril blue|long beach blue|san marino blue|'
            r'austin yellow|indianapolis red|lime rock grey)\b',
            notes.lower(),
        )
        if color_match:
            commons_queries.insert(0, f"{clean_subject} {color_match.group(0)}")
        # Extract BMW/Mercedes generation codes from notes for targeted search (e.g. F32, G80, W176)
        gen_code_match = _re.search(r'\b([FGWCEX][0-9]{2,3}[A-Z]?)\b', notes)
        if gen_code_match:
            make = clean_subject.split()[0]  # e.g. "BMW"
            gen_code = gen_code_match.group(1)  # e.g. "F32"
            commons_queries.append(f"{make} {gen_code}")
        # Fallback: first 3 words when full subject is too specific
        short = " ".join(clean_subject.split()[:3])
        if short and short != clean_subject:
            commons_queries.append(short)

        for cq in commons_queries:
            if len(candidates) >= 5:
                break
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://commons.wikimedia.org/w/api.php",
                        params={
                            "action": "query",
                            "generator": "search",
                            "gsrnamespace": 6,
                            "gsrsearch": cq,
                            "gsrlimit": 10,
                            "prop": "imageinfo",
                            "iiprop": "url|mime|thumburl",
                            "iiurlwidth": 640,
                            "format": "json",
                        },
                        headers={"User-Agent": "Stratus3DPrint/1.0 (stratus.ai; contact@stratus.ai)"},
                        timeout=8.0,
                    )
                    if resp.status_code == 200:
                        pages = resp.json().get("query", {}).get("pages", {})
                        before = len(candidates)
                        for page in pages.values():
                            for ii in page.get("imageinfo", []):
                                mime = ii.get("mime", "")
                                if not mime.startswith("image/") or mime == "image/svg+xml":
                                    continue
                                url = ii.get("thumburl") or ii.get("url", "")
                                if url and url not in candidates:
                                    candidates.append(url)
                        logger.info(
                            "Wikimedia Commons '%s': %d new images",
                            cq[:40], len(candidates) - before,
                        )
            except Exception as exc:
                logger.debug("Wikimedia Commons search failed for '%s': %s", cq, exc)

    # ── Wikipedia (article lead images) ───────────────────────────────────────
    if len(candidates) < 5:
        async with httpx.AsyncClient() as client:
            try:
                search_resp = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={"action": "query", "list": "search", "srsearch": clean_subject,
                            "srlimit": 3, "format": "json"},
                    headers={"User-Agent": "Stratus3DPrint/1.0"},
                    timeout=8.0,
                )
                if search_resp.status_code == 200:
                    for result in search_resp.json().get("query", {}).get("search", []):
                        page_title = result["title"].replace(" ", "_")
                        try:
                            s = await client.get(
                                f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}",
                                headers={"User-Agent": "Stratus3DPrint/1.0"},
                                timeout=8.0,
                            )
                            if s.status_code == 200:
                                data = s.json()
                                thumb = (data.get("originalimage", {}).get("source")
                                         or data.get("thumbnail", {}).get("source", ""))
                                if thumb:
                                    candidates.append(thumb)
                        except Exception:
                            pass
            except Exception as exc:
                logger.debug("Wikipedia search failed: %s", exc)

    # ── DuckDuckGo — always run to supplement Wikipedia ──────────────────────
    # Wikipedia Commons has limited coverage of specific trims/colors.
    # DDG finds press shots, enthusiast sites, and review articles with better specificity.
    try:
        from ddgs import DDGS

        def _ddg() -> list[dict]:
            return list(DDGS().images(query, max_results=10))

        ddg_results = await asyncio.to_thread(_ddg)
        ddg_added = 0
        for img in ddg_results:
            url = img.get("image", "")
            if url and re.search(r'\.(jpg|jpeg|png|webp)', url, re.IGNORECASE) and url not in candidates:
                candidates.append(url)
                ddg_added += 1
        if ddg_added:
            logger.info("DDG image search: added %d results", ddg_added)
    except Exception as exc:
        logger.warning("DDG image search failed: %s", exc)

    return candidates


def _commons_thumbnail(url: str, width: int = 400) -> str:
    """Convert a Wikimedia Commons full-res URL to its thumbnail URL."""
    if "/wikipedia/commons/" in url and "/thumb/" not in url:
        # https://upload.wikimedia.org/wikipedia/commons/e/e1/FILE.jpg
        # → https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/FILE.jpg/400px-FILE.jpg
        parts = url.split("/wikipedia/commons/", 1)
        if len(parts) == 2:
            path = parts[1]  # e/e1/FILE.jpg
            filename = path.rsplit("/", 1)[-1]
            return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{path}/{width}px-{filename}"
    return url


async def _fetch_thumbnail(url: str) -> bytes | None:
    """Download a thumbnail for vision evaluation. Returns None on any failure."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                url, timeout=12.0, follow_redirects=True,
                headers={"User-Agent": "Stratus3DPrint/1.0 (stratus.ai; contact@stratus.ai)"},
            )
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ct.startswith("image/") and "svg" not in ct:
                return r.content
    except Exception:
        pass
    return None


_BODY_STYLE_EXCLUSIONS: dict[str, tuple[str, ...]] = {
    # key = requested style keyword → values = URL substrings to reject
    "coupe":       ("cabriolet", "cabrio", "convertible", "roadster", "spyder", "spider", "gran_coupe", "gran-coupe", "grancoupe", "4-door", "4door"),
    "coupé":       ("cabriolet", "cabrio", "convertible", "roadster", "spyder", "spider", "gran_coupe", "gran-coupe", "grancoupe", "4-door", "4door"),
    "convertible": ("_coupe", "-coupe", "gran_coupe", "sedan", "4-door"),
    "cabriolet":   ("_coupe", "-coupe", "gran_coupe", "sedan", "4-door"),
    "sedan":       ("cabriolet", "cabrio", "convertible", "coupe", "roadster"),
    "suv":         ("cabriolet", "cabrio", "convertible", "coupe", "sedan"),
}

# URL color-name substrings that indicate a specific paint color.
# Key = color family; values = URL substrings that imply that color.
_COLOR_INDICATORS: dict[str, tuple[str, ...]] = {
    "blue":   ("_blue", "-blue", "blau", "estoril", "san_marino", "long_beach", "avus", "le_mans", "monte_carlo", "interlagos"),
    "red":    ("_red", "-red", "rot", "imola", "melbourne", "indianapolis", "jalapeno", "mugello"),
    "green":  ("_green", "-green", "gruen", "british_racing"),
    "yellow": ("_yellow", "-yellow", "gelb", "austin", "dakar"),
    "orange": ("_orange", "-orange", "fire", "phoenix"),
    "black":  ("_black", "-black", "schwarz", "carbon_black", "jet_black"),
    "white":  ("_white", "-white", "weiss", "alpine_white", "mineral_white"),
}

_SILVER_TERMS = frozenset({
    "silver", "glacier", "titan", "arktis", "arctic", "sterling",
    "cashmere", "moonstone", "quartz",
})

_WARM_COLORS = frozenset({"blue", "red", "green", "yellow", "orange"})


def _color_from_text(text: str) -> str | None:
    """Return a broad color family if text explicitly names one."""
    t = text.lower()
    if any(w in t for w in _SILVER_TERMS):
        return "silver"
    for color in _WARM_COLORS | {"black", "white"}:
        if color in t:
            return color
    return None


def _body_style_filter(
    candidates: list[str], subject: str, notes: str
) -> tuple[list[str], bool]:
    """Remove URLs whose filenames indicate a wrong body style, trim, or color.

    Returns ``(filtered_candidates, trim_relaxed)`` — ``trim_relaxed=True`` means
    the trim filter had to fall back to M Sport images for geometry coverage.
    Callers should suppress downstream trim-rejection rules in that case.
    """
    combined = f"{subject} {notes}".lower()
    trim_relaxed = False

    # ── Body style ────────────────────────────────────────────────────────────
    for style, exclusions in _BODY_STYLE_EXCLUSIONS.items():
        if style in combined:
            filtered = []
            for url in candidates:
                url_lower = url.lower()
                rejected = next((e for e in exclusions if e in url_lower), None)
                if rejected:
                    logger.info("Body-style pre-filter: excluded '%s' (matched '%s')", url[url.rfind("/")+1:url.rfind("/")+80], rejected)
                else:
                    filtered.append(url)
            candidates = filtered

    # ── Trim level — reject M Sport URLs when M Performance is requested ──────
    # Soft filter: only apply if enough candidates survive (M Sport = same body geometry,
    # just different aero kit — acceptable reference when nothing better exists).
    if "m performance" in combined:
        filtered = []
        msport_rejected: list[str] = []
        for url in candidates:
            ul = url.lower()
            has_perf = "m_performance" in ul or "mperformance" in ul or "m-performance" in ul
            has_sport = (
                "_m-sport" in ul or "_m_sport" in ul or
                "-m-sport" in ul or "-m_sport" in ul or
                "msport" in ul
            )
            if has_sport and not has_perf:
                logger.info("Trim pre-filter: excluded M Sport URL '%s'", url[url.rfind("/")+1:url.rfind("/")+80])
                msport_rejected.append(url)
            else:
                filtered.append(url)
        if len(filtered) < 2 and msport_rejected:
            logger.warning(
                "Trim filter left only %d image(s) — reintroducing %d M Sport image(s) "
                "as geometry reference (same body; texture_prompt handles trim differences)",
                len(filtered), len(msport_rejected),
            )
            candidates = filtered + msport_rejected
            trim_relaxed = True
        else:
            candidates = filtered

    # ── Color — reject obvious wrong-color URLs ───────────────────────────────
    requested_color = _color_from_text(combined)
    if requested_color:
        wrong_colors = {c: v for c, v in _COLOR_INDICATORS.items() if c != requested_color}
        if requested_color == "silver":
            wrong_colors = _COLOR_INDICATORS
        filtered = []
        for url in candidates:
            ul = url.lower()
            reject_color = next(
                (c for c, subs in wrong_colors.items() if any(s in ul for s in subs)),
                None,
            )
            if reject_color:
                logger.info("Color pre-filter: excluded '%s' (looks %s, want %s)", url[url.rfind("/")+1:url.rfind("/")+80], reject_color, requested_color)
            else:
                filtered.append(url)
        candidates = filtered

    return candidates, trim_relaxed


async def _pick_best_images(subject: str, notes: str, candidates: list[str]) -> list[str]:
    """Ask Claude Haiku vision to pick up to 4 diverse-angle images for multi-image-to-3D.

    Downloads thumbnails so Claude can actually see color, angle, and composition
    rather than guessing from URL names. Returns 1–4 URLs covering different angles.
    """
    if not candidates:
        return []

    # Pre-filter by URL filename before spending vision tokens
    candidates, trim_relaxed = _body_style_filter(candidates, subject, notes)
    if not candidates:
        return []

    if len(candidates) == 1:
        return [candidates[0]]

    # Download all thumbnails in parallel (cap at 12 to keep vision payload small)
    limited = candidates[:12]
    thumbs = await asyncio.gather(*[_fetch_thumbnail(u) for u in limited])

    content: list[dict] = []
    valid_indices: list[int] = []
    for i, (url, img_bytes) in enumerate(zip(limited, thumbs)):
        if img_bytes:
            content.append({"type": "text", "text": f"Image {i + 1}:"})
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": _detect_media_type(img_bytes),
                    "data": base64.standard_b64encode(img_bytes).decode(),
                },
            })
            valid_indices.append(i)

    if not valid_indices:
        logger.warning("No thumbnails downloaded — falling back to first candidate")
        return [candidates[0]]

    # M Sport vs M Performance share the same chassis/roofline/doors — only the aero kit
    # differs, which is handled by texture_prompt. Accept M Sport as geometry reference.
    # Only flag truly wrong generations (F80 ≠ F32, etc.).
    _ = trim_relaxed  # acknowledged; rule is now always geometry-friendly
    _trim_rule3 = (
        "Prefer M Performance images if available, but ACCEPT M Sport — "
        "body geometry is essentially identical (same doors, roofline, wheelbase). "
        "texture_prompt handles aero kit differences. "
        "REJECT wrong generation code (e.g. F80 M3 is NOT F32 435i)"
    )

    # Build subject-aware rejection rules
    _is_vehicle = any(w in (subject + " " + notes).lower() for w in (
        "car", "coupe", "sedan", "suv", "convertible", "cabriolet",
        "bmw", "mercedes", "audi", "porsche", "ferrari", "lamborghini",
        "ford", "toyota", "honda", "tesla", "maserati", "bentley",
    ))

    if _is_vehicle:
        _rule1 = (
            "RULE 1 — BODY STYLE (hardest rule):\n"
            "Reject ANY image with a different body style from what is requested.\n"
            '- "coupe" → reject: convertible, cabriolet, sedan, gran coupé (4-door fastback), SUV\n'
            '- "sedan" → reject: coupe, convertible, SUV\n'
            '- "convertible" / "cabriolet" → reject: hardtop coupe, sedan\n'
            "A convertible with roof UP still has wrong roofline + C-pillar — STILL REJECT."
        )
        _rule2 = (
            "RULE 2 — COLOUR (only when a colour is named in notes):\n"
            "Reject ANY image where the car is a DIFFERENT colour from what was requested.\n"
            '  "Glacier Silver" / "silver" → keep: silver, pearl silver, light grey-silver metallic\n'
            '  "Space Grey" → keep: dark grey, gunmetal — reject: silver, blue, black, white\n'
            "When the car is VISUALLY a different color — REJECT IT."
        )
        _rule3 = (
            f"RULE 3 — TRIM / VARIANT:\n"
            f"- {_trim_rule3}\n"
            "- Wrong generation code → reject (e.g. F80 M3 ≠ F82 M4, G22 ≠ F32)\n"
            "- Gran Coupé (4-door) ≠ Coupé (2-door) — treat as body style violation"
        )
    else:
        _rule1 = (
            "RULE 1 — WRONG SUBJECT:\n"
            "Reject any image that clearly shows a different person, character, object, or subject "
            "from what is requested. Accept variations in pose, angle, or kit/costume if the core "
            "subject is identifiably correct."
        )
        _rule2 = (
            "RULE 2 — COLOUR / KIT (only when a specific colour or kit is named in notes):\n"
            "Reject images where the colour or kit is visually incompatible with the request "
            "(e.g. wrong national team kit, wrong jersey colour)."
        )
        _rule3 = (
            "RULE 3 — VARIANT / VERSION:\n"
            "Prefer the exact variant if available. Accept close variants that share the same "
            "underlying geometry or silhouette when better options aren't available."
        )

    content.append({
        "type": "text",
        "text": f"""You are selecting reference photos for multi-angle 3D model reconstruction.

Subject: {subject}
Notes: {notes}

━━━ REJECTION RULES — apply IN ORDER ━━━

{_rule1}

{_rule2}

{_rule3}

RULE 4 — UNUSABLE SHOTS:
Reject: extreme closeups of a single detail, blurry images, illustrations/SVG/CGI renders, "wrong angle" duplicates

━━━ AFTER REJECTION — RANK SURVIVORS ━━━
Pick UP TO 4 images that together cover the most diverse viewpoints.
Each pick must show a DIFFERENT angle — no near-duplicates.

Reply with ONLY the image numbers separated by commas (e.g. "2, 5, 8"). Nothing else.
If NO images survive, reply with "none".""",
    })

    logger.info(
        "Sending %d images to Claude vision for '%s' (trim_relaxed=%s)",
        len(valid_indices), subject[:40], trim_relaxed,
    )
    resp = await asyncio.to_thread(
        _anthropic.messages.create,
        model="claude-haiku-4-5-20251001",
        system="Output ONLY what is explicitly requested — no preamble, no analysis, no explanation.",
        max_tokens=40,
        messages=[{"role": "user", "content": content}],
    )
    raw = resp.content[0].text.strip()
    if raw.lower().startswith("none"):
        logger.info("Claude rejected all candidates for '%s' — no valid images", subject[:40])
        return []

    chosen: list[str] = []
    for token in raw.replace(",", " ").split():
        try:
            idx = int(token) - 1
            if 0 <= idx < len(limited) and limited[idx] not in chosen:
                chosen.append(limited[idx])
        except ValueError:
            pass

    if chosen:
        logger.info(
            "Claude vision picked %d image(s) for '%s': %s",
            len(chosen), subject[:40],
            " | ".join(u[:60] for u in chosen),
        )
        return chosen[:4]

    logger.warning("Claude returned unexpected choice %r — falling back to first valid", raw)
    return [limited[valid_indices[0]]]


async def find_reference_images(subject: str, notes: str = "") -> list[str]:
    """Find up to 4 reference photo URLs covering different angles of the subject.

    Collects candidates from Google, Wikipedia, and DDG, then asks Claude Haiku
    vision to pick the best diverse set for multi-image 3D reconstruction.

    Returns a list of 1–4 public HTTPS URLs Meshy can fetch, or [] if nothing found.
    """
    candidates = await _collect_candidate_images(subject, notes)
    if not candidates:
        return []

    logger.info("Found %d candidate images for '%s'", len(candidates), subject[:50])
    return await _pick_best_images(subject, notes, candidates)


async def build_visual_research(brief: dict) -> str:
    """Produce a detailed colour/texture brief for any object.

    Step 1 — DuckDuckGo web search: gets factually accurate visual details
              (exact kit colours, real product specs, etc.)
    Step 2 — Claude Sonnet: turns web results + world knowledge into an
              exhaustive surface-by-surface texture brief for Meshy.
    """
    subject    = brief.get("object", "")
    color_hint = brief.get("color", "")
    notes      = brief.get("notes", "")

    # Run web search and build query in parallel
    web_context = await _web_search_visual_context(subject, notes)

    query = subject
    if color_hint and color_hint.lower() not in ("matte white", ""):
        query += f" — known colours: {color_hint}"
    if notes:
        query += f". Additional context: {notes}"
    if web_context:
        query += f"\n\n━━━ VERIFIED WEB SEARCH RESULTS (use these as ground truth) ━━━\n{web_context}"

    response = await asyncio.to_thread(
        _anthropic.messages.create,
        model="claude-sonnet-4-6",
        max_tokens=700,
        messages=[{"role": "user", "content": f"{_VISUAL_RESEARCH_PROMPT}{query}"}],
    )
    result = response.content[0].text.strip()
    logger.info("Visual research (%d chars): %s", len(result), result[:120])
    return result


# ── Utilities ─────────────────────────────────────────────────────────────────

def _strip_code_fence(text: str) -> str:
    """Remove ```json ... ``` wrappers that Claude sometimes adds."""
    if text.startswith("```"):
        parts = text.split("```")
        inner = parts[1]
        if inner.startswith("json"):
            inner = inner[4:]
        return inner.strip()
    return text


async def _download(url: str) -> bytes | None:
    """Download bytes from a URL, return None on error."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0)
            resp.raise_for_status()
            return resp.content
    except Exception:
        logger.warning("Failed to download %s", url)
        return None


async def _upload_to_public_url(image_bytes: bytes) -> str | None:
    """Upload image bytes to a public URL that Meshy can fetch.

    Priority order:
      1. Supabase Storage (permanent — uses existing project)
      2. 0x0.st (free, sometimes flaky)
      3. catbox.moe (free fallback)
    """
    # ── 1. Supabase Storage ────────────────────────────────────────────────────
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            bucket   = "print3d-uploads"
            filename = f"photo_{int(time.time() * 1000)}.jpg"
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{SUPABASE_URL}/storage/v1/object/{bucket}/{filename}",
                    headers={
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "image/jpeg",
                    },
                    content=image_bytes,
                    timeout=20.0,
                )
                resp.raise_for_status()
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{filename}"
                logger.info("Uploaded to Supabase: %s", public_url)
                return public_url
        except Exception as e:
            logger.warning("Supabase upload failed: %s — trying free hosts", e)

    # ── 2–3. Free hosts ────────────────────────────────────────────────────────
    free_hosts = [
        ("https://0x0.st",                 "file",         lambda r: r.text.strip()),
        ("https://catbox.moe/user/api.php", "fileToUpload", lambda r: r.text.strip()),
    ]
    async with httpx.AsyncClient() as client:
        for upload_url, field_name, parse in free_hosts:
            try:
                data = {"reqtype": "fileupload"} if "catbox" in upload_url else {}
                resp = await client.post(
                    upload_url,
                    data=data,
                    files={field_name: ("photo.jpg", image_bytes, "image/jpeg")},
                    timeout=20.0,
                )
                resp.raise_for_status()
                public_url = parse(resp)
                if public_url.startswith("http"):
                    logger.info("Uploaded to %s: %s", upload_url, public_url)
                    return public_url
            except Exception as e:
                logger.warning("Upload failed for %s: %s — trying next", upload_url, e)

    logger.error("All upload hosts failed")
    return None


# ── Claude helpers ────────────────────────────────────────────────────────────

def _extract_brief(history: list) -> dict:
    """Call Claude Haiku with conversation history to extract a structured brief."""
    response = _anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=_BRIEF_PROMPT,
        messages=history,
    )
    raw = _strip_code_fence(response.content[0].text.strip())
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Brief extraction returned invalid JSON: %s", raw[:200])
        return {
            "ready": False,
            "clarifying_question": "Could you describe what you want to print?",
        }


def _build_generation_prompt(brief: dict) -> str:
    """Convert a structured brief into an optimised Meshy text-to-3d prompt."""
    if brief.get("_generation_prompt"):
        return brief["_generation_prompt"]

    template = _FIGURINE_PROMPT if _is_figurine(brief) else _DESIGN_PROMPT

    brief_text = (
        f"Object:     {brief.get('object', '')}\n"
        f"Function:   {brief.get('function', '')}\n"
        f"Dimensions: {brief.get('dimensions', '~10-15cm')}\n"
        f"Color:      {brief.get('color', 'matte white')}\n"
        f"Material:   {brief.get('material', 'PLA')}\n"
        f"Style:      {brief.get('style', 'minimalist')}\n"
        f"Notes:      {brief.get('notes', '')}"
    )
    response = _anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": f"{template}{brief_text}"}],
    )
    prompt = response.content[0].text.strip()
    logger.info("Generated Meshy prompt (%d chars): %s", len(prompt), prompt[:120])
    return prompt


def _detect_media_type(data: bytes) -> str:
    """Detect Anthropic-compatible MIME type from image magic bytes."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF8"):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


async def run_vision(images: list[bytes], caption: str) -> dict:
    """Call Claude Sonnet vision on one or more images to extract a print brief.

    Multiple photos = more angles = better texture_prompt accuracy.
    """
    images = [b for b in images if b]
    if not images:
        return {"object_id": "custom object", "texture_prompt": caption or ""}

    content: list[dict] = []
    for img in images:
        media_type = _detect_media_type(img)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.standard_b64encode(img).decode("utf-8"),
            },
        })

    note = f"({len(images)} photos provided — use all angles)" if len(images) > 1 else ""
    content.append({
        "type": "text",
        "text": f"{_VISION_PROMPT}\n\nCustomer caption: {caption or 'none'} {note}".strip(),
    })

    response = await asyncio.to_thread(
        _anthropic.messages.create,
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": content}],
    )
    raw = _strip_code_fence(response.content[0].text.strip())
    try:
        result = json.loads(raw)
        logger.info("Vision — %s, %d photo(s)", result.get("object_id", "?"), len(images))
        return result
    except json.JSONDecodeError:
        logger.warning("Vision returned invalid JSON: %s", raw[:200])
        return {
            "object_id": "custom object",
            "texture_prompt": caption or "",
            "dimensions_hint": "",
            "size_question": "How big do you want this printed? (e.g. 10cm tall, palm-sized, desk ornament)",
        }
