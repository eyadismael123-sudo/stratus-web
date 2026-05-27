"""3D Print Agent — Telegram bot.

State machine per customer conversation:
  idle → collecting → generating → confirming → done

Three input paths:
  text  → Claude brief extraction → Tripo text_to_model
  voice → Whisper transcription   → text path
  photo → Claude vision           → Tripo image_to_model (or enriched text_to_model)

Run locally (polling mode — no ngrok needed):
  cd backend
  python -m app.agents.print3d.agent

Production (VPS, webhook mode):
  Set WEBHOOK_URL env var → bot switches to webhook automatically.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random

from dotenv import load_dotenv

load_dotenv()
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.agents.print3d.formatter import (
    cancelled_message,
    confirmation_sent_message,
    cousin_notification,
    error_message,
    generating_message,
    photo_caption,
    quote_fallback,
    vision_analysing_message,
    voice_transcribing_message,
)
from app.agents.print3d.core import (
    ConversationState,
    _extract_brief,
    _build_generation_prompt,
    _download,
    _upload_to_public_url,
    run_vision,
)
from app.agents.print3d.meshy import generate_from_image, generate_from_text
from app.agents.print3d.quoter import calculate_quote
from app.agents.print3d.slicer import slice_model

logger = logging.getLogger(__name__)

# ── Required env vars ─────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MESHY_API_KEY      = os.environ["MESHY_API_KEY"]
_cousin_chat_raw   = os.getenv("COUSIN_TELEGRAM_CHAT_ID", "")
COUSIN_CHAT_ID     = int(_cousin_chat_raw) if _cousin_chat_raw.strip().lstrip("-").isdigit() else None

# ── Optional ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WEBHOOK_URL    = os.getenv("WEBHOOK_URL", "")  # empty = polling mode (local)


# chat_id → state
_states: dict[int, ConversationState] = {}


def _state(chat_id: int) -> ConversationState:
    if chat_id not in _states:
        _states[chat_id] = ConversationState()
    return _states[chat_id]


# ── Handlers ─────────────────────────────────────────────────────────────────

# ── Handlers ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset conversation and greet the customer."""
    chat_id = update.effective_chat.id
    _states[chat_id] = ConversationState()
    await update.message.reply_text(
        "مرحبا! / Welcome! 👋\n"
        "\n"
        "Tell me what you'd like to 3D print — text, voice note, or a photo.\n"
        "\n"
        "أخبرني ما تريد طباعته — نص أو صوت أو صورة"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plain text messages."""
    chat_id = update.effective_chat.id
    state   = _state(chat_id)
    text    = update.message.text.strip()

    # If confirming, any text = change request — restart collection
    # (Confirm/Cancel are handled by inline button callbacks, not text)
    if state.step == "confirming":
        state.step  = "idle"
        state.brief = {}

    await _process_text_brief(update, context, state, text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Transcribe voice message (Whisper) then process as text."""
    if not OPENAI_API_KEY:
        await update.message.reply_text(
            "Voice messages aren't enabled yet. Please type your request."
        )
        return

    await update.message.reply_text(voice_transcribing_message())

    # Download voice file from Telegram
    tg_file   = await context.bot.get_file(update.message.voice.file_id)
    voice_raw = await tg_file.download_as_bytearray()

    # Transcribe with Whisper (language=None → auto-detect Arabic/English)
    from openai import AsyncOpenAI
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    transcript = await openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=("voice.ogg", bytes(voice_raw), "audio/ogg"),
        language=None,
    )
    text = transcript.text.strip()
    logger.info("Voice transcribed (chat_id=%s): %s", update.effective_chat.id, text[:100])

    chat_id = update.effective_chat.id
    state   = _state(chat_id)
    await _process_text_brief(update, context, state, text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run Claude vision on the photo, then generate with Tripo image_to_model."""
    chat_id = update.effective_chat.id
    state   = _state(chat_id)
    caption = update.message.caption or ""

    await update.message.reply_text(vision_analysing_message())

    # Telegram provides multiple sizes — take the largest
    photo      = update.message.photo[-1]
    tg_file    = await context.bot.get_file(photo.file_id)
    image_url  = tg_file.file_path  # Telegram CDN URL (contains bot token — download first)

    # Download bytes so vision can use base64 (CDN URL unreliable for direct Claude access)
    image_bytes = await _download(image_url)
    vision = await run_vision(image_bytes or b"", caption)

    if vision.get("refused"):
        await update.message.reply_text(vision.get("reason", "We can't process that request."))
        return

    # Build brief from vision output — no clarifying questions, always proceed
    state.brief = {
        "object":          vision.get("object_id", "custom object"),
        "dimensions":      vision.get("dimensions_hint", "~15cm"),
        "material":        "PLA",
        "style":           "realistic",
        "notes":           caption,
        "_texture_prompt": vision.get("texture_prompt", ""),   # Sonnet's surface-by-surface prediction
        "_image_url":      image_url,    # Telegram CDN URL — pipeline downloads+re-uploads for Meshy
    }

    await _run_pipeline(update, context, state)


# ── Core pipeline ──────────────────────────────────────────────────────────────

async def _process_text_brief(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    state: ConversationState,
    text: str,
) -> None:
    """Extract brief from text, ask a follow-up if needed, else kick off pipeline."""
    # Append customer message to history before calling Claude
    state.history.append({"role": "user", "content": text})

    result = await asyncio.to_thread(_extract_brief, state.history)

    if not result.get("ready"):
        state.step  = "collecting"
        # Merge new partial brief into existing — never lose earlier context
        merged = {**state.brief, **{k: v for k, v in result.get("brief", {}).items() if v}}
        state.brief = merged
        question = result.get("clarifying_question", "Could you give me a bit more detail?")
        # Append bot reply to history so Claude sees the full back-and-forth next turn
        state.history.append({"role": "assistant", "content": question})
        await update.message.reply_text(question)
        return

    state.brief = result.get("brief", {})
    await _run_pipeline(update, context, state)


async def _run_pipeline(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    state: ConversationState,
) -> None:
    """Generate model → slice → quote → send preview photo + inline buttons."""
    state.step = "generating"
    chat_id = update.effective_chat.id

    try:
        # Best-effort status message — ignore if Telegram times out
        try:
            await update.message.reply_text(generating_message())
        except Exception:
            pass
        # ── 1. Generate 3D model ───────────────────────────────────────────
        tg_image_url = state.brief.get("_image_url")

        if tg_image_url:
            # Photo path: download from Telegram CDN then re-upload to a public host.
            # Telegram CDN URLs contain the bot token and Meshy cannot fetch them directly.
            # Combine: Meshy sees actual photo pixels for geometry reconstruction,
            # Sonnet's texture_prompt guides colours + all unseen surfaces.
            image_bytes    = await _download(tg_image_url)
            texture_prompt = state.brief.get("_texture_prompt", "")
            public_url: str | None = None

            if image_bytes:
                public_url = await _upload_to_public_url(image_bytes)

            if image_bytes and public_url:
                model = await generate_from_image(
                    image_url=public_url,
                    api_key=MESHY_API_KEY,
                    texture_prompt=texture_prompt,
                )
            else:
                logger.warning("Image unavailable — falling back to text-to-3d")
                generation_prompt = await asyncio.to_thread(
                    _build_generation_prompt, state.brief
                )
                model = await generate_from_text(generation_prompt, MESHY_API_KEY)
        else:
            # Text/voice path — build an optimised prompt from the brief
            generation_prompt = await asyncio.to_thread(
                _build_generation_prompt, state.brief
            )
            model = await generate_from_text(generation_prompt, MESHY_API_KEY)

        state.model_result = model

        # ── 2. Slice the model ─────────────────────────────────────────────
        slice_result = await asyncio.to_thread(
            slice_model,
            model["model_url"],
            state.brief.get("material", "PLA"),
            state.brief.get("dimensions", ""),
        )

        # ── 3. Calculate quote ─────────────────────────────────────────────
        quote = calculate_quote(slice_result.grams, slice_result.print_hours)
        state.quote_result = quote

        # ── 4. Build inline keyboard ───────────────────────────────────────
        # Confirm and Cancel use callback_data; View in 3D is a URL button.
        keyboard = [
            [
                InlineKeyboardButton(
                    f"✅ Confirm — AED {quote.total_aed:.0f}",
                    callback_data="confirm",
                ),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
            ],
        ]
        glb_url = model.get("glb_url", "")
        if glb_url:
            from urllib.parse import quote as url_quote
            viewer_url = f"https://gltf.report/?model={url_quote(glb_url, safe='')}"
            keyboard.append([
                InlineKeyboardButton("🔄 View in 3D", url=viewer_url)
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)

        caption = photo_caption(
            state.brief, quote.grams, quote.print_hours, quote.total_aed
        )

        # ── 5. Send preview photo with caption + buttons ───────────────────
        preview_url = model.get("preview_url", "")
        if preview_url:
            preview_bytes = await _download(preview_url)
            if preview_bytes:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=preview_bytes,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup,
                )
                state.step = "confirming"
                return

        # Fallback: no preview — send text quote with buttons
        await update.message.reply_text(
            quote_fallback(state.brief, quote.grams, quote.print_hours, quote.total_aed),
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
        state.step = "confirming"

    except Exception as e:
        logger.exception("Pipeline failed for chat_id=%s: %s", chat_id, e)
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Error: {e}")
        except Exception:
            pass
        state.step = "idle"


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button taps (confirm / cancel)."""
    query   = update.callback_query
    chat_id = update.effective_chat.id
    state   = _state(chat_id)

    # Always acknowledge the tap to remove the loading spinner on the button
    await query.answer()

    if query.data == "confirm":
        if state.step != "confirming" or state.quote_result is None:
            await query.edit_message_caption(
                caption="Session expired — please send a new request.",
                reply_markup=None,
            )
            return
        await _confirm_order(update, context, state)

    elif query.data == "cancel":
        state.step    = "idle"
        state.brief   = {}
        state.history = []
        # Edit the photo caption to show cancelled — removes buttons cleanly
        try:
            await query.edit_message_caption(
                caption=cancelled_message(),
                reply_markup=None,
            )
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=cancelled_message())


