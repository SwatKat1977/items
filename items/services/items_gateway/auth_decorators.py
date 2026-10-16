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
from functools import wraps
from http import HTTPStatus
import json
from typing import Optional
from quart import request, Response
from items.services.items_gateway.route_injections import RouteInjections
from items.services.items_gateway.sessions import Sessions, SessionEntry
from items.shared.permission_action import PermissionAction
from items.shared.permission_area import PermissionArea

# Headers the web portal attaches to every internal call it makes to the
# gateway, carrying the caller's already-authenticated session. Named to
# mirror the ``items_user``/``items_token`` cookies they are read from.
HEADER_USER = "X-Items-User"
HEADER_TOKEN = "X-Items-Token"


def _unauthorized() -> Response:
    """Build the standard 401 response for a missing/invalid session."""
    return Response(json.dumps({"error": "Unauthorized"}),
                    status=HTTPStatus.UNAUTHORIZED,
                    content_type="application/json")


def _forbidden() -> Response:
    """Build the standard 403 response for a valid session lacking rights."""
    return Response(json.dumps({"error": "Forbidden"}),
                    status=HTTPStatus.FORBIDDEN,
                    content_type="application/json")


async def _resolve_session(sessions: Sessions) -> SessionEntry | None:
    """Resolve the caller's session from the request's auth headers.

    Args:
        sessions: The gateway's in-memory session store.

    Returns:
        The matching ``SessionEntry`` if both headers are present and match
        an active session, otherwise ``None``.
    """
    email_address = request.headers.get(HEADER_USER)
    token = request.headers.get(HEADER_TOKEN)

    if not email_address or not token:
        return None

    return await sessions.get_session_entry(email_address, token)


