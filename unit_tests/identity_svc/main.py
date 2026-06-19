import unittest
from test_application import TestApplication
from test_threadsafe_configuration import TestIdentityConfiguration
from test_da_user_data_access_layer import TestUserRepository
from test_apis_authentication_api import TestAuthenticatePasswordHandler
from test_apis_health_api import TestHealthHandler
from test_services_authentication_service import TestAuthenticationService

if __name__ == "__main__":
    unittest.main()
