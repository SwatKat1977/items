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

SQL_ADD_USER_PROFILE: str = ("INSERT INTO user_profile (email_address, "
                             "full_name, display_name, insertion_date, "
                             "account_status, logon_type) "
                             "VALUES(?, ?, ?, 0, ?, ?)")

SQL_ADD_USER_AUTH_DETAILS: str = ("INSERT INTO user_auth_details (password,"
                                  "password_salt, user_id) VALUES(?, ?, ?)")
