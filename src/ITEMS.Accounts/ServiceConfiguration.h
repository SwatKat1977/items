/*
Copyright 2026 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http ://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
#ifndef SERVICECONFIGURATION_H_
#define SERVICECONFIGURATION_H_
#include <string>

namespace ITEMS::Accounts {

class ServiceConfigurationDatabase {
 public:
    ServiceConfigurationDatabase(const std::string& file,
        const std::string& journal_mode,
        int busy_timeout) : file_(file),
                            journal_mode_(journal_mode),
                            busy_timeout_(busy_timeout) {
    }

    std::string GetFilename() const {
        return file_;
    }

    std::string GetJournalMode() const {
        return journal_mode_;
    }

    int GetBusyTimeout() const {
        return busy_timeout_;
    }

 private:
    std::string file_;
    std::string journal_mode_;
    int busy_timeout_;
};

class ServiceConfigurationLogging {
 public:
    ServiceConfigurationLogging(const std::string& level,
                                const std::string& file) : level_(level),
                                                           file_(file) {
    }

    std::string GetLevel() const {
        return level_;
    }

    std::string GetFile() const {
        return file_;
    }

 private:
    std::string level_;
    std::string file_;
};

class ServiceConfiguration {
 public:
    ServiceConfiguration(
        const ServiceConfigurationLogging& logging_config,
        const ServiceConfigurationDatabase& database_config)
        : logging_config_(logging_config),
            database_config_(database_config) {
    }

    const ServiceConfigurationLogging GetLogging() const {
        return logging_config_;
    }

    const ServiceConfigurationDatabase GetDatabase() const {
        return database_config_;
    }

 private:
    ServiceConfigurationLogging logging_config_;
    ServiceConfigurationDatabase database_config_;
};

}   // namespace ITEMS::Accounts

#endif  // SERVICECONFIGURATION_H_
