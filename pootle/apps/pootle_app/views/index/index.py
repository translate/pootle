#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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
from django.shortcuts import redirect
from django.views.generic import TemplateView

from pootle.i18n.override import get_lang_from_http_header
from pootle_language.models import Language


COOKIE_NAME = 'pootle-language'


def view(request):
    lang = request.COOKIES.get(COOKIE_NAME, None)

    if lang is None:
        supported = dict(Language.live.cached().values_list('code', 'fullname'))
        lang = get_lang_from_http_header(request, supported)

    if lang is not None and lang not in ('projects', ''):
        url = reverse('pootle-language-overview', args=[lang])
    else:
        url = reverse('pootle-projects-overview')

    # Preserve query strings
    args = request.GET.urlencode()
    qs = '?%s' % args if args else ''
    redirect_url = '%s%s' % (url, qs)

    return redirect(redirect_url)


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        from translate.__version__ import sver as toolkit_version
        from pootle.__version__ import sver as pootle_version

        return {
            'pootle_version': pootle_version,
            'toolkit_version': toolkit_version,
        }
