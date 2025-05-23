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
import logging
import os.path
import sql_values
import db_static_values
from base_sqlite_interface import BaseSqliteInterface, SqliteInterfaceException

LOGGING_DATETIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
LOGGING_DEFAULT_LOG_LEVEL = logging.DEBUG
LOGGING_LOG_FORMAT_STRING = "%(asctime)s [%(levelname)s] %(message)s"

# Default database file.
DEFAULT_DB_FILENAME: str = "items_cms_svc.db"


def open_db(logger: logging.Logger, filename: str) -> BaseSqliteInterface:
    """Opens a new SQLite database if it does not already exist.

    Logs the process of opening the database. If the file already exists,
    logs a critical message and returns None. If an error occurs while
    creating the database, logs the exception and also returns None.

    Args:
        logger (logging.Logger): Logger instance for logging messages.
        filename (str): Path to the database file to be created.

    Returns:
        BaseSqliteInterface: A database interface instance if successful.
        None: If the file already exists or an error occurs.
    """

    logger.info("Opening database...")

    if os.path.exists(filename):
        logger.critical("Database '%s' already exists!", filename)
        return None

    db = BaseSqliteInterface(filename)

    try:
        db.open(create_mode=True)

    except SqliteInterfaceException as ex:
        logger.critical(ex)
        db = None

    else:
        logger.info("Database '%s' opened successful", filename)

    return db


def add_static_values_field_types(logger: logging.Logger,
                                  database: BaseSqliteInterface) -> bool:
    """Populates the custom_field_types table with predefined static values.

    Inserts static field type ID-name pairs into the `custom_field_types` table.
    Logs the process and handles any exceptions that occur during insertion.

    Args:
        logger (logging.Logger): Logger instance used for logging messages.
        database (BaseSqliteInterface): Database interface used to execute the insert queries.

    Returns:
        bool: True if all values were inserted successfully; False if an error occurred.
    """

    logger.info("-> Populating custom field type static values")

    query: str = "INSERT INTO custom_field_types(id, name) VALUES(?,?)"

    try:
        for field_id, field_name in db_static_values.STATIC_VALUES_FIELD_TYPES:
            database.insert_query(query, (int(field_id), field_name))

    except SqliteInterfaceException as interface_except:
        logger.critical("Unable to add custom field type static value, reason: %s",
                        str(interface_except))
        return False

    return True


def add_static_values_system_test_case_fields(logger: logging.Logger,
                                              database: BaseSqliteInterface) -> bool:
    """Populates the test_case_custom_fields table with predefined system fields.

    Inserts predefined static values representing system test case fields into
    the `test_case_custom_fields` table. Each record includes metadata such as
    field name, system name, field type, entry type, and display position.

    Logs the process and handles any exceptions that occur during insertion.

    Args:
        logger (logging.Logger): Logger instance used to log messages.
        database (BaseSqliteInterface): Database interface used to execute the insert queries.

    Returns:
        bool: True if all values were inserted successfully; False if an error occurred.
    """

    logger.info("-> Populating system testcase custom fields")

    # (id, field_mame, system_name, field_type_id, entry_type, enabled, position)
    query: str = ("INSERT INTO test_case_custom_fields(id, field_name, "
                  "system_name, field_type_id, entry_type, enabled, position) "
                  "VALUES(?,?,?,?,?,?,?)")

    try:
        for field_id, field_mame, system_name, field_type_id, entry_type, \
                enabled, position in db_static_values.STATIC_VALUES_SYSTEM_FIELDS:

            values = (field_id, field_mame, system_name, field_type_id, entry_type,
                      enabled, position)
            database.insert_query(query, values)

    except SqliteInterfaceException as interface_except:
        logger.critical("Unable to add system test case fields, reason: %s",
                        str(interface_except))
        return False

    return True


def build_database(logger: logging.Logger,
                   database: BaseSqliteInterface) -> bool:
    """
    Build a new, empty database ready for use.
    """

    try:
        logger.info("-> Creating projects table")
        database.create_table(sql_values.SQL_CREATE_PROJECTS_TABLE,
                              "projects")

        logger.info("-> Creating test_case_folders table")
        database.create_table(sql_values.SQL_CREATE_TEST_CASE_FOLDERS_TABLE,
                              "test_case_folders")

        logger.info("-> Creating test_case_folders table")
        database.create_table(sql_values.SQL_CREATE_TEST_CASES_TABLE,
                              "test_cases")

        logger.info("-> Creating custom_field_type table")
        database.create_table(sql_values.SQL_CREATE_CUSTOM_FIELD_TYPES_TABLE,
                              "custom_field_type")

        logger.info("-> Creating test_case_custom_fields table")
        database.create_table(sql_values.SQL_CREATE_TEST_CASE_CUSTOM_FIELDS_TABLE,
                              "test_case_custom_fields")

        logger.info("-> Creating test_case_custom_field_projects table")
        database.create_table(sql_values.SQL_CREATE_TEST_CASE_CUSTOM_FIELD_PROJECTS_TABLE,
                              "test_case_custom_field_projects")

        logger.info("-> Creating test_case_custom_field_type_option_values table")
        database.create_table(sql_values.SQL_CREATE_TEST_CASE_CUSTOM_FIELD_TYPE_OPTION_VALUES_TABLE,
                              "test_case_custom_field_type_option_values")

    except SqliteInterfaceException as interface_except:
        logger.critical("Unable to add add tables, reason: %s",
                        str(interface_except))
        return False

    return True


def main():
    """Main entry point for initializing and populating the SQLite database.

    Sets up logging, parses command-line arguments, and creates a new database
    file (if it does not already exist). If successful, it proceeds to build the
    database schema and insert predefined static values for field types and
    system test case fields.

    Command-line Args:
        -d, --dbFile (str): Optional path to the database file. If not provided,
        a default filename is used.

    Returns:
        None
    """
    logger: logging.Logger = logging.getLogger(__name__)

    log_format: logging.Formatter =(
        logging.Formatter(LOGGING_LOG_FORMAT_STRING,
                          LOGGING_DATETIME_FORMAT_STRING))
    console_stream: logging.StreamHandler = logging.StreamHandler()
    console_stream.setFormatter(log_format)
    logger.setLevel(LOGGING_DEFAULT_LOG_LEVEL)
    logger.addHandler(console_stream)

    # Build arguments parser.
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("-d",
                        "--dbFile",
                        type=str, help="Database filename")

    # Parse the arguments
    args = parser.parse_args()

    filename: str = DEFAULT_DB_FILENAME if not args.dbFile \
        else args.dbFile
    logger.info("Database file: %s", filename)

    db: BaseSqliteInterface = open_db(logger, filename)
    if not db:
        return

    build_database(logger, db)

    if not add_static_values_field_types(logger, db):
        return

    if not add_static_values_system_test_case_fields(logger, db):
        return


if __name__ == "__main__":
    main()
