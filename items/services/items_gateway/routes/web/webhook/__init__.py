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
from quart import Blueprint
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.webhook.get_metadata_handler \
    import GetMetadataHandler


def create_webhook_routes(injections: RouteInjections) -> Blueprint:

    handler_get_metadata_handler: GetMetadataHandler = GetMetadataHandler(
        injections.logger,
        injections.configuration,
        injections.metadata_handler)

    webhook_routes = Blueprint('webhook_routes', __name__)

    injections.logger.debug(" Webhook WEB routes:")

    # Get details of a specific project.
    injections.logger.debug("=> %s GET /web/webhook/metadata",
                            "Get webhook metadata".ljust(40))

    @webhook_routes.route('/webhook/metadata', methods=['GET'])
    async def get_metadata_request():
        return await handler_get_metadata_handler.get_metadata()

    return webhook_routes
