#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from django import forms
from django.utils.translation import ugettext as _

from waffle.models import Flag

from pootle_app.views.admin import util


@util.user_is_admin
def view(request):
    """Edit feature flags.

    This view is intended to allow tying users to the existing flags, allowing
    them to use the features enabled by this flags. Flags are hardcoded, but if
    it is necessary to edit them beyond changing the users the flags are tied
    to, it is possible to alter them through the Django admin site.
    """

    class FeatureFlagForm(forms.ModelForm):
        # We don't want to show the 'superusers' field, but is necessary for
        # overriding its default value.
        superusers = forms.BooleanField(initial=False, required=False,
            widget=forms.HiddenInput()
        )

        class Meta:
            model = Flag
            widgets = {
                'name': forms.TextInput(attrs={
                    'class': 'feature-non-editable',
                    'readonly': True,
                }),
                'users': forms.SelectMultiple(attrs={
                    'class': 'js-select2 select2-multiple',
                    'data-placeholder': _('Select one or more users'),
                }),
                'note': forms.TextInput(attrs={
                    'size': 60,
                    'class': 'feature-non-editable',
                    'readonly': True,
                }),
            }

    fields = ('name', 'superusers', 'users', 'note')
    queryset = Flag.objects.order_by('-id')

    return util.edit(request, 'admin/admin_general_features.html', Flag,
                     form=FeatureFlagForm, fields=fields, queryset=queryset,
                     can_delete=True, extra=0)
