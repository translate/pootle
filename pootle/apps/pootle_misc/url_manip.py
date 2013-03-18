#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
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

import urlparse

from django.core.urlresolvers import Resolver404, resolve


def ensure_uri(uri):
    """Ensure that we return a URI that the user can click on in an a tag."""
    if not uri:
        return uri
    scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
    if scheme:
        return uri

    if u'@' in uri:
        uri = u"mailto:%s" % uri
    else:
        # If we don't supply a protocol, browsers will interpret it as a
        # relative URL, like
        # http://pootle.locamotion.org/af/pootle/bugs.locamotion.org
        # So let's assume http
        uri = u"http://" + uri
    return uri


def previous_view_url(request, view_names):
    """Returns the previous request URL if it matches certain view(s).

    :param request: Django's request object.
    :param view_names: List of view names to look for.
    """
    referer_url = request.META.get('HTTP_REFERER', '')
    script_name = request.META.get('SCRIPT_NAME', '/')

    view_path = urlparse.urlparse(referer_url)[2]
    if script_name != '/':
        try:
            index = view_path.index(script_name)
            # Just in case check if it matches at the beginning
            if index == 0:
                view_path = view_path[len(script_name):]
        except (ValueError, IndexError):
            pass

    try:
        view, args, kwargs = resolve(view_path)
    except Resolver404:
        return ''

    if view.__name__ in view_names:
        return referer_url

    return ''
