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
import json
import logging
from http import HTTPStatus
from typing import Optional
from quart import request, Response
from weaver_framework.microservice.base_api_route import BaseApiRoute
from items.services.items_cms.routes.project_id_parameter import (
    read_required_project_id)
from items.services.items_cms.services.folder_service import FolderService


def read_cascade_flag() -> tuple[bool, Optional[Response]]:
    """Read the optional ``cascade`` query parameter of a folder delete.

    Returns:
        ``(cascade, None)`` where ``cascade`` is False when the parameter is
        absent or ``false`` and True when it is ``true`` (any letter case).
        For any other value, ``(False, response)`` where ``response`` is the
        400 to return. A typo such as ``cascade=yes`` is refused and not
        treated as false, so it cannot silently change what a delete means.
    """
    raw_cascade = request.args.get("cascade")

    if raw_cascade is None:
        return False, None

    value = raw_cascade.strip().lower()
    if value in ("true", "false"):
        return value == "true", None

    return False, Response(
        json.dumps({"error": "cascade must be true or false"}),
        status=HTTPStatus.BAD_REQUEST,
        content_type="application/json")


class DeleteFolderHandler(BaseApiRoute):
    """Handles DELETE /folders/<folder_id> requests."""

    def __init__(self,
                 logger: logging.Logger,
                 service: FolderService) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
            service: Folder service used to delete folders.
        """
        self._logger = logger.getChild(__name__)
        self._service = service

    async def delete_folder(self, folder_id: int) -> Response:
        """Delete a folder, refusing if it contains test cases.

        Child folders are removed with it. Test cases in the folder or any
        descendant would be destroyed too, so by default the delete is
        refused (nothing changes) and the response says how many there are.
        ``cascade=true`` deletes them as well.

        Args:
            folder_id: ID of the folder to delete, taken from the URL path.

        Query parameters:
            project_id (int): Required. The project the folder belongs to;
                              checked against the folder itself.
            cascade (str):    Optional, ``true`` or ``false`` (default
                              ``false``). ``true`` also deletes every test
                              case in the folder and its descendants.

        Returns:
            200 with ``{}`` on success.
            400 if ``project_id`` is missing or not an integer, or
            ``cascade`` is not ``true`` or ``false``.
            404 if no folder exists with the given ID, or it belongs to a
            different project than ``project_id``.
            409 if the folder (or a descendant) contains test cases and
            ``cascade`` was not set: ``{"error": ..., "testcase_count": n}``.
            Nothing is deleted.
            500 on an internal database error.
        """
        # pylint: disable=duplicate-code

        project_id, error_response = read_required_project_id()
        if error_response is not None:
            return error_response

        cascade, error_response = read_cascade_flag()
        if error_response is not None:
            return error_response

        result = await self._service.delete_folder(
            folder_id, project_id, cascade)

        if not result.success:
            body = {"error": result.error_msg}
            if result.is_internal:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
            elif result.not_found:
                status = HTTPStatus.NOT_FOUND
            else:
                status = HTTPStatus.CONFLICT
                body["testcase_count"] = result.data["testcase_count"]
            return Response(
                json.dumps(body),
                status=status,
                content_type="application/json")

        return Response(
            json.dumps({}),
            status=HTTPStatus.OK,
            content_type="application/json")
