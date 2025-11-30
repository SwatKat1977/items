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
    """
    View responsible for handling webhook callbacks from external services.

    This class exposes endpoints intended to be invoked programmatically,
    typically by other internal microservices. It currently supports updating
    runtime instance metadata based on validated webhook payloads.

    The view uses:
        - `validate_json` to enforce schema validation for incoming webhook
          JSON bodies.
        - `MetadataSettings` to apply updates that affect the running
          configuration.
        - `BaseView` for consistent logging and API response formatting.

    Attributes:
        _logger (logging.Logger):
            Logger instance dedicated to this view.
        _metadata (MetadataSettings):
            Metadata configuration object that stores instance-level runtime
            settings such as instance name and timezone behaviour.
    """

    def __init__(self, logger: logging.Logger,
                 metadata: MetadataSettings):
        """
        Initialize a new WebhookApiView.

        Args:
            logger (logging.Logger):
                Logger from the application’s logging hierarchy. A child logger
                scoped to this view will be created.
            metadata (MetadataSettings):
                Shared metadata object that will be modified when webhook
                events request metadata updates.
        """
        self._logger = logger.getChild(__name__)
        self._metadata: MetadataSettings = metadata

    @validate_json(json_schemas.SCHEMA_UPDATE_METADATA_REQUEST)
    async def update_metadata(self, request_msg: ApiResponse):
        """
        Update instance metadata based on a validated webhook message.

        This endpoint receives a JSON body containing updates for:
            - `default_time_zone`
            - `using_server_default_time_zone`
            - `instance_name`

        After schema validation (handled by `validate_json`), the method
        applies the updates directly to the shared `MetadataSettings`
        instance. No additional processing or transformation is performed.

        Args:
            request_msg (ApiResponse):
                Parsed and validated request envelope containing a `body`
                attribute that maps directly to the metadata schema.

        Returns:
            quart.Response:
                A simple HTTP 200 OK plain-text acknowledgment indicating that
                the metadata update was applied successfully.
        """
        body = request_msg.body

        self._metadata.default_time_zone = body.default_time_zone
        self._metadata.using_server_default_time_zone = body.using_server_default_time_zone
        self._metadata.instance_name = body.instance_name

        return quart.Response("OK",
                              status=http.HTTPStatus.OK,
                              content_type="text/plain")
