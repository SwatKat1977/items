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
import http
import json
import logging
import quart
import requests
from sessions import Sessions
from base_view import ApiResponse, BaseView, validate_json
from threadsafe_configuration import ThreadSafeConfiguration


class TestCaseApiView(BaseView):
    __slots__ = ['_logger']

    def __init__(self, logger: logging.Logger, sessions: Sessions) -> None:
        self._logger = logger.getChild(__name__)
        self._sessions: Sessions = sessions

    async def testcases_details(self, project_id: int) -> quart.Response:
        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc

        request_body: dict = {
            "project_id": project_id
        }
        details_url: str = f"{cms_svc}testcases/details"

        try:
            api_response = await self._call_api_post(details_url, request_body)

            if api_response.status_code != http.HTTPStatus.OK:
                self._logger.critical("CMS svc /testcases/details request invalid"
                                      " - Reason: %s",api_response.exception_msg)
                response_json = {
                    "status": 0,
                    'error': 'Internal error!'
                }
                return quart.Response(json.dumps(response_json),
                                      status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                      content_type="application/json")

        except requests.exceptions.ConnectionError as ex:
            except_str = f"Internal error: {ex}"
            self._logger.error(except_str)

            response_json = {
                "status":  0,
                "error": str(ex)
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        return quart.Response(json.dumps(api_response.body),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

    async def get_testcase(self,
                           project_id: int,
                           case_id: int) -> quart.Response:

        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc

        request_body: dict = {
            "project_id": project_id
        }
        details_url: str = f"{cms_svc}testcases/get_case/{case_id}"

        try:
            api_response = await self._call_api_post(details_url, request_body)

            if api_response.status_code != http.HTTPStatus.OK:
                self._logger.critical("CMS svc /testcases/get_case request invalid"
                                      " - Reason: %s",api_response.exception_msg)
                response_json = {
                    "status": 0,
                    'error': 'Internal error!'
                }
                return quart.Response(json.dumps(response_json),
                                      status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                      content_type="application/json")

        except requests.exceptions.ConnectionError as ex:
            except_str = f"Internal error: {ex}"
            self._logger.error(except_str)

            response_json = {
                "status":  0,
                "error": str(ex)
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        return quart.Response(json.dumps(api_response.body),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")
