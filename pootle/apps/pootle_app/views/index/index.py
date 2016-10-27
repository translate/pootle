# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import TemplateView

from pootle.i18n.override import get_lang_from_http_header
from pootle_language.models import Language


COOKIE_NAME = 'pootle-language'


def view(request):
    if not request.user.is_authenticated:
        ctx = {
            'next': request.GET.get(REDIRECT_FIELD_NAME, ''),
        }
        return render(request, 'welcome.html', ctx)

    lang = request.COOKIES.get(COOKIE_NAME, None)

    if lang is None:
        supported = Language.live.cached_dict(
            show_all=request.user.is_superuser
        )
        lang = get_lang_from_http_header(request, supported)

    if lang is not None and lang not in ('projects', ''):
        url = reverse('pootle-language-browse', args=[lang])
    else:
        url = reverse('pootle-projects-browse')

    # Preserve query strings
    args = request.GET.urlencode()
    qs = '?%s' % args if args else ''
    redirect_url = '%s%s' % (url, qs)

    return redirect(redirect_url)


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        from translate.__version__ import sver as toolkit_version
        from pootle import __version__

        return {
            'pootle_version': __version__,
            'toolkit_version': toolkit_version,
        }
