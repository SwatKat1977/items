"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
from quart import Blueprint
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.routes.web.sessions.new_session_password_handler \
    import NewSessionPasswordHandler
from items.services.items_gateway.routes.web.sessions.delete_session_handler \
    import DeleteSessionHandler
from items.services.items_gateway.routes.web.sessions.refresh_session_handler \
    import RefreshSessionHandler
from items.services.items_gateway.routes.web.sessions.validate_session_handler \
    import ValidateSessionHandler
from items.services.items_gateway.sessions import Sessions


def create_sessions_routes(logger: logging.Logger,
                           sessions: Sessions,
                           configuration: GatewayConfiguration,
                           rest_client: RestClient) -> Blueprint:
    """
    Creates and registers a Quart Blueprint for handling authentication
    handshake API routes.

    This function initializes a `View` object with the provided SQL interface
    and logger, and then defines an API endpoint for authentication handshake.

    Args:
        logger (logging.Logger): A logger instance for logging messages.
        sessions (Sessions): A sessions instance.
        configuration (GatewayConfiguration): A gateway configuration instance.
        rest_client (RestClient) Instance of rest_client.

    Returns:
        Blueprint: A Quart `Blueprint` object containing the registered route.
    """
    sessions_routes = Blueprint("sessions_routes", __name__)

    new_session_password_handler: NewSessionPasswordHandler = \
        NewSessionPasswordHandler(logger,
                                  sessions,
                                  configuration,
                                  rest_client)
    delete_session_handler: DeleteSessionHandler = DeleteSessionHandler(logger,
                                                                        sessions)
    refresh_session_handler: RefreshSessionHandler = RefreshSessionHandler(
        logger, sessions)
    valid_session_handler: ValidateSessionHandler = ValidateSessionHandler(
        logger, sessions)

    logger.debug(" Sessions WEB routes:")

    logger.debug("=> %s POST /sessions",
                 "Log in/create new session".ljust(40))

    @sessions_routes.route('/sessions', methods=['POST'])
    async def create_new_session_request():
        # pylint: disable=no-value-for-parameter
        return await new_session_password_handler.create_new_session()

    logger.debug("=> %s POST /sessions/validate",
                 "Check if session is valid".ljust(40))

    @sessions_routes.route('/sessions/validate', methods=['POST'])
    async def session_validate_request():
        # pylint: disable=no-value-for-parameter
        return await valid_session_handler.validate_session()

    logger.debug("=> %s POST /sessions/refresh",
                 "Refresh session (remember me)".ljust(40))

    @sessions_routes.route('/sessions/refresh', methods=['POST'])
    async def refresh_session_request():
        return await refresh_session_handler.refresh_session()

    logger.debug("=> %s DELETE /sessions",
                 "Log out (invalidate session)".ljust(40))

    @sessions_routes.route('/sessions', methods=['DELETE'])
    async def logout_user():
        # pylint: disable=no-value-for-parameter
        return await delete_session_handler.delete_session()

    return sessions_routes
