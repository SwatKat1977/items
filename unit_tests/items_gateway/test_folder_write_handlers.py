"""
Unit tests for the gateway section (folder) write route handlers:
  POST   /<project_id>/folders            - CreateFolderHandler
  PATCH  /folders/<id>?project_id=        - ModifyFolderHandler
  DELETE /folders/<id>?project_id=        - DeleteFolderHandler
"""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
from quart import Quart
from weaver_framework.microservice.api_response import ApiResponse
from items.services.items_gateway.routes.web.folders.\
    create_folder_handler import CreateFolderHandler
from items.services.items_gateway.routes.web.folders.\
    delete_folder_handler import DeleteFolderHandler
from items.services.items_gateway.routes.web.folders.\
    modify_folder_handler import ModifyFolderHandler

_LOGGER = MagicMock()
_CREATE_BODY = {"parent_id": None, "name": "Regression"}
_MODIFY_BODY = {"name": "Renamed"}


def _config():
    cfg = MagicMock()
    cfg.apis_cms_svc = "http://cms/"
    return cfg


def _ok(body):
    return ApiResponse(status_code=200, body=body)


def _err(body, status):
    return ApiResponse(status_code=status, body=body)


def _conn_err():
    r = ApiResponse(status_code=0, body=None)
    r.exception_msg = "connection refused"
    return r


# ---------------------------------------------------------------------------
# CreateFolderHandler
# ---------------------------------------------------------------------------

class TestCreateFolderHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = CreateFolderHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/<int:project_id>/folders", methods=["POST"])
        async def route(project_id: int):
            return await handler.create_folder(project_id)

        self.client = app.test_client()

    async def _post(self, body, project_id=5):
        async with self.client as c:
            return await c.post(f"/{project_id}/folders", json=body)

    async def test_success_returns_200_with_id(self):
        self.mock_rc.post.return_value = _ok({"folder_id": 7})
        resp = await self._post(_CREATE_BODY)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(await resp.get_data()),
                         {"folder_id": 7})

    async def test_body_and_path_project_forwarded_to_cms(self):
        self.mock_rc.post.return_value = _ok({"folder_id": 7})
        await self._post({"parent_id": 3, "name": "Sub"}, project_id=5)
        self.mock_rc.post.assert_called_once_with(
            "http://cms/folders",
            json_data={"parent_id": 3, "name": "Sub", "project_id": 5})

    async def test_top_level_section_sends_a_null_parent(self):
        self.mock_rc.post.return_value = _ok({"folder_id": 7})
        await self._post(_CREATE_BODY)
        sent = self.mock_rc.post.call_args.kwargs["json_data"]
        self.assertIsNone(sent["parent_id"])

    async def test_project_id_in_the_body_is_rejected(self):
        """The project comes from the URL only. Any project_id in the body
        - matching, different, existing or not, whatever its type - is
        refused and the CMS is never called."""
        for body_project in (5, 99, 20, 0, "5", "abc", None):
            with self.subTest(body_project=body_project):
                resp = await self._post(
                    {**_CREATE_BODY, "project_id": body_project},
                    project_id=5)
                self.assertEqual(resp.status_code, 400)
                body = json.loads(await resp.get_data())
                self.assertIn("project_id must not be in the request body",
                              body["error"])
        self.mock_rc.post.assert_not_called()

    async def test_cms_errors_are_propagated(self):
        for status in (400, 404, 409, 500):
            with self.subTest(status=status):
                self.mock_rc.post.return_value = _err({"error": "x"}, status)
                resp = await self._post(_CREATE_BODY)
                self.assertEqual(resp.status_code, status)

    async def test_connection_error_returns_500(self):
        self.mock_rc.post.return_value = _conn_err()
        resp = await self._post(_CREATE_BODY)
        self.assertEqual(resp.status_code, 500)

    async def test_invalid_json_returns_400_without_calling_cms(self):
        async with self.client as c:
            resp = await c.post("/5/folders", data="not json",
                                headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_non_object_json_returns_400_without_calling_cms(self):
        resp = await self._post([1, 2, 3])
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.post.assert_not_called()

    async def test_response_is_json(self):
        self.mock_rc.post.return_value = _ok({"folder_id": 7})
        resp = await self._post(_CREATE_BODY)
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# ModifyFolderHandler
# ---------------------------------------------------------------------------

class TestModifyFolderHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = ModifyFolderHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/folders/<int:folder_id>", methods=["PATCH"])
        async def route(folder_id: int):
            return await handler.modify_folder(folder_id)

        self.client = app.test_client()

    async def _patch(self, body, folder_id=3, query="?project_id=5"):
        async with self.client as c:
            return await c.patch(f"/folders/{folder_id}{query}", json=body)

    async def test_success_returns_200(self):
        self.mock_rc.patch.return_value = _ok({"status": 1})
        resp = await self._patch(_MODIFY_BODY)
        self.assertEqual(resp.status_code, 200)

    async def test_url_carries_the_project_and_body_is_forwarded(self):
        self.mock_rc.patch.return_value = _ok({"status": 1})
        await self._patch(_MODIFY_BODY, folder_id=9, query="?project_id=7")
        self.mock_rc.patch.assert_called_once_with(
            "http://cms/folders/9?project_id=7", json_data=_MODIFY_BODY)

    async def test_missing_project_id_returns_400_without_calling_cms(self):
        resp = await self._patch(_MODIFY_BODY, query="")
        self.assertEqual(resp.status_code, 400)
        body = json.loads(await resp.get_data())
        self.assertIn("project_id", body["error"])
        self.mock_rc.patch.assert_not_called()

    async def test_non_integer_project_id_returns_400(self):
        resp = await self._patch(_MODIFY_BODY, query="?project_id=abc")
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_invalid_json_returns_400_without_calling_cms(self):
        async with self.client as c:
            resp = await c.patch("/folders/3?project_id=5", data="not json",
                                 headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_non_object_json_returns_400_without_calling_cms(self):
        resp = await self._patch([1, 2])
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.patch.assert_not_called()

    async def test_cms_errors_are_propagated(self):
        for status in (400, 404, 409, 500):
            with self.subTest(status=status):
                self.mock_rc.patch.return_value = _err({"error": "x"}, status)
                resp = await self._patch(_MODIFY_BODY)
                self.assertEqual(resp.status_code, status)

    async def test_connection_error_returns_500(self):
        self.mock_rc.patch.return_value = _conn_err()
        resp = await self._patch(_MODIFY_BODY)
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.patch.return_value = _ok({"status": 1})
        resp = await self._patch(_MODIFY_BODY)
        self.assertEqual(resp.content_type, "application/json")


# ---------------------------------------------------------------------------
# DeleteFolderHandler
# ---------------------------------------------------------------------------

class TestDeleteFolderHandler(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_rc = AsyncMock()
        handler = DeleteFolderHandler(_LOGGER, _config(), self.mock_rc)
        app = Quart(__name__)

        @app.route("/folders/<int:folder_id>", methods=["DELETE"])
        async def route(folder_id: int):
            return await handler.delete_folder(folder_id)

        self.client = app.test_client()

    async def _delete(self, folder_id=3, query="?project_id=5"):
        async with self.client as c:
            return await c.delete(f"/folders/{folder_id}{query}")

    async def test_success_returns_200(self):
        self.mock_rc.delete.return_value = _ok({})
        resp = await self._delete()
        self.assertEqual(resp.status_code, 200)

    async def test_url_carries_the_project_and_no_cascade_by_default(self):
        self.mock_rc.delete.return_value = _ok({})
        await self._delete(folder_id=9, query="?project_id=7")
        self.mock_rc.delete.assert_called_once_with(
            "http://cms/folders/9?project_id=7")

    async def test_cascade_is_forwarded_as_sent(self):
        self.mock_rc.delete.return_value = _ok({})
        for value in ("true", "false", "TRUE"):
            with self.subTest(value=value):
                self.mock_rc.delete.reset_mock()
                await self._delete(
                    folder_id=9, query=f"?project_id=7&cascade={value}")
                self.mock_rc.delete.assert_called_once_with(
                    f"http://cms/folders/9?project_id=7&cascade={value}")

    async def test_odd_cascade_values_are_forwarded_encoded_for_the_cms(self):
        """The Gateway has no opinion on cascade: the CMS rejects values it
        does not understand. Anything sent must still be URL-safe."""
        self.mock_rc.delete.return_value = _err(
            {"error": "cascade must be true or false"}, 400)
        resp = await self._delete(query="?project_id=5&cascade=a%26b%3Dc")
        self.mock_rc.delete.assert_called_once_with(
            "http://cms/folders/3?project_id=5&cascade=a%26b%3Dc")
        self.assertEqual(resp.status_code, 400)

    async def test_empty_cascade_is_still_forwarded(self):
        self.mock_rc.delete.return_value = _err({"error": "x"}, 400)
        await self._delete(query="?project_id=5&cascade=")
        self.mock_rc.delete.assert_called_once_with(
            "http://cms/folders/3?project_id=5&cascade=")

    async def test_missing_project_id_returns_400_without_calling_cms(self):
        resp = await self._delete(query="")
        self.assertEqual(resp.status_code, 400)
        self.mock_rc.delete.assert_not_called()

    async def test_non_integer_project_id_returns_400(self):
        resp = await self._delete(query="?project_id=abc")
        self.assertEqual(resp.status_code, 400)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["error"], "project_id must be an integer")
        self.mock_rc.delete.assert_not_called()

    async def test_cms_refusal_keeps_its_message_and_test_case_count(self):
        """The Portal builds its second confirmation prompt from this, so
        the 409 and its testcase_count must arrive intact."""
        self.mock_rc.delete.return_value = _err(
            {"error": "Folder contains 12 test case(s); delete with "
                      "cascade=true to remove them too",
             "testcase_count": 12}, 409)
        resp = await self._delete()
        self.assertEqual(resp.status_code, 409)
        body = json.loads(await resp.get_data())
        self.assertEqual(body["testcase_count"], 12)
        self.assertIn("12 test case(s)", body["error"])

    async def test_cms_404_is_propagated(self):
        self.mock_rc.delete.return_value = _err(
            {"error": "Folder not found"}, 404)
        resp = await self._delete()
        self.assertEqual(resp.status_code, 404)

    async def test_connection_error_returns_500(self):
        self.mock_rc.delete.return_value = _conn_err()
        resp = await self._delete()
        self.assertEqual(resp.status_code, 500)

    async def test_response_is_json(self):
        self.mock_rc.delete.return_value = _ok({})
        resp = await self._delete()
        self.assertEqual(resp.content_type, "application/json")


if __name__ == "__main__":
    unittest.main()
