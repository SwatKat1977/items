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
from unittest.mock import MagicMock
from items.services.items_gateway.route_injections import RouteInjections


class TestRouteInjections(unittest.TestCase):

    def test_defaults(self):
        injections = RouteInjections()
        self.assertIsNone(injections.logger)
        self.assertIsNone(injections.sessions)
        self.assertIsNone(injections.configuration)
        self.assertIsNone(injections.rest_client)
        self.assertIsNone(injections.metadata_handler)
        self.assertIsNone(injections.email_service)

    def test_populated(self):
        logger = MagicMock()
        sessions = MagicMock()
        configuration = MagicMock()
        rest_client = MagicMock()
        metadata_handler = MagicMock()
        email_service = MagicMock()

        injections = RouteInjections(
            logger=logger,
            sessions=sessions,
            configuration=configuration,
            rest_client=rest_client,
            metadata_handler=metadata_handler,
            email_service=email_service)

        self.assertIs(injections.logger, logger)
        self.assertIs(injections.sessions, sessions)
        self.assertIs(injections.configuration, configuration)
        self.assertIs(injections.rest_client, rest_client)
        self.assertIs(injections.metadata_handler, metadata_handler)
        self.assertIs(injections.email_service, email_service)

    def test_is_frozen(self):
        injections = RouteInjections()
        with self.assertRaises(Exception):
            injections.logger = MagicMock()


if __name__ == "__main__":
    unittest.main()
