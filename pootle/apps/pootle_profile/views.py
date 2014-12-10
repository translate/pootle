#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.utils.encoding import iri_to_uri
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, UpdateView

from pootle.core.views import (APIView, LoginRequiredMixin,
                               NoDefaultUserMixin, TestUserFieldMixin)

from .forms import EditUserForm


User = auth.get_user_model()


class UserAPIView(TestUserFieldMixin, APIView):
    model = User
    restrict_to_methods = ('GET', 'PUT')
    test_user_field = 'id'
    edit_form_class = EditUserForm


class UserDetailView(NoDefaultUserMixin, DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'user/profile.html'


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super(UserUpdateView, self).get_form_kwargs()
        kwargs.update({'label_suffix': ''})
        return kwargs


class UserSettingsView(UserUpdateView):
    fields = ('unit_rows', 'alt_src_langs')
    template_name = 'profiles/settings/profile.html'

    def get_form(self, *args, **kwargs):
        form = super(UserSettingsView, self).get_form(*args, **kwargs)

        form.fields['alt_src_langs'].widget.attrs['class'] = \
            'js-select2 select2-multiple'
        form.fields['alt_src_langs'].widget.attrs['data-placeholder'] = \
            _('Select one or more languages')

        return form


def redirect_after_login(request, redirect_to=None):
    if redirect_to is None:
        redirect_to = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, '')

    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = iri_to_uri(reverse('pootle-user-profile',
                                 args=[request.user.username]))

    return redirect(redirect_to)


def login(request, template_name='login.html'):
    """Log the user in."""
    if request.user.is_authenticated():
        return redirect_after_login(request)

    if request.POST:
        form = AuthenticationForm(request, data=request.POST)
        next = request.POST.get(auth.REDIRECT_FIELD_NAME, '')

        # Do login here.
        if form.is_valid():
            auth.login(request, form.get_user())
            return redirect_after_login(request)
    else:
        form = AuthenticationForm(request)
        next = request.GET.get(auth.REDIRECT_FIELD_NAME, '')

    ctx = {
        'form': form,
        'next': next,
    }

    return render(request, template_name, ctx)
