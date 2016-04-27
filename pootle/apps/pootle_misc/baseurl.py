# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Utility functions to help deploy Pootle under different url prefixes."""

from django.conf import settings


def l(path):
    """Filter URLs adding base_path prefix if required."""
    if path and path.startswith('/'):
        base_url = getattr(settings, "SCRIPT_NAME", "")
        return base_url + path
    return path
