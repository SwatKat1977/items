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
from http import HTTPStatus
import json
import logging
from quart import request, Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.routes.web.project_id_parameter \
    import read_required_project_id


class MoveFolderHandler(BaseApiRoute):
    """Handles POST /folders/<folder_id>/move - move a section.

    Proxies to the CMS service and propagates the response. The
    ``project_id`` query parameter is what ``require_project_permission``
    authorised; it is forwarded so the CMS can confirm the section really
    belongs to that project (404 otherwise), and that the new parent is in it
    too. The CMS validates the body, and refuses a move that would put a
    section inside itself or one of its own sub-sections.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def move_folder(self, folder_id: int) -> Response:
        """Move a section under another section, or to the top level.

        Query parameters: ``project_id`` (required).
        Request body (JSON): ``parent_id``, the new parent section's id, or
        null for the top level. It must always be present.

        Args:
            folder_id: The section's id (from the URL).

        Returns:
            200 on success, including when the section is already under
            that parent.
            400 if ``project_id`` is missing or not an integer, the body is
            missing, not a JSON object, or fails the CMS service's
            validation, the new parent belongs to a different project, or
            the new parent is the section itself or one of its own
            sub-sections.
            404 if the section does not exist, belongs to a different
            project than ``project_id``, or the new parent does not exist.
            409 if the new parent already holds a section with the same
            name.
            500 if the CMS service is unreachable or reports an internal
            error.
        """
        project_id, error_response = read_required_project_id()
        if error_response is not None:
            return error_response

        body = await request.get_json(force=True, silent=True)
        if not isinstance(body, dict):
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        url: str = (f"{self._configuration.apis_cms_svc}folders/{folder_id}"
                    f"/move?project_id={project_id}")
        response: ApiResponse = await self._rest_client.post(
            url, json_data=body)

        if response.exception_msg is not None:
            self._logger.error("Connection to CMS service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "CMS service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return Response(json.dumps(response.body),
                        status=response.status_code,
                        content_type="application/json")
