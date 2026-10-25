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

# What a person is told when their role does not let them do something with
# test cases or sections. Kept together so the wording is the same wherever
# the refusal is shown, and says plainly what they tried to do.

# Shown instead of a page the person's role cannot read.
NO_ACCESS_TO_TEST_CASES: str = (
    "You don't have permission to view the test cases in this project.")

# Shown when the gateway refuses a write because the person's role does not
# allow it (a 403 for someone who is on the project). Keyed by the action.
REFUSED: dict[str, str] = {
    "add_test_case":
        "You don't have permission to add test cases in this project.",
    "edit_test_case":
        "You don't have permission to edit test cases in this project.",
    "move_test_case":
        "You don't have permission to move test cases in this project.",
    "delete_test_case":
        "You don't have permission to delete test cases in this project.",
    "add_section":
        "You don't have permission to add sections in this project.",
    "rename_section":
        "You don't have permission to rename sections in this project.",
    "move_section":
        "You don't have permission to move sections in this project.",
    "delete_section":
        "You don't have permission to delete sections in this project.",
}
