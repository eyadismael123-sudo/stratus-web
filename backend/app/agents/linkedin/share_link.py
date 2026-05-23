"""LinkedIn share URL builder — pre-fills the post text in the LinkedIn composer."""
from __future__ import annotations

from urllib.parse import quote


def build_linkedin_url(post_text: str) -> str:
    """Return a LinkedIn share URL with post_text pre-filled in the composer."""
    encoded = quote(post_text, safe="")
    return f"https://www.linkedin.com/feed/?shareActive=true&text={encoded}"
