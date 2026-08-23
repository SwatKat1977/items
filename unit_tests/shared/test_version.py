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
from items.shared import _build_version_string


class TestBuildVersionString(unittest.TestCase):

    def test_no_pre_release(self):
        self.assertEqual(_build_version_string(0, 3, 0, None), "V0.3.0")

    def test_empty_string_pre_release_is_treated_as_none(self):
        self.assertEqual(_build_version_string(0, 3, 0, ""), "V0.3.0")

    def test_with_pre_release(self):
        self.assertEqual(
            _build_version_string(0, 3, 0, "Alpha Build 13"),
            "V0.3.0-Alpha Build 13")

    def test_different_major_minor_patch(self):
        self.assertEqual(_build_version_string(1, 2, 3, None), "V1.2.3")


if __name__ == "__main__":
    unittest.main()
