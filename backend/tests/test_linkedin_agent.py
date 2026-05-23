"""Unit tests for LinkedIn Ghostwriter agent — onboarding, keyboard, fallback, style notes."""

from unittest.mock import patch

import pytest

from app.agents.linkedin.agent import LinkedInGhostwriterAgent, _add_style_note


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def agent():
    return LinkedInGhostwriterAgent()


@pytest.fixture
def fake_client():
    return {"id": "client-abc", "name": "Eyad Ismael", "telegram_chat_id": "999"}


# ─── Slug ─────────────────────────────────────────────────────────────────────

def test_slug(agent):
    assert agent.slug == "linkedin"


# ─── get_intro_message ────────────────────────────────────────────────────────

def test_intro_message_uses_first_name(agent, fake_client):
    msg = agent.get_intro_message(fake_client)
    assert "Eyad" in msg
    assert "LinkedIn" in msg


def test_intro_message_full_name_uses_only_first(agent):
    msg = agent.get_intro_message({"name": "Ahmed Al Rashid"})
    assert "Ahmed" in msg
    assert "Al Rashid" not in msg


def test_intro_message_missing_name_falls_back(agent):
    msg = agent.get_intro_message({})
    assert "there" in msg


# ─── get_onboarding_question ──────────────────────────────────────────────────

def test_onboarding_question_step_0_asks_about_field(agent):
    q = agent.get_onboarding_question(0, {})
    assert q is not None
    assert "field" in q.lower() or "title" in q.lower()


def test_onboarding_question_step_1_asks_about_audience(agent):
    q = agent.get_onboarding_question(1, {})
    assert q is not None
    assert "audience" in q.lower()


def test_onboarding_question_step_3_asks_to_paste_posts(agent):
    q = agent.get_onboarding_question(3, {})
    assert q is not None
    assert "paste" in q.lower() or "posts" in q.lower()


def test_onboarding_question_step_5_is_not_none(agent):
    q = agent.get_onboarding_question(5, {})
    assert q is not None


def test_onboarding_question_beyond_last_step_returns_none(agent):
    assert agent.get_onboarding_question(6, {}) is None
    assert agent.get_onboarding_question(99, {}) is None


# ─── get_onboarding_keyboard ──────────────────────────────────────────────────

def test_keyboard_step_0_is_none(agent):
    assert agent.get_onboarding_keyboard(0, {}) is None


def test_keyboard_step_1_returns_audience_options(agent):
    kb = agent.get_onboarding_keyboard(1, {})
    assert kb is not None
    assert len(kb) > 0
    assert any("professional" in opt.lower() for opt in kb)


def test_keyboard_step_2_returns_region_options(agent):
    kb = agent.get_onboarding_keyboard(2, {})
    assert kb is not None
    assert any("UAE" in opt or "UK" in opt for opt in kb)


def test_keyboard_step_3_is_none(agent):
    assert agent.get_onboarding_keyboard(3, {}) is None


def test_keyboard_step_4_is_none(agent):
    assert agent.get_onboarding_keyboard(4, {}) is None


def test_keyboard_step_5_returns_frequency_options(agent):
    kb = agent.get_onboarding_keyboard(5, {})
    assert kb is not None
    assert any("day" in opt.lower() for opt in kb)


# ─── process_onboarding_answer ────────────────────────────────────────────────

def test_step_0_stores_field(agent):
    updated = agent.process_onboarding_answer(0, "Head of Sales at AbbVie", {})
    assert updated["field"] == "Head of Sales at AbbVie"


def test_step_1_stores_audience(agent):
    updated = agent.process_onboarding_answer(1, "Executives / C-suite", {})
    assert updated["audience"] == "Executives / C-suite"


def test_step_2_stores_region(agent):
    updated = agent.process_onboarding_answer(2, "UAE / GCC", {})
    assert updated["region"] == "UAE / GCC"


def test_step_3_done_marks_collection_complete(agent):
    updated = agent.process_onboarding_answer(3, "done", {"pasted_posts": ["post one"]})
    assert updated.get("posts_collection_done") is True
    assert "post one" in updated["pasted_posts"]  # existing posts preserved


def test_step_3_single_post_appended(agent):
    updated = agent.process_onboarding_answer(3, "My great post about pharma.", {})
    assert "My great post about pharma." in updated["pasted_posts"]


def test_step_3_multiple_posts_split_by_separator(agent):
    text = "Post A content\n---\nPost B content\n---\nPost C content"
    updated = agent.process_onboarding_answer(3, text, {})
    assert len(updated["pasted_posts"]) == 3
    assert "Post A content" in updated["pasted_posts"]
    assert "Post C content" in updated["pasted_posts"]


def test_step_3_accumulates_across_answers(agent):
    seed = {"pasted_posts": ["existing post"]}
    updated = agent.process_onboarding_answer(3, "new post", seed)
    assert len(updated["pasted_posts"]) == 2


