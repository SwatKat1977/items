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
