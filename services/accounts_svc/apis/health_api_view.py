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
from service_health_enums import (ServiceDegradationStatus,
                                  ComponentDegradationLevel)


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
        if self._state_object.database_health != \
                ComponentDegradationLevel.NONE:
            issues.append(
                {"component": "database",
                 "status": self._state_object.database_health.value,
                 "details": self._state_object.database_health_state_str})

        # Check microservice health
        if self._state_object.service_health != \
                ComponentDegradationLevel.NONE:
            issues.append(
                {"component": "service",
                 "status": self._state_object.service_health.value,
                 "details": self._state_object.service_health_state_str})

        if issues:
            status = ServiceDegradationStatus.CRITICAL.value \
                if any(issue["status"] ==
                       ComponentDegradationLevel.FULLY_DEGRADED.value
                       for issue in issues)\
                else ServiceDegradationStatus.DEGRADED.value
        else:
            status = ServiceDegradationStatus.HEALTHY.value

        response: dict = {
            "status": status,
            "dependencies": {
                "database": self._state_object.database_health.value,
                "service": self._state_object.service_health.value
            },
            "issues": issues if issues else None,
            "uptime_seconds": uptime,
            "version": self._state_object.version
        }

        return Response(json.dumps(response),
                        status=HTTPStatus.OK,
                        content_type="application/json")
