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
from base_sqlite_interface import BaseSqliteInterface, SqliteInterfaceException

LOGGING_DATETIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
LOGGING_DEFAULT_LOG_LEVEL = logging.DEBUG
LOGGING_LOG_FORMAT_STRING = "%(asctime)s [%(levelname)s] %(message)s"

# Default database file.
DEFAULT_DB_FILENAME: str = "items_cms_svc.db"


def open_db(logger: logging.Logger, filename: str) -> BaseSqliteInterface:
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

    except SqliteInterfaceException as interface_except:
        logger.critical("Unable to add add tables, reason: %s",
                        str(interface_except))
        return False

    return True


def main():
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


if __name__ == "__main__":
    main()
