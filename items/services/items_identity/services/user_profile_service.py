"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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
from dataclasses import dataclass, field
import logging
from typing import Optional
from weaver_framework.database.sqlite_interface import SqliteInterfaceException
from items.services.items_identity.data_access.user_repository import (
    UserRepository)
from items.shared.service_state import ServiceState


@dataclass
class UserProfileResult:
    """Outcome of a user profile lookup.

    Attributes:
        available: False when the service cannot serve the request at all
            (unavailable or degraded). ``profile`` is always None.
        found:     False when no user exists with the requested email
            address. ``profile`` is always None.
        profile:   The user's profile when the lookup succeeded.
    """
    available: bool = True
    found: bool = True
    profile: Optional[dict] = field(default=None)


class UserProfileService:
    """Read access to user profile details.

    Provides the profile information callers need in order to know who a user
    is and what they are permitted to do - in particular the
    ``is_administrator`` flag, which gates access to the administration
    pages.

    This is intentionally separate from authentication: authenticating a user
    and describing a user are different concerns, and keeping them apart means
    the authentication path is not disturbed when profile fields are added.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self,
                 logger: logging.Logger,
                 state: ServiceState,
                 user_repository: UserRepository) -> None:
        """Initialise the user profile service.

        Args:
            logger:          Parent logger used to create a service logger.
            state:           Shared service state used to determine
                availability and to record database degradation.
            user_repository: Repository providing user data access.
        """
        self._logger = logger.getChild(__name__)
        self._state: ServiceState = state
        self._user_repository: UserRepository = user_repository

    async def get_profile_by_email(self, email: str) -> UserProfileResult:
        """Retrieve a user's profile by email address.

        Args:
            email: Email address of the user to look up.

        Returns:
            A :class:`UserProfileResult` describing the outcome. Database
            failures mark the service as degraded and are reported as
            unavailable rather than as "not found", so callers do not mistake
            an outage for a missing account.
        """
        if not self._state.is_available():
            return UserProfileResult(available=False)

        try:
            row = await self._user_repository.get_user_profile_by_email(email)

        except SqliteInterfaceException as ex:
            self._logger.exception(
                "Database failure retrieving user profile: %s", str(ex))
            self._state.set_service_degraded(
                "User profile database unavailable")
            return UserProfileResult(available=False)

        if row is None:
            return UserProfileResult(found=False)

        (user_id, email_address, full_name, display_name, account_status,
         logon_type, is_administrator) = row

        return UserProfileResult(profile={
            "id": user_id,
            "email_address": email_address,
            "full_name": full_name,
            "display_name": display_name,
            "account_status": account_status,
            "logon_type": logon_type,
            # Exposed as a JSON boolean rather than the stored 0/1 so callers
            # do not have to know the storage representation.
            "is_administrator": bool(is_administrator),
        })
