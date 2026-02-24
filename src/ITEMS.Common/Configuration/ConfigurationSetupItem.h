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
#ifndef CONFIGURATION_CONFIGURATIONSETUPITEM_H_
#define CONFIGURATION_CONFIGURATIONSETUPITEM_H_
#include <optional>
#include <string>
#include <utility>
#include <variant>
#include <vector>
#include "ConfigurationItemType.h"

namespace ITEMS::Configuration {

using ConfigValue = std::variant<int, std::string>;

class ConfigurationSetupItem {
 public:
    ConfigurationSetupItem(
        std::string name,
        ConfigurationItemType type,
        std::vector<std::string> validValues = {},
        bool required = false,
        std::optional<ConfigValue> defaultValue = std::nullopt)
        : item_name(std::move(name)),
        item_type(type),
        valid_values(std::move(validValues)),
        is_required(required),
        default_value(std::move(defaultValue)) {
    }

    std::string item_name;
    ConfigurationItemType item_type;
    std::vector<std::string> valid_values;
    bool is_required;
    std::optional<ConfigValue> default_value;
};

}   // namespace ITEMS::Configuration

#endif  // CONFIGURATION_CONFIGURATIONSETUPITEM_H_
