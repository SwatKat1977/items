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
#include <string>
#include <utility>
#include <vector>
#include "ConfigurationSetup.h"

namespace ITEMS::Common {

ConfigurationSetup::ConfigurationSetup(LayoutMap items)
    : items_(std::move(items)) {
}

std::vector<std::string> ConfigurationSetup::GetSections() const {
    std::vector<std::string> sections;
    for (const auto& kv : items_)
        sections.push_back(kv.first);
    return sections;
}

const ConfigurationSetup::SectionItems* ConfigurationSetup::GetSection(
    const std::string& name) const {
    auto it = items_.find(name);
    if (it == items_.end())
        return nullptr;
    return &it->second;
}

}   // namespace ITEMS::Common
