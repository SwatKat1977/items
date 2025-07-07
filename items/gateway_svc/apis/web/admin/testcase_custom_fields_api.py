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


def create_blueprint(logger: logging.Logger) -> Blueprint:
    view = TestcaseCustomFieldsApiView(logger)

    blueprint = Blueprint('admin_tc_custom_fields_api', __name__)

    logger.debug("Registering WEB ADMIN TC custom fields endpoint:")

    logger.debug(f"=> {'Modify a TC custom field'.ljust(30)}"
                 "PATCH /web/admin/testcase_custom_fields")

    @blueprint.route('/testcase_custom_fields', methods=['PATCH'])
    async def modify_custom_field_request():
        return await view.modify_custom_field()

    return blueprint
