/*
Copyright 2025 Integrated Test Management Suite Development Team

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
#include "ConfigurationManager.h"
#include "ConfigurationSetupItem.h"


static std::optional<std::string> getEnv(const std::string& name)
{
    const char* value = std::getenv(name.c_str());
    if (!value) return std::nullopt;
    return std::string(value);
}

void ConfigurationManager::configure(const ConfigurationSetup& layout,
    const std::string& configFile,
    bool fileRequired)
{
    _layout = &layout;
    _configFile = configFile;
    _fileRequired = fileRequired;
}

void ConfigurationManager::processConfig()
{
    if (!_layout)
        throw std::runtime_error("Configuration layout not set.");

    if (!_configFile.empty())
    {
        loadIniFile();
        _hasConfigFile = true;
    }

    readConfiguration();
}

void ConfigurationManager::loadIniFile()
{
    std::ifstream file(_configFile);
    if (!file.is_open())
    {
        if (_fileRequired)
            throw std::runtime_error("Failed to open required config file: " + _configFile);
        return;
    }

    std::string line;
    std::string currentSection;

    while (std::getline(file, line))
    {
        line.erase(std::remove_if(line.begin(), line.end(), ::isspace), line.end());

        if (line.empty() || line[0] == '#')
            continue;

        if (line.front() == '[' && line.back() == ']')
        {
            currentSection = line.substr(1, line.size() - 2);
            continue;
        }

        auto pos = line.find('=');
        if (pos != std::string::npos && !currentSection.empty())
        {
            std::string key = line.substr(0, pos);
            std::string value = line.substr(pos + 1);
            _iniData[currentSection][key] = value;
        }
    }
}

void ConfigurationManager::readConfiguration()
{
    for (const auto& section : _layout->getSections())
    {
        const auto* items = _layout->getSection(section);
        if (!items) continue;

        for (const auto& item : *items)
        {
            if (item.item_type == ConfigItemDataType::Integer)
            {
                int value = readInt(section, item);
                _configItems[section][item.item_name] = value;
            }
            else
            {
                std::string value = readString(section, item);
                _configItems[section][item.item_name] = value;
            }
        }
    }
}

std::string ConfigurationManager::readString(
    const std::string& section,
    const ConfigurationSetupItem& fmt)
{
    std::string envName = section + "_" + fmt.item_name;
    std::transform(envName.begin(), envName.end(), envName.begin(), ::toupper);

    auto value = getEnv(envName);

    if (!value && _hasConfigFile)
    {
        auto sec = _iniData.find(section);
        if (sec != _iniData.end())
        {
            auto it = sec->second.find(fmt.item_name);
            if (it != sec->second.end())
                value = it->second;
        }
    }

    if (!value && fmt.default_value)
        value = std::get<std::string>(*fmt.default_value);

    if (!value && fmt.is_required)
        throw std::runtime_error("Missing required config option " +
            section + "::" + fmt.item_name);

    if (value && !fmt.valid_values.empty())
    {
        if (std::find(fmt.valid_values.begin(),
            fmt.valid_values.end(),
            *value) == fmt.valid_values.end())
        {
            throw std::runtime_error("Invalid value '" + *value +
                "' for " + fmt.item_name);
        }
    }

    return value.value_or("");
}

int ConfigurationManager::readInt(
    const std::string& section,
    const ConfigurationSetupItem& fmt)
{
    std::string envName = section + "_" + fmt.item_name;
    std::transform(envName.begin(), envName.end(), envName.begin(), ::toupper);

    auto value = getEnv(envName);

    if (!value && _hasConfigFile)
    {
        auto sec = _iniData.find(section);
        if (sec != _iniData.end())
        {
            auto it = sec->second.find(fmt.item_name);
            if (it != sec->second.end())
                value = it->second;
        }
    }

    if (!value && fmt.default_value)
        return std::get<int>(*fmt.default_value);

    if (!value && fmt.is_required)
        throw std::runtime_error("Missing required config option " +
            section + "::" + fmt.item_name);

    try
    {
        return std::stoi(value.value_or("0"));
    }
    catch (...)
    {
        throw std::runtime_error("Invalid integer value for " +
            fmt.item_name);
    }
}

const ConfigValue& ConfigurationManager::getEntry(
    const std::string& section,
    const std::string& item) const
{
    auto sec = _configItems.find(section);
    if (sec == _configItems.end())
        throw std::runtime_error("Invalid section '" + section + "'");

    auto it = sec->second.find(item);
    if (it == sec->second.end())
        throw std::runtime_error("Invalid config item " +
            section + "::" + item);

    return it->second;
}
