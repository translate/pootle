#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, UpdateView


User = get_user_model()


class LoginRequiredMixin(object):
    """Require a logged-in user."""
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = "account/user_form.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super(UserUpdateView, self).get_form_kwargs()
        kwargs.update({'label_suffix': ''})
        return kwargs


class UserSettingsView(UserUpdateView):
    fields = ('_unit_rows', 'alt_src_langs')
    template_name = 'profiles/settings/profile.html'

    def get_form(self, *args, **kwargs):
        form = super(UserSettingsView, self).get_form(*args, **kwargs)

        form.fields['alt_src_langs'].widget.attrs['class'] = \
            'js-select2 select2-multiple'
        form.fields['alt_src_langs'].widget.attrs['data-placeholder'] = \
            _('Select one or more languages')

        return form

edit_profile = UserSettingsView.as_view()


class UserProfileView(UserUpdateView):
    fields = ("full_name", "email")
    template_name = "profiles/settings/personal.html"

edit_personal_info = UserUpdateView.as_view()


class UserDetailView(TemplateView):
    template_name = "profiles/profile_detail.html"

    def get_context_data(self, **kwargs):
        user = User.objects.get(username=kwargs["username"])

        return {
            "profile": user,
        }

user_detail = UserDetailView.as_view()
