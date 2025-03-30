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
from base_view import ApiResponse, BaseView, validate_json
from threadsafe_configuration import ThreadSafeConfiguration
import interfaces.gateway.project as json_schemas


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
        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc
        url: str = f"{cms_svc}project/overviews?{value_fields_str}" + \
                   f"{joiner_str}{count_fields_str}"

        api_response = await self._call_api_get(url)

        if api_response.status_code != http.HTTPStatus.OK:
            self._logger.critical("CMS svc /project/overviews request invalid"
                                  " - Reason: %s",api_response.exception_msg)
            response_json = {
                "status": 0,
                'error': 'Internal error!'
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        return quart.Response(json.dumps(api_response.body),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

    @validate_json(json_schemas.SCHEMA_ADD_PROJECT_REQUEST)
    async def add_project(self, request_msg: ApiResponse):

        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc
        url: str = f"{cms_svc}project/add"

        cms_request: dict = {
            "name": request_msg.body.name,
            "announcement": request_msg.body.announcement,
            "announcement_on_overview":
                request_msg.body.announcement_on_overview,
        }
        api_response = await self._call_api_post(url, cms_request)

        if api_response.status_code != http.HTTPStatus.OK:
            self._logger.critical("CMS svc /project/add request invalid"
                                  " - Reason: %s",api_response.exception_msg)
            response_json = {
                "status": 0,
                'error': api_response.body['error_msg']
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        response_json: dict = {"status": 1}
        return quart.Response(json.dumps(response_json),
                              status=http.HTTPStatus.OK,
                              content_type="text/plain")

    @validate_json(json_schemas.SCHEMA_MODIFY_PROJECT_REQUEST)
    async def modify_project(self,
                             request_msg: ApiResponse,
                             project_id: int):
        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc
        url: str = f"{cms_svc}project/modify/{project_id}"

        cms_request: dict = {
            "name": request_msg.body.name,
            "announcement": request_msg.body.announcement,
            "announcement_on_overview":
                request_msg.body.announcement_on_overview,
        }
        api_response = await self._call_api_post(url, cms_request)

        if api_response.status_code != http.HTTPStatus.OK:
            self._logger.critical("CMS svc /project/modify request invalid"
                                  " - Reason: %s",api_response.exception_msg)
            response_json = {
                "status": 0,
                'error': api_response.body['error_msg']
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        response_json: dict = {"status": 1}
        return quart.Response(json.dumps(response_json),
                              status=http.HTTPStatus.OK,
                              content_type="text/plain")

    async def delete_project(self, project_id: int):
        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc
        url: str = f"{cms_svc}project/delete/{project_id}?hard_delete=true"

        api_response = await self._call_api_delete(url)

        if api_response.status_code == http.HTTPStatus.BAD_REQUEST:
            return quart.Response(json.dumps(api_response.body),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        if api_response.status_code != http.HTTPStatus.OK:
            self._logger.critical(
                "CMS svc %s request invalid - Reason: %s",
                url, api_response.exception_msg)
            response_json = {
                "status": 0,
                'error': 'Internal error!'
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        return quart.Response(json.dumps(api_response.body),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")
