"""Research pipeline for the Brief (Doctor Research) agent.

Two sources:
1. PubMed E-utilities API — recent peer-reviewed literature (no key required)
2. Grok API (xAI) — real-time X/Twitter clinical signals (requires GROK_API_KEY)

PubMed strategy (4-layer fallback to guarantee results):
  Layer 1: Specialty journals + focus terms, 30 days
             (journals define the specialty — no redundant specialty text filter)
  Layer 2: Specialty journals only, 30 days
             (catches papers that don't mention clinical focus terms explicitly)
  Layer 3: Any journal, specialty name + focus terms in text, 60 days
             (broadens beyond curated journals when they're thin)
  Layer 4: Free-text keyword fallback, 90 days
             (last resort — captures anything tangentially relevant)

Why the old code returned 0 results most days:
  - `[MeSH Major Topic]` is invalid for most specialty names
    (e.g. "interventional cardiology" has no such MeSH entry)
  - Requiring specialty name as text inside specialty journals is redundant —
    papers in JACC Cardiovasc Interv don't say "interventional cardiology"
    in every abstract, they just write "TAVI" or "PCI"
  - `reldate: 14` is too short for monthly journals
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_PUBMED_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
_GROK_API = "https://api.x.ai/v1/chat/completions"


# ─── PubMed helpers ───────────────────────────────────────────────────────────


def _dislike_suffix(dislikes: list[str]) -> str:
    suffix = ""
    for dislike in dislikes:
        if "review" in dislike.lower():
            suffix += " NOT Review[pt]"
        if "animal" in dislike.lower():
            suffix += " NOT (animals[MeSH] NOT humans[MeSH])"
    return suffix


def _build_journal_filter(pubmed_abbrevs: list[str]) -> str:
    return " OR ".join(f'"{j}"[jour]' for j in pubmed_abbrevs)


def _build_focus_terms(clinical_focus: list[str]) -> str:
    """Build focus-terms query fragment (Title/Abstract)."""
    return " OR ".join(f'"{f}"[Title/Abstract]' for f in clinical_focus[:3])


def _run_pubmed_query(query: str, max_results: int, reldate: int = 30) -> list[str]:
    """Return a list of PubMed IDs for the given query."""
    try:
        resp = httpx.get(
            _PUBMED_SEARCH,
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "sort": "pub+date",
                "retmode": "json",
                "datetype": "pdat",
                "reldate": reldate,
            },
            timeout=12.0,
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception:
        logger.exception("PubMed query failed: %r", query[:120])
        return []


def _fetch_summaries(pmids: list[str]) -> dict:
    """Fetch PubMed article summaries for a list of PMIDs."""
    if not pmids:
        return {}
    resp = httpx.get(
        _PUBMED_SUMMARY,
        params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
        timeout=12.0,
    )
    resp.raise_for_status()
    return resp.json().get("result", {})


def _parse_articles(
    pmids: list[str],
    result_data: dict,
    specialty_pubmed: list[str],
    trusted_journals: list[str],
) -> list[dict]:
    """Convert raw PubMed result data into article dicts with priority flags."""
    articles = []
    specialty_lower = [j.lower() for j in specialty_pubmed]
    trusted_lower = [j.lower() for j in trusted_journals]

    for pmid in pmids:
        item = result_data.get(pmid, {})
        if not item or not item.get("title"):
            continue
        journal = item.get("source", "")
        journal_lower = journal.lower()
        authors = item.get("authors", [])
        articles.append({
            "pmid": pmid,
            "title": item["title"].rstrip("."),
            "journal": journal,
            "pub_date": item.get("pubdate", ""),
            "first_author": authors[0].get("name", "") if authors else "",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "specialty_journal": any(s in journal_lower for s in specialty_lower),
            "trusted": any(t in journal_lower for t in trusted_lower),
        })
    return articles


def _add_unique(dest: list[str], seen: set[str], new_ids: list[str]) -> int:
    added = 0
    for pid in new_ids:
        if pid not in seen:
            dest.append(pid)
            seen.add(pid)
            added += 1
    return added


# ─── Public interface ─────────────────────────────────────────────────────────


def fetch_pubmed(
    specialty: str,
    clinical_focus: list[str],
    trusted_journals: list[str],
    dislikes: list[str],
    specialty_pubmed: list[str] | None = None,
    max_results: int = 8,
) -> list[dict]:
    """Fetch recent PubMed articles matching the doctor's profile.

    4-layer fallback to guarantee articles even for narrow specialties
    or slow publication weeks. Returns up to 5 articles sorted:
    specialty journals → trusted → rest.
    """
    specialty_pubmed = specialty_pubmed or []
    all_pmids: list[str] = []
    seen: set[str] = set()

    try:
        dislike_sfx = _dislike_suffix(dislikes)

        # Layer 1: journals + focus terms, 30 days
        # The journal IS the specialty — no redundant specialty text filter needed.
        if specialty_pubmed and clinical_focus:
            journal_filter = _build_journal_filter(specialty_pubmed)
            focus_terms = _build_focus_terms(clinical_focus)
            layer1_q = f"({focus_terms}) AND ({journal_filter}){dislike_sfx}"
            layer1_ids = _run_pubmed_query(layer1_q, max_results, reldate=30)
            added = _add_unique(all_pmids, seen, layer1_ids)
            logger.info("PubMed layer 1 (journals+focus, 30d): %d results", added)

        # Layer 2: journals only, 30 days — catches papers that don't mention focus keywords
        if specialty_pubmed and len(all_pmids) < 5:
            journal_filter = _build_journal_filter(specialty_pubmed)
            layer2_q = f"({journal_filter}){dislike_sfx}"
            layer2_ids = _run_pubmed_query(layer2_q, max_results, reldate=30)
            added = _add_unique(all_pmids, seen, layer2_ids)
            logger.info("PubMed layer 2 (journals only, 30d): %d new results", added)

        # Layer 3: any journal, specialty name + focus in text, 60 days
        if len(all_pmids) < 3:
            if clinical_focus:
                focus_terms = _build_focus_terms(clinical_focus)
                specialty_text = f'("{specialty}"[MeSH Terms] OR "{specialty}"[Title/Abstract])'
                layer3_q = f"({specialty_text}) AND ({focus_terms}){dislike_sfx}"
            else:
                layer3_q = f'("{specialty}"[MeSH Terms] OR "{specialty}"[Title/Abstract]){dislike_sfx}'
            layer3_ids = _run_pubmed_query(layer3_q, max_results, reldate=60)
            added = _add_unique(all_pmids, seen, layer3_ids)
            logger.info("PubMed layer 3 (broad text+focus, 60d): %d new results", added)

        # Layer 4: pure keyword fallback, 90 days
        if len(all_pmids) < 3:
            layer4_q = f"{specialty}[Title/Abstract]{dislike_sfx}"
            layer4_ids = _run_pubmed_query(layer4_q, max_results, reldate=90)
            added = _add_unique(all_pmids, seen, layer4_ids)
            logger.info("PubMed layer 4 (keyword fallback, 90d): %d new results", added)

        if not all_pmids:
            logger.warning("PubMed returned 0 results for specialty=%r after all layers", specialty)
            return []

        result_data = _fetch_summaries(all_pmids)
        articles = _parse_articles(all_pmids, result_data, specialty_pubmed, trusted_journals)

        # Sort: specialty journals → trusted journals → rest
        articles.sort(key=lambda a: (
            0 if a["specialty_journal"] else 1 if a["trusted"] else 2
        ))
        logger.info("PubMed final: %d articles for specialty=%r", len(articles[:5]), specialty)
        return articles[:5]

    except Exception:
        logger.exception("PubMed fetch failed for specialty=%r", specialty)
        return []


# ─── Grok signals ─────────────────────────────────────────────────────────────


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
        f'Each item: {{"title": "...", "summary": "...", "source": "X/Twitter or news site"}}. '
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

            import json
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])

    except Exception:
        logger.exception("Grok fetch failed for specialty=%r", specialty)

    return []
