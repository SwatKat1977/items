"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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
from weaver_framework.microservice.base_api_route import BaseApiRoute
from items.shared.api_signature import (generate_api_signature,
                                        verify_api_signature)
from items.services.items_gateway.metadata_handler import MetadataHandler
from items.services.items_gateway.gateway_configuration import GatewayConfiguration


class GetMetadataHandler(BaseApiRoute):

    def __init__(self,
                 logger: logging.Logger,
                 config: GatewayConfiguration,
                 metadata_handler: MetadataHandler) -> None:
        self._logger = logger.getChild(type(self).__name__)
        self._config: GatewayConfiguration = config
        self._metadata_handler: MetadataHandler = metadata_handler

    async def get_metadata(self):
        nonce = quart.request.args.get("nonce")
        request_path: str = quart.request.path

        if not nonce:
            return quart.Response(json.dumps({"error": "Nonce value required"}),
                                  status=http.HTTPStatus.UNAUTHORIZED,
                                  content_type="application/json")

        # Get signature from headers
        received_signature: str = quart.request.headers.get("X-Signature")
        if not received_signature:
            return quart.Response(json.dumps({"error": "Unsigned"}),
                                  status=http.HTTPStatus.UNAUTHORIZED,
                                  content_type="application/json")

        string_to_sign: bytes = f"{request_path}:{nonce}".encode()
        secret_key: str = self._config.general_api_signing_secret

        # Verify signature
        if not verify_api_signature(secret_key.encode(),
                                    string_to_sign,
                                    received_signature):
            return quart.Response(json.dumps({"error": "Invalid signature"}),
                                  status=http.HTTPStatus.UNAUTHORIZED,
                                  content_type="application/json")

        metadata = self._metadata_handler.build_metadata_dictionary()

        signature: str = generate_api_signature(secret_key.encode(),
                                                metadata)
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature
        }
        return quart.Response(json.dumps(metadata),
                              status=http.HTTPStatus.OK,
                              headers=headers,
                              content_type="application/json")
