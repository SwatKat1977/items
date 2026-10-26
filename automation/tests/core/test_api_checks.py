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

Tests of the checks, and of what their failure messages say."""
import ast
import pathlib
import pytest
from api_core import (
    ApiClient, Reply, SentRequest, describe, expect_json, expect_no_response,
    expect_status, json_value)


def _reply(body=None, status=200, request=None, exception_msg=None):
    return Reply(status_code=status, body=body, content_type=
                 "application/json", exception_msg=exception_msg,
                 request=request)


# ---------------------------------------------------------------------------
# expect_status
# ---------------------------------------------------------------------------

def test_expect_status_passes_and_returns_the_reply_for_chaining():
    reply = _reply(status=200)
    assert expect_status(reply, 200) is reply


async def test_expect_status_failure_says_what_was_expected_and_received(api):
    reply = await api.get("status/403")
    with pytest.raises(AssertionError) as failure:
        expect_status(reply, 200)
    message = str(failure.value)
    assert "expected status 200 but got 403" in message
    assert "GET " + api.base_url + "status/403" in message
    assert "received: 403" in message
    assert "status 403" in message          # the response body


async def test_expect_status_failure_says_what_was_sent(api):
    reply = await api.post("echo", json={"name": "x"},
                           params={"project_id": 5},
                           headers={"X-Extra": "1"})
    with pytest.raises(AssertionError) as failure:
        expect_status(reply, 201)
    message = str(failure.value)
    assert "POST " + api.base_url + "echo" in message
    assert '"project_id": 5' in message
    assert '"X-Extra": "1"' in message
    assert '"name": "x"' in message


async def test_expect_status_says_when_there_was_no_response(
        closed_port_url):
    async with ApiClient(closed_port_url) as client:
        reply = await client.get("anything")
    with pytest.raises(AssertionError) as failure:
        expect_status(reply, 200)
    message = str(failure.value)
    # Said plainly, not as if the service had answered with a 503.
    assert message.splitlines()[0] == (
        "expected status 200 but there was no response")
    assert "no response (" in message


# ---------------------------------------------------------------------------
# expect_no_response
# ---------------------------------------------------------------------------

def test_expect_no_response_passes_when_nothing_came_back():
    reply = _reply(status=503, exception_msg="Cannot connect")
    assert expect_no_response(reply) is reply


def test_expect_no_response_fails_when_something_did():
    with pytest.raises(AssertionError, match="expected no response"):
        expect_no_response(_reply(status=200))


# ---------------------------------------------------------------------------
# json_value / expect_json
# ---------------------------------------------------------------------------

_BODY = {"token": "t", "areas": {"test_cases": {"read": True}},
         "folders": [{"id": 4, "name": "A"}, {"id": 9, "name": "B"}]}


def test_json_value_reads_a_top_level_key():
    assert json_value(_reply(_BODY), "token") == "t"


def test_json_value_reads_nested_keys():
    assert json_value(_reply(_BODY), "areas.test_cases.read") is True


def test_json_value_reads_into_a_list_by_position():
    assert json_value(_reply(_BODY), "folders.1.id") == 9


def test_json_value_reads_from_a_list_at_the_top():
    assert json_value(_reply([{"id": 3}]), "0.id") == 3


def test_a_value_that_is_falsy_is_still_found():
    assert json_value(_reply({"count": 0, "flag": False, "n": None}),
                      "count") == 0
    assert json_value(_reply({"flag": False}), "flag") is False
    assert json_value(_reply({"n": None}), "n") is None


def test_a_missing_key_says_where_it_stopped_and_what_is_there():
    with pytest.raises(AssertionError) as failure:
        json_value(_reply(_BODY), "areas.milestones.read")
    message = str(failure.value)
    assert "'areas.milestones.read' is not in the body" in message
    assert "no 'milestones' at areas" in message
    assert "test_cases" in message


def test_a_missing_top_level_key_says_so():
    with pytest.raises(AssertionError, match="no 'nope' at the top"):
        json_value(_reply(_BODY), "nope")


@pytest.mark.parametrize("position", ["2", "5"])
def test_a_list_position_out_of_range_says_so(position):
    """The list has two items, so 2 is the edge: just past the last one."""
    with pytest.raises(AssertionError,
                       match=rf"no item '{position}' at folders"):
        json_value(_reply(_BODY), f"folders.{position}.id")


def test_the_last_item_of_a_list_is_found():
    assert json_value(_reply(_BODY), "folders.1.name") == "B"


def test_a_key_into_a_list_says_so():
    with pytest.raises(AssertionError, match="no item 'id' at folders"):
        json_value(_reply(_BODY), "folders.id")


def test_going_through_a_plain_value_says_so():
    with pytest.raises(AssertionError, match="token is str"):
        json_value(_reply(_BODY), "token.deeper")


@pytest.mark.parametrize("body", ["plain text", None, 5])
def test_a_body_that_is_not_json_says_so(body):
    with pytest.raises(AssertionError, match="expected a JSON body"):
        json_value(_reply(body), "anything")


def test_expect_json_returns_the_value_for_use_in_a_later_request():
    assert expect_json(_reply(_BODY), "token") == "t"


def test_expect_json_checks_the_value_when_given_one():
    assert expect_json(_reply(_BODY), "areas.test_cases.read", True) is True
    with pytest.raises(AssertionError) as failure:
        expect_json(_reply(_BODY), "areas.test_cases.read", False)
    assert ("expected 'areas.test_cases.read' to be False but it is True"
            in str(failure.value))


def test_expect_json_can_check_for_a_value_of_none():
    assert expect_json(_reply({"parent": None}), "parent", None) is None
    with pytest.raises(AssertionError):
        expect_json(_reply({"parent": 3}), "parent", None)


async def test_a_value_is_captured_and_used_in_the_next_request(api):
    created = await api.post("items", json={"name": "Seven"})
    new_id = expect_json(created, "id", 7)
    fetched = await api.get(f"items/{new_id}")
    expect_status(fetched, 200)
    assert expect_json(fetched, "owner.names.1") == "bob"


# ---------------------------------------------------------------------------
# What a failure message must never show
# ---------------------------------------------------------------------------

def test_secrets_in_what_was_sent_are_hidden():
    request = SentRequest(
        method="POST", url="http://x/web/sessions",
        json={"email_address": "a@b.c", "password": "hunter2hunter2"},
        headers={"X-Items-Token": "abc123", "Authorization": "Bearer zzz",
                 "X-Items-User": "a@b.c"})
    text = describe(_reply(status=401, request=request))
    assert "hunter2hunter2" not in text
    assert "abc123" not in text
    assert "zzz" not in text
    assert "***" in text
    assert "a@b.c" in text                    # not secret, still shown


def test_secrets_in_what_came_back_are_hidden_even_when_nested():
    reply = _reply({"token": "livetoken", "user": {"session_key": "k1"},
                    "items": [{"api_secret": "s1", "ok": 1}]})
    text = describe(reply)
    for secret in ("livetoken", "k1", "s1"):
        assert secret not in text
    assert '"ok": 1' in text


def test_a_long_body_is_cut_short_in_a_failure_message():
    text = describe(_reply({"data": "x" * 5000}))
    assert len(text) < 1500
    assert "characters)" in text


def test_a_text_body_is_shown_as_it_is():
    assert "hello there" in describe(_reply("hello there"))


# ---------------------------------------------------------------------------
# The library stays generic
# ---------------------------------------------------------------------------

def test_the_library_imports_nothing_from_items():
    library = pathlib.Path(__file__).resolve().parents[2] / "api_core"
    modules = sorted(library.glob("*.py"))
    assert modules, "api_core not found"
    for module in modules:
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert name.split(".")[0] != "items", (
                    f"{module.name} imports {name}: the library must stay "
                    f"generic")
