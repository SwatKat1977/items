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
import argparse
import asyncio
import logging
import os.path
import secrets
import string
from argon2 import PasswordHasher
import identity_sql
import sql_values
from weaver_framework.database.sqlite_interface import (
    SqliteInterface,
    SqliteInterfaceException)

LOGGING_DATETIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
LOGGING_DEFAULT_LOG_LEVEL = logging.DEBUG
LOGGING_LOG_FORMAT_STRING = "%(asctime)s [%(levelname)s] %(message)s"

DEFAULT_DB_FILENAME: str = "items_identity.db"
DEFAULT_FIXED_ADMIN_PASSWORD: str = "item_admin_2025"
DEFAULT_ADMIN_PASSWORD_LEN: int = 10


def generate_secure_password(length: int = DEFAULT_ADMIN_PASSWORD_LEN) -> str:
    """Generate a cryptographically secure random password.

    Args:
        length: Desired password length. Must be at least
            ``DEFAULT_ADMIN_PASSWORD_LEN`` characters.

    Returns:
        A randomly generated password string.

    Raises:
        ValueError: If the requested length is below the minimum.
    """
    if length < DEFAULT_ADMIN_PASSWORD_LEN:
        raise ValueError(f"Password length should be at least "
                         f"{DEFAULT_ADMIN_PASSWORD_LEN} characters.")
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


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
                         database: SqliteInterface,
                         admin_password: str) -> bool:
    """Create the identity tables and seed the default admin user.

    Args:
        logger:         Logger instance.
        database:       SqliteInterface connected to the target database.
        admin_password: Plaintext password to assign to the admin user.

    Returns:
        True if the database was built successfully, False otherwise.
    """
    try:
        logger.info("-> Creating user_profile table")
        await database.create_table(
            sql_values.SQL_CREATE_USER_PROFILE_TABLE, "user_profile")

        logger.info("-> Creating user_auth_details table")
        await database.create_table(
            sql_values.SQL_CREATE_USER_AUTH_DETAILS_TABLE, "user_auth_details")

        logger.info("-> Creating project_members table")
        await database.create_table(
            sql_values.SQL_CREATE_PROJECT_MEMBERS_TABLE, "project_members")

        logger.info("-> Creating project_permissions table")
        await database.create_table(
            sql_values.SQL_CREATE_PROJECT_PERMISSIONS_TABLE,
            "project_permissions")

        logger.info("-> Creating admin with password '%s'", admin_password)
        admin_profile_params: tuple = (
            sql_values.DEFAULT_ADMIN_USER.get('email_address'),
            sql_values.DEFAULT_ADMIN_USER.get('full_name'),
            sql_values.DEFAULT_ADMIN_USER.get('display_name'),
            sql_values.DEFAULT_ADMIN_USER.get('account_status'),
            sql_values.DEFAULT_ADMIN_USER.get('logon_type'),
            sql_values.DEFAULT_ADMIN_USER.get('is_administrator')
        )
        admin_user_id: int = await database.insert_query(
            identity_sql.SQL_ADD_USER_PROFILE, admin_profile_params)

        password_hash = PasswordHasher().hash(admin_password)
        await database.insert_query(identity_sql.SQL_ADD_USER_AUTH_DETAILS,
                                    (password_hash, admin_user_id))

        logger.info("Database build successful")

    except SqliteInterfaceException as interface_except:
        logger.critical("Database build failed: %s", str(interface_except))
        return False

    return True


async def async_main() -> None:
    """Async entry point for initializing and populating the identity database.

    Sets up logging, parses command-line arguments, and creates a new database
    file (if it does not already exist). Builds the schema and seeds the
    default admin user.

    Command-line Args:
        -d, --dbFile (str): Optional path to the database file. Defaults to
            ``items_identity.db`` in the current directory.
        -a, --adminPassword (str): Manual admin password.
        -r, --randomAdminPassword: Generate a random admin password.
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
    parser.add_argument("-a", "--adminPassword", type=str,
                        help="Manual admin password")
    parser.add_argument("-r", "--randomAdminPassword", action="store_true",
                        help="Random password")
    args = parser.parse_args()

    filename: str = args.dbFile if args.dbFile else DEFAULT_DB_FILENAME
    logger.info("Database file: %s", filename)

    admin_password: str = DEFAULT_FIXED_ADMIN_PASSWORD
    if args.randomAdminPassword:
        logger.info("Using random admin password...")
        admin_password = generate_secure_password()
    elif args.adminPassword:
        logger.info("Using user-defined admin password...")
        admin_password = args.adminPassword
    else:
        logger.info("Using default admin password...")

    db = open_db(logger, filename)
    if not db:
        return

    await build_database(logger, db, admin_password)


if __name__ == "__main__":
    asyncio.run(async_main())
