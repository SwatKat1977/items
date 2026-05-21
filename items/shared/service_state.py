"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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
from items.shared.service_health_enums import ComponentDegradationLevel


@dataclass(slots=True)
class ServiceState:
    """
    Represents the operational state of a service, including health,
    optional database condition, version, and maintenance mode.
    """
    # pylint: disable=too-many-instance-attributes

    # Service health
    service_health: ComponentDegradationLevel = ComponentDegradationLevel.NONE
    service_health_reason: str | None = None

    # Database health (optional, ignored if service has no DB - e.g. when
    #                  database_enabled is set false).
    database_enabled: bool = False
    database_health: ComponentDegradationLevel = ComponentDegradationLevel.NONE
    database_health_reason: str | None = None

    # Metadata
    version: str = ""
    startup_time: int = field(default_factory=lambda: int(time.time()))

    # Maintenance flag
    in_maintenance: bool = False
    maintenance_reason: str | None = None

    last_updated_time: int = field(default_factory=lambda: int(time.time()))

    # ---------------------------------------------------------------------
    # Lifecycle helpers
    # ---------------------------------------------------------------------

    @property
    def uptime_seconds(self) -> int:
        """Return service uptime in seconds."""
        return int(time.time()) - self.startup_time

    def mark_database_failed(self, reason: str = "Fatal SQL failure") -> None:
        """
        Mark the database as failed and enter maintenance mode (if DB is
        enabled).
        """
        if not self.database_enabled:
            return
        self.database_health = ComponentDegradationLevel.FULLY_DEGRADED
        self.database_health_reason = reason
        self._touch()

    def mark_service_failed(self, reason: str) -> None:
        """Mark the service as failed."""
        self.service_health = ComponentDegradationLevel.FULLY_DEGRADED
        self.service_health_reason = reason
        self._touch()

    def enter_maintenance(self,
                          reason: str = "Entering maintenance mode") -> None:
        """Enable maintenance mode."""
        self.in_maintenance = True
        self.maintenance_reason = reason
        self._touch()

    def exit_maintenance(self) -> None:
        """Disable maintenance mode (return to normal operation)."""
        self.in_maintenance = False
        self.maintenance_reason = None
        self._touch()

    def is_available(self) -> bool:
        """Return True if the service can operate normally."""
        return (not self.in_maintenance
                and self.service_health !=
                ComponentDegradationLevel.FULLY_DEGRADED)

    def set_service_degraded(self,
                             reason: str,
                             fully_degraded: bool = False) -> None:
        """Mark the service as degraded."""
        self.service_health = (
            ComponentDegradationLevel.FULLY_DEGRADED
            if fully_degraded
            else ComponentDegradationLevel.PART_DEGRADED)
        self.service_health_reason = reason
        self._touch()

    def clear_service_degradation(self) -> None:
        """Return the service to normal operation."""
        self.service_health = ComponentDegradationLevel.NONE
        self.service_health_reason = None
        self._touch()

    # ---------------------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable representation of the state."""
        data = {
            "service_health": self.service_health.name,
            "service_health_reason": self.service_health_reason,
            "version": self.version,
            "startup_time": self.startup_time,
            "in_maintenance": self.in_maintenance,
            "maintenance_reason": self.maintenance_reason,
            "last_updated_time": self.last_updated_time,
            "uptime_seconds": self.uptime_seconds
        }

        if self.database_enabled:
            data.update({
                "database_health": self.database_health.name,
                "database_health_reason": self.database_health_reason,
            })

        return data

    # ---------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------

    def _touch(self) -> None:
        """Update the last modified timestamp."""
        self.last_updated_time = int(time.time())
