"""Outcome receipts worker — daily 7pm Telegram summary per client.

Phase 4 worker. Runs as a cron job:
  python -m app.workers.outcome_receipts

Queries today's agent_logs for each active client, summarizes via Claude API,
and sends the summary via Telegram.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.db.connection import get_service_client
from app.repositories import logs as log_repo


def get_active_clients() -> list[dict]:
    """Fetch all clients with at least one active agent."""
    db = get_service_client()
    result = (
        db.table("profiles")
        .select("id, full_name, email, timezone")
        .is_("deleted_at", "null")
        .execute()
    )
    return result.data or []


def generate_receipt(user_id: str, user_name: str) -> str | None:
    """Generate a daily outcome receipt for a user.

    Returns the formatted summary text, or None if no activity today.
    """
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

    logs = log_repo.list_logs_for_user_today(user_id, today_start)
    if not logs:
        return None

    # Format logs into a summary
    lines = [f"Daily Report for {user_name}", "=" * 40, ""]

    for log in logs:
        agent_name = "Unknown Agent"
        if log.get("user_agents"):
            agent_info = log["user_agents"]
            if agent_info.get("agent_templates"):
                agent_name = agent_info["agent_templates"].get("name", agent_name)
            elif agent_info.get("name"):
                agent_name = agent_info["name"]

        status_icon = {"completed": "done", "failed": "err", "running": "..."}.get(
            log.get("status", ""), "?"
        )
        lines.append(f"[{status_icon}] {agent_name}: {log.get('status', 'unknown')}")

        if log.get("output_data") and isinstance(log["output_data"], dict):
            summary = log["output_data"].get("summary", "")
            if summary:
                lines.append(f"    {summary}")
        lines.append("")

    completed = sum(1 for l in logs if l.get("status") == "completed")
    failed = sum(1 for l in logs if l.get("status") == "failed")
    lines.append(f"Total: {len(logs)} runs | {completed} completed | {failed} failed")

    return "\n".join(lines)


def send_telegram_message(chat_id: str, text: str) -> None:
    """Send a message via Telegram Bot API.

    Placeholder — requires TELEGRAM_BOT_TOKEN in env.
    """
    # TODO: Implement when Telegram bot is configured
    # import httpx
    # token = settings.telegram_bot_token
    # url = f"https://api.telegram.org/bot{token}/sendMessage"
    # httpx.post(url, json={"chat_id": chat_id, "text": text})
    print(f"[Telegram] Would send to {chat_id}:\n{text[:200]}...")


def run_outcome_receipts() -> None:
    """Generate and send outcome receipts for all active clients."""
    clients = get_active_clients()
    print(f"Processing {len(clients)} clients...")

    for client in clients:
        receipt = generate_receipt(client["id"], client.get("full_name", "User"))
        if receipt:
            # TODO: Get Telegram chat_id from client profile or separate table
            print(f"Receipt generated for {client.get('full_name', client['id'])}")
            # send_telegram_message(chat_id, receipt)
        else:
            print(f"No activity for {client.get('full_name', client['id'])}")


if __name__ == "__main__":
    run_outcome_receipts()
