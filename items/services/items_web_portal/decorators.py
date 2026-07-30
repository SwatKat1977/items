"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
from quart import g, make_response
from items.shared.base_items_exception import BaseItemsException
import items.services.items_web_portal.page_locations as pages


async def _check_session(handler) -> tuple[bool, bool]:
    """Check cookies and validate the session against the gateway.

    As a side effect, sets ``g.is_administrator`` on the current request
    context so that templates can conditionally render admin-only UI (e.g.
    the Administration link in the navbar) without each handler needing to
    pass the flag explicitly.

    Args:
        handler: A ``SessionAuthMixin`` instance.

    Returns:
        ``(is_valid, is_administrator)``. Both ``False`` if cookies are absent.

    Raises:
        BaseItemsException: If the gateway call fails unexpectedly.
    """
    if not await handler._has_auth_cookies():  # pylint: disable=protected-access
        g.is_administrator = False
        return False, False
    is_valid, is_administrator = await handler._validate_cookies()  # pylint: disable=protected-access
    g.is_administrator = is_administrator
    return is_valid, is_administrator


def require_session(func):
    """Decorator that enforces an authenticated session on a page handler.

    Intended to wrap page handler methods on classes derived from
    ``PortalPageHandler`` (and therefore ``SessionAuthMixin``). Before the
    wrapped handler runs, the request's authentication cookies are checked and
    validated against the gateway service. Requests without a valid session are
    redirected to the login page; the handler body only executes for
    authenticated users.

    This mirrors the inline session check previously duplicated in individual
    handlers, providing a single, reusable guard.

    Args:
        func: The page handler coroutine to protect. Its first positional
            argument must be ``self`` (a ``SessionAuthMixin`` instance).

    Returns:
        The wrapped coroutine, which returns one of:

        - A redirect response to the login page for unauthenticated users.
        - The internal error page if session validation fails unexpectedly.
        - The wrapped handler's result for authenticated users.

    Example:
        @require_session
        async def projects_read(self):
            ...
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # pylint: disable=protected-access
        # This decorator only ever wraps methods on SessionAuthMixin /
        # PortalPageHandler subclasses, so `self` here is always one of
        # those - the protected-member access below is intentional.
        try:
            valid, _ = await _check_session(self)
            if not valid:
                return await make_response(self._generate_redirect('login'))

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        return await func(self, *args, **kwargs)

    return wrapper


def require_administrator(func):
    """Decorator that enforces an authenticated administrator session.

    Behaves identically to ``require_session`` for unauthenticated requests
    (redirects to login). Additionally checks the ``is_administrator`` flag
    returned by the gateway — non-administrators are redirected to the
    dashboard rather than reaching the admin page body.

    Args:
        func: The page handler coroutine to protect. Its first positional
            argument must be ``self`` (a ``SessionAuthMixin`` instance).

    Returns:
        The wrapped coroutine, which returns one of:

        - A redirect to the login page for unauthenticated users.
        - A redirect to the dashboard for authenticated non-administrators.
        - The internal error page if session validation fails unexpectedly.
        - The wrapped handler's result for authenticated administrators.

    Example:
        @require_administrator
        async def admin_overview(self):
            ...
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # pylint: disable=protected-access
        try:
            valid, is_administrator = await _check_session(self)

            if not valid:
                return await make_response(self._generate_redirect('login'))

            if not is_administrator:
                return await make_response(self._generate_redirect(''))

        except BaseItemsException as ex:
            self._logger.error('Internal Error: %s', ex)
            return await self._render_page(pages.TEMPLATE_INTERNAL_ERROR_PAGE)

        return await func(self, *args, **kwargs)

    return wrapper
