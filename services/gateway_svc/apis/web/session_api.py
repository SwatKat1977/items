"""
Copyright 2025 Integrated Test Management Suite Development Team

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
from .session_api_view import SessionApiView
from sessions import Sessions


def create_blueprint(logger: logging.Logger,
                     sessions: Sessions) -> Blueprint:
    """
    Creates and registers a Flask Blueprint for handling authentication
    handshake API routes.

    This function initializes a `View` object with the provided SQL interface
    and logger, and then defines an API endpoint for authentication handshake.

    Args:
        logger (logging.Logger): A logger instance for logging messages.
        sessions (Sessions): A sessions instance,
        prefix (str): API prefix (.e.g. /handshake)

    Returns:
        Blueprint: A Flask `Blueprint` object containing the registered route.
    """
    view = SessionApiView(logger, sessions)

    blueprint = Blueprint('session_api', __name__)

    logger.debug("Registering session endpoint:")

    logger.debug(f"=> {'Log in/create new session'.ljust(30)}"
                 "POST /web/session")

    @blueprint.route('/session', methods=['POST'])
    async def create_new_session_request():
        return await view.create_new_session()

    logger.debug(f"=> {'Check if session is valid'.ljust(30)}"
                 "GET /web/session/validate")

    @blueprint.route('/session/validate', methods=['POST'])
    async def session_validate_request():
        # pylint: disable=unused-variable
        return await view.validate_session()

    logger.debug(f"=> {'Log out (invalidate session)'.ljust(30)}"
                 "DELETE /web/session")

    @blueprint.route('/session', methods=['DELETE'])
    async def logout_user():
        # pylint: disable=unused-variable
        return await view.delete_session()
    return blueprint
