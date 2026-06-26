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
import argparse
import asyncio
import logging
import os.path
import sql_values
import db_static_values
import db_tables_test_cases as tables_test_cases
from weaver_framework.database.sqlite_interface import (
    SqliteInterface,
    SqliteInterfaceException,
)
from items.services.items_cms import cms_db_tables

LOGGING_DATETIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
LOGGING_DEFAULT_LOG_LEVEL = logging.DEBUG
LOGGING_LOG_FORMAT_STRING = "%(asctime)s [%(levelname)s] %(message)s"

# Default database file.
DEFAULT_DB_FILENAME: str = "items_cms_svc.db"


def open_db(logger: logging.Logger, filename: str) -> SqliteInterface | None:
    """Create a SqliteInterface for a new database file.

    Args:
        logger:   Logger instance for logging messages.
        filename: Path to the database file to be created.

    Returns:
        A SqliteInterface instance, or None if the file already exists.
    """
    logger.info("Opening database...")

    if os.path.exists(filename):
        logger.critical("Database '%s' already exists!", filename)
        return None

    db = SqliteInterface(logger, filename)
    logger.info("Database '%s' opened successfully", filename)
    return db


async def build_database(logger: logging.Logger,
                         database: SqliteInterface) -> bool:
    """Create all tables in the new database.

    Args:
        logger:   Logger instance.
        database: SqliteInterface connected to the target database.

    Returns:
        True if all tables were created successfully, False otherwise.
    """
    tables = [
        (cms_db_tables.PRJ_PROJECTS,
         sql_values.TABLE_SQL_PRJ_PROJECTS),
        (cms_db_tables.TC_FOLDERS,
         tables_test_cases.TABLE_SQL_TC_FOLDERS),
        (cms_db_tables.TC_TEST_CASES,
         tables_test_cases.TABLE_SQL_TC_TEST_CASES),
        (cms_db_tables.TC_CUSTOM_FIELD_TYPES,
         tables_test_cases.TABLE_SQL_TC_CUSTOM_FIELD_TYPES),
        (cms_db_tables.TC_CUSTOM_FIELDS,
         tables_test_cases.TABLE_SQL_TC_CUSTOM_FIELDS),
        (cms_db_tables.TC_CUSTOM_FIELD_OPTION_KINDS,
         tables_test_cases.TABLE_SQL_TC_CUSTOM_FIELD_OPTION_KINDS),
        (cms_db_tables.TC_CUSTOM_FIELD_OPTION_KIND_VALUES,
         tables_test_cases.TABLE_SQL_TC_CUSTOM_FIELD_OPTION_KIND_VALUES),
        (cms_db_tables.TC_CUSTOM_FIELD_TYPE_OPTIONS,
         tables_test_cases.TABLE_SQL_TC_CUSTOM_FIELD_TYPE_OPTIONS),
        (cms_db_tables.TC_CUSTOM_FIELD_PROJECTS,
         tables_test_cases.TABLE_SQL_TC_CUSTOM_FIELD_PROJECTS),
        (cms_db_tables.TC_CUSTOM_FIELD_TYPE_OPTION_VALUES,
         tables_test_cases.TABLE_SQL_TC_CUSTOM_FIELD_TYPE_OPTION_VALUES),
        (cms_db_tables.TC_CUSTOM_FIELD_OPTION_VALUES,
         tables_test_cases.TABLE_SQL_TC_CUSTOM_FIELD_OPTION_VALUES),
    ]

    try:
        for table_name, create_sql in tables:
            logger.info("-> Creating '%s' table", table_name)
            await database.create_table(create_sql, table_name)
    except SqliteInterfaceException as ex:
        logger.critical("Unable to create tables: %s", ex)
        return False

    return True


async def add_static_td_values_field_types(logger: logging.Logger,
                                           database: SqliteInterface) -> bool:
    """Populate the custom field types table with predefined static values.

    Args:
        logger:   Logger instance.
        database: SqliteInterface connected to the target database.

    Returns:
        True if all rows were inserted successfully, False otherwise.
    """
    logger.info("-> Populating test cases 'custom field type' static values")

    query: str = (f"INSERT INTO {cms_db_tables.TC_CUSTOM_FIELD_TYPES}(id, name, "
                  "supports_default_value, supports_is_required) "
                  "VALUES(?,?,?,?)")

    try:
        for field_id, field_name, default_value, is_required \
                in db_static_values.STATIC_VALUES_FIELD_TYPES:
            await database.insert_query(query,
                                        (int(field_id),
                                         field_name,
                                         default_value,
                                         is_required))
    except SqliteInterfaceException as ex:
        logger.critical("Unable to add custom field type static value: %s", ex)
        return False

    return True


