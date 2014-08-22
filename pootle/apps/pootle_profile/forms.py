#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

import urlparse

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _


class EditUserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('full_name', 'twitter', 'linkedin', 'website', 'bio')

    def clean_linkedin(self):
        url = self.cleaned_data['linkedin']
        if url != '':
            parsed = urlparse.urlparse(url)
            if 'linkedin.com' not in parsed.netloc or parsed.path == '/':
                raise forms.ValidationError(
                    _('Please enter a valid LinkedIn user profile URL.')
                )

        return url
