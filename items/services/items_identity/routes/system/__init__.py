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
from items.services.items_identity.routes.system.health_route import \
    create_blueprint as create_health_blueprint


def create_system_blueprints(logger: logging.Logger) -> quart.Blueprint:
    """Create and register system-related blueprints.

    This function creates the parent system blueprint and registers
    all system-level route blueprints, such as health check routes.

    Args:
        logger: Logger instance used by system route handlers.

    Returns:
        The configured system blueprint containing all registered
        system routes.
    """
    system_blueprint = quart.Blueprint("system_routes", __name__)

    # Health route
    system_blueprint.register_blueprint(
        create_health_blueprint(logger))

    return system_blueprint
