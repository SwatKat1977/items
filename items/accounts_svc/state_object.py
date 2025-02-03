"""
Copyright 2025 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import time
from dataclasses import dataclass, field
from service_health_enums import ComponentDegradationLevel

@dataclass
class StateObject:
    service_health: ComponentDegradationLevel = ComponentDegradationLevel.NONE
    service_health_state_str: str = ""
    database_health: ComponentDegradationLevel = ComponentDegradationLevel.NONE
    database_health_state_str: str = ""
    version: str = ""
    startup_time: int = field(default_factory=lambda: int(time.time()))
