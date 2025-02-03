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
from enum import Enum


class ServiceDegradationStatus(Enum):
    """ Service degradation Status """

    # Everything is working fine
    HEALTHY = 0

    # Some components are slow or experiencing minor issues
    DEGRADED = 1

    # A major component is down, affecting service functionality
    CRITICAL = 2


ServiceDegradationStatusStr: dict = {
    ServiceDegradationStatus.HEALTHY: "Healthy",
    ServiceDegradationStatus.DEGRADED: "Degraded",
    ServiceDegradationStatus.CRITICAL: "Critical"
}

STATUS_HEALTHY: str = ServiceDegradationStatusStr[
    ServiceDegradationStatus.HEALTHY]
STATUS_DEGRADED: str = ServiceDegradationStatusStr[
    ServiceDegradationStatus.DEGRADED]
STATUS_CRITICAL: str = ServiceDegradationStatusStr[
    ServiceDegradationStatus.CRITICAL]


class ComponentDegradationLevel(Enum):
    """ Component degradation Level """

    NONE = 0
    DEGRADED = 1
    SEVERE = 2


ComponentDegradationLevelStr: dict = {
    ComponentDegradationLevel.NONE: "None",
    ComponentDegradationLevel.DEGRADED: "Degraded",
    ComponentDegradationLevel.SEVERE: "Severe"
}

COMPONENT_DEGRADATION_LEVEL_NONE: str = ComponentDegradationLevelStr[
    ComponentDegradationLevel.NONE]
COMPONENT_DEGRADATION_LEVEL_DEGRADED: str = ComponentDegradationLevelStr[
    ComponentDegradationLevel.DEGRADED]
COMPONENT_DEGRADATION_LEVEL_SEVERE: str = ComponentDegradationLevelStr[
    ComponentDegradationLevel.SEVERE]
