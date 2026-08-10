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

# Semantic version components
MAJOR = 0
MINOR = 1
PATCH = 0

# e.g. "alpha", "beta", "rc1", or None
PRE_RELEASE = "Alpha Build 8"

# Version tuple for comparisons
VERSION = (MAJOR, MINOR, PATCH, PRE_RELEASE)

# Construct the string representation
__version__ = f"V{MAJOR}.{MINOR}.{PATCH}"

if PRE_RELEASE:
    __version__ += f"-{PRE_RELEASE}"

SERVICE_COPYRIGHT_TEXT = "Copyright 2025-2026 Integrated Test Management " + \
                         'Suite development team'

LICENSE_TEXT = "Licensed under the Apache License, Version 2.0"
