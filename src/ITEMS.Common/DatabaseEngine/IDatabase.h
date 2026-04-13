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
#ifndef IDATABASE_H_
#define IDATABASE_H_
#include <string>
#include <vector>
#include <optional>
#include <unordered_map>

namespace ITEMS::Common {

// Simple row representation: column name -> value
using Row = std::unordered_map<std::string, std::string>;

class IDatabase {
public:
    virtual ~IDatabase() = default;

    // Execute a query that does not return results
    // (INSERT, UPDATE, DELETE, CREATE, etc.)
    virtual int Execute(
        const std::string& query,
        const std::vector<std::string>& params = {}) = 0;

    // Execute a query that returns multiple rows
    virtual std::vector<Row> Query(
        const std::string& query,
        const std::vector<std::string>& params = {}) = 0;

    // Execute a query that returns a single row (or none)
    virtual std::optional<Row> QuerySingle(
        const std::string& query,
        const std::vector<std::string>& params = {}) = 0;
};

} // namespace ITEMS::Common

#endif // IDATABASE_H_
