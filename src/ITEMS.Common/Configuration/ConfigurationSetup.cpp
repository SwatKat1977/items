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
#include "ConfigurationSetup.h"

class ConfigurationSetup
{
public:
    using SectionItems = std::vector<ConfigurationSetupItem>;
    using LayoutMap = std::unordered_map<std::string, SectionItems>;

    explicit ConfigurationSetup(LayoutMap items)
        : _items(std::move(items)) {
    }

    std::vector<std::string> getSections() const
    {
        std::vector<std::string> sections;
        for (const auto& kv : _items)
            sections.push_back(kv.first);
        return sections;
    }

    const SectionItems* getSection(const std::string& name) const
    {
        auto it = _items.find(name);
        if (it == _items.end())
            return nullptr;
        return &it->second;
    }

private:
    LayoutMap _items;
};
