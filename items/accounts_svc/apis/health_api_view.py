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
from quart import Response
from base_view import BaseView


class HealthApiView(BaseView):
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger.getChild(__name__)

    async def health(self):

        response: dict = {
            "status": "healthy",
            "dependencies": {
                "database": "partial",
                "service": "fully_degraded"
            },
            "uptime_seconds": 86400,
            "version": "1.2.3"
        }

        return Response(json.dumps(response),
                        status=HTTPStatus.OK,
                        content_type="application/json")
