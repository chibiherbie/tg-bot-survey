from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Sequence

from core.logs import logger
from services.base import BaseService


class EmailService(BaseService):
    async def send_email(  # noqa: PLR0913
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        from_email: str,
        to_emails: Sequence[str],
        subject: str,
        body: str,
    ) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = from_email
        message["To"] = ", ".join(to_emails)
        message.set_content(body)

        await asyncio.to_thread(
            self._send,
            host,
            port,
            username,
            password,
            use_tls,
            from_email,
            to_emails,
            message,
        )

    def _send(  # noqa: PLR0913
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        from_email: str,
        to_emails: Sequence[str],
        message: EmailMessage,
    ) -> None:
        try:
            if use_tls:
                with smtplib.SMTP(host, port, timeout=30) as smtp:
                    smtp.starttls()
                    if username and password:
                        smtp.login(username, password)
                    smtp.send_message(message, from_email, list(to_emails))
            else:
                with smtplib.SMTP(host, port, timeout=30) as smtp:
                    if username and password:
                        smtp.login(username, password)
                    smtp.send_message(message, from_email, list(to_emails))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to send email", exc_info=exc)
            raise
