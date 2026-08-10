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
import quart
from items.services.items_identity.identity_configuration import (
    IdentityConfiguration)
from .get_invites_handler import GetInvitesHandler
from .create_invite_handler import CreateInviteHandler
from .resend_invite_handler import ResendInviteHandler
from .uninvite_handler import UninviteHandler


def create_invite_routes(logger: logging.Logger,
                         config: IdentityConfiguration) -> quart.Blueprint:
    """Create and configure invite management routes.

    Registered routes:

    * ``GET  /invites``           - List all pending invites.
    * ``POST /invites``          - Create a new pending invite.
    * ``POST /invites/resend``   - Refresh token and expiry on an existing invite.
    * ``POST /invites/uninvite`` - Cancel (soft-expire) a pending invite.

    Args:
        logger: Logger used for route registration and request handling.
        config: Identity service configuration.

    Returns:
        A configured Quart blueprint containing all invite routes.
    """
    invite_routes = quart.Blueprint("invite_routes", __name__)

    handler_get = GetInvitesHandler(logger, config)
    handler_create = CreateInviteHandler(logger, config)
    handler_resend = ResendInviteHandler(logger, config)
    handler_uninvite = UninviteHandler(logger, config)

    logger.debug("Registering Invite API routes:")

    logger.debug("=> %s GET  /invites",
                 "List pending invites".ljust(40))
    logger.debug("=> %s POST /invites",
                 "Create invite".ljust(40))
    logger.debug("=> %s POST /invites/resend",
                 "Resend invite".ljust(40))
    logger.debug("=> %s POST /invites/uninvite",
                 "Uninvite".ljust(40))

    # pylint: disable=no-value-for-parameter

    @invite_routes.route('/invites', methods=['GET'])
    async def get_invites_request():
        return await handler_get.get_invites()

    @invite_routes.route('/invites', methods=['POST'])
    async def create_invite_request():
        return await handler_create.create_invite()

    @invite_routes.route('/invites/resend', methods=['POST'])
    async def resend_invite_request():
        return await handler_resend.resend_invite()

    @invite_routes.route('/invites/uninvite', methods=['POST'])
    async def uninvite_request():
        return await handler_uninvite.uninvite()

    return invite_routes
