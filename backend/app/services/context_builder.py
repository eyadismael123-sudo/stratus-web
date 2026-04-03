"""Context builder — assembles the injected context for every agent run.

Tiered budget (hard caps):
  Static  — voice profile      ~400 tokens
  Summary — rolling memory     ~600 tokens
  Live    — signals + research ~1,000 tokens
  Total injected               ~2,000 tokens max

Claude gets the rest of the context window for generation.
"""

from __future__ import annotations

from app.db.connection import get_service_client
from app.repositories import agents as agent_repo
from app.repositories.chat import get_recent_messages


# ─── Token helpers ────────────────────────────────────────────────────

_CHARS_PER_TOKEN = 4  # rough approximation


def _truncate(text: str, max_tokens: int) -> str:
    max_chars = max_tokens * _CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


# ─── Data fetchers ────────────────────────────────────────────────────


def _get_voice_profile(agent_id: str) -> str:
    """Extract voice profile JSON from user_agents.config."""
    db = get_service_client()
    result = (
        db.table("user_agents")
        .select("config, memory_summary, memory_updated_at")
        .eq("id", agent_id)
        .single()
        .execute()
    )
    if not result.data:
        return ""

    config = result.data.get("config") or {}
    if not config:
        return ""

    # Format key voice fields into readable text
    lines = []
    if config.get("tone"):
        lines.append(f"Tone: {config['tone']}")
    if config.get("industry"):
        lines.append(f"Industry: {config['industry']}")
    if config.get("topics"):
        lines.append(f"Topics: {', '.join(config['topics'])}")
    if config.get("language"):
        lines.append(f"Language: {config['language']}")
    if config.get("posting_frequency"):
        lines.append(f"Posting frequency: {config['posting_frequency']}")
    if config.get("example_posts"):
        examples = config["example_posts"][:2]  # max 2 examples
        lines.append("Example posts:")
        for ex in examples:
            lines.append(f"  - {ex}")

    return "\n".join(lines)


def _get_memory_summary(agent_id: str) -> str:
    """Fetch the pre-summarized weekly memory for this agent."""
    db = get_service_client()
    result = (
        db.table("user_agents")
        .select("memory_summary")
        .eq("id", agent_id)
        .single()
        .execute()
    )
    if not result.data:
        return ""
    return result.data.get("memory_summary") or ""


def _get_signals(client_id: str, industries: list[str], agent_id: str) -> str:
    """Fetch top 3 unexpired signals relevant to this agent's industries."""
    db = get_service_client()
    result = (
        db.table("agent_signals")
        .select("signal_type, content, created_at")
        .eq("client_id", client_id)
        .gt("expires_at", "now()")
        .not_.contains("consumed_by", [agent_id])
        .order("created_at", desc=True)
        .limit(3)
        .execute()
    )
    signals = result.data or []
    if not signals:
        return ""

    lines = []
    for s in signals:
        lines.append(f"[{s['signal_type'].upper()}] {s['content']}")
    return "\n".join(lines)


# ─── Public API ───────────────────────────────────────────────────────


def build_agent_context(
    client_id: str,
    agent_id: str,
    today_research: str = "",
    industries: list[str] | None = None,
) -> str:
    """Assemble the full context string injected before every agent run.

    Respects hard token budgets to prevent context bloat and hallucination.
    """
    voice = _truncate(_get_voice_profile(agent_id), max_tokens=400)
    summary = _truncate(_get_memory_summary(agent_id), max_tokens=600)
    signals = _truncate(
        _get_signals(client_id, industries or [], agent_id), max_tokens=500
    )
    research = _truncate(today_research, max_tokens=800)

    sections: list[str] = []

    if voice:
        sections.append(f"## Your Voice\n{voice}")
    if summary:
        sections.append(f"## What You've Been Doing\n{summary}")
    if signals:
        sections.append(f"## What Your Team Discovered\n{signals}")
    if research:
        sections.append(f"## Today's Research\n{research}")

    return "\n\n".join(sections)


def build_cos_context(client_id: str, conversation_id: str) -> str:
    """Assemble context for the Chief of Staff agent.

    Includes all hired agents + their memory summaries, recent signals,
    and the last 10 messages of conversation history.
    """
    db = get_service_client()

    # All active agents for this client
    agents_result = (
        db.table("user_agents")
        .select(
            "id, name, status, memory_summary, config, agent_templates(name, role)"
        )
        .eq("user_id", client_id)
        .is_("deleted_at", "null")
        .execute()
    )
    agents = agents_result.data or []

    # Recent signals (last 48h)
    signals_result = (
        db.table("agent_signals")
        .select("signal_type, content, created_at")
        .eq("client_id", client_id)
        .gt("expires_at", "now()")
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    signals = signals_result.data or []

    # Last 10 conversation messages
    recent_messages = get_recent_messages(conversation_id, limit=10)

    sections: list[str] = []

    # Agent roster
    if agents:
        roster_lines = ["## Your Team"]
        for a in agents:
            template_name = ""
            if a.get("agent_templates"):
                template_name = a["agent_templates"].get("role", "")
            mem = a.get("memory_summary") or "No activity yet."
            roster_lines.append(
                f"- **{a['name']}** ({template_name}) — Status: {a['status']}\n"
                f"  Recent work: {_truncate(mem, max_tokens=100)}"
            )
        sections.append("\n".join(roster_lines))

    # Signals
    if signals:
        sig_lines = ["## Recent Intel"]
        for s in signals:
            sig_lines.append(f"[{s['signal_type'].upper()}] {s['content']}")
        sections.append("\n".join(sig_lines))

    # Conversation history
    if recent_messages:
        hist_lines = ["## Conversation History"]
        for m in recent_messages:
            hist_lines.append(f"{m['role'].upper()}: {m['content']}")
        sections.append("\n".join(hist_lines))

    full = "\n\n".join(sections)
    return _truncate(full, max_tokens=2200)