def require_session(sessions: Sessions):
    """Decorator factory requiring any valid, currently active session.

    Intended to wrap the small delegate closures registered against each
    route in the ``routes/web/*/__init__.py`` blueprint factories - not the
    handler classes themselves, which are also called directly (bypassing
    HTTP) from unit tests and should stay authorization-agnostic.

    Args:
        sessions: The gateway's in-memory session store, captured once at
            blueprint-registration time.

    Returns:
        A decorator that 401s the request if no valid session is presented,
        otherwise calls the wrapped route function unchanged.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            entry = await _resolve_session(sessions)
            if entry is None:
                return _unauthorized()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_administrator(sessions: Sessions):
    """Decorator factory requiring a valid session with administrator rights.

    Same wrapping point as :func:`require_session`, with an additional
    check on ``SessionEntry.is_administrator``.

    Args:
        sessions: The gateway's in-memory session store, captured once at
            blueprint-registration time.

    Returns:
        A decorator that 401s the request if no valid session is presented,
        403s if the session is valid but not an administrator, otherwise
        calls the wrapped route function unchanged.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            entry = await _resolve_session(sessions)
            if entry is None:
                return _unauthorized()
            if not entry.is_administrator:
                return _forbidden()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_project_member(sessions: Sessions):
    """Decorator factory requiring the caller to be a member of the project
    named in the request, or an administrator.

    The project id is read from the route's ``project_id`` keyword argument
    if present, otherwise from a ``project_id`` query parameter. If neither
    yields a parseable integer, the check is skipped entirely and the
    wrapped function is called unchanged - that's a malformed-request
    concern for the handler's own validation to report specifically (e.g.
    "project_id is required"), not something this decorator should mask
    behind a generic 403.

    Administrators bypass the membership check, matching every other
    admin-gated route in this codebase.

    Args:
        sessions: The gateway's in-memory session store, captured once at
            blueprint-registration time.

    Returns:
        A decorator that 401s the request if no valid session is presented,
        403s if the session is valid, names a specific project, and the
        caller isn't a member of it, otherwise calls the wrapped route
        function unchanged.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            entry = await _resolve_session(sessions)
            if entry is None:
                return _unauthorized()
            if entry.is_administrator:
                return await func(*args, **kwargs)

            project_id = kwargs.get("project_id")
            if project_id is None:
                raw_project_id = request.args.get("project_id")
                if raw_project_id is not None:
                    try:
                        project_id = int(raw_project_id)
                    except ValueError:
                        project_id = None

            if project_id is not None and project_id not in entry.project_ids:
                return _forbidden()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def _bad_request(message: str) -> Response:
    """Build the standard 400 response for a missing/malformed project id."""
    return Response(json.dumps({"error": message}),
                    status=HTTPStatus.BAD_REQUEST,
                    content_type="application/json")


def _identity_unavailable() -> Response:
    """Build the 500 returned when permissions could not be established."""
    return Response(json.dumps({"error": "Identity service unavailable"}),
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    content_type="application/json")


def _read_project_id(route_kwargs: dict
                     ) -> tuple[Optional[int], Optional[Response]]:
    """Read the project a request is about, from its path or query string.

    Creates carry the project in the path (``/web/<project_id>/testcases``)
    and every other route in the ``project_id`` query parameter, so the path
    is tried first.

    Unlike :func:`require_project_member`, a project that cannot be found is
    an error here, never a reason to skip the check.

    Args:
        route_kwargs: The keyword arguments Quart matched from the route.

    Returns:
        ``(project_id, None)`` when a project was found, otherwise
        ``(None, response)`` where ``response`` is the 400 to return.
    """
    project_id = route_kwargs.get("project_id")
    if project_id is not None:
        return project_id, None

    raw_project_id = request.args.get("project_id")
    if raw_project_id is None:
        return None, _bad_request("project_id query parameter is required")

    try:
        return int(raw_project_id), None
    except ValueError:
        return None, _bad_request("project_id must be an integer")


def _read_grant(body: object, area: PermissionArea,
                action: PermissionAction) -> Optional[bool]:
    """Read one grant out of Identity's effective-permissions response.

    Deliberately strict: only a real boolean counts. Anything else - a
    missing area, a missing action, a string, a null - is "I do not know",
    which the caller treats as a failure and not as either answer.

    Args:
        body: The decoded response body.
        area: The area being checked.
        action: The action being checked.

    Returns:
        ``True`` or ``False`` as granted by Identity, or ``None`` if the
        response does not contain a boolean for that area and action.
    """
    if not isinstance(body, dict):
        return None

    areas = body.get("areas")
    if not isinstance(areas, dict):
        return None

    grant = areas.get(area.value)
    if not isinstance(grant, dict):
        return None

    value = grant.get(action.value)
    return value if isinstance(value, bool) else None


async def _fetch_permissions(injections: RouteInjections,
                             user_id: str,
                             project_id: int
                             ) -> tuple[object, Optional[Response]]:
    """Fetch a user's effective permissions on a project from Identity.

    Args:
        injections: Route dependencies (REST client, configuration, logger).
        user_id: The user's Identity UUID.
        project_id: The project the request is about.

    Returns:
        ``(body, None)`` when Identity answered ``200``, otherwise
        ``(None, response)`` where ``response`` is the one to return: a 403
        if Identity does not know the user, or a 500 for anything that
        leaves the answer uncertain.
    """
    url = (f"{injections.configuration.apis_identity_svc}"
           f"users/{user_id}/projects/{project_id}/permissions")

    try:
        response = await injections.rest_client.get(url)
    except Exception:  # pylint: disable=broad-except
        # Whatever went wrong, the answer is "not allowed" - and a JSON 500
        # is kinder to the caller than Quart's default HTML error page.
        injections.logger.exception(
            "Permission lookup failed for project %s", project_id)
        return None, _identity_unavailable()

    if response.exception_msg is not None:
        injections.logger.error(
            "Connection to identity service failed: %s",
            response.exception_msg)
        return None, _identity_unavailable()

    if response.status_code == HTTPStatus.NOT_FOUND:
        # The session's user no longer exists in Identity.
        return None, _forbidden()

    if response.status_code != HTTPStatus.OK:
        injections.logger.error(
            "Identity permission lookup returned status %s",
            response.status_code)
        return None, _identity_unavailable()

    return response.body, None


async def _permission_failure(injections: RouteInjections,
                              entry: SessionEntry,
                              project_id: int,
                              area: PermissionArea,
                              action: PermissionAction) -> Optional[Response]:
    """Ask Identity whether the caller holds a permission on a project.

    Args:
        injections: Route dependencies (REST client, configuration, logger).
        entry: The caller's resolved session.
        project_id: The project the request is about.
        area: The area being checked.
        action: The action being checked.

    Returns:
        ``None`` if, and only if, Identity positively says the permission is
        granted. Otherwise the response to return: a 403 if it is not
        granted, or a 500 if that could not be established. Every
        uncertain outcome is a failure - the request is never allowed on
        a guess.
    """
    if not entry.user_id:
        # The user's id could not be resolved at login, so there is nobody
        # to ask Identity about.
        return _forbidden()

    body, failure = await _fetch_permissions(
        injections, entry.user_id, project_id)
    if failure is not None:
        return failure

    granted = _read_grant(body, area, action)
    if granted is None:
        injections.logger.error(
            "Identity permission response missing %s/%s",
            area.value, action.value)
        return _identity_unavailable()

    return None if granted else _forbidden()


def require_project_permission(injections: RouteInjections,
                               area: PermissionArea,
                               action: PermissionAction):
    """Decorator factory requiring a specific permission on the request's
    project, checked with the Identity service on every request.

    This is where the per-area role grid is enforced (§9.5 of
    user_roles_design.md). Nothing is cached: the answer comes from Identity
    each time, so a change to a role, a membership or an account applies on
    the very next request and access can be revoked at once.

    It replaces :func:`require_project_member` on a gated route, because a
    user who is not a member (or has no role) simply gets an empty grid from
    Identity. Administrators are not special-cased here - Identity already
    returns everything for them.

    Unlike :func:`require_project_member`, it never skips the check: a
    request that names no project, or a malformed one, is a 400, and any
    failure to establish the answer denies the request.

    Args:
        injections: Route dependencies. Supplies the session store, the REST
            client and configuration used to ask Identity, and the logger.
        area: The permission area the route needs.
        action: The action within that area the route needs.

    Returns:
        A decorator that:

        * 401s if no valid session is presented;
        * 400s if the request names no usable project;
        * 403s if the caller is not granted the permission;
        * 500s if Identity cannot be reached or answers unexpectedly;
        * otherwise calls the wrapped route function unchanged.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            entry = await _resolve_session(injections.sessions)
            if entry is None:
                return _unauthorized()

            project_id, bad_request = _read_project_id(kwargs)
            if bad_request is not None:
                return bad_request

            failure = await _permission_failure(
                injections, entry, project_id, area, action)
            if failure is not None:
                return failure

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_session_with_entry(sessions: Sessions):
    """Decorator factory requiring any valid session, passing the resolved
    ``SessionEntry`` to the wrapped function as ``session_entry``.

    Only exists for the rare route that genuinely needs to know who's
    calling to do its job correctly - e.g. filtering a list down to the
    caller's own permissions - rather than a simple allow/deny gate. Every
    other route stays authorization-agnostic; prefer :func:`require_session`,
    :func:`require_administrator` or :func:`require_project_member` unless
    the handler truly can't do its job without the caller's identity.

    Args:
        sessions: The gateway's in-memory session store, captured once at
            blueprint-registration time.

    Returns:
        A decorator that 401s the request if no valid session is presented,
        otherwise calls the wrapped route function with the resolved
        ``SessionEntry`` passed as ``session_entry``.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            entry = await _resolve_session(sessions)
            if entry is None:
                return _unauthorized()
            return await func(*args, session_entry=entry, **kwargs)
        return wrapper
    return decorator
