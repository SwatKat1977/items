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
from urllib.parse import quote
from quart import request, Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.routes.web.project_id_parameter \
    import read_required_project_id


class DeleteFolderHandler(BaseApiRoute):
    """Handles DELETE /folders/<folder_id> - delete a section.

    Proxies to the CMS service and propagates the response unchanged,
    including its refusal (409 with a ``testcase_count``) when the section
    contains test cases and ``cascade`` was not given. The ``cascade``
    parameter is forwarded as sent: the CMS decides what it means and rejects
    values it does not understand, so the Gateway adds no second opinion.
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client

    async def delete_folder(self, folder_id: int) -> Response:
        """Delete a section.

        Query parameters: ``project_id`` (required) and ``cascade``
        (optional, ``true`` or ``false``; ``true`` also deletes every test
        case in the section and its sub-sections).

        Args:
            folder_id: The section's id (from the URL).

        Returns:
            200 on success.
            400 if ``project_id`` is missing or not an integer, or the CMS
            rejects ``cascade``.
            404 if the section does not exist, or belongs to a different
            project than ``project_id``.
            409 ``{"error": ..., "testcase_count": n}`` if the section (or a
            sub-section) contains test cases and ``cascade`` was not true;
            nothing is deleted.
            500 if the CMS service is unreachable or reports an internal
            error.
        """
        project_id, error_response = read_required_project_id()
        if error_response is not None:
            return error_response

        url: str = (f"{self._configuration.apis_cms_svc}folders/{folder_id}"
                    f"?project_id={project_id}")

        cascade = request.args.get("cascade")
        if cascade is not None:
            url += f"&cascade={quote(cascade, safe='')}"

        response: ApiResponse = await self._rest_client.delete(url)

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
