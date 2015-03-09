#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib import auth
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
