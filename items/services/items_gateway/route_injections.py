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
from dataclasses import dataclass
import logging
from weaver_framework.microservice.rest_client import RestClient
from items.services.items_gateway.metadata_handler import MetadataHandler
from items.services.items_gateway.gateway_configuration import GatewayConfiguration
from items.services.items_gateway.sessions import Sessions
from items.services.items_gateway.services.email_service import EmailService


@dataclass(frozen=True)
class RouteInjections:
    """Container for dependencies required by HTTP route registration.

    This immutable dataclass groups together the shared services and
    application components that are injected into route factories and request
    handlers. Providing dependencies through a single object simplifies route
    construction and testing.

    Attributes:
        logger: Logger used for diagnostic and operational logging.
        sessions: Session manager for authenticated user sessions.
        configuration: Gateway application configuration.
        rest_client: REST client used to communicate with external services.
        metadata_handler: Handler responsible for generating webhook metadata.
        email_service: Email service for sending transactional notifications.
    """
    logger: logging.Logger | None = None
    sessions: Sessions | None = None
    configuration: GatewayConfiguration | None = None
    rest_client: RestClient | None = None
    metadata_handler: MetadataHandler | None = None
    email_service: EmailService | None = None
