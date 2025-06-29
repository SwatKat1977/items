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
from .testcase_custom_fields_api_view import TestcaseCustomFieldsApiView
from state_object import StateObject

# For admins
# POST   /api/web/admin/testcase_custom_fields          # create new
# PUT    /api/web/admin/testcase_custom_fields/45       # update existing
# DELETE /api/web/admin/testcase_custom_fields/45       # delete (optional)
# GET    /api/web/admin/testcase_custom_fields          # list all (optional)
# PATCH /api/wb/admin/testcase_custom_fields/45         # Move field position

def create_blueprint(logger: logging.Logger,
                     state_object: StateObject) -> Blueprint:
    view = TestcaseCustomFieldsApiView(logger, state_object)

    blueprint = Blueprint('admin_api', __name__)

    logger.debug("Registering ADMIN testcase custom fields routes:")

    logger.debug("=> /testcase_custom_fields [POST] : Add new field")

    @blueprint.route('/testcase_custom_fields', methods=['POST'])
    async def add_testcase_custom_field_request():
        return await view.add_custom_field()

    logger.debug("=> /testcase_custom_fields [PATCH] : Move position")

    @blueprint.route(
        '/testcase_custom_fields/<int:field_id>/<string:direction>',
        methods=['PATCH'])
    async def move_testcase_custom_field_request(field_id: int, direction: str):
        return await view.move_testcase_custom_field(field_id, direction)

    return blueprint
