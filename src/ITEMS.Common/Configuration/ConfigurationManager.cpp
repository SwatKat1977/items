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
#include <algorithm>
#include <fstream>
#include <stdexcept>
#include <string>
#include "ConfigurationManager.h"
#include "ConfigurationItemType.h"
#include "ConfigurationSetupItem.h"
#include "EnvironmentUtils.h"

namespace ITEMS::Common {

void ConfigurationManager::Configure(const ConfigurationSetup& layout,
    const std::string configFile,
    bool fileRequired) {
    layout_ = &layout;
    config_file_ = configFile;
    file_required_ = fileRequired;
}

void ConfigurationManager::ProcessConfig() {
    if (!layout_) {
        throw std::runtime_error("Configuration layout not set.");
    }

    if (!config_file_.empty()) {
        LoadIniFile();
        has_config_file_ = true;
    }

    ReadConfiguration();
}

void ConfigurationManager::LoadIniFile() {
    std::ifstream file(config_file_);
    if (!file.is_open()) {
        if (file_required_) {
            throw std::runtime_error("Failed to open required config file: " +
                config_file_);
        }

        return;
    }

    std::string line;
    std::string currentSection;

    while (std::getline(file, line)) {
        line.erase(std::remove_if(line.begin(), line.end(), ::isspace),
                   line.end());

        if (line.empty() || line[0] == '#')
            continue;

        if (line.front() == '[' && line.back() == ']') {
            currentSection = line.substr(1, line.size() - 2);
            continue;
        }

        auto pos = line.find('=');
        if (pos != std::string::npos && !currentSection.empty()) {
            std::string key = line.substr(0, pos);
            std::string value = line.substr(pos + 1);
            ini_data_[currentSection][key] = value;
        }
    }
}

void ConfigurationManager::ReadConfiguration() {
    for (const auto& section : layout_->GetSections()) {
        const auto* items = layout_->GetSection(section);

        if (!items) continue;

        for (const auto& item : *items) {
            if (item.item_type == ConfigurationItemType::Integer) {
                int value = ReadInt(section, item);
                config_items_[section][item.item_name] = value;
            } else {
                std::string value = ReadString(section, item);
                config_items_[section][item.item_name] = value;
            }
        }
    }
}

std::string ConfigurationManager::ReadString(
    const std::string& section,
    const ConfigurationSetupItem& fmt) {
    std::string envName = section + "_" + fmt.item_name;
    std::transform(envName.begin(), envName.end(), envName.begin(), ::toupper);

    auto value = EnvironmentUtils::GetEnvironmentVariable(envName);

    if (!value && has_config_file_) {
        auto sec = ini_data_.find(section);
        if (sec != ini_data_.end()) {
            auto it = sec->second.find(fmt.item_name);
            if (it != sec->second.end()) {
                value = it->second;
            }
        }
    }

    if (!value && fmt.default_value) {
        value = std::get<std::string>(*fmt.default_value);
    }

    if (!value && fmt.is_required)
        throw std::runtime_error("Missing required config option " +
            section + "::" + fmt.item_name);

    if (value && !fmt.valid_values.empty()) {
        if (std::find(fmt.valid_values.begin(),
            fmt.valid_values.end(),
            *value) == fmt.valid_values.end()) {
            throw std::runtime_error("Invalid value '" + *value +
                "' for " + fmt.item_name);
        }
    }

    return value.value_or("");
}

int ConfigurationManager::ReadInt(
    const std::string& section,
    const ConfigurationSetupItem& fmt) {
    std::string envName = section + "_" + fmt.item_name;
    std::transform(envName.begin(), envName.end(), envName.begin(), ::toupper);

    auto value = EnvironmentUtils::GetEnvironmentVariable(envName);

    if (!value && has_config_file_) {
        auto sec = ini_data_.find(section);
        if (sec != ini_data_.end()) {
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

    try {
        return std::stoi(value.value_or("0"));
    }
    catch (...) {
        throw std::runtime_error("Invalid integer value for " +
            fmt.item_name);
    }
}

const ConfigValue& ConfigurationManager::GetEntry(
    const std::string& section,
    const std::string& item) const {
    auto sec = config_items_.find(section);
    if (sec == config_items_.end())
        throw std::runtime_error("Invalid section '" + section + "'");

    auto it = sec->second.find(item);
    if (it == sec->second.end())
        throw std::runtime_error("Invalid config item " +
            section + "::" + item);

    return it->second;
}

}   // namespace ITEMS::Common
