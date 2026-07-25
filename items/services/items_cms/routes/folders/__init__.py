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
from quart import Blueprint
from items.shared.service_state import ServiceState
from items.services.items_cms.cms_configuration import CMSConfiguration
from items.services.items_cms.repositories.folder_repository import (
    FolderRepository)
from items.services.items_cms.services.folder_service import FolderService
from .get_folder_handler import GetFolderHandler
from .list_folders_handler import ListFoldersHandler
from .add_folder_handler import AddFolderHandler
from .modify_folder_handler import ModifyFolderHandler
from .delete_folder_handler import DeleteFolderHandler


def create_folders_routes(logger: logging.Logger,
                          service_state: ServiceState,
                          config: CMSConfiguration) -> Blueprint:
    """Create and return the folders API Blueprint.

    Instantiates the folder repository and service once, wires them
    into individual route handlers, and registers all folder endpoints
    with a Quart Blueprint.

    Args:
        logger:        Parent logger instance.
        service_state: Shared service operational state.
        config:        CMS service configuration, used to locate the
                       database file.

    Returns:
        A configured Blueprint with all folder routes registered.
    """
    # pylint: disable=too-many-locals

    folders_routes = Blueprint("folders_routes", __name__)

    repository = FolderRepository(logger, config)
    service = FolderService(logger, service_state, repository)

    get_handler = GetFolderHandler(logger, service)
    list_handler = ListFoldersHandler(logger, service)
    add_handler = AddFolderHandler(logger, service)
    modify_handler = ModifyFolderHandler(logger, service)
    delete_handler = DeleteFolderHandler(logger, service)

    logger.debug("--- Registering Folders API routes ---")

    # Get details of a specific folder.
    logger.debug("=> %s GET /folders/<int:folder_id>",
                 "Get folder details".ljust(40))

    @folders_routes.route('/folders/<int:folder_id>', methods=['GET'])
    async def get_folder(folder_id: int):
        return await get_handler.get_folder(folder_id)

    # List all folders for a project.
    logger.debug("=> %s GET /folders?project_id=<id>",
                 "List folders for project".ljust(40))

    @folders_routes.route('/folders', methods=['GET'])
    async def list_folders():
        return await list_handler.list_folders()

    # Create a folder.
    logger.debug("=> %s POST /folders",
                 "Create new folder".ljust(40))

    @folders_routes.route('/folders', methods=['POST'])
    async def add_folder():
        # pylint: disable=no-value-for-parameter
        return await add_handler.add_folder()

    # Rename a folder.
    logger.debug("=> %s PATCH /folders/<int:folder_id>",
                 "Rename folder".ljust(40))

    @folders_routes.route('/folders/<int:folder_id>', methods=['PATCH'])
    async def modify_folder(folder_id: int):
        # pylint: disable=no-value-for-parameter
        return await modify_handler.modify_folder(folder_id)

    # Delete a folder.
    logger.debug("=> %s DELETE /folders/<int:folder_id>",
                 "Delete a folder".ljust(40))

    @folders_routes.route('/folders/<int:folder_id>', methods=['DELETE'])
    async def delete_folder(folder_id: int):
        return await delete_handler.delete_folder(folder_id)

    return folders_routes
