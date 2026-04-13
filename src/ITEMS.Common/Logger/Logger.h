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
#ifndef LOGGER_LOGGER_H_
#define LOGGER_LOGGER_H_
#include <string>
#include "LoggerConfig.h"

namespace ITEMS::Common {

class Logger {
 public:
    static void Initialise(const LoggerConfig& config);
    static void Shutdown();

    static void Trace(std::string message);
    static void Debug(std::string message);
    static void Info(std::string message);
    static void Warn(std::string message);
    static void Error(std::string message);
    static void Critical(std::string message);

 private:
    static void EnsureInitialised();
};

}   // namespace ITEMS::Common

#endif  // LOGGER_LOGGER_H_
