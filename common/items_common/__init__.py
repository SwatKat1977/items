"""
Copyright (C) 2025  Integrated Test Management Suite Development Team
SPDX-License-Identifier: AGPL-3.0-or-later

This file is part of Integrated Test Management Suite. See the LICENSE
file in the project root for full license details.
"""

# Semantic version components
MAJOR = 0
MINOR = 0
PATCH = 0

# e.g. "alpha", "beta", "rc1", or None
PRE_RELEASE = "MVP #1"

# Version tuple for comparisons
VERSION = (MAJOR, MINOR, PATCH, PRE_RELEASE)

# Construct the string representation
__version__ = f"V{MAJOR}.{MINOR}.{PATCH}"

if PRE_RELEASE:
    __version__ += f"-{PRE_RELEASE}"

SERVICE_COPYRIGHT_TEXT = 'Copyright 2025 Integrated Test Management ' + \
                         'Suite development team'

LICENSE_TEXT = 'Licensed under the Apache License, Version 2.0'
