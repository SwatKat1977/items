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
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from items.services.items_cms.routes.case_types.add_case_type_handler import (
    AddCaseTypeHandler,
)
from items.services.items_cms.routes.case_types.get_case_type_handler import (
    GetCaseTypeHandler,
)
from items.services.items_cms.routes.case_types.get_case_types_handler import (
    GetCaseTypesHandler,
)
from items.services.items_cms.routes.case_types.update_case_type_handler import (
    UpdateCaseTypeHandler,
)
from items.services.items_cms.routes.case_types.set_default_case_type_handler import (
    SetDefaultCaseTypeHandler,
)
from items.services.items_cms.services.case_types_service import (
    CaseTypesService,
    CaseTypeResult,
)

_LOGGER = MagicMock()
_BODY = {"name": "Smoke", "description": "desc"}


def _ok(**kwargs):
    return CaseTypeResult(success=True, **kwargs)


def _internal():
    return CaseTypeResult(success=False, error_msg="err", is_internal=True)


def _not_found():
    return CaseTypeResult(success=False, error_msg="nf", not_found=True)


def _conflict():
    return CaseTypeResult(success=False, error_msg="dup", is_conflict=True)


def _bad_request():
    return CaseTypeResult(success=False, error_msg="bad")


class TestGetCaseTypeHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.service = AsyncMock(spec=CaseTypesService)
        handler = GetCaseTypeHandler(_LOGGER, self.service)
        app = Quart(__name__)

        @app.route("/case_types/<int:type_id>")
        async def get_one(type_id):
            return await handler.get_case_type(type_id)

        self.client = app.test_client()

    async def _get(self):
        async with self.client as c:
            return await c.get("/case_types/1")

    async def test_success(self):
        data = {"id": 1, "name": "Smoke", "description": "d",
                "is_default": False}
        self.service.get_case_type.return_value = _ok(data=data)
        response = await self._get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(await response.get_json(), data)

    async def test_not_found(self):
        self.service.get_case_type.return_value = _not_found()
        self.assertEqual((await self._get()).status_code, 404)

    async def test_internal(self):
        self.service.get_case_type.return_value = _internal()
        self.assertEqual((await self._get()).status_code, 500)

    async def test_bad_request(self):
        self.service.get_case_type.return_value = _bad_request()
        self.assertEqual((await self._get()).status_code, 400)


class TestGetCaseTypesHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.service = AsyncMock(spec=CaseTypesService)
        handler = GetCaseTypesHandler(_LOGGER, self.service)
        app = Quart(__name__)

        @app.route("/case_types")
        async def get_all():
            return await handler.get_case_types()

        self.client = app.test_client()

    async def test_success(self):
        data = [{"id": 1, "name": "A", "description": "",
                 "is_default": True}]
        self.service.get_all_case_types.return_value = _ok(data=data)
        async with self.client as c:
            response = await c.get("/case_types")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(await response.get_json(), data)

    async def test_internal(self):
        self.service.get_all_case_types.return_value = _internal()
        async with self.client as c:
            response = await c.get("/case_types")
        self.assertEqual(response.status_code, 500)


class TestAddCaseTypeHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.service = AsyncMock(spec=CaseTypesService)
        handler = AddCaseTypeHandler(_LOGGER, self.service)
        app = Quart(__name__)

        @app.route("/case_types", methods=["POST"])
        async def add():
            return await handler.add_case_type()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/case_types", json=body)

    async def test_success(self):
        self.service.add_case_type.return_value = _ok(data=7)
        response = await self._post(_BODY)
        self.assertEqual(response.status_code, 200)
        self.assertEqual((await response.get_json())["case_type_id"], 7)

    async def test_missing_field(self):
        response = await self._post({"name": "Smoke"})
        self.assertEqual(response.status_code, 400)
        self.service.add_case_type.assert_not_called()

    async def test_empty_name(self):
        response = await self._post({"name": "", "description": ""})
        self.assertEqual(response.status_code, 400)

    async def test_whitespace_only_name(self):
        response = await self._post({"name": "   ", "description": ""})
        self.assertEqual(response.status_code, 400)
        self.service.add_case_type.assert_not_called()

    async def test_extra_field_rejected(self):
        response = await self._post({**_BODY, "is_default": True})
        self.assertEqual(response.status_code, 400)

    async def test_conflict(self):
        self.service.add_case_type.return_value = _conflict()
        self.assertEqual((await self._post(_BODY)).status_code, 409)

    async def test_internal(self):
        self.service.add_case_type.return_value = _internal()
        self.assertEqual((await self._post(_BODY)).status_code, 500)

    async def test_bad_request(self):
        self.service.add_case_type.return_value = _bad_request()
        self.assertEqual((await self._post(_BODY)).status_code, 400)


class TestUpdateCaseTypeHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.service = AsyncMock(spec=CaseTypesService)
        handler = UpdateCaseTypeHandler(_LOGGER, self.service)
        app = Quart(__name__)

        @app.route("/case_types/<int:type_id>", methods=["PATCH"])
        async def update(type_id):
            return await handler.update_case_type(type_id)

        self.client = app.test_client()

    async def _patch(self, body):
        async with self.client as c:
            return await c.patch("/case_types/1", json=body)

    async def test_success(self):
        self.service.update_case_type.return_value = _ok()
        response = await self._patch(_BODY)
        self.assertEqual(response.status_code, 200)
        self.service.update_case_type.assert_awaited_once_with(
            type_id=1, name="Smoke", description="desc")

    async def test_is_default_not_accepted(self):
        response = await self._patch({**_BODY, "is_default": True})
        self.assertEqual(response.status_code, 400)
        self.service.update_case_type.assert_not_called()

    async def test_whitespace_only_name(self):
        response = await self._patch({"name": "  ", "description": ""})
        self.assertEqual(response.status_code, 400)
        self.service.update_case_type.assert_not_called()

    async def test_missing_field(self):
        self.assertEqual((await self._patch({"name": "x"})).status_code, 400)

    async def test_not_found(self):
        self.service.update_case_type.return_value = _not_found()
        self.assertEqual((await self._patch(_BODY)).status_code, 404)

    async def test_conflict(self):
        self.service.update_case_type.return_value = _conflict()
        self.assertEqual((await self._patch(_BODY)).status_code, 409)

    async def test_internal(self):
        self.service.update_case_type.return_value = _internal()
        self.assertEqual((await self._patch(_BODY)).status_code, 500)

    async def test_bad_request(self):
        self.service.update_case_type.return_value = _bad_request()
        self.assertEqual((await self._patch(_BODY)).status_code, 400)


class TestSetDefaultCaseTypeHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.service = AsyncMock(spec=CaseTypesService)
        handler = SetDefaultCaseTypeHandler(_LOGGER, self.service)
        app = Quart(__name__)

        @app.route("/case_types/<int:type_id>/set_default",
                   methods=["POST"])
        async def set_default(type_id):
            return await handler.set_default_case_type(type_id)

        self.client = app.test_client()

    async def _post(self):
        async with self.client as c:
            return await c.post("/case_types/1/set_default")

    async def test_success(self):
        self.service.set_default_case_type.return_value = _ok()
        self.assertEqual((await self._post()).status_code, 200)

    async def test_not_found(self):
        self.service.set_default_case_type.return_value = _not_found()
        self.assertEqual((await self._post()).status_code, 404)

    async def test_internal(self):
        self.service.set_default_case_type.return_value = _internal()
        self.assertEqual((await self._post()).status_code, 500)
