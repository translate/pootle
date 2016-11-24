# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin


class CacheAnonymousOnly(MiddlewareMixin):
    """Imitate the deprecated `CACHE_MIDDLEWARE_ANONYMOUS_ONLY` behavior."""

    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            add_never_cache_headers(response)

        return response
