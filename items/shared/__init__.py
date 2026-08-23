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
MINOR = 3
PATCH = 0

# e.g. "alpha", "beta", "rc1", or None
PRE_RELEASE = None

# Version tuple for comparisons
VERSION = (MAJOR, MINOR, PATCH, PRE_RELEASE)


def _build_version_string(major: int, minor: int, patch: int,
                          pre_release: str | None) -> str:
    """Build the ``__version__`` string from its components.

    Pulled out as its own function - rather than the equivalent
    module-level ``if PRE_RELEASE: ...`` - specifically so both branches
    are actually testable. A module-level conditional on a constant only
    ever exercises whichever branch that constant currently takes; the
    other is permanently uncovered regardless of how thorough the rest of
    the test suite is, and which branch that is flips every time
    ``PRE_RELEASE`` changes (e.g. cleared to ``None`` for a real release).

    Args:
        major: Major version component.
        minor: Minor version component.
        patch: Patch version component.
        pre_release: Pre-release label (e.g. ``"alpha"``, ``"rc1"``), or
            ``None``/empty for a final release.

    Returns:
        ``"V{major}.{minor}.{patch}"``, with ``"-{pre_release}"``
        appended if one is set.
    """
    version = f"V{major}.{minor}.{patch}"
    if pre_release:
        version += f"-{pre_release}"
    return version


# Construct the string representation
__version__ = _build_version_string(MAJOR, MINOR, PATCH, PRE_RELEASE)

SERVICE_COPYRIGHT_TEXT = "Copyright 2025-2026 Integrated Test Management " + \
                         'Suite development team'

LICENSE_TEXT = "Licensed under the Apache License, Version 2.0"
