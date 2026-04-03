"""Memory summarizer — weekly Sonnet summarization of agent activity.

Runs every Sunday at midnight UTC (per cron schedule).
Pulls last 7 days of agent_logs per active user_agent,
sends to Claude Sonnet, writes compressed summary back to
user_agents.memory_summary (replacing previous summary — NOT appending).

Run standalone:
  python -m app.workers.memory_summarizer
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import anthropic

from app.config import settings
from app.db.connection import get_service_client

_anthropic = anthropic.Anthropic(api_key=settings.anthropic_api_key)
_SONNET = "claude-sonnet-4-6"

_SUMMARIZE_PROMPT = """\
You are summarizing an AI agent's activity log for the past 7 days.
Write a compact paragraph (max 120 words) describing:
1. What the agent accomplished
2. Any recurring patterns or preferences you noticed
3. One thing the agent should remember for next week

Logs:
{logs}

Write only the summary paragraph. No headers. No bullet points."""


def _get_active_agents() -> list[dict]:
    db = get_service_client()
    result = (
        db.table("user_agents")
        .select("id, name, user_id")
        .eq("is_active", True)
        .is_("deleted_at", "null")
        .execute()
    )
    return result.data or []


def _get_week_logs(user_agent_id: str) -> list[dict]:
    db = get_service_client()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    result = (
        db.table("agent_logs")
        .select("status, trigger_type, output_data, error_message, started_at, duration_ms")
        .eq("user_agent_id", user_agent_id)
        .gt("started_at", week_ago)
        .order("started_at", desc=False)
        .execute()
    )
    return result.data or []


def _format_logs_for_summary(logs: list[dict]) -> str:
    if not logs:
        return "No activity this week."
    lines = []
    for log in logs:
        status = log.get("status", "unknown")
        started = log.get("started_at", "")[:10]
        duration = log.get("duration_ms")
        duration_str = f" ({duration}ms)" if duration else ""
        output = log.get("output_data") or {}
        summary_hint = output.get("summary", "")
        line = f"[{started}] {status}{duration_str}"
        if summary_hint:
            line += f" — {summary_hint}"
        if log.get("error_message"):
            line += f" ERROR: {log['error_message']}"
        lines.append(line)
    return "\n".join(lines)


def _write_summary(agent_id: str, summary: str) -> None:
    db = get_service_client()
    db.table("user_agents").update(
        {
            "memory_summary": summary,
            "memory_updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", agent_id).execute()


def summarize_agent(agent: dict) -> None:
    agent_id = agent["id"]
    agent_name = agent.get("name", agent_id)

    logs = _get_week_logs(agent_id)
    if not logs:
        print(f"[memory_summarizer] No logs for {agent_name} — skipping")
        return

    log_text = _format_logs_for_summary(logs)
    prompt = _SUMMARIZE_PROMPT.format(logs=log_text)

    response = _anthropic.messages.create(
        model=_SONNET,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    summary = response.content[0].text.strip()
    _write_summary(agent_id, summary)
    print(f"[memory_summarizer] Updated memory for {agent_name}")


def run_memory_summarizer() -> None:
    """Summarize all active agents' weekly activity."""
    agents = _get_active_agents()
    print(f"[memory_summarizer] Processing {len(agents)} agents...")
    for agent in agents:
        try:
            summarize_agent(agent)
        except Exception as exc:  # noqa: BLE001
            print(f"[memory_summarizer] ERROR for {agent.get('name')}: {exc}")


if __name__ == "__main__":
    run_memory_summarizer()
