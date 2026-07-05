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
from base_view import BaseView
from threadsafe_configuration import ThreadSafeConfiguration


class TestcaseCustomFieldsApiView(BaseView):

    def __init__(self, logger : logging.Logger) -> None:
        self._logger = logger.getChild(__name__)

    async def get_all_custom_fields(self):

        cms_svc: str = ThreadSafeConfiguration().apis_cms_svc
        url: str = f"{cms_svc}admin/testcase_custom_fields/" \
                   f"testcase_custom_fields"

        api_response = await self._call_api_get(url)

        return quart.Response(json.dumps(api_response.body),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")
