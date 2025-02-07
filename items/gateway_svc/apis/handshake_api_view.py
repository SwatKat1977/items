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


class HandshakeApiView(BaseView):
    __slots__ = ['_logger', '_sql_interface']

    def __init__(self, logger : logging.Logger, sessions: Sessions) -> None:
        self._logger = logger.getChild(__name__)
        self._sessions = sessions

    async def basic_authenticate(self) -> Response:
        """
        Handler method for basic user authentication endpoint.

        returns:
            Instance of Quart Response class.
        """

        try:
            '''
            STEP 1:
            Validate the message body:
            1) Is JSON format
            2) Validates against JSON schema
            '''
            request_msg: ApiResponse = self._validate_json_body(
                await request.get_data(),
                handshake_api.SCHEMA_BASIC_AUTHENTICATE_REQUEST)

            if request_msg.status_code != HTTPStatus.OK:
                response_json = {
                    'status': 0,
                    'error': request_msg.exception_msg
                }
                return Response(json.dumps(response_json),
                                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                content_type="application/json")

            '''
            STEP 2:
            Request authentication verification from accounts service.
            '''
            accounts_svc: str = ThreadSafeConfiguration().apis_accounts_svc

            auth_request: dict = {
                "email_address": request_msg.body.email_address,
                "password": request_msg.body.password
            }
            auth_url: str = (f"{accounts_svc}"
                             "/basic_auth/authenticate")

            response = await self._call_api_post(auth_url, auth_request)

            if response.status_code != HTTPStatus.OK:
                self._logger.critical("Accounts svc request invalid - Reason: %s",
                                      response.exception_msg)
                response_json = {
                    "status": 'BAD',
                    'error': 'Internal error!'
                }
                return Response(json.dumps(response_json),
                                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                content_type="application/json")

            response_status = HTTPStatus.OK

            if not response.body.get("status"):
                response_json = {
                    "status":  0,
                    "error": response.body.get("error")
                }

            else:
                token = uuid.uuid4().hex
                self._sessions.add_session(
                    request_msg.body.email_address,
                    token, AccountLogonType.BASIC)

                response_json = {
                    "status": 1,
                    "token": token
                }
                self._logger.info("User '%s' logged in",
                                  request_msg.body.email_address)

        except requests.exceptions.ConnectionError as ex:
            except_str = f"Internal error: {ex}"
            self._logger.error(except_str)

            response_json = {
                "status":  0,
                "error": str(ex)
            }
            response_status = HTTPStatus.INTERNAL_SERVER_ERROR

        return Response(json.dumps(response_json), status=response_status,
                        content_type="application/json")

    async def logout_user(self) -> Response:
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
