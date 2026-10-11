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
from http import HTTPStatus
from typing import Optional
from quart import request, Response


def read_required_project_id() -> tuple[Optional[int], Optional[Response]]:
    """Read the required ``project_id`` query parameter of a write request.

    ``PATCH`` and ``DELETE /testcases/<id>`` must state which project the
    test case belongs to, so the service can confirm it genuinely does
    (an integrity check - the CMS stays permission-agnostic, see
    user_roles_design.md section 9). Unlike ``GET``, where the parameter is
    optional, it is required here: a write that leaves it out would silently
    skip the check.

    Returns:
        ``(project_id, None)`` when the parameter is present and an integer,
        otherwise ``(None, response)`` where ``response`` is the 400 to
        return to the caller.
    """
    raw_project_id = request.args.get("project_id")

    if raw_project_id is None:
        return None, _bad_request("project_id is required")

    try:
        return int(raw_project_id), None
    except ValueError:
        return None, _bad_request("project_id must be an integer")


def _bad_request(message: str) -> Response:
    """Build the 400 response for a missing or malformed project_id."""
    return Response(json.dumps({"error": message}),
                    status=HTTPStatus.BAD_REQUEST,
                    content_type="application/json")
