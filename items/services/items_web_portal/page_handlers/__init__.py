"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
import quart
from items.services.items_web_portal.page_handler_injections import (
    PageHandlerInjections)
from .auth import create_auth_page_handlers


def create_page_handlers(injections: PageHandlerInjections) -> quart.Blueprint:
    routes = quart.Blueprint("page_handler_routes", __name__)

    routes.register_blueprint(create_auth_page_handlers(injections))

    return routes
