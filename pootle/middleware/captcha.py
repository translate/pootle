# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin

from pootle.core.forms import MathCaptchaForm


URL_RE = re.compile("https?://", re.I)

CAPTCHA_EXEMPT_URLPATTERNS = (
    'account_login',
    'account_signup',
    'account_reset_password',
    'account_reset_password_from_key',
    'pootle-social-verify',
    'pootle-contact',
    'pootle-tp-paths',
    'pootle-project-paths')


class CaptchaMiddleware(MiddlewareMixin):
    """Middleware to display a captcha question to verify POST submissions
    are made by humans.
    """

    def process_request(self, request):
        if (not settings.POOTLE_CAPTCHA_ENABLED or not request.POST or
            request.session.get('ishuman', False)):
            return

        try:
            # No captcha for exempted pages
            resolver_match = resolve(request.path_info)
            if resolver_match.url_name in CAPTCHA_EXEMPT_URLPATTERNS:
                return
        except Http404:
            pass

        if request.user.is_authenticated:
            if ('target_f_0' not in request.POST or
                'translator_comment' not in request.POST):
                return

            # We are in translate page. Users introducing new URLs in the
            # target or comment field are suspect even if authenticated
            try:
                target_urls = len(URL_RE.findall(request.POST['target_f_0']))
            except KeyError:
                target_urls = 0

            try:
                comment_urls = len(URL_RE.findall(
                    request.POST['translator_comment']))
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
