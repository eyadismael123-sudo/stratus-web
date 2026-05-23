"""Integration tests for Brief research pipeline — hits real PubMed API.

These tests make real HTTP calls to PubMed. They verify the 4-layer
fallback strategy actually returns results for typical doctor profiles.
No API key needed (PubMed E-utilities are public).
"""

import pytest

from app.agents.brief.research import (
    _build_focus_terms,
    _build_journal_filter,
    _dislike_suffix,
    _run_pubmed_query,
    fetch_pubmed,
)


# ─── Unit tests (no network) ─────────────────────────────────────────────────

def test_build_journal_filter_single():
    result = _build_journal_filter(["JACC Cardiovasc Interv"])
    assert result == '"JACC Cardiovasc Interv"[jour]'


def test_build_journal_filter_multiple():
    result = _build_journal_filter(["JACC", "Lancet"])
    assert '"JACC"[jour]' in result
    assert '"Lancet"[jour]' in result
    assert " OR " in result


def test_build_focus_terms_all_used():
    # Confirm no [:3] cap — all terms used
    terms = ["TAVI", "PCI", "heart failure", "stent", "atrial fibrillation"]
    result = _build_focus_terms(terms)
    for term in terms:
        assert term in result


def test_build_focus_terms_empty():
    assert _build_focus_terms([]) == ""


def test_dislike_suffix_review():
    suffix = _dislike_suffix(["review articles"])
    assert "NOT Review[pt]" in suffix


def test_dislike_suffix_animal():
    suffix = _dislike_suffix(["animal studies"])
    assert "NOT (animals[MeSH]" in suffix


def test_dislike_suffix_empty():
    assert _dislike_suffix([]) == ""


# ─── Integration tests (real PubMed API) ─────────────────────────────────────

@pytest.mark.integration
def test_pubmed_query_returns_results():
    """Basic PubMed query should return at least 1 result."""
    ids = _run_pubmed_query("cardiology[Title/Abstract]", max_results=5, reldate=180)
    assert isinstance(ids, list)
    assert len(ids) >= 1


@pytest.mark.integration
def test_fetch_pubmed_interventional_cardiology():
    """Interventional cardiology — a real narrow specialty — should return articles."""
    articles = fetch_pubmed(
        specialty="interventional cardiology",
        clinical_focus=["TAVI", "PCI", "coronary artery disease"],
        trusted_journals=["NEJM", "JACC", "Lancet"],
        dislikes=["animal studies"],
        specialty_pubmed=["JACC Cardiovasc Interv", "EuroIntervention", "Circ Cardiovasc Interv"],
    )
    assert len(articles) >= 2, (
        f"Expected ≥2 articles for interventional cardiology, got {len(articles)}"
    )
    for a in articles:
        assert "title" in a
        assert "pmid" in a
        assert "url" in a
        assert a["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/")


@pytest.mark.integration
def test_fetch_pubmed_oncology():
    """Oncology should return articles — broad specialty."""
    articles = fetch_pubmed(
        specialty="oncology",
        clinical_focus=["immunotherapy", "checkpoint inhibitors", "NSCLC"],
        trusted_journals=["NEJM", "JCO", "Lancet Oncol"],
        dislikes=[],
        specialty_pubmed=["J Clin Oncol", "Ann Oncol", "Cancer"],
    )
    assert len(articles) >= 2


@pytest.mark.integration
def test_fetch_pubmed_no_journals_falls_through_to_layer3():
    """When specialty_pubmed is empty, should still return results via layers 3/4."""
    articles = fetch_pubmed(
        specialty="nephrology",
        clinical_focus=["chronic kidney disease", "dialysis"],
        trusted_journals=["NEJM", "JASN"],
        dislikes=[],
        specialty_pubmed=[],  # no journals — forces L3/L4
    )
    assert len(articles) >= 1


@pytest.mark.integration
def test_fetch_pubmed_articles_have_required_fields():
    """Each returned article must have all required fields."""
    articles = fetch_pubmed(
        specialty="cardiology",
        clinical_focus=["heart failure"],
        trusted_journals=["NEJM"],
        dislikes=[],
        specialty_pubmed=["Circulation", "J Am Coll Cardiol"],
    )
    required = {"pmid", "title", "journal", "pub_date", "url", "specialty_journal", "trusted"}
    for a in articles:
        missing = required - set(a.keys())
        assert not missing, f"Article missing fields: {missing}"


@pytest.mark.integration
def test_fetch_pubmed_max_8_results():
    """Should return at most 8 results."""
    articles = fetch_pubmed(
        specialty="internal medicine",
        clinical_focus=["diabetes", "hypertension"],
        trusted_journals=["NEJM", "JAMA"],
        dislikes=[],
        specialty_pubmed=["Ann Intern Med", "JAMA Intern Med"],
    )
    assert len(articles) <= 8
