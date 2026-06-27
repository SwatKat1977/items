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


if __name__ == "__main__":
    unittest.main()
