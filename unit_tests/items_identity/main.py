import unittest
from test_service import TestService
from test_threadsafe_configuration import TestIdentityConfiguration
from test_da_user_data_access_layer import TestUserRepository
from test_da_invite_data_access_layer import TestInviteRepository
from test_apis_authentication_api import TestAuthenticatePasswordHandler
from test_apis_health_api import TestHealthHandler
from test_services_authentication_service import TestAuthenticationService
from test_services_user_profile_service import TestUserProfileService
from test_services_user_management_service import TestUserManagementService
from test_services_invite_management_service import TestInviteManagementService
from test_apis_user_profile_api import TestGetUserProfileHandler
from test_apis_user_management import (
    TestListUsersHandler,
    TestGetUserHandler,
    TestCreateUserHandler,
    TestModifyUserHandler,
    TestResetPasswordHandler,
    TestChangePasswordHandler,
)
from test_apis_invite_management import (
    TestCreateInviteHandler,
    TestResendInviteHandler,
    TestUninviteHandler,
)
from test_create_routes import (TestCreateAuthRoutes, TestCreateSystemRoutes,
                                TestCreateInviteRoutes, TestCreateUsersRoutes,
                                TestCreateRoutes)

if __name__ == "__main__":
    unittest.main()
