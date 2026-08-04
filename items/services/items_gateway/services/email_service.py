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
from abc import ABC, abstractmethod


class EmailService(ABC):
    """Abstract base class for sending transactional emails.

    Implementations must provide an async ``send`` method. The interface is
    intentionally minimal — subject, body (plain text), and a single
    recipient. Callers are responsible for constructing the message content.
    """

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None:
        """Send a plain-text email.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Plain-text message body.

        Raises:
            EmailServiceError: If the message could not be delivered.
        """


class EmailServiceError(Exception):
    """Raised when an email cannot be sent."""
