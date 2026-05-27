"""Telegram message formatter for the 3D print agent.

Keeps all user-facing strings in one place so they're easy to tune.
"""
from __future__ import annotations


def generating_message() -> str:
    """Sent immediately after user submits their request."""
    return (
        "Got it. Generating your 3D model... ⏳\n"
        "\n"
        "This takes about 30–60 seconds."
    )


def photo_caption(
    brief: dict,
    grams: float,
    print_hours: float,
    total_aed: float,
) -> str:
    """Caption attached directly to the preview photo.

    Keeps the experience tight: one message = image + quote + buttons.
    """
    obj      = brief.get("object", "your model")
    material = brief.get("material", "PLA")
    dims     = brief.get("dimensions", "")

    hours   = int(print_hours)
    minutes = int(round((print_hours - hours) * 60))
    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    dims_line = f"📐 {dims}\n" if dims else ""

    return (
        f"*{obj}* — {material}\n"
        f"{dims_line}"
        f"⚖️ {grams:.0f}g  ·  🕐 ~{time_str}\n"
        f"\n"
        f"*AED {total_aed:.0f}*"
    )


def quote_fallback(
    brief: dict,
    grams: float,
    print_hours: float,
    total_aed: float,
) -> str:
    """Fallback text quote if the photo upload failed."""
    obj      = brief.get("object", "your model")
    material = brief.get("material", "PLA")
    dims     = brief.get("dimensions", "")

    hours   = int(print_hours)
    minutes = int(round((print_hours - hours) * 60))
    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    dims_line = f"Dimensions: {dims}\n" if dims else ""

    return (
        f"Object: {obj}\n"
        f"Material: {material}\n"
        f"{dims_line}"
        f"Weight: {grams:.0f}g\n"
        f"Print time: ~{time_str}\n"
        f"\n"
        f"Quote: *AED {total_aed:.0f}*"
    )


def cousin_notification(
    order_id: str,
    brief: dict,
    customer_name: str,
    grams: float,
    print_hours: float,
    total_aed: float,
) -> str:
    """Notification sent to cousin's Telegram when a customer confirms."""
    obj      = brief.get("object", "unknown")
    material = brief.get("material", "PLA")
    dims     = brief.get("dimensions", "")

    hours   = int(print_hours)
    minutes = int(round((print_hours - hours) * 60))
    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    dims_line = f"Dimensions: {dims}\n" if dims else ""

    return (
        f"🖨️ New Order — #{order_id}\n"
        f"\n"
        f"Customer: {customer_name}\n"
        f"Item: {obj}, {material}\n"
        f"{dims_line}"
        f"Weight: {grams:.0f}g\n"
        f"Print time: {time_str}\n"
        f"Quote paid: AED {total_aed:.0f}\n"
        f"\n"
        f"Open the attached file in Bambu Studio → ready to print."
    )


def confirmation_sent_message(total_aed: float) -> str:
    """Sent to customer after they confirm and cousin is notified."""
    return (
        f"Order confirmed! AED {total_aed:.0f} ✓\n"
        f"\n"
        f"Your order is with our team. We'll be in touch when it's ready."
    )


def cancelled_message() -> str:
    """Sent when customer cancels."""
    return "No problem — cancelled. Send a new description whenever you're ready."


def error_message() -> str:
    """Sent when model generation or slicing fails."""
    return (
        "Something went wrong generating your model. "
        "Please try again, or describe your request differently."
    )


def voice_transcribing_message() -> str:
    return "🎤 Transcribing your voice note..."


def vision_analysing_message() -> str:
    return "📷 Analysing your image..."
