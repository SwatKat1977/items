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
from quart import request, Response
from items.services.items_gateway.sessions import Sessions, SessionEntry

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
