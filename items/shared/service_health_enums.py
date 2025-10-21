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
    HEALTHY = "healthy"

    # Some components are slow or experiencing minor issues
    DEGRADED = "degraded"

    # A major component is down, affecting service functionality
    CRITICAL = "critical"


class ComponentDegradationLevel(Enum):
    """
    Represents the degradation state of a vehicle or system component.

    This enumeration defines the possible levels of degradation that a component
    can experience during simulation or operation.

    Attributes:
        NONE (str): The component is in perfect condition, with no degradation.
        PART_DEGRADED (str): The component is partially degraded, causing minor
            performance loss or inefficiency.
        FULLY_DEGRADED (str): The component is fully degraded and no longer
            functioning as intended.
    """

    # The component is in perfect condition, with no degradation.
    NONE = "none"

    # The component is partially degraded, causing minor performance loss or
    # inefficiency.
    PART_DEGRADED = "partial"

    # The component is fully degraded and no longer functioning as intended.
    FULLY_DEGRADED = "fully_degraded"
