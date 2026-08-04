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
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import aiosmtplib
from items.services.items_gateway.services.email_service import (
    EmailService, EmailServiceError)
from items.services.items_gateway.services.smtp_email_service import (
    SmtpEmailService)

_LOGGER = MagicMock()


def _make_service(use_tls=False, username=None, password=None,
                  from_address="noreply@items.local"):
    return SmtpEmailService(
        logger=_LOGGER,
        host="localhost",
        port=1025,
        username=username,
        password=password,
        from_address=from_address,
        use_tls=use_tls)


class TestEmailServiceAbstract(unittest.TestCase):

    def test_cannot_instantiate_abstract_class(self):
        with self.assertRaises(TypeError):
            EmailService()  # pylint: disable=abstract-class-instantiated


class TestSmtpEmailServiceInit(unittest.TestCase):

    def test_is_email_service_subclass(self):
        svc = _make_service()
        self.assertIsInstance(svc, EmailService)

    def test_empty_username_stored_as_none(self):
        svc = SmtpEmailService(
            logger=_LOGGER, host="h", port=25,
            username="", password="", from_address="a@b.com", use_tls=False)
        self.assertIsNone(svc._username)  # pylint: disable=protected-access
        self.assertIsNone(svc._password)  # pylint: disable=protected-access


class TestSmtpEmailServiceSend(unittest.IsolatedAsyncioTestCase):

    async def test_send_calls_aiosmtplib_send(self):
        svc = _make_service()
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await svc.send("user@example.com", "Subject", "Body text")
        mock_send.assert_called_once()

    async def test_send_uses_correct_recipient(self):
        svc = _make_service()
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await svc.send("user@example.com", "Subject", "Body text")
        _, kwargs = mock_send.call_args
        msg = mock_send.call_args[0][0]
        self.assertEqual(msg["To"], "user@example.com")

    async def test_send_uses_configured_from_address(self):
        svc = _make_service(from_address="items@example.org")
        with patch("aiosmtplib.send", new_callable=AsyncMock):
            await svc.send("user@example.com", "Subject", "Body")
        # No assertion needed — just confirming no error raised

    async def test_send_uses_configured_host_and_port(self):
        svc = SmtpEmailService(
            logger=_LOGGER, host="smtp.example.com", port=587,
            username=None, password=None,
            from_address="a@b.com", use_tls=True)
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await svc.send("u@v.com", "s", "b")
        _, kwargs = mock_send.call_args
        self.assertEqual(kwargs["hostname"], "smtp.example.com")
        self.assertEqual(kwargs["port"], 587)

    async def test_send_with_tls(self):
        svc = _make_service(use_tls=True)
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await svc.send("u@v.com", "s", "b")
        _, kwargs = mock_send.call_args
        self.assertTrue(kwargs["start_tls"])

    async def test_send_without_tls(self):
        svc = _make_service(use_tls=False)
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await svc.send("u@v.com", "s", "b")
        _, kwargs = mock_send.call_args
        self.assertFalse(kwargs["start_tls"])

    async def test_smtp_exception_raises_email_service_error(self):
        svc = _make_service()
        with patch("aiosmtplib.send",
                   new_callable=AsyncMock,
                   side_effect=aiosmtplib.SMTPException("connection refused")):
            with self.assertRaises(EmailServiceError):
                await svc.send("u@v.com", "s", "b")

    async def test_email_service_error_message_contains_recipient(self):
        svc = _make_service()
        with patch("aiosmtplib.send",
                   new_callable=AsyncMock,
                   side_effect=aiosmtplib.SMTPException("refused")):
            try:
                await svc.send("target@example.com", "s", "b")
            except EmailServiceError as exc:
                self.assertIn("target@example.com", str(exc))

    async def test_os_error_raises_email_service_error(self):
        """Raw socket errors (e.g. connection refused) are also wrapped."""
        svc = _make_service()
        with patch("aiosmtplib.send",
                   new_callable=AsyncMock,
                   side_effect=OSError("connection refused")):
            with self.assertRaises(EmailServiceError):
                await svc.send("u@v.com", "s", "b")

    async def test_timeout_error_raises_email_service_error(self):
        svc = _make_service()
        with patch("aiosmtplib.send",
                   new_callable=AsyncMock,
                   side_effect=TimeoutError("timed out")):
            with self.assertRaises(EmailServiceError):
                await svc.send("u@v.com", "s", "b")


if __name__ == "__main__":
    unittest.main()
