"""Human-feel layer for agent responses.

Controls quiet hours per client timezone.
Typing delays are handled in whatsapp/client.py.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

QUIET_START = 23  # 11pm
QUIET_END = 6     # 6am


def is_quiet_hours(timezone_str: str) -> bool:
    """Return True if it's currently outside messaging hours for this client.

    Quiet window: 23:00–06:00 in the client's local timezone.
    """
    try:
        tz = ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, Exception):
        tz = ZoneInfo("Asia/Dubai")

    local_hour = datetime.now(tz).hour
    return local_hour >= QUIET_START or local_hour < QUIET_END


def local_hour(timezone_str: str) -> int:
    """Return current hour in the client's local timezone."""
    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        tz = ZoneInfo("Asia/Dubai")
    return datetime.now(tz).hour


def familiarity_prefix(level: int, name: str) -> str:
    """Return a greeting prefix based on familiarity_level (0–5).

    0-1: formal ("Dr. {name}")
    2-3: semi-formal ("Doctor")
    4-5: casual (first name if available)
    """
    if level <= 1:
        return f"Dr. {name}"
    if level <= 3:
        return "Doctor"
    return name.split()[0] if name else "Doctor"
