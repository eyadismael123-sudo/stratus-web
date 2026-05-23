"""Unit tests for LinkedIn post generator — parsing, voice kwargs, join logic."""

import pytest

from app.agents.linkedin.post_generator import (
    PostVersions,
    _build_style_notes_section,
    _join_field,
    _parse_versions,
    _voice_kwargs,
)


# ─── _join_field ─────────────────────────────────────────────────────────────

def test_join_field_list():
    assert _join_field(["a", "b", "c"]) == "a, b, c"


def test_join_field_single_item_list():
    assert _join_field(["only one"]) == "only one"


def test_join_field_string_passthrough():
    """Strings must be returned as-is — NOT iterated character by character."""
    result = _join_field("short punchy sentences")
    assert result == "short punchy sentences"
    assert "," not in result  # not split into chars


def test_join_field_empty_list():
    assert _join_field([]) == ""


def test_join_field_none():
    assert _join_field(None) == ""


# ─── _voice_kwargs ────────────────────────────────────────────────────────────

def test_voice_kwargs_all_lists():
    """Voice profile with list values (the norm from voice_extractor) must not produce char joins."""
    profile = {
        "tone": "authoritative yet approachable",
        "sentence_patterns": ["short punchy sentences", "longer explanatory ones"],
        "formatting_style": "Short paragraphs, no bullet spam",
        "signature_phrases": ["here's what I'm seeing", "worth noting"],
        "emoji_usage": "minimal",
        "post_length": "medium (150-300 words)",
        "engagement_hooks": ["bold observation", "contrarian take"],
        "calls_to_action": ["ends with a question"],
        "voice_summary": "A senior leader who writes like a practitioner",
    }
    kwargs = _voice_kwargs(profile)
    assert kwargs["sentence_patterns"] == "short punchy sentences, longer explanatory ones"
    assert kwargs["signature_phrases"] == "here's what I'm seeing, worth noting"
    assert kwargs["engagement_hooks"] == "bold observation, contrarian take"
    assert kwargs["calls_to_action"] == "ends with a question"
    assert kwargs["tone"] == "authoritative yet approachable"


def test_voice_kwargs_string_values():
    """Voice profile with string values (legacy/manually set) must not split into characters."""
    profile = {
        "sentence_patterns": "Mix of short and long sentences",
        "engagement_hooks": "bold claim",
        "calls_to_action": "asks a question",
    }
    kwargs = _voice_kwargs(profile)
    # Must not be "M, i, x, ..."
    assert "M, i, x" not in kwargs["sentence_patterns"]
    assert kwargs["sentence_patterns"] == "Mix of short and long sentences"


def test_voice_kwargs_missing_fields_get_defaults():
    profile = {}
    kwargs = _voice_kwargs(profile)
    assert kwargs["tone"] == "professional"
    assert kwargs["emoji_usage"] == "minimal"
    assert kwargs["post_length"] == "medium"


# ─── _build_style_notes_section ───────────────────────────────────────────────

def test_style_notes_section_empty():
    assert _build_style_notes_section([]) == ""


def test_style_notes_section_has_notes():
    result = _build_style_notes_section(["Keep it under 150 words", "No bullet points"])
    assert "Keep it under 150 words" in result
    assert "No bullet points" in result
    assert "Learned style preferences" in result


# ─── _parse_versions ─────────────────────────────────────────────────────────

def test_parse_versions_standard_format():
    raw = "VERSION_A:\nThis is version A content.\n\nVERSION_B:\nThis is version B content."
    result = _parse_versions(raw)
    assert result.version_a == "This is version A content."
    assert result.version_b == "This is version B content."


def test_parse_versions_multiline():
    raw = "VERSION_A:\nLine one.\nLine two.\n\nVERSION_B:\nOther line one.\nOther line two."
    result = _parse_versions(raw)
    assert "Line one." in result.version_a
    assert "Line two." in result.version_a
    assert "Other line one." in result.version_b


def test_parse_versions_fallback_on_bad_format():
    """If VERSION_B: marker is missing, fall back to splitting in half."""
    raw = "A" * 100 + "B" * 100
    result = _parse_versions(raw)
    assert isinstance(result, PostVersions)
    assert len(result.version_a) > 0
    assert len(result.version_b) > 0


def test_parse_versions_strips_whitespace():
    raw = "VERSION_A:\n\n  Hello there.  \n\nVERSION_B:\n\n  Goodbye.  "
    result = _parse_versions(raw)
    assert result.version_a == "Hello there."
    assert result.version_b == "Goodbye."


def test_parse_versions_returns_named_tuple():
    raw = "VERSION_A:\nA\n\nVERSION_B:\nB"
    result = _parse_versions(raw)
    assert hasattr(result, "version_a")
    assert hasattr(result, "version_b")
