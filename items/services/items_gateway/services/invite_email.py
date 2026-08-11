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
from http import HTTPStatus
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.services.email_service import (
    EmailService, EmailServiceError)

INVITE_SUBJECT: str = "You have been invited to ITEMS"

# Portal path the invitation link points at. The recipient exchanges the token
# there for an account.
INVITE_ACCEPT_PATH: str = "/accept_invite"


def build_invite_url(portal_url: str, token: str) -> str:
    """Build the link an invited user follows to accept their invitation.

    Args:
        portal_url: Base URL of the web portal.
        token:      The invite token issued by the identity service.

    Returns:
        The absolute URL to include in the invitation email.
    """
    return f"{portal_url.rstrip('/')}{INVITE_ACCEPT_PATH}?token={token}"


def build_invite_body(portal_url: str, token: str) -> str:
    """Build the body of an invitation email.

    Args:
        portal_url: Base URL of the web portal.
        token:      The invite token issued by the identity service.

    Returns:
        The plain-text email body.
    """
    return (
        "Hello,\n\n"
        "You have been invited to join ITEMS.\n\n"
        "To accept the invitation and set up your account, follow this link:\n"
        f"{build_invite_url(portal_url, token)}\n\n"
        "This invitation will expire. If it does, ask an administrator to "
        "send you a new one.\n\n"
        "If you were not expecting this invitation you can ignore this "
        "message.\n"
    )


async def send_invite_email(logger: logging.Logger,
                            email_service: EmailService | None,
                            portal_url: str,
                            response: ApiResponse,
                            email_address: str,
                            expected_status: HTTPStatus) -> None:
    """Email an invitation, if the invite was issued successfully.

    Shared by the create and resend handlers so the two cannot drift apart.
    Delivery failures are logged rather than raised: the invite already exists
    in the identity service, and the caller's request succeeded. Raising here
    would report failure for an operation that did in fact happen.

    Args:
        logger:          Logger used to record delivery problems.
        email_service:   Service used to send the message. When None, no mail
            is configured and the send is skipped.
        portal_url:      Base URL of the web portal, used to build the link.
        response:        The identity service's response to the invite request.
        email_address:   Recipient of the invitation.
        expected_status: The status indicating the invite was issued (created
            for a new invite, OK for a resend).
    """
    # pylint: disable=too-many-arguments, too-many-positional-arguments

    if email_service is None:
        logger.warning(
            "No email service configured; invitation for %s was not sent",
            email_address)
        return

    if response.status_code != expected_status:
        return

    token = (response.body or {}).get("token")
    if not token:
        logger.error(
            "Identity service issued an invite for %s without a token; "
            "cannot send the invitation email", email_address)
        return

    try:
        await email_service.send(
            to=email_address,
            subject=INVITE_SUBJECT,
            body=build_invite_body(portal_url, token))

    except EmailServiceError as exc:
        logger.error("Failed to send invitation email to %s: %s",
                     email_address, exc)
