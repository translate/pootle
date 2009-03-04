#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import locale
import urllib

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.conf import settings
from django.http import HttpResponseRedirect

from pootle_app.views.util import render_to_kid, KidRequestContext
from pootle_app import project_tree
from pootle_app.core import Language

from Pootle import pan_app
from Pootle.pagelayout import completetemplatevars
from Pootle.i18n.jtoolkit_i18n import localize, tr_lang
from Pootle.i18n.user_lang_discovery import get_language_from_request

def login(request):
    message = None
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')
    if not redirect_to or '://' in redirect_to or ' ' in redirect_to:
        redirect_to = '/home/'

    if request.user.is_authenticated():
        return HttpResponseRedirect(redirect_to)
    else:
        if request.POST:
            form = AuthenticationForm(request, data=request.POST)
            # do login here
            if form.is_valid():
                from django.contrib.auth import login
                login(request, form.get_user())
                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                language = request.POST.get('language') # FIXME: validation missing
                response = HttpResponseRedirect(redirect_to)
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
                return response
        else:
            form = AuthenticationForm(request)
        request.session.set_test_cookie()
        context = {
            'languages': [{'name': tr_lang(language.fullname),
                           'code': language.code,
                           'selected': is_selected(request, language.code)}
                          for language in Language.objects.all()],
            'form': form,
            }
        context["languages"].sort(cmp=locale.strcoll, key=lambda dict: dict["name"])

        # kid template compatibility
        context.update({
            'pagetitle': localize("Login to Pootle"),
            'introtext': None,
            'login_title': localize("Pootle Login"),
            'language_title': localize('Language'),
            'password_title': localize("Password"),
            'register_long_text': localize("Don't have an account yet? <a href='register.html' title='Register'>Register</a>.")
            })

        return render_to_kid("login.html", KidRequestContext(request, context))
        #return render_to_response("login.html", RequestContext(request, context))

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/')

def redirect(url, **kwargs):
    if len(kwargs) > 0:
        return HttpResponseRedirect('%s?%s' % (url, urllib.urlencode(kwargs)))
    else:
        return HttpResponseRedirect(url)

def is_selected(request, new_code):
    code = get_language_from_request(request).language.code
    if code == new_code:
        return "selected"
    return None

