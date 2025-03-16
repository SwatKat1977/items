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
from apis.dashboard_api_view import DashboardApiView
from metadata_settings import MetadataSettings


def create_blueprint(logger: logging.Logger,
                     metadata: MetadataSettings) -> Blueprint:
    """
    Creates and registers a Quart Blueprint for handling dashboard API routes.

    Args:
        logger (logging.Logger): A logger instance for logging messages.
        metadata (MetadataSettings): A metadata settings instance.

    Returns:
        Blueprint: A Quart `Blueprint` object containing the registered route.
    """
    view = DashboardApiView(logger, metadata)

    blueprint = Blueprint('dashboard_api', __name__)

    logger.info("Registering Dashboard endpoint:")

    logger.info("=> /admin/overview [GET]")

    @blueprint.route('/admin/overview', methods=['GET'])
    async def admin_overview_request():
        return await view.admin_overview()

    logger.info("=> /admin/site_settings [GET]")

    @blueprint.route('/admin/site_settings', methods=['GET'])
    async def admin_site_settings_request():
        return await view.admin_site_settings()

    return blueprint
