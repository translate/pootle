#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012, 2013 Zuza Software Foundation
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

from django import forms
from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from .models import PootleProfile


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


def pootle_profile_form_factory(exclude_fields):

    class PootleProfileForm(forms.ModelForm):

        class Meta:
            model = PootleProfile

        def __init__(self, *args, **kwargs):
            self.exclude_fields = exclude_fields
            super(PootleProfileForm, self).__init__(*args, **kwargs)

            # Delete the fields the user can't edit.
            for field in self.exclude_fields:
                del self.fields[field]
            self.fields['alt_src_langs'].widget.attrs['class'] = \
                "js-select2 select2-multiple"
            self.fields['alt_src_langs'].widget.attrs['data-placeholder'] = \
                _('Select one or more languages')

    return PootleProfileForm
