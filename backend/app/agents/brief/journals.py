"""Specialty-to-journal resolver for the Brief agent.

Loads journals.json and matches a doctor's free-text specialty
to the curated list of top 3 peer-reviewed journals for that specialty.

Matching rules (checked in order):
1. Any alias is a substring of the doctor's input
2. The doctor's input is a substring of any alias
3. Falls back to General Medicine (NEJM, JAMA, Lancet)
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent / "journals.json"


@lru_cache(maxsize=1)
def _load_specialties() -> list[dict]:
    return json.loads(_DATA_FILE.read_text())["specialties"]


def resolve_journals(specialty: str) -> list[dict]:
    """Return the top 3 journal dicts for the given specialty string.

    Each dict has "display" (human-readable) and "pubmed" (NLM abbreviation).
    Returns general medicine journals if no match found.

    Matching prefers the longest matching alias so that specific specialties
    beat their parent. Example: "interventional cardiology" should match
    "Interventional Cardiology" (alias len=25) not "Cardiology" (alias len=9),
    even if the file has Cardiology listed first.
    """
    if not specialty:
        return _fallback_journals()

    normalized = specialty.lower().strip()
    specialties = _load_specialties()

    # Two-pass matching — prefer `alias in input` (alias is a subset of what
    # the user typed) over `input in alias` (user typed a prefix/subset of
    # an alias).  Within each pass, the longest matching alias wins so that
    # "interventional cardiology" beats "cardiology" for the same input.
    best_forward: tuple[int, list[dict], str] | None = None   # alias ⊆ input
    best_reverse: tuple[int, list[dict], str] | None = None   # input ⊆ alias

    for spec in specialties:
        spec_best_fwd = 0
        spec_best_rev = 0
        for alias in spec["aliases"]:
            if alias in normalized and len(alias) > spec_best_fwd:
                spec_best_fwd = len(alias)
            elif normalized in alias and len(alias) > spec_best_rev:
                spec_best_rev = len(alias)
        if spec_best_fwd > 0:
            if best_forward is None or spec_best_fwd > best_forward[0]:
                best_forward = (spec_best_fwd, spec["journals"], spec["name"])
        elif spec_best_rev > 0:
            if best_reverse is None or spec_best_rev > best_reverse[0]:
                best_reverse = (spec_best_rev, spec["journals"], spec["name"])

    best = best_forward or best_reverse
    if best is not None:
        logger.debug("Journals resolved: %s → %s", specialty, best[2])
        return best[1]

    logger.info("No journal match for specialty=%r — using general medicine", specialty)
    return _fallback_journals()


def _fallback_journals() -> list[dict]:
    specialties = _load_specialties()
    for spec in specialties:
        if spec["name"] == "General Medicine":
            return spec["journals"]
    return [
        {"display": "NEJM", "pubmed": "N Engl J Med"},
        {"display": "JAMA", "pubmed": "JAMA"},
        {"display": "Lancet", "pubmed": "Lancet"},
    ]


def display_names(journals: list[dict]) -> list[str]:
    """Extract display names from a journal list."""
    return [j["display"] for j in journals]


def pubmed_abbrevs(journals: list[dict]) -> list[str]:
    """Extract PubMed NLM abbreviations from a journal list."""
    return [j["pubmed"] for j in journals]
