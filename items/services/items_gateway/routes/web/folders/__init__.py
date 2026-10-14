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
from quart import Blueprint
from items.services.items_gateway.auth_decorators import require_project_member
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.folders.create_folder_handler \
    import CreateFolderHandler
from items.services.items_gateway.routes.web.folders.delete_folder_handler \
    import DeleteFolderHandler
from items.services.items_gateway.routes.web.folders.modify_folder_handler \
    import ModifyFolderHandler


def create_folders_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing section (folder) write routes.

    Sections are read through the test case list (``GET /<project_id>/
    testcases`` already returns the whole folder tree), so only the writes
    are routed here.

    Every route requires a valid session and membership of the project the
    section belongs to (``@require_project_member``); administrators bypass
    the check. As with test cases, writes are authorised by membership only
    for now: the per-area role grid is not enforced anywhere yet.

    The ``project_id`` of a route with no project in its path (``PATCH`` and
    ``DELETE /web/folders/<id>``) is a query parameter that membership is
    checked against before ever calling CMS. That's safe despite being
    client-supplied: CMS independently verifies the section actually belongs
    to the stated project and 404s otherwise. The decorator skips its check
    when the parameter is missing or malformed, so those handlers reject that
    with a 400 themselves.

    Registered routes:
        - POST /<project_id>/folders:
            Create a section, at the top level or inside another section.
        - PATCH /folders/<folder_id>?project_id=:
            Rename a section.
        - DELETE /folders/<folder_id>?project_id=[&cascade=true]:
            Delete a section. Refused with a 409 and a test case count if
            the section contains test cases, unless ``cascade=true``.

    Args:
        injections: Collection of shared application dependencies, including
            the logger, configuration, and REST client used by the route
            handlers.

    Returns:
        Blueprint: A configured Quart Blueprint containing the folder routes.
    """
    handler_create: CreateFolderHandler = CreateFolderHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)
    handler_modify: ModifyFolderHandler = ModifyFolderHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)
    handler_delete: DeleteFolderHandler = DeleteFolderHandler(
        injections.logger,
        injections.configuration,
        injections.rest_client)

    routes = Blueprint('folders_routes', __name__)

    injections.logger.debug(" Folders WEB routes:")

    injections.logger.debug("=> %s POST /web/<project_id>/folders",
                            "Create a section".ljust(40))

    @routes.route('/<int:project_id>/folders', methods=['POST'])
    @require_project_member(injections.sessions)
    async def create_folder_request(project_id: int):
        return await handler_create.create_folder(project_id)

    injections.logger.debug("=> %s PATCH /web/folders/<int:folder_id>",
                            "Rename a section".ljust(40))

    @routes.route('/folders/<int:folder_id>', methods=['PATCH'])
    @require_project_member(injections.sessions)
    async def modify_folder_request(folder_id: int):
        return await handler_modify.modify_folder(folder_id)

    injections.logger.debug("=> %s DELETE /web/folders/<int:folder_id>",
                            "Delete a section".ljust(40))

    @routes.route('/folders/<int:folder_id>', methods=['DELETE'])
    @require_project_member(injections.sessions)
    async def delete_folder_request(folder_id: int):
        return await handler_delete.delete_folder(folder_id)

    return routes
