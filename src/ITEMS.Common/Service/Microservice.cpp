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
#include <csignal>
#include <string>
#include "Service/Microservice.h"
#include "Logger/Logger.h"


namespace ITEMS::Common {

namespace {

std::atomic<Microservice*> g_service_instance = nullptr;

void SignalHandler(int) {
    auto* instance = g_service_instance.load();
    if (instance) {
        instance->Stop();
    }
}

}   // namespace

Microservice::Microservice() {
    SetupSignalHandlers();
}

void Microservice::SetupSignalHandlers() {
    g_service_instance = this;

    std::signal(SIGINT, SignalHandler);
    std::signal(SIGTERM, SignalHandler);
}

void Microservice::Run() {
    if (_running) {
        Common::Logger::Warn("Service already running.");
        return;
    }

    if (!_Initialise()) {
        Common::Logger::Error("Initialisation failed.");
        return;
    }

    _running = true;

    Common::Logger::Info("Service starting");

    try {
        // Runs until Stop() triggers shutdown
        _MainLoop();
    }
    catch (const std::exception& ex) {
        Common::Logger::Error(std::string("Microservice crashed: ")
            + ex.what());
        throw;
    }

    Common::Logger::Info("Service exited cleanly.");
}

void Microservice::Stop() {
    bool expected = true;
    if (_running.compare_exchange_strong(expected, false)) {
        _Shutdown();
        Common::Logger::Info("Service stopped.");
    }
}

}   // namespace ITEMS::Common
