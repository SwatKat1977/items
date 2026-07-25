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
import os
from quart import Quart
import items.services.items_web_portal as portal_pkg

_TEMPLATE_FOLDER = os.path.join(os.path.dirname(portal_pkg.__file__),
                                "templates")


def make_app(name: str = __name__) -> Quart:
    """Create a Quart app wired to the real portal templates directory.

    Handler tests render real Jinja templates via ``_render_page`` /
    ``render_template``; without pointing the test app at the actual
    ``items/services/items_web_portal/templates`` directory, every render
    would fail with ``TemplateNotFound``.
    """
    return Quart(name, template_folder=_TEMPLATE_FOLDER)