def test_step_4_default_keyword_stores_0900(agent):
    for answer in ("default", "ok", "yes", "9:00", "9am", "09:00"):
        updated = agent.process_onboarding_answer(4, answer, {})
        assert updated["post_time"] == "09:00", f"Failed for answer={answer!r}"


def test_step_4_custom_time_stored_as_is(agent):
    updated = agent.process_onboarding_answer(4, "08:30", {})
    assert updated["post_time"] == "08:30"


def test_step_5_maps_frequency_every_day(agent):
    updated = agent.process_onboarding_answer(5, "Every day", {"pasted_posts": []})
    assert updated["post_frequency"] == "daily"


def test_step_5_maps_frequency_twice_a_week(agent):
    updated = agent.process_onboarding_answer(5, "Twice a week", {"pasted_posts": []})
    assert updated["post_frequency"] == "twice_a_week"


def test_step_5_unknown_frequency_defaults_to_daily(agent):
    updated = agent.process_onboarding_answer(5, "whenever I feel like it", {"pasted_posts": []})
    assert updated["post_frequency"] == "daily"


def test_step_5_no_posts_skips_voice_extraction(agent):
    """When pasted_posts is empty, no voice extraction API call should happen."""
    updated = agent.process_onboarding_answer(5, "Every day", {"pasted_posts": []})
    assert "voice_profile" not in updated


def test_step_5_with_posts_calls_voice_extractor(agent):
    """When pasted_posts exist, voice_profile should be populated (mocked)."""
    mock_profile = {"tone": "authoritative", "voice_summary": "A seasoned pharma leader"}
    collected = {
        "pasted_posts": ["Post one about pharma", "Post two about leadership"],
        "_client_id": "abc-123",
        "_client_name": "Eyad Ismael",
    }
    with patch("app.agents.linkedin.agent.extract_voice_profile", return_value=mock_profile), \
         patch.object(agent, "_save_voice_profile"):
        updated = agent.process_onboarding_answer(5, "Every day", collected)
    assert updated["voice_profile"] == mock_profile


def test_step_5_client_context_passes_through(agent):
    """_client_id and _client_name must survive the step-5 update."""
    seed = {"_client_id": "xyz", "_client_name": "Eyad Ismael", "pasted_posts": []}
    updated = agent.process_onboarding_answer(5, "Every day", seed)
    assert updated["_client_id"] == "xyz"
    assert updated["_client_name"] == "Eyad Ismael"


# ─── _add_style_note ─────────────────────────────────────────────────────────

def test_add_style_note_appends(agent):
    memory = {"style_notes": ["keep it short"]}
    updated = _add_style_note(memory, "no bullet points")
    assert "no bullet points" in updated["style_notes"]
    assert "keep it short" in updated["style_notes"]


def test_add_style_note_does_not_mutate_original():
    original = {"style_notes": ["keep it short"]}
    _add_style_note(original, "new note")
    assert "new note" not in original["style_notes"]


def test_add_style_note_creates_list_when_missing():
    memory = {}
    updated = _add_style_note(memory, "first note")
    assert updated["style_notes"] == ["first note"]


# ─── _fallback_suggestions ───────────────────────────────────────────────────

def test_fallback_suggestions_returns_five(agent):
    suggestions = agent._fallback_suggestions("pharma")
    assert len(suggestions) == 5


def test_fallback_suggestions_have_required_keys(agent):
    suggestions = agent._fallback_suggestions("cardiology")
    for s in suggestions:
        assert "topic" in s
        assert "angle" in s


def test_fallback_suggestions_include_industry(agent):
    suggestions = agent._fallback_suggestions("real estate")
    assert all("real estate" in s["topic"] for s in suggestions)


# ─── get_completion_message ───────────────────────────────────────────────────

def test_completion_message_includes_all_fields(agent, fake_client):
    collected = {
        "field": "pharmaceutical affairs",
        "audience": "Executives / C-suite",
        "region": "UAE / GCC",
        "post_time": "08:00",
        "post_frequency": "daily",
    }
    msg = agent.get_completion_message(fake_client, collected)
    assert "Eyad" in msg
    assert "pharmaceutical affairs" in msg
    assert "Executives / C-suite" in msg
    assert "UAE / GCC" in msg
    assert "08:00" in msg
    assert "every day" in msg


def test_completion_message_default_time(agent, fake_client):
    """Missing post_time falls back to 09:00."""
    msg = agent.get_completion_message(fake_client, {})
    assert "09:00" in msg


def test_completion_message_freq_label_once_a_week(agent, fake_client):
    collected = {"post_frequency": "once_a_week"}
    msg = agent.get_completion_message(fake_client, collected)
    assert "once a week" in msg.lower()
