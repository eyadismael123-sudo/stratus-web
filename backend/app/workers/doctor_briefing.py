"""Doctor Morning Briefing worker.

Runs at 8am per doctor's local timezone (called by a cron job).

Pipeline:
  1. Fetch all users with an active Doctor Morning Briefing subscription
  2. For each doctor: pull clinical news from PubMed + NewsAPI
  3. Format into a concise briefing via Claude (Haiku — fast + cheap)
  4. Deliver via Telegram (or log if not configured)

Run manually:
  python -m app.workers.doctor_briefing
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from anthropic import Anthropic

from app.config import settings
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)

DOCTOR_BRIEFING_SLUG = "doctor-morning-briefing"

_anthropic_client: Anthropic | None = None


def _get_anthropic() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


# ─── News fetching ──────────────────────────────────────────────────────────


def fetch_pubmed_headlines(specialty: str, max_results: int = 5) -> list[dict]:
    """Fetch recent PubMed articles for a specialty. No API key required."""
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    try:
        search_resp = httpx.get(
            search_url,
            params={
                "db": "pubmed",
                "term": f"{specialty}[MeSH Major Topic]",
                "retmax": max_results,
                "sort": "pub+date",
                "retmode": "json",
                "datetype": "pdat",
                "reldate": 7,  # last 7 days
            },
            timeout=10.0,
        )
        search_resp.raise_for_status()
        ids = search_resp.json().get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        summary_resp = httpx.get(
            summary_url,
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            timeout=10.0,
        )
        summary_resp.raise_for_status()
        result_data = summary_resp.json().get("result", {})

        articles = []
        for pmid in ids:
            item = result_data.get(pmid, {})
            if not item or not item.get("title"):
                continue
            authors = item.get("authors", [])
            articles.append({
                "title": item["title"].rstrip("."),
                "source": item.get("source", ""),
                "pub_date": item.get("pubdate", ""),
                "author": authors[0].get("name", "") if authors else "",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })

        return articles

    except Exception:
        logger.exception("PubMed fetch failed for specialty=%s", specialty)
        return []


def fetch_health_news(query: str) -> list[dict]:
    """Fetch general health news headlines via NewsAPI. Requires NEWS_API_KEY."""
    if not settings.news_api_key:
        return []

    try:
        resp = httpx.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 5,
                "apiKey": settings.news_api_key,
            },
            timeout=10.0,
        )
        resp.raise_for_status()

        return [
            {
                "title": a.get("title", ""),
                "source": a.get("source", {}).get("name", ""),
                "pub_date": (a.get("publishedAt") or "")[:10],
                "url": a.get("url", ""),
                "description": (a.get("description") or "")[:150],
            }
            for a in resp.json().get("articles", [])
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]

    except Exception:
        logger.exception("NewsAPI fetch failed for query=%s", query)
        return []


# ─── Briefing formatter ─────────────────────────────────────────────────────


def format_briefing(
    doctor_name: str,
    specialty: str,
    region: str,
    pubmed_articles: list[dict],
    news_articles: list[dict],
) -> str:
    """Format raw news into a concise morning briefing via Claude Haiku."""
    all_articles = pubmed_articles + news_articles

    if not all_articles:
        today = datetime.now(timezone.utc).strftime("%A, %B %d")
        return f"Good morning, Dr. {doctor_name}. {today} — no major updates in {specialty} overnight. Clear schedule to focus on your patients."

    raw_sections: list[str] = []

    if pubmed_articles:
        raw_sections.append(
            "RECENT RESEARCH (PubMed, last 7 days):\n"
            + "\n".join(
                f"- {a['title']} ({a['source']}, {a['pub_date']})"
                for a in pubmed_articles
            )
        )

    if news_articles:
        raw_sections.append(
            "CLINICAL NEWS:\n"
            + "\n".join(
                f"- {a['title']} ({a['source']}, {a['pub_date']})"
                + (f"\n  {a['description']}" if a.get("description") else "")
                for a in news_articles
            )
        )

    today = datetime.now(timezone.utc).strftime("%A, %B %d")
    raw_content = "\n\n".join(raw_sections)

    prompt = f"""You are writing a morning briefing for Dr. {doctor_name}, a {specialty} specialist practicing in {region}.

Today is {today}.

Raw clinical information gathered this morning:

{raw_content}

Write a concise morning briefing in plain text (no markdown symbols, no bullet dashes).
Structure:
- One-line greeting with today's date
- 2-3 short paragraphs covering the most clinically relevant updates
- One practical takeaway for their day

