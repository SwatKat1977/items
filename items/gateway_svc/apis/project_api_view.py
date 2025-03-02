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
from base_view import BaseView
from threadsafe_configuration import ThreadSafeConfiguration


class ProjectApiView(BaseView):
    __slots__ = ['_logger']

    def __init__(self, logger : logging.Logger) -> None:
        self._logger = logger.getChild(__name__)

    async def project_overviews(self):

        # Get fields from query parameters
        value_fields = quart.request.args.get("value_fields")
        count_fields = quart.request.args.get("count_fields")

        value_fields_str = f"value_fields={value_fields}" if value_fields \
            else ""
        count_fields_str = f"count_fields={count_fields}" if count_fields \
            else ""
        joiner_str = "&" if value_fields and count_fields else ""

        # http://127.0.0.1:4000/project/overviews?count_fields=no_of_test_runs

        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc

        details_url: str = f"{cms_svc}project/overviews?{value_fields_str}" + \
                           f"{joiner_str}{count_fields_str}"

        print(f"Details: {details_url}")

        return quart.Response(json.dumps({}),
                              status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                              content_type="application/json")

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


        return await view.project_overviews()
