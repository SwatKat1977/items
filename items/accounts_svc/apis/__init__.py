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
import quart
from state_object import StateObject


def create_routes(logger: logging.Logger, state: StateObject) -> quart.Blueprint:
    from .authentication_api import create_blueprint as create_auth_bp

    basic_auth_blueprint = create_auth_bp(logger)
    self._quart_instance.register_blueprint(basic_auth_blueprint)

    health_blueprint = health_api.create_blueprint(self._logger,
                                                   self._state_object)
    self._quart_instance.register_blueprint(health_blueprint)




    admin_bp = quart.Blueprint("admin_routes", __name__)
    admin_bp.register_blueprint(create_cf_bp(logger, state), url_prefix="/testcase_custom_fields")
    return admin_bp
