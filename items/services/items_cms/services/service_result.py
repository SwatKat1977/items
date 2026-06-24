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
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class ServiceResult:
    """
    Outcome of a service operation.

    Attributes:
        success:     True if the operation completed without error.
        data:        Operation payload on success (project dict, list, or
                     new project ID depending on the operation).
        error_msg:   Human-readable error description when success is False.
        is_internal: True when the failure is a server-side fault (maps to
                     HTTP 500); False when it is a client-side fault.
        not_found:   True when the failure is because the requested resource
                     does not exist (maps to HTTP 404). Only meaningful when
                     success is False and is_internal is False.
    """
    success: bool
    data: Optional[Any] = None
    error_msg: str = ""
    is_internal: bool = False
    not_found: bool = False
