#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

from django.conf import settings


class BaseUrlMiddleware(object):
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

            #FIXME: DIRTY HACK ALERT if this works then something is
            #wrong with the universe
            # poison sites cache using detected domain
            from django.contrib.sites import models as sites_models

            new_site = sites_models.Site(settings.SITE_ID, request.get_host(),
                                         settings.TITLE)
            sites_models.SITE_CACHE[settings.SITE_ID] = new_site
