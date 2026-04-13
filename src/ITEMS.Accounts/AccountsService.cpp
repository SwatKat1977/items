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
#include <iostream>
#include <string>
#include "AccountsService.h"
#include "Configuration/ConfigurationManager.h"
#include "Configuration/ConfigurationSetupItem.h"
#include "Logger/Logger.h"
#include "ServiceConfiguration.h"

namespace ITEMS::Accounts {

Common::ConfigurationSetup CONFIG_LAYOUT({
    {"logging", {
        Common::StringItem("level", "info",
                           true,
                           {"debug", "info", "warn", "error"}),
        Common::StringItem("file", "app.log")
    }},
    {"database", {
        Common::StringItem("file", std::nullopt, true),
        Common::StringItem("journal_mode", "wal"),
        Common::IntItem("busy_timeout", 5000)
    }}
});


AccountsService::AccountsService() : Common::Microservice() {
    Common::LoggerConfig loggerConfig;
    loggerConfig.level = Common::LogLevel::Info;
    loggerConfig.console = true;
    loggerConfig.include_thread_id = true;
    loggerConfig.include_milliseconds = true;
    Common::Logger::Initialise(loggerConfig);
}

bool AccountsService::_Initialise() {
    config_.Configure(CONFIG_LAYOUT);

    try {
        config_.ProcessConfig();

        ServiceConfigurationDatabase db_config(
            std::get<std::string>(config_.GetEntry("database", "file")),
            std::get<std::string>(config_.GetEntry("database", "journal_mode")),
            std::get<int>(config_.GetEntry("database", "busy_timeout")));
        ServiceConfigurationLogging logging_config(
            std::get<std::string>(config_.GetEntry("logging", "level")),
            std::get<std::string>(config_.GetEntry("logging", "file")));
        serviceConfig_.emplace(logging_config, db_config);
    }
    catch (std::runtime_error& ex) {
        std::cout << "Error processing config: " << ex.what() << std::endl;
        return false;
    }

    Common::Logger::Info("Configuration");
    Common::Logger::Info("=============");

    std::string required_str = config_.IsFileRequired() ? "True" : "False";
    std::string config_file = config_.IsFileRequired()
        ? serviceConfig_->GetDatabase().GetFilename() : "None";
    Common::Logger::Info("Configuration file required: " + required_str);
    Common::Logger::Info("Configuration file : " + config_file);
    Common::Logger::Info("[logging]");
    Common::Logger::Info("=> Log level : " +
        serviceConfig_->GetLogging().GetLevel());
    Common::Logger::Info("=> Log file : " +
        serviceConfig_->GetLogging().GetFile());
    Common::Logger::Info("[database]");
    Common::Logger::Info("=> Filename : " +
        serviceConfig_->GetDatabase().GetFilename());
    Common::Logger::Info("=> Journal mode : " +
        serviceConfig_->GetDatabase().GetJournalMode());
    Common::Logger::Info("=> Busy timeout : " +
        std::to_string(serviceConfig_->GetDatabase().GetBusyTimeout()) +
        std::string(" ms"));

    config_.GetEntry("database", "file");

    SetupRoutes();

    return true;
}

void AccountsService::_MainLoop() {
    int port = 8080;

    try {
        Common::Logger::Info("Starting service on port " +
            std::to_string(port));
        app_.loglevel(crow::LogLevel::Warning);
        app_.port(port).multithreaded().run();
    }
    catch (const std::exception& ex) {
        Common::Logger::Error(std::string("Service crashed: ") + ex.what());
        throw;
    }
}

void AccountsService::_Shutdown() {
}

void AccountsService::SetupRoutes() {
    CROW_ROUTE(app_, "/health")
    ([]() {
        return "OK";
        });

    CROW_ROUTE(app_, "/hello")
    ([]() {
        return "Hello from ITEMS service";
    });
}

}   // namespace ITEMS::Accounts
