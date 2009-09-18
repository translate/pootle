#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

import locale

from translate.lang import data

from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle.i18n.user_lang_discovery import get_language_from_request
from pootle.i18n.gettext import tr_lang
from pootle_app.models import Language
from pootle_misc.baseurl import redirect
from pootle_app.views               import pagelayout


def view(request):
    message = None
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')

    if request.user.is_authenticated():
        return redirect(redirect_to)
    else:
        if request.POST:
            form = AuthenticationForm(request, data=request.POST)
            # do login here
            if form.is_valid():
                from django.contrib.auth import login
                login(request, form.get_user())

                if not redirect_to or '://' in redirect_to or ' ' in redirect_to:
                    redirect_to = '/accounts/'+form.get_user().username + '/'

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                language = request.POST.get('language') # FIXME: validation missing
                response = redirect(redirect_to)
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
                return response
        else:
            form = AuthenticationForm(request)
        request.session.set_test_cookie()
        context = {
            'pagetitle': _('%(title)s: Login',
                           {"title": pagelayout.get_title()}),
            'languages': language_list(request),
            'form': form
            }
        return render_to_response("index/login.html", context, context_instance=RequestContext(request))
    

def language_list(request):
    """returns the list of localised language names, with 'default'"""
    tr_default = _("Default")
    if tr_default != "Default":
        tr_default = u"%s | \u202dDefault" % tr_default
    request_code = data.normalize_code(get_language_from_request(request).language.code)
    if request_code in ["en", "en-us", settings.LANGUAGE_CODE]:
        preferred_language = ""
    else:
        preferred_language = request_code
    finallist = [{"code": '', "name": tr_default, "selected": is_selected("", preferred_language)}]
    for language in Language.objects.all():
        code = language.code
        name = language.fullname
        tr_name = tr_lang(request, name)
        if tr_name != name:
            # We have to use the LRO (left-to-right override) to ensure that 
            # brackets in the English part of the name is rendered correctly
            # in an RTL layout like Arabic. We can't use markup because this 
            # is used inside an option tag.
            name = u"%s | \u202d%s" % (tr_name, name)
        finallist.append({"code": code, "name": name, "selected": is_selected(language.code, preferred_language)})
    finallist.sort(cmp=locale.strcoll, key=lambda dict: unicode(dict["name"]))
    return finallist

def is_selected(new_code, preferred_language):
    if data.normalize_code(new_code) == preferred_language:
        return "selected"
    return None