async def add_static_values_system_test_case_fields(
        logger: logging.Logger,
        database: SqliteInterface) -> bool:
    """Populate the custom fields table with predefined system fields.

    Args:
        logger:   Logger instance.
        database: SqliteInterface connected to the target database.

    Returns:
        True if all rows were inserted successfully, False otherwise.
    """
    logger.info("-> Populating system testcase custom fields")

    query: str = (f"INSERT INTO {cms_db_tables.TC_CUSTOM_FIELDS}(id, field_name, "
                  "system_name, field_type_id, entry_type, enabled, position, "
                  "applies_to_all_projects) VALUES(?,?,?,?,?,?,?,?)")

    try:
        for field_id, field_name, system_name, field_type_id, entry_type, \
                enabled, position in db_static_values.STATIC_VALUES_SYSTEM_FIELDS:
            await database.insert_query(
                query,
                (field_id, field_name, system_name, field_type_id,
                 entry_type, enabled, position, True))
    except SqliteInterfaceException as ex:
        logger.critical("Unable to add system test case fields: %s", ex)
        return False

    return True


async def add_static_values_test_case_custom_field_option_kinds(
        logger: logging.Logger,
        database: SqliteInterface) -> bool:
    """Populate the custom field option kinds table with predefined values.

    Args:
        logger:   Logger instance.
        database: SqliteInterface connected to the target database.

    Returns:
        True if all rows were inserted successfully, False otherwise.
    """
    logger.info("-> Populating test case custom field option kinds")

    query: str = (f"INSERT INTO {cms_db_tables.TC_CUSTOM_FIELD_OPTION_KINDS}(id, "
                  "option_name) VALUES(?,?)")

    try:
        for kind_id, option_name in \
                db_static_values.STATIC_VALUES_TEST_CASE_CUSTOM_FIELD_OPTION_KINDS:
            await database.insert_query(query, (kind_id, option_name))
    except SqliteInterfaceException as ex:
        logger.critical("Unable to add custom field option kinds: %s", ex)
        return False

    return True


async def add_static_values_test_case_custom_field_option_kind_values(
        logger: logging.Logger,
        database: SqliteInterface) -> bool:
    """Populate the custom field option kind values table with predefined values.

    Args:
        logger:   Logger instance.
        database: SqliteInterface connected to the target database.

    Returns:
        True if all rows were inserted successfully, False otherwise.
    """
    logger.info("-> Populating test case custom field option kind values")

    query: str = (f"INSERT INTO {cms_db_tables.TC_CUSTOM_FIELD_OPTION_KIND_VALUES}("
                  "id, kind_id, value) VALUES(?,?,?)")

    try:
        for option_value_id, kind_id, option_value in \
                db_static_values.STATIC_VALUES_TEST_CASE_CUSTOM_FIELD_OPTION_VALUES:
            await database.insert_query(
                query, (option_value_id, kind_id, option_value))
    except SqliteInterfaceException as ex:
        logger.critical("Unable to add custom field option kind values: %s", ex)
        return False

    return True


async def async_main() -> None:
    """Async entry point for initializing and populating the SQLite database.

    Sets up logging, parses command-line arguments, and creates a new database
    file (if it does not already exist). Builds the schema then inserts all
    predefined static values.

    Command-line Args:
        -d, --dbFile (str): Optional path to the database file. Defaults to
        ``items_cms_svc.db`` in the current directory.
    """
    logger: logging.Logger = logging.getLogger(__name__)

    log_format = logging.Formatter(LOGGING_LOG_FORMAT_STRING,
                                   LOGGING_DATETIME_FORMAT_STRING)
    console_stream = logging.StreamHandler()
    console_stream.setFormatter(log_format)
    logger.setLevel(LOGGING_DEFAULT_LOG_LEVEL)
    logger.addHandler(console_stream)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dbFile", type=str, help="Database filename")
    args = parser.parse_args()

    filename: str = DEFAULT_DB_FILENAME if not args.dbFile else args.dbFile
    logger.info("Database file: %s", filename)

    db = open_db(logger, filename)
    if not db:
        return

    if not await build_database(logger, db):
        return

    if not await add_static_td_values_field_types(logger, db):
        return

    if not await add_static_values_system_test_case_fields(logger, db):
        return

    if not await add_static_values_test_case_custom_field_option_kinds(logger, db):
        return

    if not await add_static_values_test_case_custom_field_option_kind_values(logger, db):
        return

    logger.info("Database build complete.")


if __name__ == "__main__":
    asyncio.run(async_main())
