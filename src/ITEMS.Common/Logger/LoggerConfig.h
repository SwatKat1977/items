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
#ifndef LOGGER_LOGGERCONFIG_H_
#define LOGGER_LOGGERCONFIG_H_
#include <string>

namespace ITEMS::Common {

enum class LogLevel {
    Trace,
    Debug,
    Info,
    Warn,
    Error,
    Critical,
    Off
};

constexpr size_t ONE_MEGABYTE = 1024 * 1024;

struct LoggerConfig {
    LogLevel level = LogLevel::Info;

    bool console = true;
    bool async = true;

    // Optional file logging
    bool use_file = false;
    std::string file_path;

    // Default to 5 MB and 3 files for rotation
    std::size_t max_file_size = 5 * ONE_MEGABYTE;
    std::size_t max_rotation_files = 3;
};

}   // namespace ITEMS::Common

#endif  // LOGGER_LOGGERCONFIG_H_
