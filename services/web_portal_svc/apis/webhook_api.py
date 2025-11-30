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
from apis.webhook_api_view import WebhookApiView
from metadata_settings import MetadataSettings


def create_blueprint(logger: logging.Logger,
                     metadata_settings: MetadataSettings) -> Blueprint:
    """
    Creates and registers a Quart Blueprint for handling webhook API routes.

    This function initializes a `View` object that defines an API endpoint for
    webhook api calls.

    Args:
        logger (logging.Logger): A logger instance for logging messages.
        metadata_settings (MetadataSettings): A metadata settings instances.

    Returns:
        Blueprint: A Quart `Blueprint` object containing the registered route.
    """
    view = WebhookApiView(logger, metadata_settings)

    blueprint = Blueprint('webhook_api', __name__)

    logger.debug("-------------- Registering Webhook routes ----------------")

    logger.debug("=> /webhook/update_metadata [POST] : Update metadata from "
                 "gateway")

    @blueprint.route('/webhook/update_metadata', methods=['POST'])
    async def update_metadata_request():
        return await view.update_metadata()

    return blueprint
