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
    API view for reporting service health status.

    This class provides an endpoint to retrieve the current health and
    operational status of the application and its dependencies, such as the
    database, along with metadata like uptime and version.
    """
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        """
        Initialize the HealthApiView.

        Args:
            logger (logging.Logger): Logger instance used for emitting logs.
            state_object (StateObject): A shared object containing application state,
                such as startup time, version, and component health statuses.
        """
        self._logger = logger.getChild(__name__)
        self._state_object = state_object

    async def health(self):
        """
        Asynchronously retrieve the current health status of the application.

        This method reports:
        - Overall health status (healthy, degraded, or critical).
        - Health of key dependencies (e.g., the database).
        - Application uptime in seconds.
        - Application version.
        - Detailed issue information if degradation is present.

        Returns:
            Response: A JSON HTTP response containing the health status and related metadata.
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
            },
            "issues": issues if issues else None,
            "uptime_seconds": uptime,
            "version": self._state_object.version
        }

        return Response(json.dumps(response),
                        status=HTTPStatus.OK,
                        content_type="application/json")
