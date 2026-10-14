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


class CreateFolderHandler(BaseApiRoute):
    """Handles POST /<project_id>/folders - create a section.

    Proxies to the CMS service and propagates the response. The project comes
    from the URL path only, which is what ``require_project_member``
    authorised. The body must not contain a ``project_id``: it would be a
    second source for the same fact, so it is rejected with a 400 rather
    than ignored or compared. The CMS validates the rest of the body.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def create_folder(self, project_id: int) -> Response:
        """Create a section (folder) in a project.

        Request body (JSON): ``parent_id`` (int, or null for a top-level
        section) and ``name``.

        Args:
            project_id: The project to create the section in (from the URL).

        Returns:
            200 with ``{"folder_id": <int>}`` on success.
            400 if the body is missing, not a JSON object, contains a
            ``project_id`` (the project is taken from the URL), or fails the
            CMS service's validation.
            404 if the project or the parent section does not exist.
            409 if the name is already used by a sibling section.
            500 if the CMS service is unreachable or reports an internal
            error.
        """
        body = await request.get_json(force=True, silent=True)
        if not isinstance(body, dict):
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        if "project_id" in body:
            return Response(
                json.dumps({"error": "project_id must not be in the request "
                                     "body; the project is taken from the "
                                     "URL"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        payload = {**body, "project_id": project_id}

        url: str = f"{self._configuration.apis_cms_svc}folders"
        response: ApiResponse = await self._rest_client.post(
            url, json_data=payload)

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
