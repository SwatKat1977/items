import unittest
from test_configuration import TestConfiguration
from test_metadata_settings import TestMetadataSettings
from test_page_handler_injections import TestPageHandlerInjections
from test_authenticated_rest_client import TestAuthenticatedRestClient
from test_decorators import TestRequireSession
from test_portal_page_handler import (
    TestSessionAuthMixinGenerateRedirect,
    TestHasAuthCookies,
    TestValidateCookies,
    TestPortalPageHandlerRenderPage,
)
from test_service import (
    TestServiceManageConfiguration,
    TestServiceInitialise,
    TestServiceTasksAndShutdown,
    TestGetMetadata,
)
from test_accept_invite_page_handler import TestAcceptInvitePageHandler
from test_auth_handlers import (
    TestIndexPageHandler,
    TestLoginGetPageHandler,
    TestLoginPostPageHandler,
    TestLogoutPageHandler,
)
from test_route_factories import TestRouteWiring
from test_admin_stub_handlers import (
    TestAdminOverviewPageHandler,
    TestAdminIntegrationsPageHandler,
    TestAdminManageDataPageHandler,
    TestAdminSiteSettingsPageHandler,
)
from test_admin_customisations_page_handler import (
    TestCustomisationsRead,
    TestCaseFieldAdd,
    TestCaseFieldModify,
    TestCaseFieldDelete,
    TestCaseFieldMove,
    TestRowToField,
)
from test_admin_users_and_roles_page_handler import (
    TestUsersAndRolesRead,
    TestInviteUser,
    TestResendInvite,
    TestUninvite,
    TestUsersAndRolesReadRoles,
    TestRoleAdd,
    TestRoleModify,
    TestRoleDelete,
    TestParsePermissionsFromForm,
    TestFormatEpoch,
)
from test_admin_projects_handlers import (
    TestAdminProjectsPageHandlers,
    TestAdminAddProjectPageHandlers,
    TestAdminModifyProjectPageHandlers,
)
from test_admin_users_handlers import (
    TestAdminAddUserPageHandler,
    TestAdminModifyUserPageHandler,
    TestAdminResetPasswordPageHandler,
)
from test_projects_testcases_handlers import (
    TestGetProjectOverviewPageHandler,
    TestGetProjectTestcasesPageHandler,
)

if __name__ == "__main__":
    unittest.main()
