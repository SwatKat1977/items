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
from items.services.items_web_portal.metadata_settings import MetadataSettings


class TestMetadataSettings(unittest.TestCase):

    def test_defaults(self):
        settings = MetadataSettings()
        self.assertEqual(settings.default_time_zone, "")
        self.assertFalse(settings.using_server_default_time_zone)
        self.assertEqual(settings.instance_name, "")

    def test_populated(self):
        settings = MetadataSettings(
            default_time_zone="Europe/London",
            using_server_default_time_zone=True,
            instance_name="INSTANCE")
        self.assertEqual(settings.default_time_zone, "Europe/London")
        self.assertTrue(settings.using_server_default_time_zone)
        self.assertEqual(settings.instance_name, "INSTANCE")


if __name__ == "__main__":
    unittest.main()
