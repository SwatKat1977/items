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
import logging
import quart
from base_view import ApiResponse, BaseView, validate_json
import interfaces.gateway.metadata  as json_schemas
from metadata_settings import MetadataSettings


class WebhookApiView(BaseView):

    def __init__(self, logger: logging.Logger,
                 metadata: MetadataSettings):
        self._logger = logger.getChild(__name__)
        self._metadata: MetadataSettings = metadata

    @validate_json(json_schemas.SCHEMA_UPDATE_METADATA_REQUEST)
    async def update_metadata(self, request_msg: ApiResponse):
        body = request_msg.body

        self._metadata.default_time_zone = body.default_time_zone
        self._metadata.using_server_default_time_zone = body.using_server_default_time_zone
        self._metadata.instance_name = body.instance_name

        return quart.Response("OK",
                              status=http.HTTPStatus.OK,
                              content_type="text/plain")
