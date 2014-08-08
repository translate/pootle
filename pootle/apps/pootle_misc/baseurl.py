#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Utility functions to help deploy Pootle under different url prefixes."""

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.http import urlencode


def l(path):
    """Filter URLs adding base_path prefix if required."""
    if path and path.startswith('/'):
        base_url = getattr(settings, "SCRIPT_NAME", "")
        return base_url + path
    return path


def get_next(request):
    """Return a query string to use as a next URL."""
    try:
        next = request.GET.get(REDIRECT_FIELD_NAME, '')

        if not next:
            next = request.path_info
    except AttributeError:
        next = ''

    return u"?%s" % urlencode({REDIRECT_FIELD_NAME: next})
