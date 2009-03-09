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

"""This view defines the home / account pages for a user."""

from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from Pootle import indexpage
from pootle_app.profile import get_profile, PootleProfile
from pootle_app.views.util import render_to_kid, KidRequestContext
from pootle_app.views.util import render_jtoolkit
from Pootle.i18n import gettext
from pootle_app.views.auth import redirect

def user_is_authenticated(f):
    def decorated_f(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/login.html', message=_("You need to log in to access your home page"))
        else:
            return f(request, *args, **kwargs)
    return decorated_f

class UserForm(ModelForm):
    password = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class PootleProfileForm(ModelForm):
    class Meta:
        model = PootleProfile
        exclude = ('user', 'activation_code', 'login_type')

@user_is_authenticated
def options(request):
    if request.method == 'POST':
        post = request.POST.copy()
        if 'password' in post and post['password'].strip() != u'':
            request.user.set_password('password')
        del post['password']

        user_form = UserForm(post, instance=request.user)
        profile_form = PootleProfileForm(post, instance=get_profile(request.user))

        user_form.save()
        profile_form.save()
        # Activate the newly selected interface language so that the user will
        # immediately see a translated interface. But only do this if the user
        # selected an interface language.
        if profile_form['ui_lang'].data != '':
            gettext.activate_for_profile(get_profile(request.user))
    elif request.method == 'GET':
        user_form = UserForm(instance=request.user)
        profile_form = PootleProfileForm(instance=get_profile(request.user))

    template_vars = {"pagetitle":      _("Options for: %s") % request.user.username,
                     "introtext":      _("Configure your settings here"),
                     "detailstitle":   _("Personal Details"),
                     "fullname_title": _("Name"),
                     "user_form":      user_form,
                     "profile_form":   profile_form }

    return render_to_kid("options.html", KidRequestContext(request, template_vars))

@user_is_authenticated
def index(request, path):
    return render_jtoolkit(indexpage.UserIndex(request))
