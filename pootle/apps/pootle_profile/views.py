# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib import auth
from django.utils.translation import get_language
from django.views.generic import DetailView, UpdateView

from pootle.core.delegate import profile
from pootle.core.views import APIView
from pootle.core.views.mixins import (NoDefaultUserMixin, TestUserFieldMixin,
                                      UserObjectMixin)
from pootle.i18n.gettext import ugettext_lazy as _

from .forms import EditUserForm


User = auth.get_user_model()


class UserAPIView(TestUserFieldMixin, APIView):
    model = User
    restrict_to_methods = ('GET', 'PUT')
    test_user_field = 'id'
    edit_form_class = EditUserForm


class UserDetailView(NoDefaultUserMixin, UserObjectMixin, DetailView):
    template_name = 'user/profile.html'

    @property
    def request_lang(self):
        return get_language()

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        context["profile"] = profile.get(self.object.__class__)(self.object)
        return context


class UserSettingsView(TestUserFieldMixin, UserObjectMixin, UpdateView):
    fields = ('unit_rows', 'alt_src_langs')
    template_name = 'user/settings.html'

    def get_form_kwargs(self):
        kwargs = super(UserSettingsView, self).get_form_kwargs()
        kwargs.update({'label_suffix': ''})
        return kwargs

    def get_form(self, *args, **kwargs):
        form = super(UserSettingsView, self).get_form(*args, **kwargs)

        form.fields['alt_src_langs'].help_text = None
        form.fields['alt_src_langs'].widget.attrs['class'] = \
            'js-select2 select2-multiple'
        form.fields['alt_src_langs'].widget.attrs['data-placeholder'] = \
            _('Select one or more languages')

        return form
