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
import logging
# import typing
from sql.extended_sql_interface import ExtendedSqlInterface
from state_object import StateObject
# import databases.cms_db_tables as cms_tables


class SqlTCCustomFields(ExtendedSqlInterface):
    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        super().__init__(logger, state_object)
