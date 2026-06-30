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

'''
from http import HTTPStatus
import json
import logging
import requests
from quart import request, Response
from base_view import ApiResponse, BaseView
import interfaces.gateway.handshake as handshake_api
from threadsafe_configuration import ThreadSafeConfiguration
from sessions import Sessions
from account_logon_type import AccountLogonType
'''
from http import HTTPStatus
import logging
from quart import Response
from weaver_framework.microservice.api_response import ApiResponse
from weaver_framework.microservice.base_api_route import BaseApiRoute
from weaver_framework.microservice.microservice_decorators import validate_json
from items.services.items_gateway.sessions import Sessions


SCHEMA_LOGOUT_REQUEST: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",

    "type": "object",
    "additionalProperties": False,

    "properties":
        {
            "email_address":
                {
                    "type": "string"
                },
            "token":
                {
                    "type": "string"
                },
        },
    "required": ["email_address", "token"]
}


class DeleteSessionHandler(BaseApiRoute):
    __slots__ = ['_logger', '_sql_interface']

    def __init__(self, logger : logging.Logger, sessions: Sessions) -> None:
        self._logger = logger.getChild(__name__)
        self._sessions = sessions

    @validate_json(SCHEMA_LOGOUT_REQUEST)
    async def delete_session(self, request_msg: ApiResponse) -> Response:
        """
        Handler method for user session logout endpoint.

        returns:
            Instance of Quart Response class.
        """

        if self._sessions.is_valid_session(request_msg.body.email_address,
                                           request_msg.body.token):
            await self._sessions.delete_session(request_msg.body.email_address)
            self._logger.info("User '%s' logged out",
                              request_msg.body.email_address)

        response = "OK"
        response_status = HTTPStatus.OK

        return Response(response, status=response_status,
                        content_type="application/json")
