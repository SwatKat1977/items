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
#ifndef SERVICE_H_
#define SERVICE_H_
#include <optional>
#include "CrowIncludes.h"
#include "Service/Microservice.h"
#include "Configuration/ConfigurationManager.h"
#include "ServiceConfiguration.h"


namespace ITEMS::Accounts {

class AccountsService : public Common::Microservice {
 public:
    AccountsService();

 private:
    bool _Initialise() override;
    void _MainLoop() override;
    void _Shutdown() override;

    void SetupRoutes();

    Common::ConfigurationManager config_;
    std::optional<ServiceConfiguration> serviceConfig_;
    crow::SimpleApp app_;
};

}   // namespace ITEMS::Accounts

#endif  // SERVICE_H_
