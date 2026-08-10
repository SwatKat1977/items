import unittest
from test_gateway_configuration import TestGatewayConfiguration
from test_sessions import TestSessions
from test_route_injections import TestRouteInjections
from test_web_portal_client import TestWebPortalClient
from test_metadata_handler import (
    TestReadMetadataFile,
    TestWriteMetadataFile,
    TestBuildMetadataDictionary,
)
from test_service import (
    TestServiceManageConfiguration,
    TestServiceInitialise,
    TestServiceTasksAndShutdown,
    TestIdentitySvcHealthCheck,
    TestCmsSvcHealthCheck,
)
from test_sessions_handlers import (
    TestNewSessionPasswordHandler,
    TestDeleteSessionHandler,
    TestRefreshSessionHandler,
    TestValidateSessionHandler,
)
from test_route_factories import TestRouteWiring
from test_projects_handlers import (
    TestAddProjectHandler,
    TestDeleteProjectHandler,
    TestGetAllProjectsHandler,
    TestGetProjectHandler,
    TestUpdateProjectHandler,
)
from test_testcases_handlers import (
    TestGetTestcaseHandler,
    TestGetTestcasesHandler,
)
from test_testcase_custom_fields_handlers import (
    TestGetAllCustomFieldsHandler,
    TestGetCustomFieldHandler,
    TestAddCustomFieldHandler,
    TestDeleteCustomFieldHandler,
    TestModifyCustomFieldHandler,
    TestMoveCustomFieldHandler,
)
from test_users_handlers import (
    TestListUsersHandler,
    TestGetUserHandler,
    TestCreateUserHandler,
    TestModifyUserHandler,
    TestResetPasswordHandler,
    TestResetPasswordHandlerEmail,
)
from test_invites_handlers import (
    TestGetInvitesHandler,
    TestCreateInviteHandler,
    TestResendInviteHandler,
    TestUninviteHandler,
)
from test_email_service import (
    TestEmailServiceAbstract,
    TestSmtpEmailServiceInit,
    TestSmtpEmailServiceSend,
)
from test_webhook_handler import TestGetMetadataHandler

if __name__ == "__main__":
    unittest.main()
