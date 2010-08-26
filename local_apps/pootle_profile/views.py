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

from django import forms
from django.utils.translation import ugettext as _
from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from pootle.i18n.override import lang_choices

from pootle_misc.baseurl import redirect


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

@login_required
def edit_personal_info(request):
    if request.POST:
        post = request.POST.copy()
        user_form = UserForm(post, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            response = redirect('/accounts/'+request.user.username)
    else:
        user_form = UserForm(instance=request.user)
    template_vars = { "form": user_form }
    response = render_to_response('profiles/edit_personal.html', template_vars, context_instance=RequestContext(request))
    return response


def redirect_after_login(request):
    redirect_to = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, None)
    if not redirect_to or '://' in redirect_to or ' ' in redirect_to:
        redirect_to = iri_to_uri('/accounts/%s/' % urlquote(request.user.username))
    return redirect(redirect_to)

def language_list(request):
    """returns the list of localised language names, with 'default'"""
    tr_default = _("Default")
    if tr_default != "Default":
        tr_default = u"%s | \u202dDefault" % tr_default
    choices = lang_choices()
    choices.insert(0, ('', tr_default))
    return choices


def login(request):
    class LangAuthenticationForm(AuthenticationForm):
        language = forms.ChoiceField(label=_('Interface Language'), choices=language_list(request),
                                     initial="", required=False)

    if request.user.is_authenticated():
        return redirect_after_login(request)
    else:
        if request.POST:
            form = LangAuthenticationForm(request, data=request.POST)
            # do login here
            if form.is_valid():
                auth.login(request, form.get_user())

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()
                language = request.POST.get('language')
                request.session['django_language'] = language
                response = redirect_after_login(request)
                return response
        else:
            form = LangAuthenticationForm(request)
        request.session.set_test_cookie()
        context = {
            'form': form,
            }
        return render_to_response("index/login.html", context, context_instance=RequestContext(request))


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')
