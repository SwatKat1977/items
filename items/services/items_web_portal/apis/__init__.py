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
import quart
from metadata_settings import MetadataSettings
from .auth_api import create_blueprint as create_auth_bp
from .dashboard_api import create_blueprint as create_dashboard_bp
from .projects_api import create_blueprint as create_projects_bp
from .webhook_api import create_blueprint as create_webhook_bp


def create_api_routes(logger: logging.Logger,
                      metadata_settings: MetadataSettings) -> quart.Blueprint:
    """
    Create and register all API route blueprints for the application.

    This function initializes a Quart Blueprint and registers sub-blueprints
    for health checks, project management, test case handling, and admin
    routes. Each sub-blueprint is assigned an appropriate URL prefix.

    Args:
        logger (logging.Logger): Logger instance for route logging.
        metadata_settings (MetadataSettings): Shared application state and configuration.

    Returns:
        quart.Blueprint: The assembled API blueprint with all routes
        registered.
    """
    web_bp = quart.Blueprint("api_routes", __name__)

    web_bp.register_blueprint(create_auth_bp(logger, metadata_settings))
    web_bp.register_blueprint(create_dashboard_bp(logger, metadata_settings))
    web_bp.register_blueprint(create_projects_bp(logger, metadata_settings))
    web_bp.register_blueprint(create_webhook_bp(logger, metadata_settings))

    return web_bp
