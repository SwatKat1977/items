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
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from items.services.items_gateway.metadata_handler import MetadataHandler


def _make_handler(config_file: str) -> MetadataHandler:
    config = MagicMock()
    config.general_metadata_config_file = config_file
    handler = MetadataHandler(MagicMock(), config)
    handler._logger = MagicMock()
    return handler


class TestReadMetadataFile(unittest.TestCase):

    def test_file_missing_returns_false(self):
        handler = _make_handler("/does/not/exist.config")
        self.assertFalse(handler.read_metadata_file())

    def test_invalid_json_returns_false(self):
        fd, path = tempfile.mkstemp(suffix=".config")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write("not valid json {")
            handler = _make_handler(path)
            self.assertFalse(handler.read_metadata_file())
        finally:
            os.unlink(path)

    def test_io_error_returns_false(self):
        handler = _make_handler("/does/exist.config")
        with patch("items.services.items_gateway.metadata_handler.os.path.exists",
                   return_value=True), \
             patch("builtins.open", side_effect=IOError("disk error")):
            self.assertFalse(handler.read_metadata_file())

    def test_schema_validation_failure_returns_false(self):
        fd, path = tempfile.mkstemp(suffix=".config")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump({"unexpected": "shape"}, file)
            handler = _make_handler(path)
            self.assertFalse(handler.read_metadata_file())
        finally:
            os.unlink(path)

    def test_server_default_time_zone_valid(self):
        fd, path = tempfile.mkstemp(suffix=".config")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump({
                    "server_settings": {
                        "instance_name": "INSTANCE",
                        "default_time_zone": "_server_tz_"
                    }
                }, file)
            handler = _make_handler(path)
            with patch(
                "items.services.items_gateway.metadata_handler.tzlocal."
                "get_localzone_name", return_value="Europe/London"):
                result = handler.read_metadata_file()
            self.assertTrue(result)
            self.assertTrue(handler._metadata_settings.using_server_default_time_zone)
            self.assertEqual(handler._metadata_settings.default_time_zone,
                             "Europe/London")
            self.assertEqual(handler._metadata_settings.instance_name, "INSTANCE")
        finally:
            os.unlink(path)

    def test_server_default_time_zone_invalid_returns_false(self):
        fd, path = tempfile.mkstemp(suffix=".config")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump({
                    "server_settings": {
                        "instance_name": "INSTANCE",
                        "default_time_zone": "_server_tz_"
                    }
                }, file)
            handler = _make_handler(path)
            with patch(
                "items.services.items_gateway.metadata_handler.tzlocal."
                "get_localzone_name", return_value="Not/A_Real_Zone"):
                result = handler.read_metadata_file()
            self.assertFalse(result)
        finally:
            os.unlink(path)

    def test_explicit_time_zone_valid(self):
        fd, path = tempfile.mkstemp(suffix=".config")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump({
                    "server_settings": {
                        "instance_name": "INSTANCE",
                        "default_time_zone": "Europe/Paris"
                    }
                }, file)
            handler = _make_handler(path)
            result = handler.read_metadata_file()
            self.assertTrue(result)
            self.assertFalse(handler._metadata_settings.using_server_default_time_zone)
            self.assertEqual(handler._metadata_settings.default_time_zone,
                             "Europe/Paris")
        finally:
            os.unlink(path)

    def test_explicit_time_zone_invalid_returns_false(self):
        fd, path = tempfile.mkstemp(suffix=".config")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump({
                    "server_settings": {
                        "instance_name": "INSTANCE",
                        "default_time_zone": "Not/A_Real_Zone"
                    }
                }, file)
            handler = _make_handler(path)
            self.assertFalse(handler.read_metadata_file())
        finally:
            os.unlink(path)


class TestWriteMetadataFile(unittest.TestCase):

    def test_write_success(self):
        fd, path = tempfile.mkstemp(suffix=".config")
        os.close(fd)
        try:
            handler = _make_handler(path)
            result = handler.write_metadata_file({"a": 1})
            self.assertTrue(result)
            with open(path, "r", encoding="utf-8") as file:
                self.assertEqual(json.load(file), {"a": 1})
        finally:
            os.unlink(path)

    def test_write_file_not_found(self):
        handler = _make_handler("/no/such/dir/file.config")
        with patch("builtins.open", side_effect=FileNotFoundError()):
            self.assertFalse(handler.write_metadata_file({"a": 1}))

    def test_write_permission_error(self):
        handler = _make_handler("/some/file.config")
        with patch("builtins.open", side_effect=PermissionError()):
            self.assertFalse(handler.write_metadata_file({"a": 1}))

    def test_write_os_error(self):
        handler = _make_handler("/some/file.config")
        with patch("builtins.open", side_effect=OSError("disk full")):
            self.assertFalse(handler.write_metadata_file({"a": 1}))


class TestBuildMetadataDictionary(unittest.TestCase):

    def test_build_metadata_dictionary(self):
        handler = _make_handler("unused.config")
        handler._metadata_settings.default_time_zone = "Europe/London"
        handler._metadata_settings.using_server_default_time_zone = True
        handler._metadata_settings.instance_name = "INSTANCE"

        result = handler.build_metadata_dictionary()

        self.assertEqual(result, {
            "default_time_zone": "Europe/London",
            "using_server_default_time_zone": True,
            "instance_name": "INSTANCE"
        })


if __name__ == "__main__":
    unittest.main()
