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
from items.services.items_web_portal.metadata_settings import MetadataSettings


@dataclass
class PageHandlerInjections:
    """Provides shared dependencies for page handlers.

    This dataclass acts as a lightweight dependency injection container,
    supplying commonly used services to page handlers. Bundling these
    dependencies together simplifies construction and makes it easier to
    extend the set of injected services in the future.

    Attributes:
        logger: Logger instance used for recording diagnostic and runtime
            information.
        metadata: Application metadata and configuration settings used by
            page handlers.
    """
    logger: logging.Logger
    metadata: MetadataSettings
