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
from state_object import StateObject
from .testcase_custom_fields_api import create_blueprint as create_cf_bp


def create_admin_routes(logger: logging.Logger,
                        state: StateObject) -> quart.Blueprint:
    """
    Create and register admin-related API route blueprints.

    This function sets up the admin routes for the application by
    initializing an admin blueprint and registering the blueprint for
    managing custom testcase fields under the '/testcase_custom_fields'
    prefix.

    Args:
        logger (logging.Logger): Logger instance for admin logging.
        state (StateObject): Shared application state and configuration.

    Returns:
        quart.Blueprint: The admin API blueprint with registered routes.
    """
    admin_bp = quart.Blueprint("admin_routes", __name__)
    admin_bp.register_blueprint(create_cf_bp(logger, state), url_prefix="/testcase_custom_fields")
    return admin_bp
