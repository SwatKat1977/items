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
from collections.abc import Mapping
from typing import Any
from weaver_framework.microservice.api_response import ApiResponse

# ``__tracebackhide__`` is read by pytest, which then leaves the check's own
# frames out of a failure's traceback so it points at the test, not at this
# file. Nothing here reads it.
# pylint: disable=unused-variable

# Anything whose name contains one of these is hidden when a failure message
# shows what was sent or received, so a token or password never lands in a
# test log.
_SECRET_WORDS = ("authorization", "cookie", "token", "secret", "password",
                 "key")
_MASK = "***"
_BODY_LIMIT = 600
_MISSING = object()


def _is_secret(name: Any) -> bool:
    lowered = str(name).lower()
    return any(word in lowered for word in _SECRET_WORDS)


def _masked(value: Any) -> Any:
    """Copy of a JSON value with the values of secret-looking keys hidden."""
    if isinstance(value, Mapping):
        return {key: _MASK if _is_secret(key) else _masked(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [_masked(item) for item in value]
    return value


def _shown(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(
        _masked(value), default=str)
    if len(text) > _BODY_LIMIT:
        text = text[:_BODY_LIMIT] + f"... ({len(text)} characters)"
    return text


def describe(reply: ApiResponse) -> str:
    """Say what was sent and what came back, for a failure message.

    Args:
        reply: A reply from ``ApiClient`` (any ``ApiResponse`` works, but only
            a ``Reply`` knows what was sent).

    Returns:
        A few lines: the request (method, URL, query, headers and body, with
        secrets hidden) and the response (status and body, or why there was
        none).
    """
    lines: list[str] = []
    request = getattr(reply, "request", None)
    if request is not None:
        lines.append(f"  sent:     {request.method} {request.url}")
        if request.params:
            lines.append(f"  query:    {_shown(dict(request.params))}")
        if request.headers:
            lines.append(f"  headers:  {_shown(dict(request.headers))}")
        if request.json is not None:
            lines.append(f"  body:     {_shown(request.json)}")

    if reply.exception_msg is not None:
        lines.append(f"  received: no response ({reply.exception_msg})")
    else:
        lines.append(f"  received: {reply.status_code}")
        if reply.body is not None:
            lines.append(f"  body:     {_shown(reply.body)}")
    return "\n".join(lines)


def _fail(message: str, reply: ApiResponse) -> None:
    raise AssertionError(f"{message}\n{describe(reply)}")


def expect_status(reply: ApiResponse, status: int) -> ApiResponse:
    """Check the reply has the given status code.

    Args:
        reply: The reply to check.
        status: The status code expected.

    Returns:
        The reply, so a check can be followed by another.

    Raises:
        AssertionError: If it has a different status, or there was no
            response at all (the message says which, and what was sent).
    """
    __tracebackhide__ = True
    if reply.exception_msg is not None:
        _fail(f"expected status {status} but there was no response", reply)
    if reply.status_code != status:
        _fail(f"expected status {status} but got {reply.status_code}", reply)
    return reply


def expect_no_response(reply: ApiResponse) -> ApiResponse:
    """Check that nothing came back (the service was unreachable or timed out).

    Args:
        reply: The reply to check.

    Returns:
        The reply.

    Raises:
        AssertionError: If a response did come back.
    """
    __tracebackhide__ = True
    if reply.exception_msg is None:
        _fail("expected no response but got one", reply)
    return reply


def json_value(reply: ApiResponse, path: str) -> Any:
    """Read one value out of a JSON reply.

    The path is the keys from the top, joined with dots; a number picks an
    item of a list, so ``areas.test_cases.read`` and ``folders.0.id`` both
    work. Keys that themselves contain a dot are not supported.

    Args:
        reply: The reply to read.
        path: Where the value is.

    Returns:
        The value (use it in a later request).

    Raises:
        AssertionError: If the body is not JSON, or the path is not in it (the
            message says where it stopped and what was there).
    """
    __tracebackhide__ = True
    current: Any = reply.body
    if not isinstance(current, (dict, list)):
        _fail(f"expected a JSON body to read '{path}' from, "
              f"but it is {type(current).__name__}", reply)

    walked: list[str] = []
    for key in path.split("."):
        here = ".".join(walked) or "the top"
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit() \
                and int(key) < len(current):
            current = current[int(key)]
        elif isinstance(current, dict):
            _fail(f"'{path}' is not in the body: no '{key}' at {here} "
                  f"(it has {sorted(map(str, current))})", reply)
        elif isinstance(current, list):
            _fail(f"'{path}' is not in the body: no item '{key}' at {here} "
                  f"(a list of {len(current)})", reply)
        else:
            _fail(f"'{path}' is not in the body: {here} is "
                  f"{type(current).__name__}, not something with '{key}'",
                  reply)
        walked.append(key)
    return current


def expect_json(reply: ApiResponse, path: str, expected: Any = _MISSING) -> Any:
    """Check a JSON reply has a value at a path, and optionally what it is.

    Args:
        reply: The reply to check.
        path: Where the value should be (see ``json_value``).
        expected: The value it should equal. Leave out to check only that it
            is there.

    Returns:
        The value found, so it can be kept for a later request::

            token = expect_json(login, "token")

    Raises:
        AssertionError: If the path is missing, or the value differs.
    """
    __tracebackhide__ = True
    value = json_value(reply, path)
    if expected is not _MISSING and value != expected:
        _fail(f"expected '{path}' to be {expected!r} but it is {value!r}",
              reply)
    return value
