"""Order email sender — shared by web.py (internal chatbox) and v1 API."""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)


def send_order_email(
    order_id: str | int,
    brief: dict,
    total_egp: float,
    glb_path: str,
    tmf_path: "Path | str | None",
    model_url: str = "",
) -> None:
    smtp_host    = os.environ.get("PRINT3D_SMTP_HOST", "smtp.gmail.com")
    smtp_port    = int(os.environ.get("PRINT3D_SMTP_PORT", "587"))
    smtp_user    = os.environ.get("PRINT3D_SMTP_USER", "")
    smtp_pass    = os.environ.get("PRINT3D_SMTP_PASS", "")
    cousin_email = os.environ.get("PRINT3D_COUSIN_EMAIL", "")

    if not all([smtp_user, smtp_pass, cousin_email]):
        logger.error(
            "SMTP not configured — set PRINT3D_SMTP_USER, PRINT3D_SMTP_PASS, "
            "PRINT3D_COUSIN_EMAIL in .env to enable order emails"
        )
        return

    brief_lines = "\n".join(f"  {k}: {v}" for k, v in brief.items()) if brief else "  (no brief recorded)"
    note_3mf = ""
    if tmf_path is None:
        note_3mf = "\n⚠️  3MF conversion failed — use the GLB fallback or re-generate the model."
        if model_url:
            note_3mf += f"\nOriginal Meshy model URL: {model_url}"

    body = (
        f"New 3D print order received.\n\n"
        f"Order ID  : #{order_id}\n"
        f"Total     : EGP {total_egp:.0f}\n\n"
        f"Brief\n"
        f"─────\n"
        f"{brief_lines}\n"
        f"{note_3mf}\n\n"
        f"Files attached below. Open the .3mf in Bambu Studio to review and slice."
    )

    msg = EmailMessage()
    msg["Subject"] = f"New 3D Print Order #{order_id} — EGP {total_egp:.0f}"
    msg["From"]    = smtp_user
    msg["To"]      = cousin_email
    msg.set_content(body)

    if tmf_path is not None and Path(str(tmf_path)).exists():
        msg.add_attachment(
            Path(str(tmf_path)).read_bytes(),
            maintype="application",
            subtype="octet-stream",
            filename=f"order_{order_id}.3mf",
        )

    if Path(glb_path).exists():
        msg.add_attachment(
            Path(glb_path).read_bytes(),
            maintype="model",
            subtype="gltf-binary",
            filename=f"order_{order_id}.glb",
        )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)

    logger.info("Order email sent to %s for order #%s", cousin_email, order_id)
