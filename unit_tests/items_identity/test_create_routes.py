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

    @patch("routes.users.GetUserProfileHandler")
    async def test_returns_blueprint_with_correct_name(self, mock_handler_cls):
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        self.assertIsInstance(bp, quart.Blueprint)
        self.assertEqual(bp.name, "users_routes")

    @patch("routes.users.GetUserProfileHandler")
    async def test_initialises_handler_with_correct_args(self, mock_handler_cls):
        create_users_routes(self.mock_logger, self.mock_state,
                            self.mock_config)
        mock_handler_cls.assert_called_once_with(
            self.mock_logger, self.mock_state, self.mock_config)

    @patch("routes.users.GetUserProfileHandler")
    async def test_logs_route_registration(self, mock_handler_cls):
        create_users_routes(self.mock_logger, self.mock_state,
                            self.mock_config)
        self.mock_logger.debug.assert_called()

    @patch("routes.users.UserManagementHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_all_user_routes_are_registered(self, _profile_cls,
                                                  _mgmt_cls):
        app = quart.Quart(__name__)
        app.register_blueprint(create_users_routes(
            self.mock_logger, self.mock_state, self.mock_config))

        registered = {(r.rule, method)
                      for r in app.url_map.iter_rules()
                      for method in r.methods}

        for rule, method in (
                ("/users/profile", "POST"),
                ("/users", "GET"),
                ("/users", "POST"),
                ("/users/<int:user_id>", "GET"),
                ("/users/<int:user_id>", "PATCH"),
                ("/users/<int:user_id>/password", "POST"),
        ):
            with self.subTest(rule=rule, method=method):
                self.assertIn((rule, method), registered)

    @patch("routes.users.UserManagementHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_no_delete_route_is_exposed(self, _profile_cls, _mgmt_cls):
        """Accounts are deactivated, never deleted - see design doc 10.6."""
        app = quart.Quart(__name__)
        app.register_blueprint(create_users_routes(
            self.mock_logger, self.mock_state, self.mock_config))

        for rule in app.url_map.iter_rules():
            self.assertNotIn("DELETE", rule.methods,
                             f"unexpected DELETE on {rule.rule}")

    @patch("routes.users.UserManagementHandler")
    @patch("routes.users.GetUserProfileHandler")
    async def test_route_handler_calls_get_user_profile(self, mock_handler_cls,
                                                       _mgmt_cls):
        mock_handler = MagicMock()
        mock_handler.get_user_profile = AsyncMock(
            return_value=Response(
                json.dumps({"id": 1, "is_administrator": True}),
                status=200,
                content_type="application/json"))
        mock_handler_cls.return_value = mock_handler

        app = quart.Quart(__name__)
        bp = create_users_routes(self.mock_logger, self.mock_state,
                                 self.mock_config)
        app.register_blueprint(bp)

        async with app.test_client() as client:
            await client.post("/users/profile",
                              json={"email_address": "a@b.com"})

        mock_handler.get_user_profile.assert_called_once()


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
