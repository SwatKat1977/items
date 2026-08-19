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
from items.services.items_gateway.sessions import Sessions


class AddUserProjectHandler(BaseApiRoute):
    """Handles POST /users/<user_id>/projects — add a user to a project.

    Unlike every other handler in this domain, this one talks to *both*
    backend services for a single request: identity can't validate
    ``project_id`` itself (no foreign key is possible across the database
    boundary - see §7 of user_roles_design.md), so the gateway confirms the
    project actually exists in CMS before proxying the membership creation
    to identity. Without this, a typo'd ``project_id`` would silently
    succeed and sit as a dangling, inert reference - a confusing failure
    mode with no error anywhere pointing at why (see the discussion
    recorded when this branch was scoped).

    This check only runs on creation. It's deliberately not repeated
    elsewhere in this domain - membership creation is a rare, deliberate
    admin action, so the extra CMS round trip is cheap in aggregate; it
    would not be worth adding to a request that runs on every page load
    (that reasoning is exactly why the testcase routes avoid an equivalent
    extra hop - see routes/web/testcases/get_testcase_handler.py).
    """

    def __init__(self,
                 logger: logging.Logger,
                 configuration: GatewayConfiguration,
                 rest_client: RestClient,
                 sessions: Sessions) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._configuration = configuration
        self._rest_client = rest_client
        self._sessions = sessions

    async def add_user_project(self, user_id: str) -> Response:
        """Add a user to a project, optionally assigning a role.

        On success, live-patches the new project id into the user's
        already-open session (if any) - see
        ``Sessions.add_project_id_for_user`` - so a newly granted project
        is usable immediately rather than only after their next login.

        Args:
            user_id: The user's UUID (from the URL).

        Returns:
            201 on success.
            400 if the request body is missing or not valid JSON, or a
            supplied ``role_id`` doesn't exist.
            404 if no user exists with that UUID, or ``project_id`` doesn't
            match a real CMS project.
            409 if the user is already a member of this project.
            500 if either backend service is unreachable.
        """
        body = await request.get_json(force=True, silent=True)
        if body is None:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                content_type="application/json")

        project_id = body.get("project_id")
        if isinstance(project_id, int):
            cms_error = await self._check_project_exists(project_id)
            if cms_error is not None:
                return cms_error

        url: str = (f"{self._configuration.apis_identity_svc}"
                    f"users/{user_id}/projects")
        response: ApiResponse = await self._rest_client.post(url,
                                                              json_data=body)

        if response.exception_msg is not None:
            self._logger.error("Connection to identity service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "Identity service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        if response.status_code == HTTPStatus.CREATED \
                and isinstance(project_id, int):
            await self._sessions.add_project_id_for_user(user_id, project_id)

        return Response(json.dumps(response.body),
                        status=response.status_code,
                        content_type="application/json")

    async def _check_project_exists(self, project_id: int) -> Response | None:
        """Confirm a project exists in CMS before creating a membership.

        Args:
            project_id: The project id to check.

        Returns:
            ``None`` if the project exists and the caller should proceed.
            Otherwise, the ``Response`` to return immediately - a 404 if
            CMS reports the project doesn't exist, or a 500 if CMS is
            unreachable or returns something unexpected.
        """
        url: str = f"{self._configuration.apis_cms_svc}projects/{project_id}"
        response: ApiResponse = await self._rest_client.get(url)

        if response.exception_msg is not None:
            self._logger.error("Connection to CMS service failed: %s",
                               response.exception_msg)
            return Response(
                json.dumps({"error": "CMS service unavailable"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        if response.status_code == HTTPStatus.NOT_FOUND:
            return Response(
                json.dumps({"error": "Project not found"}),
                status=HTTPStatus.NOT_FOUND,
                content_type="application/json")

        if response.status_code != HTTPStatus.OK:
            self._logger.error(
                "CMS service returned unexpected status %s checking "
                "project %d", response.status_code, project_id)
            return Response(
                json.dumps({"error": "Internal error!"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json")

        return None
