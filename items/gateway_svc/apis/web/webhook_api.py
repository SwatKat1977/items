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
from .webhook_api_view import WebhookApiView
from metadata_handler import MetadataHandler


def create_blueprint(logger: logging.Logger,
                     metadata_handler: MetadataHandler,
                     prefix: str) -> Blueprint:
    view = WebhookApiView(logger, metadata_handler)

    blueprint = Blueprint('webhook_api', __name__)

    logger.debug("Registering WEB Webhook endpoints:")

    logger.debug("=> %s/get_metadata [GET]", prefix)

    @blueprint.route('/get_metadata', methods=['GET'])
    async def get_metadata_request():
        return await view.get_metadata()

    return blueprint
