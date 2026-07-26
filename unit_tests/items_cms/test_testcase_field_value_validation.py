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
from items.services.items_cms.services.testcase_field_value_validation import (
    validate_value,
)


class TestValidateValue(unittest.TestCase):
    """Unit tests for validate_value."""

    # ------------------------------------------------------------------
    # Integer
    # ------------------------------------------------------------------

    def test_integer_accepts_valid_integer(self):
        self.assertIsNone(validate_value("Integer", "42"))

    def test_integer_accepts_negative_integer(self):
        self.assertIsNone(validate_value("Integer", "-7"))

    def test_integer_rejects_non_numeric(self):
        self.assertIsNotNone(validate_value("Integer", "abc"))

    def test_integer_rejects_decimal(self):
        self.assertIsNotNone(validate_value("Integer", "3.14"))

    # ------------------------------------------------------------------
    # Checkbox
    # ------------------------------------------------------------------

    def test_checkbox_accepts_true(self):
        self.assertIsNone(validate_value("Checkbox", "true"))

    def test_checkbox_accepts_false_case_insensitive(self):
        self.assertIsNone(validate_value("Checkbox", "False"))

    def test_checkbox_accepts_zero_and_one(self):
        self.assertIsNone(validate_value("Checkbox", "0"))
        self.assertIsNone(validate_value("Checkbox", "1"))

    def test_checkbox_rejects_other_values(self):
        self.assertIsNotNone(validate_value("Checkbox", "maybe"))

    # ------------------------------------------------------------------
    # Date
    # ------------------------------------------------------------------

    def test_date_accepts_iso_format(self):
        self.assertIsNone(validate_value("Date", "2026-07-25"))

    def test_date_rejects_invalid_format(self):
        self.assertIsNotNone(validate_value("Date", "25/07/2026"))

    def test_date_rejects_garbage(self):
        self.assertIsNotNone(validate_value("Date", "not-a-date"))

    # ------------------------------------------------------------------
    # Url (Link)
    # ------------------------------------------------------------------

    def test_url_accepts_https(self):
        self.assertIsNone(validate_value("Url (Link)", "https://example.com"))

    def test_url_accepts_http(self):
        self.assertIsNone(validate_value("Url (Link)", "http://example.com"))

    def test_url_rejects_missing_scheme(self):
        self.assertIsNotNone(validate_value("Url (Link)", "example.com"))

    def test_url_rejects_unsupported_scheme(self):
        self.assertIsNotNone(validate_value("Url (Link)", "ftp://example.com"))

    # ------------------------------------------------------------------
    # Types with no specific format
    # ------------------------------------------------------------------

    def test_dropdown_accepts_any_string(self):
        self.assertIsNone(validate_value("Dropdown", "anything"))

    def test_string_accepts_any_string(self):
        self.assertIsNone(validate_value("String", "anything"))

    def test_text_accepts_any_string(self):
        self.assertIsNone(validate_value("Text", "anything"))

    def test_user_accepts_any_string(self):
        self.assertIsNone(validate_value("User", "anything"))

    def test_unknown_type_accepts_any_string(self):
        self.assertIsNone(validate_value("SomeFutureType", "anything"))


if __name__ == "__main__":
    unittest.main()
