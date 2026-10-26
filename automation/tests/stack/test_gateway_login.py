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

The first real tests: logging in, and using what the login returns.

They need a running stack (Identity, CMS and Gateway), so they are marked
'stack' and run with:  pytest -m stack
"""
import pytest
from api_core import expect_json, expect_status

pytestmark = pytest.mark.stack


def _login_headers(email: str, token: str) -> dict:
    return {"X-Items-User": email, "X-Items-Token": token}


async def test_a_token_from_logging_in_works_on_the_next_request(
        gateway, admin):
    login = await gateway.post("web/sessions", json=admin)
    expect_status(login, 200)
    token = expect_json(login, "token")

    projects = await gateway.get(
        "web/projects",
        headers=_login_headers(admin["email_address"], token))
    expect_status(projects, 200)


async def test_a_wrong_password_is_refused(gateway, admin):
    reply = await gateway.post("web/sessions", json={
        "email_address": admin["email_address"],
        "password": "not-the-password-1"})
    expect_status(reply, 401)


async def test_a_request_without_logging_in_is_refused(gateway):
    expect_status(await gateway.get("web/projects"), 401)


async def test_a_made_up_token_is_refused(gateway, admin):
    reply = await gateway.get(
        "web/projects",
        headers=_login_headers(admin["email_address"], "0" * 32))
    expect_status(reply, 401)