async def _confirm_order(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    state: ConversationState,
) -> None:
    """Customer said YES — notify cousin and confirm to customer."""
    order_id      = str(random.randint(1000, 9999))
    customer_name = update.effective_chat.full_name or "Customer"
    quote         = state.quote_result

    notification = cousin_notification(
        order_id=order_id,
        brief=state.brief,
        customer_name=customer_name,
        grams=quote.grams,
        print_hours=quote.print_hours,
        total_aed=quote.total_aed,
    )

    # Text notification to cousin
    await context.bot.send_message(chat_id=COUSIN_CHAT_ID, text=notification)

    # Send the model file URL (OBJ from Meshy) — cousin can import into Bambu Studio
    # TODO: replace with actual .3mf once OrcaSlicer CLI is installed on VPS
    model_url = state.model_result.get("model_url")
    if model_url:
        await context.bot.send_message(
            chat_id=COUSIN_CHAT_ID,
            text=f"Model file (OBJ): {model_url}",
        )

    # Confirm to customer
    await update.message.reply_text(confirmation_sent_message(quote.total_aed))
    state.step = "done"


# ── Entry point ────────────────────────────────────────────────────────────────

_PID_FILE = "/tmp/print3d_bot.pid"


def _kill_existing_instance() -> None:
    """Kill any previously running instance of this bot using the PID file."""
    import signal

    if not os.path.exists(_PID_FILE):
        return
    try:
        with open(_PID_FILE) as f:
            old_pid = int(f.read().strip())
        if old_pid != os.getpid():
            os.kill(old_pid, signal.SIGTERM)
            logger.info("Killed previous bot instance (pid=%s)", old_pid)
    except (ProcessLookupError, ValueError):
        pass  # process already gone
    finally:
        try:
            os.remove(_PID_FILE)
        except FileNotFoundError:
            pass


def _write_pid_file() -> None:
    with open(_PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
        level=logging.INFO,
    )

    # Kill any existing instance before starting — prevents Telegram conflict errors
    _kill_existing_instance()
    _write_pid_file()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_callback))  # inline button taps
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    if WEBHOOK_URL:
        # Production mode — Telegram pushes updates to our server
        logger.info("Starting webhook mode at %s", WEBHOOK_URL)
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            webhook_url=WEBHOOK_URL,
        )
    else:
        # Local development — bot polls Telegram every few seconds, no ngrok needed
        logger.info("Starting polling mode (local dev)...")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
