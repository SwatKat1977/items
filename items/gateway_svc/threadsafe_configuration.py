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
from configuration.configuration_manager import ConfigurationManager
from configuration_layout import ConfigurationConstants as Constants
from thread_safe_singleton import ThreadSafeSingleton


class ThreadSafeConfiguration(ConfigurationManager,
                              metaclass=ThreadSafeSingleton):
    """ Thread-safe singleton for the config """

    @property
    def logging_log_level(self) -> str:
        """ Configuration property : Logging | log level """
        return ThreadSafeConfiguration().get_entry(
            Constants.SECTION_LOGGING,
            Constants.LOGGING_LOG_LEVEL)

    @property
    def general_metadata_config_file(self) -> str:
        """ Configuration property : General | metadata config file """
        return ThreadSafeConfiguration().get_entry(
            Constants.SECTION_GENERAL,
            Constants.GENERAL_METADATA_CONFIG_FILE)

    @property
    def apis_accounts_svc(self) -> str:
        """ Configuration property : APIs | Accounts Service base path """
        return ThreadSafeConfiguration().get_entry(
            Constants.SECTION_APIS, Constants.APIS_ACCOUNTS_SVC)

    @property
    def apis_cms_svc(self) -> str:
        """ Configuration property : APIs | CMS Service base path """
        return ThreadSafeConfiguration().get_entry(
            Constants.SECTION_APIS, Constants.APIS_CMS_SVC)
