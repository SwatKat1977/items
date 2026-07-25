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
from items.services.items_cms.routes.folders.get_folder_handler import (
    GetFolderHandler,
)
from items.services.items_cms.routes.folders.list_folders_handler import (
    ListFoldersHandler,
)
from items.services.items_cms.routes.folders.add_folder_handler import (
    AddFolderHandler,
)
from items.services.items_cms.routes.folders.modify_folder_handler import (
    ModifyFolderHandler,
)
from items.services.items_cms.routes.folders.delete_folder_handler import (
    DeleteFolderHandler,
)
from items.services.items_cms.services.folder_service import (
    FolderService,
    FolderResult,
)

_LOGGER = MagicMock()

_VALID_ADD_BODY = {"project_id": 5, "parent_id": None, "name": "Root"}


def _ok(**kwargs):
    return FolderResult(success=True, **kwargs)


def _internal():
    return FolderResult(success=False, error_msg="err", is_internal=True)


def _not_found(msg="not found"):
    return FolderResult(success=False, error_msg=msg, not_found=True)


def _conflict(msg="already exists"):
    return FolderResult(success=False, error_msg=msg, is_conflict=True)


def _bad_request(msg="bad"):
    return FolderResult(success=False, error_msg=msg)


# ------------------------------------------------------------------
# GetFolderHandler
# ------------------------------------------------------------------

class TestGetFolderHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=FolderService)
        handler = GetFolderHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/folders/<int:folder_id>")
        async def get_folder(folder_id):
            return await handler.get_folder(folder_id)

        self.client = app.test_client()

    async def test_success_returns_200(self):
        self.mock_service.get_folder.return_value = _ok(
            data={"id": 1, "name": "Root"})
        async with self.client as c:
            response = await c.get("/folders/1")
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["name"], "Root")

    async def test_not_found_returns_404(self):
        self.mock_service.get_folder.return_value = _not_found()
        async with self.client as c:
            response = await c.get("/folders/99")
        self.assertEqual(response.status_code, 404)

    async def test_internal_error_returns_500(self):
        self.mock_service.get_folder.return_value = _internal()
        async with self.client as c:
            response = await c.get("/folders/1")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# ListFoldersHandler
# ------------------------------------------------------------------

class TestListFoldersHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=FolderService)
        handler = ListFoldersHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/folders")
        async def list_folders():
            return await handler.list_folders()

        self.client = app.test_client()

    async def test_missing_project_id_returns_400(self):
        async with self.client as c:
            response = await c.get("/folders")
        self.assertEqual(response.status_code, 400)
        self.mock_service.list_folders.assert_not_called()

    async def test_non_integer_project_id_returns_400(self):
        async with self.client as c:
            response = await c.get("/folders?project_id=abc")
        self.assertEqual(response.status_code, 400)
        self.mock_service.list_folders.assert_not_called()

    async def test_success_returns_200(self):
        self.mock_service.list_folders.return_value = _ok(
            data=[{"id": 1, "name": "Root"}])
        async with self.client as c:
            response = await c.get("/folders?project_id=5")
        self.assertEqual(response.status_code, 200)
        self.mock_service.list_folders.assert_called_once_with(5)
        data = await response.get_json()
        self.assertEqual(data["folders"][0]["name"], "Root")

    async def test_project_not_found_returns_404(self):
        self.mock_service.list_folders.return_value = _not_found()
        async with self.client as c:
            response = await c.get("/folders?project_id=999")
        self.assertEqual(response.status_code, 404)

    async def test_internal_error_returns_500(self):
        self.mock_service.list_folders.return_value = _internal()
        async with self.client as c:
            response = await c.get("/folders?project_id=5")
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# AddFolderHandler
# ------------------------------------------------------------------

class TestAddFolderHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=FolderService)
        handler = AddFolderHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/folders", methods=["POST"])
        async def add_folder():
            return await handler.add_folder()

        self.client = app.test_client()

    async def _post(self, body):
        async with self.client as c:
            return await c.post("/folders", json=body)

    async def test_success_returns_200(self):
        self.mock_service.create_folder.return_value = _ok(data=7)
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["folder_id"], 7)
        self.mock_service.create_folder.assert_called_once_with(
            project_id=5, parent_id=None, name="Root")

    async def test_missing_field_returns_400(self):
        response = await self._post({"project_id": 5, "name": "Root"})
        self.assertEqual(response.status_code, 400)
        self.mock_service.create_folder.assert_not_called()

    async def test_project_not_found_returns_404(self):
        self.mock_service.create_folder.return_value = _not_found(
            "Project id is invalid")
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 404)

    async def test_conflict_returns_409(self):
        self.mock_service.create_folder.return_value = _conflict()
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 409)

    async def test_bad_request_returns_400(self):
        self.mock_service.create_folder.return_value = _bad_request()
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 400)

    async def test_internal_error_returns_500(self):
        self.mock_service.create_folder.return_value = _internal()
        response = await self._post(_VALID_ADD_BODY)
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# ModifyFolderHandler
# ------------------------------------------------------------------

class TestModifyFolderHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=FolderService)
        handler = ModifyFolderHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/folders/<int:folder_id>", methods=["PATCH"])
        async def modify_folder(folder_id):
            return await handler.modify_folder(folder_id)

        self.client = app.test_client()

    async def _patch(self, folder_id, body):
        async with self.client as c:
            return await c.patch(f"/folders/{folder_id}", json=body)

    async def test_success_returns_200(self):
        self.mock_service.update_folder.return_value = _ok()
        response = await self._patch(1, {"name": "New"})
        self.assertEqual(response.status_code, 200)
        data = await response.get_json()
        self.assertEqual(data["status"], 1)
        self.mock_service.update_folder.assert_called_once_with(
            folder_id=1, name="New")

    async def test_missing_field_returns_400(self):
        response = await self._patch(1, {})
        self.assertEqual(response.status_code, 400)
        self.mock_service.update_folder.assert_not_called()

    async def test_not_found_returns_404(self):
        self.mock_service.update_folder.return_value = _not_found()
        response = await self._patch(99, {"name": "New"})
        self.assertEqual(response.status_code, 404)

    async def test_conflict_returns_409(self):
        self.mock_service.update_folder.return_value = _conflict()
        response = await self._patch(1, {"name": "New"})
        self.assertEqual(response.status_code, 409)

    async def test_bad_request_returns_400(self):
        self.mock_service.update_folder.return_value = _bad_request()
        response = await self._patch(1, {"name": "New"})
        self.assertEqual(response.status_code, 400)

    async def test_internal_error_returns_500(self):
        self.mock_service.update_folder.return_value = _internal()
        response = await self._patch(1, {"name": "New"})
        self.assertEqual(response.status_code, 500)


# ------------------------------------------------------------------
# DeleteFolderHandler
# ------------------------------------------------------------------

class TestDeleteFolderHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_service = AsyncMock(spec=FolderService)
        handler = DeleteFolderHandler(_LOGGER, self.mock_service)

        app = Quart(__name__)

        @app.route("/folders/<int:folder_id>", methods=["DELETE"])
        async def delete_folder(folder_id):
            return await handler.delete_folder(folder_id)

        self.client = app.test_client()

    async def test_success_returns_200(self):
        self.mock_service.delete_folder.return_value = _ok()
        async with self.client as c:
            response = await c.delete("/folders/1")
        self.assertEqual(response.status_code, 200)

    async def test_not_found_returns_404(self):
        self.mock_service.delete_folder.return_value = _not_found()
        async with self.client as c:
            response = await c.delete("/folders/99")
        self.assertEqual(response.status_code, 404)

    async def test_internal_error_returns_500(self):
        self.mock_service.delete_folder.return_value = _internal()
        async with self.client as c:
            response = await c.delete("/folders/1")
        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
