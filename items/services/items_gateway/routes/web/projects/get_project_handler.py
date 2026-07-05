"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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


class ProjectsApiView(BaseView):
    __slots__ = ['_logger']

    async def retrieve_a_project(self, project_id: int):
        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc
        url: str = f"{cms_svc}projects/{project_id}"

        api_response = await self._call_api_get(url)

        if api_response.status_code == http.HTTPStatus.BAD_REQUEST:
            response_json = {
                "status": 0,
                'error': 'Invalid project ID'
            }
            return quart.Response(json.dumps(response_json),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        if api_response.status_code != http.HTTPStatus.OK:
            self._logger.critical("CMS SVC /projects/details request invalid"
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
