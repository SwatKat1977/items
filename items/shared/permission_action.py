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
from enum import Enum


class PermissionAction(Enum):
    """The three things a role's grid can grant within an area.

    Matches the columns of the grid in §4 of user_roles_design.md (Read,
    Add/Modify, Delete). The values are the keys of each area's entry in the
    Identity service's effective-permissions response (§9.5), so an action
    can be looked up there directly.

    A typo in a permission check should be an error at import time, not a
    missing key at request time, which is why the Gateway's permission
    decorator takes this enum rather than a bare string.
    """

    READ = "read"
    ADD_MODIFY = "add_modify"
    DELETE = "delete"
