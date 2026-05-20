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
#ifndef SERVICE_MICROSERVICE_H_
#define SERVICE_MICROSERVICE_H_
#include <atomic>

namespace ITEMS::Common {

class Microservice {
 public:
    Microservice();

    void Run();
    void Stop();

 private:
    void SetupSignalHandlers();

    virtual bool _Initialise() = 0;
    virtual void _MainLoop() = 0;
    virtual void _Shutdown() = 0;

    std::atomic<bool> _running{ false };
};

}   // namespace ITEMS::Common

#endif  // SERVICE_MICROSERVICE_H_
