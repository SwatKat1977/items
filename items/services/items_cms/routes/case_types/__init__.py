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
from items.services.items_cms.repositories.case_types_repository import (
    CaseTypesRepository,
)
from items.services.items_cms.services.case_types_service import (
    CaseTypesService,
)
from .add_case_type_handler import AddCaseTypeHandler
from .get_case_type_handler import GetCaseTypeHandler
from .get_case_types_handler import GetCaseTypesHandler
from .update_case_type_handler import UpdateCaseTypeHandler
from .set_default_case_type_handler import SetDefaultCaseTypeHandler


def create_case_types_routes(logger: logging.Logger,
                             service_state: ServiceState,
                             config: CMSConfiguration) -> Blueprint:
    """Create and return the case types API Blueprint.

    Instantiates the repository and service once, wires them into
    individual route handlers, and registers all case type endpoints
    with a Quart Blueprint.

    No delete route yet - deliberately deferred to its own branch, along
    with wiring a case type onto test cases themselves (see
    cms_case_types_core's changes.md).

    Args:
        logger:        Parent logger instance.
        service_state: Shared service operational state.
        config:        CMS service configuration, used to locate the
                       database file.

    Returns:
        A configured Blueprint with all case type routes registered.
    """
    # pylint: disable=too-many-locals
    case_types_routes = Blueprint("case_types_routes", __name__)

    repository = CaseTypesRepository(logger, config)
    service = CaseTypesService(logger, service_state, repository)

    add_handler = AddCaseTypeHandler(logger, service)
    get_handler = GetCaseTypesHandler(logger, service)
    get_one_handler = GetCaseTypeHandler(logger, service)
    update_handler = UpdateCaseTypeHandler(logger, service)
    set_default_handler = SetDefaultCaseTypeHandler(logger, service)

    logger.debug("--- Registering Case Types API routes ---")

    logger.debug("=> %s POST /case_types",
                 "Add case type".ljust(40))

    @case_types_routes.route('/case_types', methods=['POST'])
    async def add_case_type():
        # pylint: disable=no-value-for-parameter
        return await add_handler.add_case_type()

    logger.debug("=> %s GET /case_types",
                 "Get case types".ljust(40))

    @case_types_routes.route('/case_types', methods=['GET'])
    async def get_case_types():
        return await get_handler.get_case_types()

    logger.debug("=> %s GET /case_types/<type_id>",
                 "Get case type".ljust(40))

    @case_types_routes.route('/case_types/<int:type_id>', methods=['GET'])
    async def get_case_type(type_id: int):
        return await get_one_handler.get_case_type(type_id)

    logger.debug("=> %s PATCH /case_types/<type_id>",
                 "Update case type".ljust(40))

    @case_types_routes.route('/case_types/<int:type_id>', methods=['PATCH'])
    async def update_case_type(type_id: int):
        # pylint: disable=no-value-for-parameter
        return await update_handler.update_case_type(type_id)

    logger.debug("=> %s POST /case_types/<type_id>/set_default",
                 "Set default case type".ljust(40))

    @case_types_routes.route(
        '/case_types/<int:type_id>/set_default', methods=['POST'])
    async def set_default_case_type(type_id: int):
        return await set_default_handler.set_default_case_type(type_id)

    return case_types_routes
