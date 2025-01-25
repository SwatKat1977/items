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
import secrets
import string
import sql_values

LOGGING_DATETIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
LOGGING_DEFAULT_LOG_LEVEL = logging.DEBUG
LOGGING_LOG_FORMAT_STRING = "%(asctime)s [%(levelname)s] %(message)s"

# Default database file.
DEFAULT_DB_FILENAME: str = "items_accounts_svc.db"

# Default admin password
DEFAULT_FIXED_ADMIN_PASSWORD: str = "item_admin_2025"

# Default random password length
DEFAULT_ADMIN_PASSWORD_LEN: int = 10


def generate_secure_password(length: int = DEFAULT_ADMIN_PASSWORD_LEN) -> str:
    """
    Generate a secure random password.

    Returns:
        str: The generated secure password.
    """
    if length < DEFAULT_ADMIN_PASSWORD_LEN:  # Enforce a minimum length for security
        raise ValueError("Password length should be at least " +
                         f"{DEFAULT_ADMIN_PASSWORD_LEN} characters.")

    # Define the character pool: letters, digits, and special characters
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Generate a password by randomly selecting from the pool
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


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
    parser.add_argument("-a",
                        "--adminPassword",
                        type=str,
                        help="Manual admin password")
    parser.add_argument("-r",
                        "--randomAdminPassword",
                        action="store_true",
                        help="Random password")

    # Parse the arguments
    args = parser.parse_args()

    filename: str = DEFAULT_DB_FILENAME if not args.dbFile \
        else args.dbFile
    logger.info("Database file: %s", filename)

    admin_password: str = DEFAULT_FIXED_ADMIN_PASSWORD
    if args.randomAdminPassword:
        logger.info("Using random admin password...")
        admin_password = generate_secure_password()
    else:
        if args.adminPassword:
            admin_password = args.adminPassword
    logger.info("Admin password: %s", admin_password)


if __name__ == "__main__":
    main()
