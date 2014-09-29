#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Zuza Software Foundation
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

import re

from django.conf import settings
from django.core.urlresolvers import resolve
from django.http import Http404
from django.shortcuts import render

from pootle.core.forms import MathCaptchaForm


URL_RE = re.compile("https?://", re.I)

CAPTCHA_EXEMPT_URLPATTERNS = (
    'account_login', 'pootle-contact',
)


class CaptchaMiddleware:
    """Middleware to display a captcha question to verify POST submissions
    are made by humans.
    """
    def process_request(self, request):
        if (not settings.USE_CAPTCHA or not request.POST or
            request.path.startswith('/api/') or
            request.session.get('ishuman', False)):
            return

        try:
            # No captcha for exempted pages
            resolver_match = resolve(request.path_info)
            if resolver_match.url_name in CAPTCHA_EXEMPT_URLPATTERNS:
                return
        except Http404:
            pass

        if request.user.is_authenticated():
            if ('target_f_0' not in request.POST or
                'translator_comment' not in request.POST or
                ('submit' not in request.POST and
                 'suggest' not in request.POST)):
                return

            # We are in translate page. Users introducing new URLs in the
            # target or comment field are suspect even if authenticated
            try:
                target_urls = len(URL_RE.findall(request.POST['target_f_0']))
            except KeyError:
                target_urls = 0

            try:
                comment_urls = len(URL_RE.findall(request.POST['translator_comment']))
            except KeyError:
                comment_urls = 0

            try:
                source_urls = len(URL_RE.findall(request.POST['source_f_0']))
            except KeyError:
                source_urls = 0

            if (comment_urls == 0 and
                (target_urls == 0 or target_urls == source_urls)):
                return

        if 'captcha_answer' in request.POST:
            form = MathCaptchaForm(request.POST)
            if form.is_valid():
                request.session['ishuman'] = True
                return
            else:
                # new question
                form.reset_captcha()

        else:
            form = MathCaptchaForm()

        template_name = 'core/captcha.html'
        ctx = {
            'form': form,
            'url': request.path,
            'post_data': request.POST,
        }

        if (request.is_ajax() and ('sfn' in request.POST and
                                   'efn' in request.POST)):
            template_name = 'core/xhr_captcha.html'

        response = render(request, template_name, ctx)
        response.status_code = 402  # (Ab)using 402 for captcha purposes.
        return response
