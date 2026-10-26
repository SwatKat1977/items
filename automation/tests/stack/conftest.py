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

What the tests that need a running ITEMS stack share.

This is the ITEMS-specific side: where the Gateway is and who the
administrator is. The generic library (``api_core``) knows neither.

Settings come from the environment:

    ITEMS_GATEWAY_URL      default http://127.0.0.1:7050/
    ITEMS_ADMIN_EMAIL      default admin@localhost
    ITEMS_ADMIN_PASSWORD   no default: the stack tests are skipped without it
"""
import os
import pytest
from api_core import ApiClient


@pytest.fixture(scope="session")
async def gateway():
    """A client for the Gateway, open for the whole test run."""
    url = os.environ.get("ITEMS_GATEWAY_URL", "http://127.0.0.1:7050/")
    async with ApiClient(url) as client:
        yield client


@pytest.fixture(scope="session")
def admin() -> dict:
    """The administrator's login details, as the login route takes them."""
    password = os.environ.get("ITEMS_ADMIN_PASSWORD")
    if not password:
        pytest.skip("set ITEMS_ADMIN_PASSWORD to run the stack tests")
    return {"email_address": os.environ.get("ITEMS_ADMIN_EMAIL",
                                            "admin@localhost"),
            "password": password}
