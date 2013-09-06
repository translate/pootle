#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
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

import os

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.utils.http import urlencode


def l(path):
    """Filter URLs adding base_path prefix if required."""
    if path and path.startswith('/'):
        base_url = getattr(settings, "SCRIPT_NAME", "")
        return base_url + path
    return path


def abs_l(path):
    """Filter paths adding full URL prefix if required."""
    return settings.BASE_URL + path


def m(path):
    """Filter URLs adding MEDIA_URL prefix if required."""
    return l(settings.MEDIA_URL + path)


def s(path):
    """Filter URLs adding STATIC_URL prefix."""
    return settings.STATIC_URL + path


def redirect(url, **kwargs):
    if os.name == 'nt':
        # A catch-all to fix any issues on Windows
        url = url.replace("\\", "/")
    if len(kwargs) > 0:
        return HttpResponseRedirect(l('%s?%s' % (url, urlencode(kwargs))))
    else:
        return HttpResponseRedirect(l(url))


def get_next(request):
    """Return a query string to use as a next URL."""
    try:
        next = request.GET.get(REDIRECT_FIELD_NAME, '')
        if not next:
            next = request.path_info
    except AttributeError as e:
        next = ''

    return u"?%s" % urlencode({REDIRECT_FIELD_NAME: next})
