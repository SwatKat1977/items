import logging
import typing
import bcrypt
from items_common.safe_sqlite_interface import SafeSqliteInterface
from items_common.service_state import ServiceState
from account_status import AccountStatus
from threadsafe_configuration import ThreadSafeConfiguration as Configuration


class UserDataAccessLayer:
    """
    Handles direct database interactions for user authentication operations.
    """

    def __init__(self, state: ServiceState, logger: logging.Logger):
        self._db = SafeSqliteInterface(logger,
                                       state,
                                       Configuration().backend_db_filename)
        self._logger = logger.getChild(__name__)

    def get_user_for_logon(self,
                           email: str,
                           logon_type: int) \
            -> typing.Tuple[typing.Optional[int], str]:
        """Retrieve the user ID for a given email/logon type combination."""
        error_str: str = ""

        query: str = ("SELECT id, logon_type, account_status "
                      "FROM user_profile "
                      "WHERE email_address = ?")

        row = self._db.safe_query(query, (email,),
                                  "Query failed for basic user auth",
                                  logging.CRITICAL,
                                  fetch_one=True)

        if row is None:
            return None, "Internal error"

        if not row:
            return 0, "Username/password don't match"

        user_id, account_logon_type, account_status = row

        if account_logon_type != logon_type:
            return 0, "Incorrect logon type"

        if account_status != AccountStatus.ACTIVE.value:
            return 0, "Account is not active"

        return user_id, error_str

    def authenticate_basic_user(self,
                                user_id: int,
                                password: str) -> typing.Tuple[bool, str]:
        """
        Authenticate a user using basic authentication (email address and a
        password.

        parameters:
            user_id - User's unique id\n
            password - Password to authenticate

        returns:
            tuple : (status, error string)
        """
        return_status: bool = False
        return_status_str: str = ""

        query: str = ("SELECT password FROM user_auth_details "
                      "WHERE user_id = ?")

        row = self._db.safe_query(query, (user_id,),
                                  "Query failed for basic user auth",
                                  logging.CRITICAL,
                                  fetch_one=True)

        if row is None:
            return False, "Internal error"

        if not row:
            return False, 'Invalid user id'

        stored_password = row[0]

        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            return_status = True

        else:
            return_status = False
            return_status_str = "Username/password don't match"

        return return_status, return_status_str
