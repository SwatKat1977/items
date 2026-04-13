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
#ifndef CONFIGURATION_CONFIGURATIONSETUP_H_
#define CONFIGURATION_CONFIGURATIONSETUP_H_
#include <string>
#include <unordered_map>
#include <vector>
#include "ConfigurationSetupItem.h"

namespace ITEMS::Common {

ConfigurationSetupItem StringItem(
    std::string name,
    std::optional<std::string> defaultValue = std::nullopt,
    bool required = false,
    std::vector<std::string> valid = {});

ConfigurationSetupItem IntItem(std::string name,
                               std::optional<int> defaultValue = std::nullopt,
                               bool required = false);

class ConfigurationSetup {
 public:
    using SectionItems = std::vector<ConfigurationSetupItem>;
    using LayoutMap = std::unordered_map<std::string, SectionItems>;

    explicit ConfigurationSetup(LayoutMap items);

    std::vector<std::string> GetSections() const;

    const SectionItems* GetSection(const std::string& name) const;

 private:
    LayoutMap items_;
};

}   // namespace ITEMS::Common

#endif  // CONFIGURATION_CONFIGURATIONSETUP_H_
