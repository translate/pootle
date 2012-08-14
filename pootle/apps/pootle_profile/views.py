#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
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

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote

from profiles.views import edit_profile

from pootle_app.models import Directory
from pootle_app.models.permissions import check_profile_permission
from pootle_misc.baseurl import redirect
from pootle_profile.models import get_profile
from pootle_profile.forms import (LangAuthenticationForm, PootleProfileForm,
                                  UserForm)


def profile_edit(request):
    can_view = check_profile_permission(get_profile(request.user), "view",
                                        Directory.objects.root)

    if can_view:
        excluded = ('user',)
    else:
        excluded = ('user', 'projects')

    return edit_profile(request, form_class=PootleProfileForm,
                        extra_form_args={'exclude_fields': excluded})


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

    template_vars = {"form": user_form}

    return render_to_response('profiles/edit_personal.html', template_vars,
                              context_instance=RequestContext(request))


def redirect_after_login(request):
    redirect_to = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, None)

    if not redirect_to or '://' in redirect_to or ' ' in redirect_to:
        redirect_to = iri_to_uri('/accounts/%s/' % \
                                 urlquote(request.user.username))

    return redirect(redirect_to)


def login(request):
    """Logs the user in."""
    if request.user.is_authenticated():
        return redirect_after_login(request)
    else:
        if request.POST:
            form = LangAuthenticationForm(data=request.POST)

            # Do login here
            if form.is_valid():
                auth.login(request, form.get_user())

                language = request.POST.get('language')
                request.session['django_language'] = language
                response = redirect_after_login(request)

                return response
        else:
            form = LangAuthenticationForm()

        context = {
            'form': form,
            }

        return render_to_response("index/login.html", context,
                                  context_instance=RequestContext(request))


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')
