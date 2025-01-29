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
from sqlite_interface import SqliteInterface
from apis.basic_authentication_api_view import BasicAuthenticationApiView


def create_blueprint(sql_interface: SqliteInterface,
                     logger: logging.Logger) -> Blueprint:
    """
    Creates and registers a Flask Blueprint for handling basic authentication API routes.

    This function initializes a `View` object with the provided SQL interface and logger,
    and then defines an API endpoint for authentication. It registers the route
    `/basic_auth/authenticate` with the POST method to handle authentication requests.

    Args:
        sql_interface (SqliteInterface): An instance of the `SqliteInterface` class used for
                                         database operations.
        logger (logging.Logger): A logger instance for logging messages.

    Returns:
        Blueprint: A Flask `Blueprint` object containing the registered route.

    Example:
        >>> from flask import Flask
        >>> from your_module import create_blueprint
        >>> app = Flask(__name__)
        >>> blueprint = create_blueprint(sql_interface, logger)
        >>> app.register_blueprint(blueprint)
    """
    view = BasicAuthenticationApiView(sql_interface, logger)

    blueprint = Blueprint('basic_auth_api', __name__)

    logger.info("Registering Basic Authentication API:")
    logger.info("=> basic_auth/authenticate [POST]")

    @blueprint.route('/basic_auth/authenticate', methods=['POST'])
    async def authenticate_request():
        return await view.authenticate()

    return blueprint
