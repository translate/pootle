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


from django.utils.cache import patch_vary_headers
from Pootle.i18n import gettext, user_lang_discovery

class LocaleMiddleware(object):
    """
    When a request comes in, discover the language to use for the
    UI. This request returns a Pootle project object (which contains
    methods for doing the UI translations). The active method in the
    gettext module associates the project object with the thread in
    which we are running.

    When the request is done, make sure that the Content-Language HTTP
    header matches the language in the project object. After that,
    break the association between the thread in which we are running
    and the project object (so that the same thread can serve another
    HTTP request which will cause it to be associated with a possibly
    different project object).
    """

    def process_request(self, request):
        gettext.activate(user_lang_discovery.get_language_from_request(request))

    def process_response(self, request, response):
        patch_vary_headers(response, ('Accept-Language',))
        if 'Content-Language' not in response:
            response['Content-Language'] = gettext.get_active().language.code
        gettext.deactivate()
        return response
