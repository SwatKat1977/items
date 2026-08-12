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
from quart import Blueprint
from items.services.items_gateway.auth_decorators import require_administrator
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.invites.get_invites_handler import (
    GetInvitesHandler)
from items.services.items_gateway.routes.web.invites.create_invite_handler import (
    CreateInviteHandler)
from items.services.items_gateway.routes.web.invites.resend_invite_handler import (
    ResendInviteHandler)
from items.services.items_gateway.routes.web.invites.uninvite_handler import (
    UninviteHandler)
from items.services.items_gateway.routes.web.invites.accept_invite_handler import (
    AcceptInviteHandler)
from items.services.items_gateway.routes.web.invites.get_invite_by_token_handler import (
    GetInviteByTokenHandler)


def create_invite_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing invite management web routes.

    The management routes are admin-only, enforced here via
    ``@require_administrator`` rather than trusted to the caller - the web
    portal also checks ``is_administrator`` before calling, but that is UX,
    not the security boundary.

    ``GET /invites/token/<token>`` and ``POST /accept_invite`` are the
    exceptions: both are **deliberately unauthenticated**, because the
    person redeeming an invitation does not yet have an account. The invite
    token authorises those requests instead - they are explicitly left
    undecorated rather than being caught by a blanket rule.

    Registered routes:
        GET  /invites              List all pending invites. (admin)
        POST /invites              Create a new pending invite. (admin)
        POST /invites/resend       Refresh token and expiry on an existing invite. (admin)
        POST /invites/uninvite     Cancel (soft-expire) a pending invite. (admin)
        GET  /invites/token/<token> Resolve an invite token. (unauthenticated)
        POST /accept_invite        Redeem an invitation. (unauthenticated)

    Args:
        injections: Shared application dependencies.

    Returns:
        A configured Quart Blueprint.
    """
    # pylint: disable=too-many-locals

    routes = Blueprint('invites_routes', __name__)

    handler_get = GetInvitesHandler(
        injections.logger, injections.configuration, injections.rest_client)
    handler_accept = AcceptInviteHandler(
        injections.logger, injections.configuration, injections.rest_client,
        injections.email_service)
    handler_by_token = GetInviteByTokenHandler(
        injections.logger, injections.configuration, injections.rest_client)

    # Both of these send mail: creating an invite emails the invitation, and
    # resending it regenerates the token and emails the new link. Omitting the
    # email service leaves them silently issuing invites nobody receives.
    handler_create = CreateInviteHandler(
        injections.logger, injections.configuration, injections.rest_client,
        injections.email_service)
    handler_resend = ResendInviteHandler(
        injections.logger, injections.configuration, injections.rest_client,
        injections.email_service)
    handler_uninvite = UninviteHandler(
        injections.logger, injections.configuration, injections.rest_client)

    injections.logger.debug(" Invites WEB routes:")

    injections.logger.debug("=> %s GET  /web/invites",
                            "List pending invites".ljust(40))

    @routes.route('/invites', methods=['GET'])
    @require_administrator(injections.sessions)
    async def get_invites_request():
        return await handler_get.get_invites()

    injections.logger.debug("=> %s POST /web/invites",
                            "Create invite".ljust(40))

    @routes.route('/invites', methods=['POST'])
    @require_administrator(injections.sessions)
    async def create_invite_request():
        return await handler_create.create_invite()

    injections.logger.debug("=> %s POST /web/invites/resend",
                            "Resend invite".ljust(40))

    @routes.route('/invites/resend', methods=['POST'])
    @require_administrator(injections.sessions)
    async def resend_invite_request():
        return await handler_resend.resend_invite()

    injections.logger.debug("=> %s GET  /web/invites/token/<token>",
                            "Resolve invite token (unauthenticated)".ljust(40))

    @routes.route('/invites/token/<string:token>', methods=['GET'])
    async def get_invite_by_token_request(token: str):
        return await handler_by_token.get_invite_by_token(token)

    injections.logger.debug("=> %s POST /web/accept_invite",
                            "Accept invite (unauthenticated)".ljust(40))

    @routes.route('/accept_invite', methods=['POST'])
    async def accept_invite_request():
        return await handler_accept.accept_invite()

    injections.logger.debug("=> %s POST /web/invites/uninvite",
                            "Uninvite".ljust(40))

    @routes.route('/invites/uninvite', methods=['POST'])
    @require_administrator(injections.sessions)
    async def uninvite_request():
        return await handler_uninvite.uninvite()

    return routes
