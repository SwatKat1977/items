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
from items.services.items_web_portal.portal_page_handler import (
    PortalPageHandler)
import items.services.items_web_portal.page_locations as pages


class GetProjectOverviewPageHandler(PortalPageHandler):
    """Handles requests for the project overview page.

    This handler is responsible for rendering the overview page for an
    individual project.
    """

    async def project_overview(self, _project_id: int):
        """Render the overview page for a project.

        Args:
            _project_id: Identifier of the project to display.

        Returns:
            The rendered project overview page response.
        """
        return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)
