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
from items.services.items_cms.cms_configuration import CMSConfiguration
from .projects import create_projects_routes
from .folders import create_folders_routes
from .testcases import create_testcases_routes
from .testcase_custom_fields import create_testcase_custom_fields_routes
from .testcase_field_values import create_testcase_field_values_routes
from .system import create_system_routes


def create_routes(logger: logging.Logger,
                  state: ServiceState,
                  configuration: CMSConfiguration) -> quart.Blueprint:
    """Create and register all CMS API routes.

    This function creates the root API blueprint for the CMS service and
    registers all feature-specific route blueprints.

    Args:
        logger: Logger instance used for route registration and diagnostics.
        state: Shared service state object containing runtime dependencies.
        configuration: CMS service configuration.

    Returns:
        A Quart blueprint containing all registered CMS API routes.
    """
    routes_bp = quart.Blueprint("api_routes", __name__)

    routes_bp.register_blueprint(create_projects_routes(logger,
                                                        state,
                                                        configuration))
    routes_bp.register_blueprint(create_folders_routes(logger,
                                                       state,
                                                       configuration))
    routes_bp.register_blueprint(create_testcases_routes(logger,
                                                         state,
                                                         configuration))
    routes_bp.register_blueprint(create_testcase_custom_fields_routes(
        logger, state, configuration))
    routes_bp.register_blueprint(create_testcase_field_values_routes(
        logger, state, configuration))
    routes_bp.register_blueprint(create_system_routes(logger, state))

    return routes_bp
