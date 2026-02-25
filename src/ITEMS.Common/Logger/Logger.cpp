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
#include "Logger.h"
#include <spdlog/spdlog.h>
#include <spdlog/async.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/rotating_file_sink.h>
#include <memory>
#include <mutex>
#include <string>
#include <utility>
#include <vector>


namespace ITEMS::Common {

namespace {

std::shared_ptr<spdlog::logger> g_logger;
std::once_flag g_initFlag;

spdlog::level::level_enum ConvertLevel(LogLevel level) {
    switch (level) {
    case LogLevel::Trace:    return spdlog::level::trace;
    case LogLevel::Debug:    return spdlog::level::debug;
    case LogLevel::Info:     return spdlog::level::info;
    case LogLevel::Warn:     return spdlog::level::warn;
    case LogLevel::Error:    return spdlog::level::err;
    case LogLevel::Critical: return spdlog::level::critical;
    case LogLevel::Off:      return spdlog::level::off;
    }
    return spdlog::level::info;
}

}   // namespace

void Logger::Initialise(const LoggerConfig& config) {
    std::call_once(g_initFlag, [&]() {
        std::vector<spdlog::sink_ptr> sinks;

        if (config.console) {
            sinks.push_back(
                std::make_shared<spdlog::sinks::stdout_color_sink_mt>());
        }

        if (config.use_file && !config.file_path.empty()) {
            sinks.push_back(
                std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
                    config.file_path,
                    config.max_file_size,
                    config.max_rotation_files));
        }

        if (config.async) {
            spdlog::init_thread_pool(8192, 1);

            g_logger = std::make_shared<spdlog::async_logger>(
                "ITEMS",
                sinks.begin(),
                sinks.end(),
                spdlog::thread_pool(),
                spdlog::async_overflow_policy::block);
        } else {
            g_logger = std::make_shared<spdlog::logger>(
                "ITEMS",
                sinks.begin(),
                sinks.end());
        }

        g_logger->set_level(ConvertLevel(config.level));
        g_logger->set_pattern(
            "[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] [thread %t] %v");

        spdlog::register_logger(g_logger);
        });
}

void Logger::Shutdown() {
    if (g_logger) {
        g_logger->flush();
        spdlog::shutdown();
        g_logger.reset();
    }
}

void Logger::EnsureInitialised() {
    if (!g_logger) {
        LoggerConfig defaultConfig;
        Initialise(defaultConfig);
    }
}

void Logger::Trace(std::string message) {
    EnsureInitialised();
    g_logger->trace(std::move(message));
}

void Logger::Debug(std::string message) {
    EnsureInitialised();
    g_logger->debug(std::move(message));
}

void Logger::Info(std::string message) {
    EnsureInitialised();
    g_logger->info(std::move(message));
}

void Logger::Warn(std::string message) {
    EnsureInitialised();
    g_logger->warn(std::move(message));
}

void Logger::Error(std::string message) {
    EnsureInitialised();
    g_logger->error(std::move(message));
}

void Logger::Critical(std::string message) {
    EnsureInitialised();
    g_logger->critical(std::move(message));
}

}   // namespace ITEMS::Common
