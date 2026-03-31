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
#include <atomic>
#include <csignal>
#include <memory>
#include "Service.h"
#include "Logger/Logger.h"
#include "Configuration/ConfigurationManager.h"
#include "Configuration/ConfigurationSetupItem.h"   

namespace ITEMS::Accounts {

Common::ConfigurationSetup CONFIG_LAYOUT({
    {"logging", {
        Common::StringItem("level", "info", true, {"debug", "info", "warn", "error"}),
        Common::StringItem("file", "app.log")
    }},
    {"database", {
        Common::StringItem("file", std::nullopt, true),
        Common::StringItem("journal_mode", "wal"),
        Common::IntItem("busy_timeout", 5000)
    }}
});

namespace {

Service* g_service_instance = nullptr;

void SignalHandler(int) {
    if (g_service_instance) {
        Common::Logger::Info("Shutdown signal received.");
        g_service_instance->Stop();
    }
}

}

Service::Service() {
    Common::LoggerConfig loggerConfig;
    loggerConfig.level = Common::LogLevel::Info;
    loggerConfig.console = true;
    Common::Logger::Initialise(loggerConfig);

    /*
    Common::ConfigurationSetup configLayout({
        {"logging", {
            Common::StringItem("level", "info", true, {"debug", "info", "warn", "error"}),
            Common::StringItem("file", "app.log")
        }},
        {"database", {
            Common::StringItem("file", std::nullopt, true),
            Common::StringItem("journal_mode", "wal"),
            Common::IntItem("busy_timeout", 5000)
        }}
    });
    // CONFIG_LAYOUT
    config_.Configure(configLayout);

    try {
        config_.ProcessConfig();
    }
    catch (std::runtime_error &ex) {
        printf("%s\n", ex.what());
        return;
    }

    SetupRoutes();
    SetupSignalHandlers();
    */
}

void Service::SetupRoutes()
{
    CROW_ROUTE(_app, "/health")
        ([]() {
        return "OK";
            });

    CROW_ROUTE(_app, "/hello")
        ([]() {
        return "Hello from ITEMS service";
            });
}

void Service::SetupSignalHandlers()
{
    g_service_instance = this;

    std::signal(SIGINT, SignalHandler);
    std::signal(SIGTERM, SignalHandler);
}

void Service::Run()
{
    _running = true;

    int port = 8080;

    if (!Initialise()) {
        Common::Logger::Error("Failed to initialize service. Exiting.");
        return;
    }

    try {
        Common::Logger::Info("Starting service on port " + port); // if formatting outside
        _app.port(port).multithreaded().run();
    }
    catch (const std::exception& ex) {
        Common::Logger::Error(std::string("Service crashed: ") + ex.what());
        throw;
    }

    Common::Logger::Info("Service exited cleanly.");
}

bool Service::Initialise() {
    config_.Configure(CONFIG_LAYOUT);

    try {
        config_.ProcessConfig();
    }
    catch (std::runtime_error& ex) {
        printf("%s\n", ex.what());
        return false;
    }

    /*
    Common::Logger::Info("Configuration");
    Common::Logger::Info("=============");

    Common::Logger::Info("Configuration file required: " +
                         "True" ? required : "False");
    Common::Logger::Info("Configuration file : %s",
        "None"if not required else config_file);
    Common::Logger::Info("[logging]");
    Common::Logger::Info("=> Log level : %s",
        ServiceConfiguration().logging_log_level);
    Common::Logger::Info("[database]");
    Common::Logger::Info("=> Filename : %s",
        ServiceConfiguration().database_filename);
    Common::Logger::Info("=> Journal mode : %s",
        ServiceConfiguration().database_journal_mode);
    Common::Logger::Info("=> Busy timeout : %d",
        ServiceConfiguration().database_busy_timeout);
    */

    SetupRoutes();
    SetupSignalHandlers();

    return true;
}

void Service::Stop()
{
    if (_running)
    {
        _running = false;
        _app.stop();
        Common::Logger::Info("Service stopped.");
    }
}

}
