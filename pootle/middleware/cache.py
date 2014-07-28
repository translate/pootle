#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

from django.utils.cache import add_never_cache_headers


class CacheAnonymousOnly(object):
    """Imitate the deprecated `CACHE_MIDDLEWARE_ANONYMOUS_ONLY` behavior."""

    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated():
            add_never_cache_headers(response)

        return response
