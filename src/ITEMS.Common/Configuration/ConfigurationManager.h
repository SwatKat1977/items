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
#ifndef CONFIGURATION_CONFIGURATIONMANAGER_H_
#define CONFIGURATION_CONFIGURATIONMANAGER_H_
#include <string>
#include <unordered_map>
#include "ConfigurationSetup.h"

namespace ITEMS::Common {

class ConfigurationManager {
 public:
    void Configure(const ConfigurationSetup& layout,
        const std::string configFile = "",
        bool fileRequired = false);

    void ProcessConfig();

    const ConfigValue& GetEntry(const std::string& section,
        const std::string& item) const;

 private:
    const ConfigurationSetup* layout_ = nullptr;

    std::string config_file_;
    bool file_required_ = false;
    bool has_config_file_ = false;

    using SectionMap = std::unordered_map<std::string,
                                          std::unordered_map<std::string,
                                                             ConfigValue>>;

    using IniData = std::unordered_map<std::string,
        std::unordered_map<std::string, std::string>>;

    SectionMap config_items_;


    IniData ini_data_;

    void ReadConfiguration();
    void LoadIniFile();

    std::string ReadString(const std::string& section,
                           const ConfigurationSetupItem& fmt);

    int ReadInt(const std::string& section,
                const ConfigurationSetupItem& fmt);
};

}   // namespace ITEMS::Common

#endif  // CONFIGURATION_CONFIGURATIONMANAGER_H_
