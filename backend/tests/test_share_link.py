"""Unit tests for LinkedIn share link builder."""

from app.agents.linkedin.share_link import build_linkedin_url


def test_basic_url_structure():
    url = build_linkedin_url("Hello world")
    assert url.startswith("https://www.linkedin.com/feed/?shareActive=true&text=")


def test_spaces_encoded():
    url = build_linkedin_url("Hello world")
    assert " " not in url
    assert "Hello" in url


def test_special_chars_encoded():
    url = build_linkedin_url("AI & healthcare #pharma")
    assert "&" not in url.split("text=")[1]
    assert "#" not in url.split("text=")[1]


def test_empty_string():
    url = build_linkedin_url("")
    assert url == "https://www.linkedin.com/feed/?shareActive=true&text="


def test_long_post_encoded():
    post = "This is a long post. " * 50
    url = build_linkedin_url(post)
    assert url.startswith("https://www.linkedin.com/feed/")
    assert "text=" in url
