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


def create_web_routes(logger: logging.Logger,
                      state: StateObject) -> quart.Blueprint:
    from .health_api import create_blueprint as create_heath_bp
    from .projects_api import create_blueprint as create_projects_bp
    from .testcases_api import create_blueprint as create_testcases_bp
    from .admin import create_admin_routes

    web_bp = quart.Blueprint("web_routes", __name__)

    web_bp.register_blueprint(create_heath_bp(logger, state), url_prefix="/health")
    web_bp.register_blueprint(create_projects_bp(logger, state), url_prefix="/projects")
    web_bp.register_blueprint(create_testcases_bp(logger, state), url_prefix="/testcases")

    web_bp.register_blueprint(create_admin_routes(logger, state), url_prefix="/admin")

    return web_bp
