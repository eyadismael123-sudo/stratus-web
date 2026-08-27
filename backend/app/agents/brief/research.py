"""Research pipeline for the Brief (Doctor Research) agent.

Two sources:
1. PubMed E-utilities API — recent peer-reviewed literature (no key required)
2. Grok API (xAI) — real-time X/Twitter clinical signals (requires GROK_API_KEY)

PubMed strategy (4-layer cascade — all layers run, guaranteed results):
  Layer 1: Specialty journals + focus terms, 60 days
  Layer 2: Specialty journals only, 60 days  (always runs — supplements layer 1)
             Queried per-journal, not as one merged OR filter — a prolific
             journal (e.g. one that runs a weekly correspondence column)
             would otherwise fill the whole date-sorted cap and starve out
             quieter journals in the same doctor's list.
  Layer 3: Any journal, specialty name + focus terms in text, 90 days
             (triggers if total < 4 after layers 1+2)
  Layer 4: Free-text keyword fallback, 180 days
             (triggers if total still < 4 — last resort)

Why broader windows are correct:
  - Monthly specialty journals publish 4-8 papers/month — 30 days often yields 0
  - Layer 1 AND logic (focus AND journals) is strict; Layer 2 always fills the gap
  - 180-day fallback guarantees at least a couple results for any specialty

Non-research filtering: PubMed's [pt] (publication type) tag is unreliable for
correspondence — journals like Plast Reconstr Surg tag "Reply:", "Discussion:"
and "Journal Club:" pieces as plain "Journal Article", same as primary research.
_looks_like_correspondence() filters these out by title pattern instead.
"""

from __future__ import annotations

import logging
import re

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


# Correspondence/digest pieces that PubMed's [pt] tag doesn't reliably flag —
# these journals index them as plain "Journal Article", so filtering has to
# happen on the title itself. Two patterns:
#  - _CORRESPONDENCE_PREFIX_RE: the title itself starts with the marker
#    ("Reply: ...", "Discussion: ...")
#  - _CORRESPONDENCE_LABEL_RE: the marker appears as a colon-terminated label
#    after a journal-branded prefix ("PRS Journal Club: ...", "... Highlights: ...")
_CORRESPONDENCE_PREFIX_RE = re.compile(
    r"^(reply|response to|re:|discussion|comment on|letter to the editor|"
    r"erratum|corrigendum)\b",
    re.IGNORECASE,
)
_CORRESPONDENCE_LABEL_RE = re.compile(r"\b(journal club|highlights?)\s*:", re.IGNORECASE)


def _looks_like_correspondence(title: str) -> bool:
    stripped = title.strip()
    return bool(_CORRESPONDENCE_PREFIX_RE.match(stripped) or _CORRESPONDENCE_LABEL_RE.search(stripped))


def _run_per_journal_query(
    pubmed_abbrevs: list[str],
    dislike_sfx: str,
    reldate: int,
    per_journal_max: int,
) -> list[str]:
    """Query each journal individually, then interleave round-robin.

    Querying per-journal stops one prolific journal from crowding every slot
    in a shared, date-sorted cap. Interleaving matters just as much as the
    per-journal query itself: appending journal-by-journal would still let a
    downstream cap (articles[:8]) exhaust the first journal in the list
    before ever reaching the next — e.g. a doctor with "ortho and plastics"
    would only ever see ortho, since it's listed first. Round-robin gives
    every journal a slot in the cap regardless of list order.
    """
    import time

    # NCBI's unauthenticated limit is 3 req/s; pace requests to stay under it
    # even under scheduler load (many doctors' journal batches back-to-back).
    # With an API key the limit is 10 req/s, so pacing can relax.
    pace = 0.1 if settings.ncbi_api_key else 0.34

    per_journal_ids: list[list[str]] = []
    for i, jour in enumerate(pubmed_abbrevs):
        if i > 0:
            time.sleep(pace)
        query = f'"{jour}"[jour]{dislike_sfx}'
        results = _run_pubmed_query(query, per_journal_max, reldate=reldate)
        per_journal_ids.append(results)
        logger.info("PubMed layer 2 journal=%r: %d results", jour, len(results))

    ids: list[str] = []
    seen: set[str] = set()
    max_len = max((len(lst) for lst in per_journal_ids), default=0)
    for i in range(max_len):
        for lst in per_journal_ids:
            if i < len(lst) and lst[i] not in seen:
                ids.append(lst[i])
                seen.add(lst[i])
    return ids


def _build_focus_terms(clinical_focus: list[str]) -> str:
    """Build focus-terms query fragment (Title/Abstract). Uses all focus terms."""
    return " OR ".join(f'"{f}"[Title/Abstract]' for f in clinical_focus)


def _ncbi_params(**params: object) -> dict:
    """Attach the NCBI API key when configured (raises the rate limit from
    3 req/s to 10 req/s). Safe to omit — E-utilities works without one."""
    if settings.ncbi_api_key:
        params["api_key"] = settings.ncbi_api_key
    return params


