"""Order email sender — shared by web.py (internal chatbox) and v1 API."""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)


def _build_message(
    smtp_user: str,
    to: str,
    cc: str | None,
    subject: str,
    body: str,
    glb_path: str,
    tmf_path: "Path | str | None",
    order_id: "str | int",
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = to
    if cc:
        msg["Cc"] = cc
    msg.set_content(body)

    if tmf_path is not None and Path(str(tmf_path)).exists():
        msg.add_attachment(
            Path(str(tmf_path)).read_bytes(),
            maintype="application",
            subtype="octet-stream",
            filename=f"order_{order_id}.3mf",
        )

    if glb_path and Path(glb_path).exists():
        msg.add_attachment(
            Path(glb_path).read_bytes(),
            maintype="model",
            subtype="gltf-binary",
            filename=f"order_{order_id}.glb",
        )

    return msg


def send_order_email(
    order_id: str | int,
    brief: dict,
    total_egp: float,
    glb_path: str,
    tmf_path: "Path | str | None",
    model_url: str = "",
    order_type: str | None = None,
    customer_email: str | None = None,
    merchant_email: str | None = None,
) -> None:
    smtp_host    = os.environ.get("PRINT3D_SMTP_HOST", "smtp.gmail.com")
    smtp_port    = int(os.environ.get("PRINT3D_SMTP_PORT", "587"))
    smtp_user    = os.environ.get("PRINT3D_SMTP_USER", "")
    smtp_pass    = os.environ.get("PRINT3D_SMTP_PASS", "")
    cousin_email = merchant_email or os.environ.get("PRINT3D_COUSIN_EMAIL", "")

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

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)

        if order_type == "download" and customer_email:
            # Customer paid for a digital download — send files to them, CC merchant
            customer_body = (
                f"Your 3D model is ready for download.\n\n"
                f"Order ID  : #{order_id}\n"
                f"Total     : EGP {total_egp:.0f}\n\n"
                f"Brief\n"
                f"─────\n"
                f"{brief_lines}\n"
                f"{note_3mf}\n\n"
                f"Your .3mf and .glb files are attached. "
                f"Open the .3mf in Bambu Studio, Orca Slicer, or PrusaSlicer to print."
            )
            msg = _build_message(
                smtp_user=smtp_user,
                to=customer_email,
                cc=cousin_email,
                subject=f"Your 3D Model is Ready — Order #{order_id}",
                body=customer_body,
                glb_path=glb_path,
                tmf_path=tmf_path,
                order_id=order_id,
            )
            smtp.send_message(msg)
            logger.info("Download order email sent to %s (CC %s) for order #%s", customer_email, cousin_email, order_id)

        else:
            # Print order — send to merchant (cousin) for fulfillment
            merchant_body = (
                f"New 3D print order received.\n\n"
                f"Order ID  : #{order_id}\n"
                f"Total     : EGP {total_egp:.0f}\n"
                f"Customer  : {customer_email or 'N/A'}\n\n"
                f"Brief\n"
                f"─────\n"
                f"{brief_lines}\n"
                f"{note_3mf}\n\n"
                f"Files attached below. Open the .3mf in Bambu Studio to review and slice."
            )
            msg = _build_message(
                smtp_user=smtp_user,
                to=cousin_email,
                cc=None,
                subject=f"New 3D Print Order #{order_id} — EGP {total_egp:.0f}",
                body=merchant_body,
                glb_path=glb_path,
                tmf_path=tmf_path,
                order_id=order_id,
            )
            smtp.send_message(msg)
            logger.info("Print order email sent to %s for order #%s", cousin_email, order_id)
