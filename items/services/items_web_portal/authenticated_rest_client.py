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
from quart import request
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient

# Headers attached to every outgoing gateway call, carrying the caller's
# already-authenticated session so the gateway can enforce admin-only
# routes itself rather than trusting that only the portal calls it. Names
# mirror the ``items_user``/``items_token`` cookies they are read from -
# kept in sync with items_gateway.auth_decorators.HEADER_USER/HEADER_TOKEN.
HEADER_USER = "X-Items-User"
HEADER_TOKEN = "X-Items-Token"

COOKIE_USER = "items_user"
COOKIE_TOKEN = "items_token"


class AuthenticatedRestClient:
    """Wraps a ``RestClient``, forwarding the caller's session to the gateway.

    Page handlers already read ``items_user``/``items_token`` from the
    browser's cookies to validate the session with the gateway
    (``SessionAuthMixin``). This wrapper reads the same two cookies and
    attaches them as headers on every *other* gateway call a handler makes,
    so the gateway does not have to be told the caller is authenticated
    twice - once to validate the session, and again to actually act on
    their behalf.

    Every method's parameter order deliberately mirrors ``RestClient``'s
    exactly (``url, json_data, headers, params, timeout`` - or
    ``url, headers, params, timeout`` for ``get``, which has no body).
    Existing call sites in this codebase call these methods both
    positionally and by keyword (e.g. ``rest_client.post(url, body)`` as
    well as ``rest_client.put(url, json_data=body)``) - a wrapper with a
    different parameter order would silently misroute a positional
    argument into the wrong parameter rather than raising, which is worse
    than just matching the original signature exactly.

    Must only be used from within an active Quart request context - it
    reads ``quart.request`` on every call. It is not safe for
    background/startup calls that have no request to read from (e.g. the
    web portal's own webhook-metadata retrieval in ``service.py``, which
    uses the unwrapped ``RestClient`` and its own HMAC signature instead).
    """

    def __init__(self, rest_client: RestClient) -> None:
        """Initialise the wrapper.

        Args:
            rest_client: The underlying client used to actually perform
                requests, once the auth headers have been attached.
        """
        self._rest_client = rest_client

    @staticmethod
    def _with_auth_headers(headers: dict | None) -> dict:
        """Merge the caller's session credentials into a headers dict.

        Args:
            headers: Headers already supplied by the call site, if any.

        Returns:
            A new dict with the session headers added. If the browser
            didn't send both session cookies (e.g. an unauthenticated page
            like accept-invite), the headers are simply omitted rather than
            sent empty - the gateway treats a missing header the same as an
            invalid one, so there is no difference in outcome.
        """
        merged = dict(headers) if headers else {}
        user = request.cookies.get(COOKIE_USER)
        token = request.cookies.get(COOKIE_TOKEN)
        if user and token:
            merged[HEADER_USER] = user
            merged[HEADER_TOKEN] = token
        return merged

    async def get(self, url: str, headers: dict | None = None,
                  params: dict | None = None, timeout: int = 2
                  ) -> ApiResponse:
        """Send an authenticated GET request. See ``RestClient.get``."""
        return await self._rest_client.get(
            url, headers=self._with_auth_headers(headers), params=params,
            timeout=timeout)

    async def post(self, url: str, json_data: dict | None = None,
                   headers: dict | None = None, params: dict | None = None,
                   timeout: int = 2) -> ApiResponse:
        """Send an authenticated POST request. See ``RestClient.post``."""
        return await self._rest_client.post(
            url, json_data=json_data,
            headers=self._with_auth_headers(headers), params=params,
            timeout=timeout)

    async def put(self, url: str, json_data: dict | None = None,
                  headers: dict | None = None, params: dict | None = None,
                  timeout: int = 2) -> ApiResponse:
        """Send an authenticated PUT request. See ``RestClient.put``."""
        return await self._rest_client.put(
            url, json_data=json_data,
            headers=self._with_auth_headers(headers), params=params,
            timeout=timeout)

    async def patch(self, url: str, json_data: dict | None = None,
                    headers: dict | None = None, params: dict | None = None,
                    timeout: int = 2) -> ApiResponse:
        """Send an authenticated PATCH request. See ``RestClient.patch``."""
        return await self._rest_client.patch(
            url, json_data=json_data,
            headers=self._with_auth_headers(headers), params=params,
            timeout=timeout)

    async def delete(self, url: str, json_data: dict | None = None,
                     headers: dict | None = None, params: dict | None = None,
                     timeout: int = 2) -> ApiResponse:
        """Send an authenticated DELETE request. See ``RestClient.delete``."""
        return await self._rest_client.delete(
            url, json_data=json_data,
            headers=self._with_auth_headers(headers), params=params,
            timeout=timeout)
