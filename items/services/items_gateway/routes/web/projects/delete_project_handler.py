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

class AddProjectHandler(BaseApiRoute):
    """Handles POST /projects requests."""

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 rest_client: RestClient) -> None:
        """Initialise the handler.

        Args:
            logger:  Parent logger instance.
        """
        self._logger = logger.getChild(type(self).__name__)
        self._config: GatewayConfiguration = config
        self._rest_client: RestClient = rest_client

    async def delete_project(self, project_id: int):
        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc
        url: str = f"{cms_svc}projects/delete/{project_id}?hard_delete=true"

        api_response = await self._call_api_delete(url)

        if api_response.status_code == http.HTTPStatus.BAD_REQUEST:
            return quart.Response(json.dumps(api_response.body),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        if api_response.status_code != http.HTTPStatus.OK:
            self._logger.critical(
                "CMS SVC %s request invalid - Reason: %s",
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
