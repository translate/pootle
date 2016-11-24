# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class BaseUrlMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """calculate settings.BASEURL based on HTTP headers"""
        domain = None

        if 'HTTP_HOST' in request.META:
            domain = request.get_host()

        if 'SCRIPT_NAME' in request.META:
            settings.SCRIPT_NAME = request.META['SCRIPT_NAME']
            if domain is not None:
                domain += request.META['SCRIPT_NAME']

        if domain is not None:
            if request.is_secure():
                settings.BASE_URL = 'https://' + domain
            else:
                settings.BASE_URL = 'http://' + domain

            # FIXME: DIRTY HACK ALERT if this works then something is wrong
            # with the universe poison sites cache using detected domain
            from django.contrib.sites import models as sites_models

            new_site = sites_models.Site(settings.SITE_ID, request.get_host(),
                                         settings.POOTLE_TITLE)
            sites_models.SITE_CACHE[settings.SITE_ID] = new_site
