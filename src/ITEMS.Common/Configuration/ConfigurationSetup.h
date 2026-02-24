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

namespace ITEMS::Configuration {

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

}   // namespace ITEMS::Configuration

#endif  // CONFIGURATION_CONFIGURATIONSETUP_H_
