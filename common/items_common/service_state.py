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
from dataclasses import dataclass, field
import time
from typing import Dict, Any
from service_health_enums import ComponentDegradationLevel


@dataclass
class ServiceState:
    """
    Represents the operational state of a service, including health,
    optional database condition, version, and maintenance mode.
    """
    # pylint: disable=too-many-instance-attributes

    # Service health
    service_health: ComponentDegradationLevel = ComponentDegradationLevel.NONE
    service_health_state_str: str = ""

    # Database health (optional, ignored if service has no DB)
    database_enabled: bool = True  # Controls whether DB health is used
    database_health: ComponentDegradationLevel = ComponentDegradationLevel.NONE
    database_health_state_str: str = ""

    # Metadata
    version: str = ""
    startup_time: int = field(default_factory=lambda: int(time.time()))

    # Maintenance flag
    in_maintenance: bool = False

    # ---------------------------------------------------------------------
    # Lifecycle helpers
    # ---------------------------------------------------------------------

    def mark_database_failed(self, reason: str = "Fatal SQL failure") -> None:
        """
        Mark the database as failed and enter maintenance mode (if DB is
        enabled).
        """
        if not self.database_enabled:
            return
        self.database_health = ComponentDegradationLevel.FULLY_DEGRADED
        self.database_health_state_str = reason
        self.enter_maintenance(f"Database failure: {reason}")

    def mark_service_failed(self, reason: str) -> None:
        """Mark the service as failed and enter maintenance mode."""
        self.service_health = ComponentDegradationLevel.FULLY_DEGRADED
        self.service_health_state_str = reason
        self.enter_maintenance(reason)

    def enter_maintenance(self,
                          reason: str = "Entering maintenance mode") -> None:
        """Enable maintenance mode."""
        self.in_maintenance = True
        self.service_health = ComponentDegradationLevel.FULLY_DEGRADED
        self.service_health_state_str = reason

    def exit_maintenance(self) -> None:
        """Disable maintenance mode (return to normal operation)."""
        self.in_maintenance = False
        self.service_health = ComponentDegradationLevel.NONE
        self.service_health_state_str = "Normal operation"

    def is_operational(self) -> bool:
        """Return True if the service is fully operational."""
        return not self.in_maintenance

    # ---------------------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable representation of the state."""
        data = {
            "service_health": self.service_health.name,
            "service_health_state_str": self.service_health_state_str,
            "version": self.version,
            "startup_time": self.startup_time,
            "in_maintenance": self.in_maintenance
        }

        if self.database_enabled:
            data.update({
                "database_health": self.database_health.name,
                "database_health_state_str": self.database_health_state_str,
            })

        return data
