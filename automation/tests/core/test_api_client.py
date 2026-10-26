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

Tests of ApiClient, against a small local server."""
import pytest
from weaver_framework.microservice.api_response import ApiResponse
from api_core import (
    ApiClient, DEFAULT_TIMEOUT, Reply, expect_no_response)


async def test_a_reply_is_an_api_response_with_status_and_json_body(api):
    reply = await api.get("echo")
    assert isinstance(reply, ApiResponse)
    assert isinstance(reply, Reply)
    assert reply.status_code == 200
    assert reply.success is True
    assert reply.body["method"] == "GET"
    assert reply.content_type == "application/json"


async def test_a_reply_remembers_what_was_sent(api):
    reply = await api.post("echo", json={"a": 1}, params={"q": "x"},
                           headers={"X-Extra": "1"})
    assert reply.request.method == "POST"
    assert reply.request.url == api.base_url + "echo"
    assert reply.request.json == {"a": 1}
    assert reply.request.params == {"q": "x"}
    assert reply.request.headers == {"X-Extra": "1"}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
async def test_each_write_method_sends_its_json_body(api, method):
    reply = await getattr(api, method)("echo", json={"name": "n"})
    assert reply.body["method"] == method.upper()
    assert reply.body["json"] == {"name": "n"}


async def test_get_sends_no_body(api):
    reply = await api.get("echo")
    assert reply.body["json"] is None


async def test_query_parameters_are_sent(api):
    reply = await api.get("echo", params={"project_id": 5, "q": "a b"})
    assert reply.body["query"] == {"project_id": "5", "q": "a b"}


async def test_the_clients_headers_are_sent_with_every_request(server):
    async with ApiClient(str(server.make_url("/")),
                         headers={"X-Default": "d"}) as client:
        first = await client.get("echo")
        second = await client.post("echo", json={})
    assert first.body["headers"] == {"X-Default": "d"}
    assert second.body["headers"] == {"X-Default": "d"}


async def test_a_request_header_is_added_to_the_clients_headers(server):
    async with ApiClient(str(server.make_url("/")),
                         headers={"X-Default": "d"}) as client:
        reply = await client.get("echo", headers={"X-Extra": "e"})
    assert reply.body["headers"] == {"X-Default": "d", "X-Extra": "e"}


async def test_a_request_header_replaces_the_clients_header_of_that_name(
        server):
    async with ApiClient(str(server.make_url("/")),
                         headers={"X-Override": "client"}) as client:
        reply = await client.get("echo", headers={"X-Override": "request"})
    assert reply.body["headers"] == {"X-Override": "request"}


@pytest.mark.parametrize("path", ["echo", "/echo"])
async def test_a_leading_slash_on_the_path_makes_no_difference(api, path):
    reply = await api.get(path)
    assert reply.status_code == 200
    assert reply.request.url == api.base_url + "echo"


@pytest.mark.parametrize("base", ["{}", "{}/"])
async def test_a_trailing_slash_on_the_base_url_makes_no_difference(
        server, base):
    base_url = base.format(str(server.make_url("/")).rstrip("/"))
    async with ApiClient(base_url) as client:
        reply = await client.get("echo")
    assert reply.status_code == 200
    assert client.base_url.endswith("/") and not client.base_url.endswith("//")


async def test_an_error_status_is_a_reply_not_an_exception(api):
    reply = await api.get("status/403")
    assert reply.status_code == 403
    assert reply.success is False
    assert reply.body == {"error": "status 403"}
    assert reply.exception_msg is None


async def test_a_text_body_comes_back_as_text(api):
    reply = await api.get("text")
    assert reply.body == "hello"
    assert reply.content_type == "text/plain"


async def test_an_empty_body_comes_back_as_none(api):
    reply = await api.get("empty")
    assert reply.status_code == 204
    assert reply.body is None


async def test_unreadable_json_is_reported_with_the_status_kept(api):
    reply = await api.get("bad_json")
    assert reply.status_code == 200
    assert reply.exception_msg is not None


async def test_an_unreachable_service_is_a_reply_not_an_exception(
        closed_port_url):
    async with ApiClient(closed_port_url) as client:
        reply = await client.get("anything")
    assert reply.exception_msg
    assert reply.status_code == 503
    assert reply.success is False
    expect_no_response(reply)


async def test_a_timeout_is_a_reply_not_an_exception(api):
    reply = await api.get("slow", timeout=0.2)
    assert reply.status_code == 504
    assert reply.exception_msg is not None
    expect_no_response(reply)


async def test_the_clients_timeout_applies_to_every_request(server):
    """The server takes 1 s; the client gives up after 0.2 s."""
    async with ApiClient(str(server.make_url("/")), timeout=0.2) as client:
        reply = await client.get("slow", params={"delay": 1})
    assert reply.status_code == 504


async def test_a_requests_own_timeout_replaces_the_clients(server):
    """The client would wait 5 s; this request will not wait 0.2 s."""
    async with ApiClient(str(server.make_url("/")), timeout=5) as client:
        reply = await client.get("slow", params={"delay": 1}, timeout=0.2)
    assert reply.status_code == 504


async def test_a_reply_that_arrives_within_the_timeout_is_returned(server):
    async with ApiClient(str(server.make_url("/")), timeout=5) as client:
        reply = await client.get("slow", params={"delay": 0.1})
    assert reply.status_code == 200
    assert reply.body == "too late"


async def test_the_default_timeout_is_longer_than_the_services(server):
    async with ApiClient(str(server.make_url("/"))) as client:
        assert client.timeout == DEFAULT_TIMEOUT
    assert DEFAULT_TIMEOUT > 2


async def test_an_unsupported_method_is_refused(api):
    with pytest.raises(ValueError, match="unsupported method"):
        await api.request("TRACE", "echo")


async def test_a_client_that_is_not_open_says_how_to_open_it(server):
    client = ApiClient(str(server.make_url("/")))
    with pytest.raises(RuntimeError, match="async with"):
        await client.get("echo")


async def test_a_closed_client_cannot_be_used_again(server):
    async with ApiClient(str(server.make_url("/"))) as client:
        await client.get("echo")
    with pytest.raises(RuntimeError, match="async with"):
        await client.get("echo")


async def test_one_session_is_used_for_every_request(api):
    """The session is opened once and kept, not opened per request."""
    await api.get("echo")
    session = api._session  # pylint: disable=protected-access
    await api.get("echo")
    assert api._session is session  # pylint: disable=protected-access


async def test_a_value_from_one_reply_can_be_used_in_the_next_request(api):
    created = await api.post("items", json={"name": "Seven"})
    new_id = created.body["id"]
    fetched = await api.get(f"items/{new_id}")
    assert fetched.body["id"] == 7
