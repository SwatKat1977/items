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
from items_common.service_state import ServiceState
from sql.extended_sql_interface import ExtendedSqlInterface
from sql.sql_projects import SqlProjects
from sql.sql_tc_custom_fields import SqlTCCustomFields
from sql.sql_testcases import SqlTestcases


class SqlInterface(ExtendedSqlInterface):
    def __init__(self, logger: logging.Logger,
                 state_object: ServiceState) -> None:
        super().__init__(logger, state_object)

        self.projects: SqlProjects = SqlProjects(logger, state_object, self)
        self.tc_custom_fields: SqlTCCustomFields = SqlTCCustomFields(
            logger, state_object, self)
        self.testcases: SqlTestcases = SqlTestcases(logger, state_object, self)
