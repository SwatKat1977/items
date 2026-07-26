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
from datetime import date
from typing import Optional
from urllib.parse import urlparse

_CHECKBOX_VALUES = {"true", "false", "1", "0"}


def _validate_integer(value: str) -> Optional[str]:
    try:
        int(value)
    except ValueError:
        return "Value must be an integer"
    return None


def _validate_checkbox(value: str) -> Optional[str]:
    if value.lower() not in _CHECKBOX_VALUES:
        return "Value must be a boolean (true/false)"
    return None


def _validate_date(value: str) -> Optional[str]:
    try:
        date.fromisoformat(value)
    except ValueError:
        return "Value must be a date in YYYY-MM-DD format"
    return None


def _validate_url(value: str) -> Optional[str]:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "Value must be a valid http(s) URL"
    return None


_VALIDATORS = {
    "Integer": _validate_integer,
    "Checkbox": _validate_checkbox,
    "Date": _validate_date,
    "Url (Link)": _validate_url,
}


def validate_value(field_type: str, value: str) -> Optional[str]:
    """Validate a custom field value string against its field type.

    Types with a well-defined, unambiguous format (Integer, Checkbox, Date,
    Url (Link)) are checked accordingly. All other types (Dropdown, String,
    Text, User) accept any string — Dropdown in particular has no way to
    define its valid choices yet (the option-kind tables exist in the
    schema but nothing currently populates them), so it cannot be
    meaningfully validated beyond presence, which callers handle separately
    via each field's ``is_required`` flag.

    Args:
        field_type: Name of the field's type (e.g. "Integer", "Dropdown").
        value:      Value string to validate.

    Returns:
        A human-readable error message if the value is invalid for the
        given type, or None if it is valid (or the type has no specific
        format to check).
    """
    validator = _VALIDATORS.get(field_type)
    if validator is None:
        return None
    return validator(value)
