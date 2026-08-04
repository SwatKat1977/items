"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
from email.message import EmailMessage
import aiosmtplib
from items.services.items_gateway.services.email_service import (
    EmailService, EmailServiceError)


class SmtpEmailService(EmailService):
    """Email service implementation that sends via SMTP using aiosmtplib.

    Works with any SMTP relay, including a local ``aiosmtpd`` daemon for
    development and production relays (SendGrid, Mailgun, AWS SES, etc.).

    Authentication is optional: if ``username`` and ``password`` are both
    ``None`` or empty strings, the connection is made without credentials
    (suitable for a local dev relay that does not require authentication).

    Args:
        logger: Logger for diagnostic output.
        host: SMTP server hostname or IP address.
        port: SMTP server port (typically 587 for STARTTLS, 465 for SSL,
              or 1025 for a local dev relay).
        username: SMTP authentication username. May be ``None``.
        password: SMTP authentication password. May be ``None``.
        from_address: The ``From:`` address used on all outgoing messages.
        use_tls: If ``True``, connect with STARTTLS (default ``True``).
                 Set to ``False`` for a plain local dev relay.
    """
    # pylint: disable=too-few-public-methods

    def __init__(
            self,
            logger: logging.Logger,
            host: str,
            port: int,
            username: str | None,
            password: str | None,
            from_address: str,
            use_tls: bool = True) -> None:
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        self._logger = logger.getChild(type(self).__name__)
        self._host = host
        self._port = port
        self._username = username or None
        self._password = password or None
        self._from_address = from_address
        self._use_tls = use_tls

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send a plain-text email via SMTP.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Plain-text message body.

        Raises:
            EmailServiceError: If the SMTP connection fails or the message
                               is rejected by the server.
        """
        message = EmailMessage()
        message["From"] = self._from_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                start_tls=self._use_tls,
            )
            self._logger.info("Email sent to %s: %s", to, subject)

        except aiosmtplib.SMTPException as exc:
            self._logger.error(
                "Failed to send email to %s: %s", to, str(exc))
            raise EmailServiceError(
                f"Failed to send email to {to}: {exc}") from exc

        except (OSError, TimeoutError) as exc:
            # Catches raw socket/connection errors that aiosmtplib may not wrap
            # (e.g. connection refused before SMTP negotiation begins).
            self._logger.error(
                "Network error sending email to %s: %s", to, str(exc))
            raise EmailServiceError(
                f"Network error sending email to {to}: {exc}") from exc
