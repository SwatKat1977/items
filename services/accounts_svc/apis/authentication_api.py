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
from apis.authentication_api_view import AuthenticationApiView
from state_object import StateObject


def create_blueprint(logger: logging.Logger,
                     state_object: StateObject) -> Blueprint:
    """
    Creates and registers a Quart Blueprint for handling authentication.

    This function initializes a `View` object with the provided logger, and
    then defines an API endpoints for authentication.

    Args:
        logger (logging.Logger): A logger instance for logging messages.
        state_object (StateObject): A StateObject instance.

    Returns:
        Blueprint: A Flask `Blueprint` object containing the registered route.
    """
    view = AuthenticationApiView(logger, state_object)

    blueprint = Blueprint('authentication_api', __name__)

    logger.debug("Registering Authentication API routes:")

    logger.debug("=> /authentication/basic [POST]")

    # pylint: disable=no-value-for-parameter
    @blueprint.route('/basic', methods=['POST'])
    async def authenticate_basic_request():
        return await view.authenticate_basic()

    return blueprint
