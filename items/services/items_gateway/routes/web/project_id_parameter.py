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
from typing import Optional
from quart import request, Response


def read_required_project_id() -> tuple[Optional[int], Optional[Response]]:
    """Read the required ``project_id`` query parameter of a write request.

    Shared by the test case and folder write handlers.

    ``require_project_member`` authorises a request from this same
    parameter, but deliberately skips the check when it is missing or not an
    integer, leaving that as a malformed-request concern for the handler. For
    a write that must not be a way round the check, so every write handler
    calls this first and rejects the request itself.

    Returns:
        ``(project_id, None)`` when the parameter is present and an integer,
        otherwise ``(None, response)`` where ``response`` is the 400 to
        return to the caller.
    """
    raw_project_id = request.args.get("project_id")

    if raw_project_id is None:
        return None, _bad_request("project_id query parameter is required")

    try:
        return int(raw_project_id), None
    except ValueError:
        return None, _bad_request("project_id must be an integer")


def _bad_request(message: str) -> Response:
    """Build the 400 response for a missing or malformed project_id."""
    return Response(json.dumps({"error": message}),
                    status=HTTPStatus.BAD_REQUEST,
                    content_type="application/json")
