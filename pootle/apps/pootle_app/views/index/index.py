#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from pootle.i18n.override import get_lang_from_http_header
from pootle_language.models import Language


COOKIE_NAME = 'pootle-language'


def view(request):
    lang = request.COOKIES.get(COOKIE_NAME, None)
    set_cookie = False

    if lang is None:
        set_cookie = True
        supported = dict(Language.live.cached().values_list('code', 'fullname'))
        lang = get_lang_from_http_header(request, supported)

    if lang is not None and lang not in ('projects', ''):
        url = reverse('pootle-language-overview', args=[lang])
    else:
        url = reverse('pootle-project-list')

    # Preserve query strings
    args = request.GET.urlencode()
    qs = '?%s' % args if args else ''
    redirect_url = '%s%s' % (url, qs)
    response = HttpResponseRedirect(redirect_url)

    if set_cookie:
        response.set_cookie(COOKIE_NAME,
                            lang if lang is not None else 'projects')

    return response
