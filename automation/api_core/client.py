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
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
import aiohttp
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.rest_client import RestClient

# pylint: disable=too-many-arguments, too-many-positional-arguments
# Each request method mirrors the framework's RestClient, which takes the
# same optional arguments.

# Seconds. The services' own default of 2 is too short for a test run (a slow
# password hash alone can pass it).
DEFAULT_TIMEOUT: float = 10


@dataclass(frozen=True)
class SentRequest:
    """What was sent, kept with the reply so a failed check can say so.

    Attributes:
        method: The HTTP method, upper case.
        url: The full URL, without the query string.
        json: The JSON body, or None.
        params: The query parameters, or None.
        headers: The headers sent (defaults merged with per-call ones), or
            None if there were none.
    """

    method: str
    url: str
    json: Any = None
    params: Mapping[str, Any] | None = None
    headers: Mapping[str, str] | None = None


@dataclass
class Reply(ApiResponse):
    """An ``ApiResponse`` that also remembers the request that produced it.

    It is an ``ApiResponse`` in every other respect (``status_code``,
    ``headers``, ``body``, ``content_type``, ``exception_msg``, ``success``),
    so anything written for the framework's response type works on it.

    A network failure does not raise: it comes back as a reply with
    ``exception_msg`` set (status 503, or 504 for a timeout), so a test can
    check an outage like any other response.

    Attributes:
        request: The request that was sent.
    """

    request: SentRequest | None = None


class ApiClient:
    """Sends requests to an API and returns what came back.

    Generic: it knows nothing about the service it talks to. Built on the
    framework's own ``RestClient`` so the automation uses the same client code
    as the services. Use it as an async context manager, so the one HTTP
    session is opened and closed with it::

        async with ApiClient("http://host:7050/") as api:
            reply = await api.get("web/projects")
    """

    def __init__(self,
                 base_url: str,
                 headers: Mapping[str, str] | None = None,
                 timeout: float = DEFAULT_TIMEOUT) -> None:
        """Initialise the client.

        Args:
            base_url: The address every path is added to.
            headers: Headers sent with every request (a per-request header of
                the same name wins).
            timeout: Seconds each request may take, unless it says otherwise.
        """
        self._base_url: str = base_url.rstrip("/") + "/"
        self._headers: dict[str, str] = dict(headers or {})
        self._timeout: float = timeout
        self._session: aiohttp.ClientSession | None = None
        self._rest: RestClient | None = None

    @property
    def base_url(self) -> str:
        """The address every path is added to (always ends in ``/``)."""
        return self._base_url

    @property
    def timeout(self) -> float:
        """Seconds each request may take, unless it says otherwise."""
        return self._timeout

    async def __aenter__(self) -> "ApiClient":
        self._session = aiohttp.ClientSession()
        self._rest = RestClient(self._session)
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._session is not None:
            await self._session.close()
        self._session = None
        self._rest = None

    async def get(self, path: str, headers: Mapping[str, str] | None = None,
                  params: Mapping[str, Any] | None = None,
                  timeout: float | None = None) -> Reply:
        """Send a GET request. See ``request``."""
        return await self.request("GET", path, headers=headers,
                                  params=params, timeout=timeout)

    async def post(self, path: str, json: Any = None,
                   headers: Mapping[str, str] | None = None,
                   params: Mapping[str, Any] | None = None,
                   timeout: float | None = None) -> Reply:
        """Send a POST request. See ``request``."""
        return await self.request("POST", path, json=json, headers=headers,
                                  params=params, timeout=timeout)

    async def put(self, path: str, json: Any = None,
                  headers: Mapping[str, str] | None = None,
                  params: Mapping[str, Any] | None = None,
                  timeout: float | None = None) -> Reply:
        """Send a PUT request. See ``request``."""
        return await self.request("PUT", path, json=json, headers=headers,
                                  params=params, timeout=timeout)

    async def patch(self, path: str, json: Any = None,
                    headers: Mapping[str, str] | None = None,
                    params: Mapping[str, Any] | None = None,
                    timeout: float | None = None) -> Reply:
        """Send a PATCH request. See ``request``."""
        return await self.request("PATCH", path, json=json, headers=headers,
                                  params=params, timeout=timeout)

    async def delete(self, path: str, json: Any = None,
                     headers: Mapping[str, str] | None = None,
                     params: Mapping[str, Any] | None = None,
                     timeout: float | None = None) -> Reply:
        """Send a DELETE request. See ``request``."""
        return await self.request("DELETE", path, json=json, headers=headers,
                                  params=params, timeout=timeout)

    async def request(self, method: str, path: str, json: Any = None,
                      headers: Mapping[str, str] | None = None,
                      params: Mapping[str, Any] | None = None,
                      timeout: float | None = None) -> Reply:
        """Send a request and return the reply.

        Args:
            method: GET, POST, PUT, PATCH or DELETE.
            path: Added to the base URL; a leading ``/`` makes no difference.
            json: The JSON body, if any (not sent with GET).
            headers: Sent in addition to the client's own headers; one of the
                same name replaces it.
            params: Query parameters.
            timeout: Seconds to wait, instead of the client's own.

        Returns:
            The reply. A network failure is returned, not raised (see
            ``Reply``).

        Raises:
            RuntimeError: If the client is not open (not used with ``async
                with``).
            ValueError: If the method is not one of those listed.
        """
        if self._rest is None:
            raise RuntimeError(
                "ApiClient is not open: use 'async with ApiClient(...)'")

        method = method.upper()
        sent = SentRequest(
            method=method,
            url=self._base_url + path.lstrip("/"),
            json=json,
            params=dict(params) if params else None,
            headers={**self._headers, **(headers or {})} or None)
        wait = self._timeout if timeout is None else timeout

        if method == "GET":
            response = await self._rest.get(
                sent.url, headers=sent.headers, params=sent.params,
                timeout=wait)
        elif method in ("POST", "PUT", "PATCH", "DELETE"):
            send = getattr(self._rest, method.lower())
            response = await send(
                sent.url, json_data=sent.json, headers=sent.headers,
                params=sent.params, timeout=wait)
        else:
            raise ValueError(f"unsupported method: {method}")

        return Reply(status_code=response.status_code,
                     headers=response.headers,
                     body=response.body,
                     content_type=response.content_type,
                     exception_msg=response.exception_msg,
                     request=sent)
