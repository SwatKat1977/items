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
from http import HTTPStatus
import json
import logging
import time
from quart import Response
from base_view import BaseView
from state_object import StateObject
import service_health_enums as health_enums


class HealthApiView(BaseView):
    """
    A view that provides health check information for the application.

    This includes the health status of core components like the database and microservices,
    system uptime, and application version.

    Attributes:
        _logger (logging.Logger): Logger instance for recording events.
        _state_object (StateObject): Shared state object containing health and version info.
    """
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        """
        Initializes the HealthApiView with logging and application state.

        Args:
            logger (logging.Logger): Logger for emitting structured health
                                     check logs.
            state_object (StateObject): Application-wide state for tracking
                                        health, startup time, etc.
        """
        self._logger = logger.getChild(__name__)
        self._state_object = state_object

    async def health(self):
        """
        Performs a health check and returns a JSON response with system status.

        Checks the health of the database and the microservice components,
        calculates system uptime, and reports any degraded statuses.

        Returns:
            quart.Response: A JSON-formatted HTTP response indicating the overall health,
                            dependency statuses, current issues (if any), uptime, and version.
        """
        uptime: int = int(time.time()) - self._state_object.startup_time

        issues: list = []

        # Check database health
        if (self._state_object.database_health !=
                health_enums.ComponentDegradationLevel.NONE):
            status = health_enums.ComponentDegradationLevelStr[
                self._state_object.database_health]
            issues.append(
                {"component": "database",
                 "status": status,
                 "details": self._state_object.database_health_state_str})

        # Check microservice health
        if (self._state_object.service_health !=
                health_enums.ComponentDegradationLevel.NONE):
            status = health_enums.ComponentDegradationLevelStr[
                self._state_object.service_health]
            issues.append(
                {"component": "service",
                 "status": status,
                 "details": self._state_object.service_health_state_str})

        if issues:
            status = health_enums.STATUS_CRITICAL \
                if any(issue["status"] ==
                       health_enums.COMPONENT_DEGRADATION_LEVEL_FULLY_DEGRADED
                       for issue in issues) else health_enums.STATUS_DEGRADED
        else:
            status = health_enums.STATUS_HEALTHY

        response: dict = {
            "status": status,
            "dependencies": {
                "database": health_enums.ComponentDegradationLevelStr[
                    self._state_object.database_health],
                "service": health_enums.ComponentDegradationLevelStr[
                    self._state_object.service_health]
            },
            "issues": issues if issues else None,
            "uptime_seconds": uptime,
            "version": self._state_object.version
        }

        return Response(json.dumps(response),
                        status=HTTPStatus.OK,
                        content_type="application/json")
