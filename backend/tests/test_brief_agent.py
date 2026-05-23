"""Unit tests for Brief agent — onboarding questions, messages, formatter fallback."""

import pytest

from app.agents.brief.agent import DoctorBriefAgent
from app.agents.brief.formatter import _fallback


# ─── DoctorBriefAgent ────────────────────────────────────────────────────────

@pytest.fixture
def agent():
    return DoctorBriefAgent()


@pytest.fixture
def fake_client():
    return {"id": "abc-123", "name": "Eyad Ismael", "telegram_chat_id": "999"}


def test_slug(agent):
    assert agent.slug == "brief"


def test_intro_message_uses_last_name(agent, fake_client):
    msg = agent.get_intro_message(fake_client)
    assert "Ismael" in msg
    assert "Brief" in msg


def test_intro_message_missing_name(agent):
    msg = agent.get_intro_message({})
    assert "Doctor" in msg


def test_onboarding_question_step_0(agent):
    q = agent.get_onboarding_question(0, {})
    assert q is not None
    assert "specialty" in q.lower()


def test_onboarding_question_step_5(agent):
    q = agent.get_onboarding_question(5, {})
    assert q is not None  # 6 steps (0-5)


def test_onboarding_question_past_last_step_returns_none(agent):
    assert agent.get_onboarding_question(6, {}) is None
    assert agent.get_onboarding_question(99, {}) is None


def test_completion_message_includes_time(agent, fake_client):
    collected = {"peak_reading_time": "07:00", "clinical_focus": ["TAVI", "PCI"], "trusted_journals": ["JACC"]}
    msg = agent.get_completion_message(fake_client, collected)
    assert "07:00" in msg
    assert "Ismael" in msg


def test_completion_message_default_time(agent, fake_client):
    """When no peak_reading_time in collected, falls back to 06:30."""
    msg = agent.get_completion_message(fake_client, {})
    assert "06:30" in msg


def test_process_onboarding_answer_step_0_stores_specialty(agent):
    updated = agent.process_onboarding_answer(0, "interventional cardiology", {})
    assert updated.get("specialty") == "interventional cardiology"


def test_process_onboarding_answer_injects_client_context(agent):
    """_client_id and _client_name pass through to updated collected."""
    seed = {"_client_id": "xyz", "_client_name": "Eyad Ismael"}
    updated = agent.process_onboarding_answer(0, "oncology", seed)
    assert updated["_client_id"] == "xyz"
    assert updated["_client_name"] == "Eyad Ismael"


# ─── _fallback formatter ─────────────────────────────────────────────────────

def test_fallback_no_articles():
    result = _fallback("oncology", [], [])
    assert "oncology" in result
    assert "Good morning" in result


def test_fallback_with_articles():
    articles = [
        {"title": "Test paper one", "journal": "NEJM", "url": "https://pubmed.ncbi.nlm.nih.gov/1/"},
        {"title": "Test paper two", "journal": "JACC", "url": "https://pubmed.ncbi.nlm.nih.gov/2/"},
    ]
    result = _fallback("cardiology", articles, [])
    assert "Test paper one" in result
    assert "NEJM" in result


def test_fallback_with_grok_signals():
    signals = [{"title": "Big cardiology news", "summary": "Something happened"}]
    result = _fallback("cardiology", [], signals)
    assert "Big cardiology news" in result
