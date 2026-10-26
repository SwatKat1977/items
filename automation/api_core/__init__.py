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

A small, generic library for API automation tests.

It sends a request and checks the response, and it knows nothing about the
service it is testing: everything specific to ITEMS lives in the tests and
their helpers. It must never import anything from ``items``.

    from api_core import ApiClient, expect_status, expect_json

    async with ApiClient("http://host:7050/") as api:
        login = await api.post("web/sessions", json={...})
        expect_status(login, 200)
        token = expect_json(login, "token")
"""
from .checks import (
    describe, expect_json, expect_no_response, expect_status, json_value)
from .client import ApiClient, DEFAULT_TIMEOUT, Reply, SentRequest

__all__ = ["ApiClient", "DEFAULT_TIMEOUT", "Reply", "SentRequest", "describe",
           "expect_json", "expect_no_response", "expect_status",
           "json_value"]
