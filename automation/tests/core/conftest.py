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

A small local server for testing the library itself.

The library has to be tested without an ITEMS stack, and it must not depend
on one, so these tests talk to a tiny aiohttp server started on a free port.
"""
import asyncio
import socket
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from api_core import ApiClient


async def _echo(request: web.Request) -> web.Response:
    body = await request.json() if request.can_read_body else None
    return web.json_response({
        "method": request.method,
        "json": body,
        "query": dict(request.query),
        "headers": {name: request.headers[name]
                    for name in ("X-Default", "X-Override", "X-Extra")
                    if name in request.headers}})


async def _status(request: web.Request) -> web.Response:
    code = int(request.match_info["code"])
    return web.json_response({"error": f"status {code}"}, status=code)


async def _text(_request: web.Request) -> web.Response:
    return web.Response(text="hello", content_type="text/plain")


async def _empty(_request: web.Request) -> web.Response:
    return web.Response(status=204)


async def _slow(request: web.Request) -> web.Response:
    await asyncio.sleep(float(request.query.get("delay", "2")))
    return web.Response(text="too late")


async def _bad_json(_request: web.Request) -> web.Response:
    return web.Response(text="{not json", content_type="application/json")


async def _create_item(request: web.Request) -> web.Response:
    body = await request.json()
    return web.json_response({"id": 7, "name": body["name"]})


async def _get_item(request: web.Request) -> web.Response:
    return web.json_response({"id": int(request.match_info["item_id"]),
                              "owner": {"names": ["ann", "bob"]}})


@pytest.fixture
async def server():
    app = web.Application()
    app.add_routes([
        web.route("*", "/echo", _echo),
        web.get("/status/{code}", _status),
        web.get("/text", _text),
        web.get("/empty", _empty),
        web.get("/slow", _slow),
        web.get("/bad_json", _bad_json),
        web.post("/items", _create_item),
        web.get("/items/{item_id}", _get_item)])
    async with TestServer(app) as running:
        yield running


@pytest.fixture
async def api(server):
    async with ApiClient(str(server.make_url("/"))) as client:
        yield client


@pytest.fixture
def closed_port_url() -> str:
    """An address nothing is listening on."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    return f"http://127.0.0.1:{port}/"
