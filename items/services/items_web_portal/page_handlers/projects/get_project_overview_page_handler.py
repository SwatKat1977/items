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
from http import HTTPStatus
import json
import logging
from quart import make_response, Response
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_web_portal.configuration import Configuration
from items.services.items_web_portal.decorators import require_session
from items.services.items_web_portal.metadata_settings import MetadataSettings
from items.services.items_web_portal.portal_page_handler import PortalPageHandler
import items.services.items_web_portal.page_locations as pages


class GetProjectOverviewPageHandler(PortalPageHandler):
    """Handles requests for the project overview page.

    This handler fetches project details from the gateway service and renders
    the project overview page, including the project name, announcement banner,
    and stubbed statistics sections.
    """

    def __init__(self,
                 logger: logging.Logger,
                 config: Configuration,
                 rest_client: RestClient,
                 metadata: MetadataSettings):
        """Initialises the project overview page handler.

        Args:
            logger: Logger used for diagnostic and error messages.
            config: Application configuration containing service endpoints.
            rest_client: REST client used to communicate with backend services.
            metadata: Metadata settings used when rendering portal pages.
        """
        super().__init__(logger, config, rest_client)
        self._metadata_settings = metadata

    @require_session
    async def project_overview(self, project_id: int):
        """Render the overview page for a project.

        Fetches project details from the gateway service and renders the
        overview page. A 403 (not a member of this project) or 404
        (project doesn't exist) redirects to the dashboard rather than
        showing an error - both are normal, expected states (e.g. an
        admin removed the user's access while they still had the page
        bookmarked), not failures worth surfacing as one. Any other
        non-200 is treated as a genuine unexpected failure.

        Args:
            project_id: Identifier of the project to display.

        Returns:
            The rendered project overview page, a redirect to the
            dashboard on 403/404, or a JSON error response with HTTP 500
            for any other gateway failure.
        """
        gateway_svc: str = self._config.apis_gateway_svc
        url: str = f"{gateway_svc}web/projects/{project_id}"

        response = await self._rest_client.get(url)

        if response.status_code in (HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND):
            return await make_response(self._generate_redirect('/'))

        if response.status_code != HTTPStatus.OK:
            self._logger.critical(
                "Gateway svc request invalid - Reason: %s",
                response.exception_msg)
            response_json = {"status": 0, "error": "Internal error!"}
            return Response(json.dumps(response_json),
                            status=HTTPStatus.INTERNAL_SERVER_ERROR,
                            content_type="application/json")

        project = response.body
        project_name: str = project.get("name", "Unknown Project")
        announcement: str = project.get("announcement", "")
        show_announcement: bool = project.get("show_announcement_on_overview",
                                              False)

        return await self._render_page(
            pages.PAGE_PROJECT_OVERVIEW,
            active_page="overview",
            project_id=project_id,
            project_name=project_name,
            announcement=announcement,
            show_announcement=show_announcement,
            instance_name=self._metadata_settings.instance_name)
