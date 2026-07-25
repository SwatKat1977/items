import unittest
from test_cms_configuration import TestCMSConfiguration
from test_health_handler import TestApiHealthApiView
from test_project_handlers import (
    TestGetProjectHandler,
    TestListProjectsHandler,
    TestCreateProjectHandler,
    TestModifyProjectHandler,
    TestDeleteProjectHandler,
)
from test_project_service import TestProjectService
from test_folder_handlers import (
    TestGetFolderHandler,
    TestListFoldersHandler,
    TestAddFolderHandler,
    TestModifyFolderHandler,
    TestDeleteFolderHandler,
)
from test_folder_service import TestFolderService
from test_folder_repository import TestFolderRepository
from test_testcase_handlers import (
    TestGetTestcaseHandler,
    TestListTestcasesHandler,
)
from test_testcase_custom_field_handlers import (
    TestGetCustomFieldHandler,
    TestGetCustomFieldsHandler,
    TestAddCustomFieldHandler,
    TestDeleteCustomFieldHandler,
    TestMoveCustomFieldHandler,
    TestUpdateCustomFieldHandler,
)
from test_testcase_service import TestTestcaseService
from test_testcase_custom_fields_service import (
    TestTestcaseCustomFieldsService,
)
from test_testcase_custom_fields_repository import (
    TestTestcaseCustomFieldsRepository,
)
from test_project_repository import TestProjectRepository
from test_testcase_repository import TestTestcaseRepository
from test_route_factories import TestRouteWiring
from test_service import (
    TestServiceManageConfiguration,
    TestServiceInitialise,
    TestServiceTasks,
)


if __name__ == "__main__":
    unittest.main()
