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
from apis.admin_api_view import AdminApiView


def create_blueprint(logger: logging.Logger) -> Blueprint:
    view = AdminApiView(logger)

    blueprint = Blueprint('admin_api', __name__)

    logger.info("Registering Admin API Endpoints :")

    logger.info("=> admin/add_testcase_custom_field [POST]")

    @blueprint.route('/admin/add_testcase_custom_field',
                     methods=['POST'])
    async def add_testcase_custom_field_request():
        return await view.add_testcase_custom_field()

    logger.info("=> admin/move_testcase_custom_field_position [POST]")

    @blueprint.route('/admin/move_testcase_custom_field_position',
                     methods=['POST'])
    async def move_testcase_custom_field_position_request():
        return await move_testcase_custom_field_position_field()

    return blueprint
