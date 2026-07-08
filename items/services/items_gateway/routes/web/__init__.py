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
import quart
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.projects import (
    create_projects_routes)
from items.services.items_gateway.routes.web.sessions import (
    create_sessions_routes)
from items.services.items_gateway.routes.web.webhook import (
    create_webhook_routes)


def create_web_routes(injections: RouteInjections) -> quart.Blueprint:
    """Create and register all CMS API routes.

    Top-level function to create the WEB routes for the Gateway service and
    registers all feature-specific route blueprints.

    Args:
        injections: Container providing the shared dependencies required by
            the route factories, including the logger, session manager,
            configuration, and REST client.

    Returns:
        A Quart blueprint containing all registered Gateway API routes.
    """
    routes_bp = quart.Blueprint("api_routes", __name__)

    injections.logger.debug("|--- Registering WEB routes ---|")

    # Register sessions routes.
    routes_bp.register_blueprint(create_sessions_routes(injections.logger,
                                                        injections.sessions,
                                                        injections.configuration,
                                                        injections.rest_client))

    # Register projects routes.
    routes_bp.register_blueprint(create_projects_routes(
        injections.logger,
        injections.configuration,
        injections.rest_client))

    # Register Webhook routes.
    routes_bp.register_blueprint(create_webhook_routes(injections))

    return routes_bp
