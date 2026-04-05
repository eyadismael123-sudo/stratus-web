"""Research pipeline for the Brief (Doctor Research) agent.

Two sources:
1. PubMed E-utilities API — recent peer-reviewed literature (no key required)
2. Grok API (xAI) — real-time X/Twitter clinical signals (requires GROK_API_KEY)

Each returns a list of article/signal dicts that the formatter receives.
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_PUBMED_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
_GROK_API = "https://api.x.ai/v1/chat/completions"


def fetch_pubmed(
    specialty: str,
    clinical_focus: list[str],
    trusted_journals: list[str],
    dislikes: list[str],
    max_results: int = 8,
) -> list[dict]:
    """Fetch recent PubMed articles matching the doctor's profile.

    Builds a targeted MeSH query combining specialty + focus areas,
    then filters out article types the doctor dislikes.
    """
    focus_terms = " OR ".join(f'"{f}"' for f in clinical_focus[:3]) if clinical_focus else ""
    query = f"{specialty}[MeSH Major Topic]"
    if focus_terms:
        query = f"({query}) AND ({focus_terms})"

    # Exclude disliked study types
    for dislike in dislikes:
        if "review" in dislike.lower():
            query += " NOT Review[pt]"
        if "animal" in dislike.lower():
            query += " NOT (animals[MeSH] NOT humans[MeSH])"

    try:
        search_resp = httpx.get(
            _PUBMED_SEARCH,
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "sort": "pub+date",
                "retmode": "json",
                "datetype": "pdat",
                "reldate": 14,  # last 2 weeks
            },
            timeout=12.0,
        )
        search_resp.raise_for_status()
        ids = search_resp.json().get("esearchresult", {}).get("idlist", [])

        if not ids:
            logger.info("PubMed returned 0 results for specialty=%s", specialty)
            return []

        summary_resp = httpx.get(
            _PUBMED_SUMMARY,
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            timeout=12.0,
        )
        summary_resp.raise_for_status()
        result_data = summary_resp.json().get("result", {})

        articles = []
        for pmid in ids:
            item = result_data.get(pmid, {})
            if not item or not item.get("title"):
                continue

            journal = item.get("source", "")

            # Prioritise trusted journals — put them first
            authors = item.get("authors", [])
            articles.append({
                "pmid": pmid,
                "title": item["title"].rstrip("."),
                "journal": journal,
                "pub_date": item.get("pubdate", ""),
                "first_author": authors[0].get("name", "") if authors else "",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "trusted": any(j.lower() in journal.lower() for j in trusted_journals),
            })

        # Trusted journals float to the top
        articles.sort(key=lambda a: (0 if a["trusted"] else 1))
        return articles[:5]

    except Exception:
        logger.exception("PubMed fetch failed for specialty=%s", specialty)
        return []


async def fetch_grok_signals(specialty: str, clinical_focus: list[str]) -> list[dict]:
    """Use Grok API to pull real-time X/Twitter clinical signals.

    Grok has live access to X — asks it to surface what's being discussed
    in the clinical community around the doctor's specialty today.
    Returns up to 5 signal dicts with title + summary.
    """
    if not settings.grok_api_key:
        logger.info("No GROK_API_KEY — skipping X/Twitter signals")
        return []

    focus = ", ".join(clinical_focus[:3]) if clinical_focus else specialty
    prompt = (
        f"Search X/Twitter and medical news right now for what clinicians are discussing "
        f"in {specialty}, especially around: {focus}. "
        f"Return the top 5 most clinically relevant signals as a JSON array. "
        f"Each item: {{\"title\": \"...\", \"summary\": \"...\", \"source\": \"X/Twitter or news site\"}}. "
        f"No markdown. Only the JSON array."
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _GROK_API,
                headers={
                    "Authorization": f"Bearer {settings.grok_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "grok-3",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.3,
                },
                timeout=20.0,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            # Parse the JSON array Grok returns
            import json
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])

    except Exception:
        logger.exception("Grok fetch failed for specialty=%s", specialty)

    return []
