import unittest
from test_service import TestService
from test_threadsafe_configuration import TestIdentityConfiguration
from test_da_user_data_access_layer import TestUserRepository
from test_da_invite_data_access_layer import TestInviteRepository
from test_da_role_data_access_layer import TestRoleRepository
from test_apis_authentication_api import TestAuthenticatePasswordHandler
from test_apis_health_api import TestHealthHandler
from test_services_authentication_service import TestAuthenticationService
from test_services_user_profile_service import TestUserProfileService
from test_services_user_management_service import TestUserManagementService
from test_services_invite_management_service import TestInviteManagementService
from test_services_role_management_service import TestRoleManagementService
from test_apis_user_profile_api import TestGetUserProfileHandler
from test_apis_user_management import (
    TestListUsersHandler,
    TestGetUserHandler,
    TestCreateUserHandler,
    TestModifyUserHandler,
    TestResetPasswordHandler,
    TestChangePasswordHandler,
)
from test_apis_role_management import (
    TestListRolesHandler,
    TestGetRoleHandler,
    TestCreateRoleHandler,
    TestModifyRoleHandler,
    TestDeleteRoleHandler,
)
from test_apis_invite_management import (
    TestGetInvitesHandler,
    TestCreateInviteHandler,
    TestResendInviteHandler,
    TestUninviteHandler,
)
from test_invite_token_lookup import (
    TestGetInviteByTokenService,
    TestGetInviteByTokenHandler,
)
from test_create_routes import (TestCreateAuthRoutes, TestCreateSystemRoutes,
                                TestCreateInviteRoutes, TestCreateRolesRoutes,
                                TestCreateUsersRoutes, TestCreateRoutes)

if __name__ == "__main__":
    unittest.main()