def _run_pubmed_query(query: str, max_results: int, reldate: int = 30) -> list[str]:
    """Return a list of PubMed IDs for the given query.

    Retries up to 3 times on 429 (rate-limit) with exponential back-off —
    same pattern as _fetch_summaries. Without this, a doctor with several
    curated journals (or a scheduler tick processing many doctors) reliably
    outruns NCBI's 3 req/s unauthenticated limit, and journals silently drop
    out of the briefing instead of just waiting a beat and retrying.
    """
    import time

    for attempt in range(3):
        try:
            resp = httpx.get(
                _PUBMED_SEARCH,
                params=_ncbi_params(
                    db="pubmed",
                    term=query,
                    retmax=max_results,
                    sort="pub+date",
                    retmode="json",
                    datetype="pdat",
                    reldate=reldate,
                ),
                timeout=12.0,
            )
            if resp.status_code == 429:
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    "PubMed esearch 429 — retrying in %ds (attempt %d/3): %r",
                    wait, attempt + 1, query[:80],
                )
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json().get("esearchresult", {}).get("idlist", [])
        except Exception:
            logger.exception("PubMed query failed: %r", query[:120])
            return []

    logger.warning("PubMed esearch still 429 after 3 retries — skipping: %r", query[:80])
    return []


def _fetch_summaries(pmids: list[str]) -> dict:
    """Fetch PubMed article summaries for a list of PMIDs.

    Retries up to 3 times on 429 (rate-limit) with exponential back-off.
    NCBI allows 3 req/s without an API key; a brief wait resolves transient limits.
    """
    import time

    if not pmids:
        return {}

    for attempt in range(3):
        resp = httpx.get(
            _PUBMED_SUMMARY,
            params=_ncbi_params(db="pubmed", id=",".join(pmids), retmode="json"),
            timeout=12.0,
        )
        if resp.status_code == 429:
            wait = 2 ** attempt  # 1s, 2s, 4s
            logger.warning("PubMed 429 — retrying in %ds (attempt %d/3)", wait, attempt + 1)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json().get("result", {})

    raise RuntimeError("PubMed esummary returned 429 after 3 retries")


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
        title = item.get("title", "")
        if not item or not title:
            continue
        if _looks_like_correspondence(title):
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
    max_results: int = 15,
) -> list[dict]:
    """Fetch recent PubMed articles matching the doctor's profile.

    4-layer cascade to guarantee at least a couple of articles daily even for
    narrow specialties. Returns up to 8 articles sorted:
    specialty journals → trusted → rest.
    """
    specialty_pubmed = specialty_pubmed or []
    all_pmids: list[str] = []
    seen: set[str] = set()

    try:
        dislike_sfx = _dislike_suffix(dislikes)

        # Layer 1: journals + focus terms, 60 days
        if specialty_pubmed and clinical_focus:
            journal_filter = _build_journal_filter(specialty_pubmed)
            focus_terms = _build_focus_terms(clinical_focus)
            layer1_q = f"({focus_terms}) AND ({journal_filter}){dislike_sfx}"
            layer1_ids = _run_pubmed_query(layer1_q, max_results, reldate=60)
            added = _add_unique(all_pmids, seen, layer1_ids)
            logger.info("PubMed layer 1 (journals+focus, 60d): %d results", added)

        # Layer 2: journals only, 60 days — always runs to supplement layer 1.
        # Queried per-journal (see _run_per_journal_query) so a prolific journal
        # can't fill the entire cap and starve out quieter ones in the same list.
        if specialty_pubmed:
            per_journal_max = max(3, max_results // len(specialty_pubmed))
            layer2_ids = _run_per_journal_query(specialty_pubmed, dislike_sfx, 60, per_journal_max)
            added = _add_unique(all_pmids, seen, layer2_ids)
            logger.info("PubMed layer 2 (journals only, per-journal, 60d): %d new results", added)

        # Layer 3: any journal, specialty name + focus in text, 90 days
        if len(all_pmids) < 4:
            if clinical_focus:
                focus_terms = _build_focus_terms(clinical_focus)
                specialty_text = f'("{specialty}"[MeSH Terms] OR "{specialty}"[Title/Abstract])'
                layer3_q = f"({specialty_text}) AND ({focus_terms}){dislike_sfx}"
            else:
                layer3_q = f'("{specialty}"[MeSH Terms] OR "{specialty}"[Title/Abstract]){dislike_sfx}'
            layer3_ids = _run_pubmed_query(layer3_q, max_results, reldate=90)
            added = _add_unique(all_pmids, seen, layer3_ids)
            logger.info("PubMed layer 3 (broad text+focus, 90d): %d new results", added)

        # Layer 4: pure keyword fallback, 180 days
        if len(all_pmids) < 4:
            layer4_q = f"{specialty}[Title/Abstract]{dislike_sfx}"
            layer4_ids = _run_pubmed_query(layer4_q, max_results, reldate=180)
            added = _add_unique(all_pmids, seen, layer4_ids)
            logger.info("PubMed layer 4 (keyword fallback, 180d): %d new results", added)

        if not all_pmids:
            logger.warning("PubMed returned 0 results for specialty=%r after all layers", specialty)
            return []

        result_data = _fetch_summaries(all_pmids)
        articles = _parse_articles(all_pmids, result_data, specialty_pubmed, trusted_journals)

        # Sort: specialty journals → trusted journals → rest
        articles.sort(key=lambda a: (
            0 if a["specialty_journal"] else 1 if a["trusted"] else 2
        ))
        logger.info("PubMed final: %d articles for specialty=%r", len(articles[:8]), specialty)
        return articles[:8]

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
