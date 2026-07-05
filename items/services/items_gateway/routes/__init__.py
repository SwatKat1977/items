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
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.sessions import Sessions
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.routes.web import create_web_routes


def create_routes(logger: logging.Logger,
                  sessions_instance: Sessions,
                  configuration: GatewayConfiguration,
                  rest_client: RestClient) -> quart.Blueprint:
    """Create and register routes for web.

    This function creates the root API blueprint for the Gateway service and
    registers all feature-specific route blueprints.

    Args:
        logger: Logger instance used for route registration and diagnostics.
        sessions_instance: User sessions.
        configuration (GatewayConfiguration): Gateway configuration.
        rest_client (RestClient) Instance of rest_client.

    Returns:
        A Quart blueprint containing all registered Gateway API routes.
    """
    routes_bp = quart.Blueprint("public_routes", __name__)

    # Register web routes.
    routes_bp.register_blueprint(create_web_routes(logger,
                                                   sessions_instance,
                                                   configuration,
                                                   rest_client),
                                 url_prefix="/web")

    return routes_bp
