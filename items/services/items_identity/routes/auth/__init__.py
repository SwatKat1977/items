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
from items.shared.service_state import ServiceState
from items.services.items_identity.routes.auth.authentication_routes import (
    create_blueprint as create_auth_routes)


def create_auth_blueprints(logger: logging.Logger,
                           state_object: ServiceState) -> quart.Blueprint:
    """Create and register auth-related blueprints.

    This function creates the parent auth blueprint and registers
    all auth-level route blueprints, such as login, logout and register routes.

    Args:
        logger: Logger instance used by route handlers.
        state_object (ServiceState): A StateObject instance.

    Returns:
        The configured  blueprint containing all registered routes.
    """
    auth_blueprint = quart.Blueprint("auth_routes", __name__)

    auth_blueprint.register_blueprint(create_auth_routes(logger, state), url_prefix="/authentication")

    return system_blueprint