Tone: collegial, sharp, no fluff. Like a trusted colleague over morning coffee. Under 200 words."""

    if not settings.anthropic_api_key:
        logger.warning("No Anthropic API key — using fallback briefing format")
        return _fallback_briefing(doctor_name, specialty, all_articles)

    try:
        message = _get_anthropic().messages.create(
            model="claude-haiku-4-5-20251001",  # fast + cheap for daily cron
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    except Exception:
        logger.exception("Claude formatting failed — falling back to raw format")
        return _fallback_briefing(doctor_name, specialty, all_articles)


def _fallback_briefing(
    doctor_name: str,
    specialty: str,
    articles: list[dict],
) -> str:
    """Plain-text fallback when Claude is unavailable."""
    today = datetime.now(timezone.utc).strftime("%A, %B %d")
    lines = [f"Good morning, Dr. {doctor_name} — {today}", "", f"Today in {specialty}:"]
    for a in articles[:5]:
        lines.append(f"{a['title']} ({a.get('source', '')})")
    return "\n".join(lines)


# ─── Delivery ───────────────────────────────────────────────────────────────


def deliver_briefing(doctor: dict, briefing: str) -> None:
    """Send the briefing via the doctor's configured delivery channel."""
    config = doctor.get("config") or {}
    channel = config.get("delivery_channel", "telegram")
    name = doctor.get("full_name", "Doctor")

    if channel == "telegram":
        chat_id = config.get("telegram_chat_id")
        if not chat_id:
            logger.warning("No telegram_chat_id for Dr. %s — skipping", name)
            return
        _send_telegram(chat_id, briefing)
    else:
        # Email delivery — add when email service is configured
        logger.info("Delivery channel '%s' not yet wired for Dr. %s", channel, name)


def _send_telegram(chat_id: str, text: str) -> None:
    """POST a message to Telegram Bot API."""
    if not settings.telegram_bot_token:
        # Print so we can verify output during development
        logger.warning("TELEGRAM_BOT_TOKEN not set — printing briefing to stdout")
        print(f"\n{'='*60}\nBriefing for chat_id={chat_id}:\n{text}\n{'='*60}\n")
        return

    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10.0,
        )
        resp.raise_for_status()
        logger.info("Briefing delivered to Telegram chat_id=%s", chat_id)
    except Exception:
        logger.exception("Telegram delivery failed for chat_id=%s", chat_id)


# ─── Active doctors ─────────────────────────────────────────────────────────


def get_active_doctors() -> list[dict]:
    """Fetch all users with an active Doctor Morning Briefing subscription."""
    db = get_service_client()

    result = (
        db.table("user_agents")
        .select(
            "id, config, user_id, "
            "profiles(full_name, email, timezone), "
            "agent_templates(slug)"
        )
        .eq("is_active", True)
        .eq("status", "active")
        .is_("deleted_at", "null")
        .execute()
    )

    doctors = []
    for row in result.data or []:
        template = row.get("agent_templates") or {}
        if template.get("slug") != DOCTOR_BRIEFING_SLUG:
            continue

        profile = row.get("profiles") or {}
        doctors.append({
            "agent_id": row["id"],
            "user_id": row["user_id"],
            "full_name": profile.get("full_name", "Doctor"),
            "email": profile.get("email", ""),
            "timezone": profile.get("timezone", "Asia/Dubai"),
            "config": row.get("config") or {},
        })

    return doctors


# ─── Orchestrator ────────────────────────────────────────────────────────────


def run_doctor_briefing() -> None:
    """Main entry point — called by the cron job at 8am per doctor's timezone."""
    logger.info("Doctor Morning Briefing worker starting")
    doctors = get_active_doctors()

    if not doctors:
        logger.info("No active doctors found — nothing to do")
        return

    logger.info("Generating briefings for %d doctor(s)", len(doctors))

    for doctor in doctors:
        config = doctor["config"]
        specialty = config.get("specialty", "general medicine")
        region = config.get("region", "UAE")
        name = doctor["full_name"]

        logger.info("Processing Dr. %s (specialty=%s, region=%s)", name, specialty, region)

        pubmed_articles = fetch_pubmed_headlines(specialty)
        news_articles = fetch_health_news(f"{specialty} clinical medicine {region}")

        logger.info(
            "Fetched %d PubMed + %d news articles for Dr. %s",
            len(pubmed_articles), len(news_articles), name,
        )

        briefing = format_briefing(name, specialty, region, pubmed_articles, news_articles)
        deliver_briefing(doctor, briefing)

        logger.info("Briefing complete for Dr. %s", name)

    logger.info("Doctor Morning Briefing worker finished")


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO, format="%(levelname)s %(name)s — %(message)s")
    run_doctor_briefing()
