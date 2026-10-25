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
from items.services.items_gateway.auth_decorators import (
    require_project_permission)
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.routes.web.folders.create_folder_handler \
    import CreateFolderHandler
from items.services.items_gateway.routes.web.folders.delete_folder_handler \
    import DeleteFolderHandler
from items.services.items_gateway.routes.web.folders.modify_folder_handler \
    import ModifyFolderHandler
from items.services.items_gateway.routes.web.folders.move_folder_handler \
    import MoveFolderHandler
from items.shared.permission_action import PermissionAction
from items.shared.permission_area import PermissionArea


def create_folders_routes(injections: RouteInjections) -> Blueprint:
    """Create the Blueprint containing section (folder) write routes.

    Sections are read through the test case list (``GET /<project_id>/
    testcases`` already returns the whole folder tree), so only the writes
    are routed here.

    Sections belong to the Test Cases area of the role grid, so every route
    requires a valid session and the **Test Cases** permission that matches
    what it does, checked with the Identity service on every request
    (``@require_project_permission``, see section 9.5 of
    ``design_docs/user_roles_design.md``): Add/Modify to create, rename or
    move a section, Delete to delete one. A member whose role does not grant it gets
    a 403, and so does a user who is not a member at all (they have an empty
    grid). Administrators are not special-cased: Identity grants them
    everything. Nothing is cached, so a change to a role or membership
    applies on the very next request.

    Deleting a section needs **Delete** whether or not ``cascade=true`` is
    sent, and not merely Add/Modify. A section's delete can destroy the test
    cases inside it, so it is authorised against what it destroys (rule 6 of
    section 8 of the design doc), and a narrow grant cannot become a wide one
    by going through the parent.

    The checks fail closed: if Identity cannot be reached or answers
    unexpectedly the route returns a 500, never access.

    The ``project_id`` of a route with no project in its path (``PATCH`` and
    ``DELETE /web/folders/<id>``, and ``POST /web/folders/<id>/move``) is a
    query parameter that the permission is
    checked against before ever calling CMS. That's safe despite being
    client-supplied: CMS independently verifies the section actually belongs
    to the stated project and 404s otherwise. Unlike the old membership
    check, the decorator never skips: a missing or malformed ``project_id``
    is a 400 before anything else happens.

    Registered routes (permission in brackets):
        - POST /<project_id>/folders [Add/Modify]:
            Create a section, at the top level or inside another section.
        - PATCH /folders/<folder_id>?project_id= [Add/Modify]:
            Rename a section.
        - POST /folders/<folder_id>/move?project_id= [Add/Modify]:
            Move a section under another section, or to the top level.
            Refused if the new parent is the section itself or one of its
            own sub-sections.
        - DELETE /folders/<folder_id>?project_id=[&cascade=true] [Delete]:
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
    handler_move: MoveFolderHandler = MoveFolderHandler(
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
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.ADD_MODIFY)
    async def create_folder_request(project_id: int):
        return await handler_create.create_folder(project_id)

    injections.logger.debug("=> %s PATCH /web/folders/<int:folder_id>",
                            "Rename a section".ljust(40))

    @routes.route('/folders/<int:folder_id>', methods=['PATCH'])
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.ADD_MODIFY)
    async def modify_folder_request(folder_id: int):
        return await handler_modify.modify_folder(folder_id)

    injections.logger.debug("=> %s POST /web/folders/<int:folder_id>/move",
                            "Move a section".ljust(40))

    @routes.route('/folders/<int:folder_id>/move', methods=['POST'])
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.ADD_MODIFY)
    async def move_folder_request(folder_id: int):
        return await handler_move.move_folder(folder_id)

    injections.logger.debug("=> %s DELETE /web/folders/<int:folder_id>",
                            "Delete a section".ljust(40))

    @routes.route('/folders/<int:folder_id>', methods=['DELETE'])
    @require_project_permission(
        injections, PermissionArea.TEST_CASES,
        PermissionAction.DELETE)
    async def delete_folder_request(folder_id: int):
        return await handler_delete.delete_folder(folder_id)

    return routes
