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
#ifndef CONFIGURATIONMANAGER_H_
#define CONFIGURATIONMANAGER_H_
#include <string>
#include <unordered_map>

class ConfigurationManager {
public:
    void configure(const ConfigurationSetup& layout,
        const std::string& configFile = "",
        bool fileRequired = false);

    void processConfig();

    const ConfigValue& getEntry(const std::string& section,
        const std::string& item) const;

private:
    const ConfigurationSetup* _layout = nullptr;

    std::string _configFile;
    bool _fileRequired = false;
    bool _hasConfigFile = false;

    using SectionMap = std::unordered_map<std::string,
        std::unordered_map<std::string, ConfigValue>>;

    SectionMap _configItems;

    using IniData = std::unordered_map<std::string,
        std::unordered_map<std::string, std::string>>;

    IniData _iniData;

    void readConfiguration();
    void loadIniFile();

    std::string readString(const std::string& section,
        const ConfigurationSetupItem& fmt);

    int readInt(const std::string& section,
        const ConfigurationSetupItem& fmt);
};

#endif  // CONFIGURATIONMANAGER_H_
