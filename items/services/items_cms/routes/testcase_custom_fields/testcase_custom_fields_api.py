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
from items_common.service_state import ServiceState
from .testcase_custom_fields_api_view import TestcaseCustomFieldsApiView


def create_blueprint(logger: logging.Logger,
                     state_object: ServiceState) -> Blueprint:

    # pylint: disable=no-value-for-parameter
    view = TestcaseCustomFieldsApiView(logger, state_object)

    blueprint = Blueprint('testcase_custom_fields_routes', __name__)

    logger.debug("--- Registering Testcases custom fields API routes ---")

    # Add new field.
    logger.debug("=> %s POST /testcase_custom_fields",
                 "Add new field".ljust(40))

    @blueprint.route('/testcase_custom_fields', methods=['POST'])
    async def add_testcase_custom_field_request():
        return await view.add_custom_field()

    # Move position of custom testcase field.
    logger.debug("=> %s PATCH /testcase_custom_fields/<int:field_id>",
                 "Move custom field position (up/down)".ljust(40))

    @blueprint.route('/testcase_custom_fields/<int:field_id>',
                     methods=['PATCH'])
    async def move_testcase_custom_field_request(field_id: int):
        return await view.move_testcase_custom_field(field_id)

    # Get custom testcase fields.
    logger.debug("=> %s GET /testcase_custom_fields",
                 "Get custom testcase fields".ljust(40))

    @blueprint.route('/testcase_custom_fields', methods=['GET'])
    async def get_custom_fields_request():
        return await view.get_custom_fields()

    # Update custom testcase field.
    logger.debug("=> %s PUT /testcase_custom_fields/<int:field_id>",
                 "Update custom testcase field".ljust(40))

    @blueprint.route('/testcase_custom_fields/<int:field_id>', methods=['PUT'])
    async def update_custom_field_request(field_id: int):
        return await view.update_custom_field(field_id)

    # Delete a custom testcase field.
    logger.debug("=> %s DELETE /testcase_custom_fields/<int:field_id>",
                 "Delete a custom testcase field".ljust(40))

    @blueprint.route('/testcase_custom_fields/<int:field_id>',
                     methods=['DELETE'])
    async def delete_custom_field_request(field_id: int):
        return await view.delete_custom_field(field_id)

    return blueprint
