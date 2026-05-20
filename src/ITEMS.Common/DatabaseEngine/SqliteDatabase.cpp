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
#include <stdexcept>
#include <string>
#include <vector>
#include "SqliteDatabase.h"


namespace ITEMS::Common {

SqliteDatabase::SqliteDatabase(const std::string& filename)
    : db_(nullptr) {

    if (sqlite3_open(filename.c_str(), &db_) != SQLITE_OK) {
        throw std::runtime_error("Failed to open SQLite database");
    }
}

SqliteDatabase::~SqliteDatabase() {
    if (db_) {
        sqlite3_close(db_);
    }
}

void SqliteDatabase::BindParameters(sqlite3_stmt* stmt,
    const std::vector<DbValue>& params) {

    for (size_t i = 0; i < params.size(); ++i) {
        int index = static_cast<int>(i + 1);

        if (std::holds_alternative<int>(params[i])) {
            sqlite3_bind_int(stmt, index, std::get<int>(params[i]));
        } else if (std::holds_alternative<std::string>(params[i])) {
            sqlite3_bind_text(stmt, index,
                std::get<std::string>(params[i]).c_str(),
                -1, SQLITE_TRANSIENT);
        }
    }
}


Row SqliteDatabase::ExtractRow(sqlite3_stmt* stmt) {
    Row row;

    int column_count = sqlite3_column_count(stmt);

    for (int i = 0; i < column_count; ++i) {
        const char* column_name = sqlite3_column_name(stmt, i);

        const unsigned char* text = sqlite3_column_text(stmt, i);

        row[column_name] = text ? reinterpret_cast<const char*>(text) : "";
    }

    return row;
}

int SqliteDatabase::Execute(const std::string& query,
    const std::vector<DbValue>& params) {

    sqlite3_stmt* stmt = nullptr;

    if (sqlite3_prepare_v2(db_,
                           query.c_str(),
                           -1,
                           &stmt, nullptr) != SQLITE_OK) {
        throw std::runtime_error("Failed to prepare statement");
    }

    BindParameters(stmt, params);

    int rc = sqlite3_step(stmt);

    if (rc != SQLITE_DONE) {
        sqlite3_finalize(stmt);
        throw std::runtime_error("Execution failed");
    }

    int changes = sqlite3_changes(db_);

    sqlite3_finalize(stmt);

    return changes;
}

std::vector<Row> SqliteDatabase::Query(
    const std::string& query,
    const std::vector<DbValue>& params) {

    sqlite3_stmt* stmt = nullptr;

    if (sqlite3_prepare_v2(db_,
                           query.c_str(),
                           -1, &stmt,
                           nullptr) != SQLITE_OK) {
        throw std::runtime_error("Failed to prepare statement");
    }

    BindParameters(stmt, params);

    std::vector<Row> results;

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        results.push_back(ExtractRow(stmt));
    }

    sqlite3_finalize(stmt);

    return results;
}

std::optional<Row> SqliteDatabase::QuerySingle(
    const std::string& query,
    const std::vector<DbValue>& params) {

    sqlite3_stmt* stmt = nullptr;

    if (sqlite3_prepare_v2(db_,
                           query.c_str(),
                           -1,
                           &stmt,
                           nullptr) != SQLITE_OK) {
        throw std::runtime_error("Failed to prepare statement");
    }

    BindParameters(stmt, params);

    int rc = sqlite3_step(stmt);

    if (rc == SQLITE_ROW) {
        Row row = ExtractRow(stmt);
        sqlite3_finalize(stmt);
        return row;
    }

    sqlite3_finalize(stmt);
    return std::nullopt;
}

}   // namespace ITEMS::Common
