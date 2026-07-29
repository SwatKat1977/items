"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
from items.shared.account_status import AccountStatus
from items.shared.account_logon_type import AccountLogonType

SQL_CREATE_USER_PROFILE_TABLE: str = """
    CREATE TABLE IF NOT EXISTS user_profile (
        id integer PRIMARY KEY,
        email_address text NOT NULL,
        full_name text NOT NULL,
        display_name text NOT NULL,
        insertion_date integer NOT NULL,
        account_status integer DEFAULT 0,
        logon_type integer DEFAULT 0 NOT NULL,
        is_administrator integer DEFAULT 0 NOT NULL
    )
"""

SQL_CREATE_USER_AUTH_DETAILS_TABLE: str = """
    CREATE TABLE IF NOT EXISTS user_auth_details (
        id integer PRIMARY KEY,
        password text NOT NULL,
        user_id integer NOT NULL,

        FOREIGN KEY(user_id) REFERENCES user_profile(id)
    )
"""

SQL_CREATE_PROJECT_MEMBERS_TABLE: str = """
    CREATE TABLE IF NOT EXISTS project_members (
        id             integer PRIMARY KEY AUTOINCREMENT,
        principal_type text    NOT NULL CHECK (principal_type IN ('user', 'group')),
        principal_id   integer NOT NULL,
        project_id     integer NOT NULL,
        UNIQUE (principal_type, principal_id, project_id)
    )
"""

SQL_CREATE_PROJECT_PERMISSIONS_TABLE: str = """
    CREATE TABLE IF NOT EXISTS project_permissions (
        member_id      integer NOT NULL,
        area           text    NOT NULL,
        can_read       integer NOT NULL DEFAULT 0,
        can_add_modify integer NOT NULL DEFAULT 0,
        can_delete     integer NOT NULL DEFAULT 0,

        PRIMARY KEY (member_id, area),
        FOREIGN KEY (member_id) REFERENCES project_members(id) ON DELETE CASCADE,

        -- Invariant: add/modify always implies read (§4.1 of user_roles_design.md)
        CHECK (can_add_modify = 0 OR can_read = 1)
    )
"""

DEFAULT_ADMIN_USER: dict = {
    'email_address': 'admin@localhost',
    'full_name': 'Local Admin',
    'display_name': 'Local Admin',
    'account_status': AccountStatus.ACTIVE.value,
    'logon_type': AccountLogonType.BASIC.value,
    # A fresh install must have exactly one administrator, otherwise nobody
    # can reach the admin pages to grant the flag to anyone else.
    'is_administrator': 1
}
