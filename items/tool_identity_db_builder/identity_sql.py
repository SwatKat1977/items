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

SQL_ADD_USER_PROFILE: str = ("INSERT INTO user_profile (uuid, email_address, "
                             "full_name, display_name, insertion_date, "
                             "account_status, logon_type, is_administrator) "
                             "VALUES(?, ?, ?, ?, 0, ?, ?, ?)")

SQL_ADD_USER_AUTH_DETAILS: str = ("INSERT INTO user_auth_details (password, "
                                  "user_id) VALUES(?, ?)")

SQL_ADD_USER_INVITE: str = ("INSERT INTO user_invite (token, email_address, "
                            "created_at, expires_at) "
                            "VALUES(?, ?, ?, ?)")

SQL_GET_INVITE_BY_TOKEN: str = ("SELECT id, token, email_address, created_at, "
                                "expires_at, is_expired, expired_at "
                                "FROM user_invite WHERE token = ?")

SQL_GET_INVITE_BY_EMAIL: str = ("SELECT id, token, email_address, created_at, "
                                "expires_at, is_expired, expired_at "
                                "FROM user_invite "
                                "WHERE email_address = ? AND is_expired = 0")

SQL_RESEND_INVITE: str = ("UPDATE user_invite SET token = ?, expires_at = ? "
                          "WHERE email_address = ? AND is_expired = 0")

SQL_SOFT_EXPIRE_INVITE_BY_EMAIL: str = ("UPDATE user_invite "
                                        "SET is_expired = 1, expired_at = ? "
                                        "WHERE email_address = ? "
                                        "AND is_expired = 0")

SQL_SOFT_EXPIRE_PENDING_INVITES: str = ("UPDATE user_invite "
                                        "SET is_expired = 1, expired_at = ? "
                                        "WHERE is_expired = 0 "
                                        "AND expires_at < ?")
