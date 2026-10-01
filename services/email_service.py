from __future__ import annotations

import logging
import json
import smtplib
from email.message import EmailMessage
from urllib.request import Request, urlopen

from flask import current_app


logger = logging.getLogger(__name__)


def send_email(*, to: str, subject: str, text: str) -> None:
    """Send transactional email using the configured backend.

    The ``console`` backend is intentionally safe for local development and tests.
    Production can use any SMTP provider by supplying the SMTP environment values.
    """
    backend = current_app.config.get("EMAIL_BACKEND", "console").strip().lower()

    if backend == "console":
        outbox = current_app.extensions.setdefault("email_outbox", [])
        outbox.append({"to": to, "subject": subject, "text": text})
        logger.info("Transactional email queued for console backend: to=%s subject=%s", to, subject)
        return

    if backend == "resend":
        api_key = current_app.config.get("RESEND_API_KEY", "")
        sender = current_app.config.get("EMAIL_FROM", "")
        if not api_key or not sender:
            raise RuntimeError("RESEND_API_KEY and AVATARFORGE_EMAIL_FROM are required for Resend email.")
        body = json.dumps({"from": sender, "to": [to], "subject": subject, "text": text}).encode("utf-8")
        request = Request(
            "https://api.resend.com/emails",
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            if response.status >= 300:
                raise RuntimeError(f"Resend email failed with status {response.status}.")
        return

    if backend != "smtp":
        raise RuntimeError(f"Unsupported email backend: {backend}")

    host = current_app.config.get("SMTP_HOST", "")
    port = int(current_app.config.get("SMTP_PORT", 587))
    username = current_app.config.get("SMTP_USERNAME", "")
    password = current_app.config.get("SMTP_PASSWORD", "")
    sender = current_app.config.get("EMAIL_FROM", "")
    use_tls = bool(current_app.config.get("SMTP_USE_TLS", True))

    if not host or not sender:
        raise RuntimeError("SMTP_HOST and AVATARFORGE_EMAIL_FROM are required for SMTP email.")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)

    with smtplib.SMTP(host, port, timeout=20) as client:
        if use_tls:
            client.starttls()
        if username:
            client.login(username, password)
        client.send_message(message)
