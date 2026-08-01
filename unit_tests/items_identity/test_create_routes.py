import json
import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import quart
from quart import Response
from routes import create_routes
from routes.auth import create_auth_routes
from routes.system import create_system_routes
from routes.users import create_users_routes


class TestCreateAuthRoutes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock()
        self.mock_config = MagicMock()

    @patch("routes.auth.AuthenticatePasswordHandler")
    async def test_returns_blueprint_with_correct_name(self, mock_handler_cls):
        bp = create_auth_routes(self.mock_logger, self.mock_state, self.mock_config)
        self.assertIsInstance(bp, quart.Blueprint)
        self.assertEqual(bp.name, "auth_routes")

    @patch("routes.auth.AuthenticatePasswordHandler")
    async def test_initialises_handler_with_correct_args(self, mock_handler_cls):
        create_auth_routes(self.mock_logger, self.mock_state, self.mock_config)
        mock_handler_cls.assert_called_once_with(
            self.mock_logger, self.mock_state, self.mock_config)

    @patch("routes.auth.AuthenticatePasswordHandler")
    async def test_logs_route_registration(self, mock_handler_cls):
        create_auth_routes(self.mock_logger, self.mock_state, self.mock_config)
        self.mock_logger.debug.assert_called()

    @patch("routes.auth.AuthenticatePasswordHandler")
    async def test_route_handler_calls_authenticate(self, mock_handler_cls):
        mock_handler = MagicMock()
        mock_handler.authenticate_password = AsyncMock(
            return_value=Response(
                json.dumps({"success": True, "message": "ok"}),
                status=200,
                content_type="application/json"))
        mock_handler_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_auth_routes(self.mock_logger, self.mock_state, self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.post("/auth/login",
                              json={"email_address": "a@b.com",
                                    "password": "pass"})

        mock_handler.authenticate_password.assert_called_once()


class TestCreateSystemRoutes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock()

    @patch("routes.system.HealthHandler")
    async def test_returns_blueprint_with_correct_name(self, mock_handler_cls):
        bp = create_system_routes(self.mock_logger, self.mock_state)
        self.assertIsInstance(bp, quart.Blueprint)
        self.assertEqual(bp.name, "system_routes")

    @patch("routes.system.HealthHandler")
    async def test_initialises_handler_with_correct_args(self, mock_handler_cls):
        create_system_routes(self.mock_logger, self.mock_state)
        mock_handler_cls.assert_called_once_with(self.mock_logger, self.mock_state)

    @patch("routes.system.HealthHandler")
    async def test_logs_route_registration(self, mock_handler_cls):
        create_system_routes(self.mock_logger, self.mock_state)
        self.mock_logger.debug.assert_called()

    @patch("routes.system.HealthHandler")
    async def test_route_handler_calls_health(self, mock_handler_cls):
        mock_handler = MagicMock()
        mock_handler.health = AsyncMock(
            return_value=Response(
                json.dumps({"status": "healthy"}),
                status=200,
                content_type="application/json"))
        mock_handler_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_system_routes(self.mock_logger, self.mock_state)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.get("/system/health")

        mock_handler.health.assert_called_once()


class TestCreateUsersRoutes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock()
        self.mock_config = MagicMock()

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_returns_blueprint_with_correct_name(
            self, *_mocks):
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        self.assertIsInstance(bp, quart.Blueprint)
        self.assertEqual(bp.name, "users_routes")

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_initialises_all_handlers_with_correct_args(
            self, mock_profile, mock_list, mock_get, mock_create,
            mock_modify, mock_reset, mock_change):
        create_users_routes(self.mock_logger, self.mock_state, self.mock_config)
        for mock_cls in (mock_profile, mock_list, mock_get, mock_create,
                         mock_modify, mock_reset, mock_change):
            mock_cls.assert_called_once_with(
                self.mock_logger, self.mock_state, self.mock_config)

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_logs_route_registration(self, *_mocks):
        create_users_routes(self.mock_logger, self.mock_state, self.mock_config)
        self.mock_logger.debug.assert_called()

    def _ok_response(self, body=None):
        return Response(
            json.dumps(body or {"status": "ok"}),
            status=200,
            content_type="application/json")

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_route_handler_calls_get_user_profile(
            self, mock_profile_cls, *_rest):
        mock_handler = MagicMock()
        mock_handler.get_user_profile = AsyncMock(
            return_value=self._ok_response({"id": 1, "is_administrator": True}))
        mock_profile_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.post("/users/profile",
                              json={"email_address": "a@b.com"})

        mock_handler.get_user_profile.assert_called_once()

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_route_handler_calls_list_users(
            self, _profile, mock_list_cls, *_rest):
        mock_handler = MagicMock()
        mock_handler.list_users = AsyncMock(
            return_value=self._ok_response({"users": []}))
        mock_list_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.get("/users")

        mock_handler.list_users.assert_called_once()

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_route_handler_calls_create_user(
            self, _profile, _list, _get, mock_create_cls, *_rest):
        mock_handler = MagicMock()
        mock_handler.create_user = AsyncMock(
            return_value=Response(
                json.dumps({"id": 1}), status=201,
                content_type="application/json"))
        mock_create_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.post("/users", json={
                "email_address": "new@b.com", "full_name": "F",
                "display_name": "D", "password": "pw"})

        mock_handler.create_user.assert_called_once()

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_route_handler_calls_get_user(
            self, _profile, _list, mock_get_cls, *_rest):
        mock_handler = MagicMock()
        mock_handler.get_user = AsyncMock(
            return_value=self._ok_response({"id": 1}))
        mock_get_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.get("/users/1")

        mock_handler.get_user.assert_called_once()

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_route_handler_calls_modify_user(
            self, _profile, _list, _get, _create, mock_modify_cls, *_rest):
        mock_handler = MagicMock()
        mock_handler.modify_user = AsyncMock(
            return_value=self._ok_response())
        mock_modify_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.patch("/users/1", json={
                "full_name": "F", "display_name": "D",
                "account_status": 1, "is_administrator": True,
                "requesting_user_id": 2})

        mock_handler.modify_user.assert_called_once()

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_route_handler_calls_reset_password(
            self, _profile, _list, _get, _create, _modify,
            mock_reset_cls, _change):
        mock_handler = MagicMock()
        mock_handler.reset_password = AsyncMock(
            return_value=self._ok_response())
        mock_reset_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.post("/users/1/password",
                              json={"new_password": "newpass123"})

        mock_handler.reset_password.assert_called_once()

    @patch("routes.users.ChangePasswordHandler")
    @patch("routes.users.ResetPasswordHandler")
    @patch("routes.users.ModifyUserHandler")
    @patch("routes.users.CreateUserHandler")
    @patch("routes.users.GetUserHandler")
    @patch("routes.users.ListUsersHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_route_handler_calls_change_password(
            self, _profile, _list, _get, _create, _modify,
            _reset, mock_change_cls):
        mock_handler = MagicMock()
        mock_handler.change_password = AsyncMock(
            return_value=self._ok_response())
        mock_change_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.post("/users/me/password", json={
                "user_id": 1, "current_password": "old",
                "new_password": "newpass123"})

        mock_handler.change_password.assert_called_once()


class TestCreateRoutes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_state = MagicMock()
        self.mock_config = MagicMock()

    @patch("routes.create_users_routes")
    @patch("routes.create_system_routes")
    @patch("routes.create_auth_routes")
    async def test_returns_blueprint_with_correct_name(self, mock_auth, mock_sys,
                                                       mock_users):
        mock_auth.return_value = quart.Blueprint("mock_auth", __name__)
        mock_sys.return_value = quart.Blueprint("mock_sys", __name__)
        mock_users.return_value = quart.Blueprint("mock_users", __name__)
        bp = create_routes(self.mock_logger, self.mock_state, self.mock_config)
        self.assertIsInstance(bp, quart.Blueprint)
        self.assertEqual(bp.name, "api_routes")

    @patch("routes.create_users_routes")
    @patch("routes.create_system_routes")
    @patch("routes.create_auth_routes")
    async def test_registers_all_sub_blueprints(self, mock_auth, mock_sys,
                                                mock_users):
        mock_auth.return_value = quart.Blueprint("mock_auth", __name__)
        mock_sys.return_value = quart.Blueprint("mock_sys", __name__)
        mock_users.return_value = quart.Blueprint("mock_users", __name__)
        create_routes(self.mock_logger, self.mock_state, self.mock_config)
        mock_auth.assert_called_once_with(
            self.mock_logger, self.mock_state, self.mock_config)
        mock_sys.assert_called_once_with(self.mock_logger, self.mock_state)
        mock_users.assert_called_once_with(
            self.mock_logger, self.mock_state, self.mock_config)
