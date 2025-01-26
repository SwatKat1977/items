"""
Copyright 2025 Integrated Test Management Suite Development Team

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
from account_logon_type import AccountLogonType
from account_status import AccountStatus

SQL_CREATE_USER_PROFILE_TABLE: str = """
    CREATE TABLE IF NOT EXISTS user_profile (
        id integer PRIMARY KEY,
        email_address text NOT NULL,
        full_name text NOT NULL,
        display_name text NOT NULL,
        insertion_date integer NOT NULL,
        account_status integer DEFAULT 0,
        logon_type integer DEFAULT 0 NOT NULL
    )
"""

DEFAULT_ADMIN_USER: dict = {
    'email_address': 'admin@localhost',
    'full_name': 'Local Admin',
    'display_name': 'Local Admin',
    'account_status': AccountStatus.ACTIVE.value,
    'logon_type': AccountLogonType.BASIC.value
}

SQL_CREATE_USER_AUTH_DETAILS_TABLE: str = """
    CREATE TABLE IF NOT EXISTS user_auth_details (
        id integer PRIMARY KEY,
        password text NOT NULL,
        password_salt text NOT NULL,
        user_id integer NOT NULL,

        FOREIGN KEY(user_id) REFERENCES user_profile(id)
    )
"""
