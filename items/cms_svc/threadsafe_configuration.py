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
from configuration_layout import ConfigurationConstants as consts
from configuration.configuration_manager import ConfigurationManager
from thread_safe_singleton import ThreadSafeSingleton


class ThreadSafeConfiguration(ConfigurationManager,
                              metaclass=ThreadSafeSingleton):
    """ Thread-safe singleton for the config """

    @property
    def logging_log_level(self) -> str:
        """ Configuration property : Logging | log level """
        return self.get_entry(
            consts.SECTION_LOGGING, consts.ITEM_LOGGING_LOG_LEVEL)

    @property
    def backend_db_filename(self) -> str:
        """ Configuration property : Backend | database filename """
        return self.get_entry(
            consts.SECTION_BACKEND, consts.ITEM_BACKEND_DB_FILENAME)
