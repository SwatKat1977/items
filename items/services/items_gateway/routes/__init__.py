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
from items.services.items_gateway.routes.web import create_web_routes


def create_routes(injections: RouteInjections) -> quart.Blueprint:
    """Create the public API routes.

    Creates and configures the root Blueprint for the gateway's public API.
    This function registers all public route groups, including the web API
    routes, under their respective URL prefixes.

    Args:
        injections: Container providing the shared dependencies required by
            the route factories, including the logger, session manager,
            configuration, and REST client.

    Returns:
        A configured Quart ``Blueprint`` containing the gateway's public API
        routes.
    """
    routes_bp = quart.Blueprint("public_routes", __name__)

    # Register web routes.
    routes_bp.register_blueprint(create_web_routes(injections),
                                 url_prefix="/web")

    return routes_bp
