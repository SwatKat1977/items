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
import requests
import uuid
from quart import request, Response
from base_view import ApiResponse, BaseView
import interfaces.gateway.handshake as handshake_api
from threadsafe_configuration import ThreadSafeConfiguration
from sessions import Sessions
from account_logon_type import AccountLogonType


class SessionApiView(BaseView):

    async def validate_session(self):
        """
        Endpoint to check to see if the current session is valid.

        returns:
            Response instance
        """
        request_obj: ApiResponse = self._validate_json_body(
            await request.get_data(),
            handshake_api.SCHEMA_SESSION_VALIDATE_REQUEST)

        if request_obj.status_code != HTTPStatus.OK:
            response_json = { 'status': 'BAD REQUEST' }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.INTERNAL_SERVER_ERROR,
                            content_type="application/json")

        valid = self._sessions.is_valid_session(request_obj.body.email_address,
                                                request_obj.body.token)

        response_json = {"status": "VALID" if valid else "INVALID"}
        response_status = HTTPStatus.OK

        return Response(json.dumps(response_json), response_status,
                        content_type="application/json")

    async def delete_session(self) -> Response:
        """
        Handler method for user session logout endpoint.

        returns:
            Instance of Quart Response class.
        """

        request_msg: ApiResponse = self._validate_json_body(
            await request.get_data(),
            handshake_api.SCHEMA_LOGOUT_REQUEST)

        if request_msg.status_code != HTTPStatus.OK:
            response_json = {
                'status': 0,
                'error': request_msg.exception_msg
            }
            return Response(json.dumps(response_json),
                            status=HTTPStatus.INTERNAL_SERVER_ERROR,
                            content_type="application/json")

        if self._sessions.is_valid_session(request_msg.body.email_address,
                                           request_msg.body.token):
            self._sessions.delete_session(request_msg.body.email_address)
            self._logger.info("User '%s' logged out",
                              request_msg.body.email_address)

        response = "OK"
        response_status = HTTPStatus.OK

        return Response(response, status=response_status,
                        content_type="application/json")
