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
        fields = ('full_name', 'email', 'twitter', 'linkedin', 'website', 'bio')

    def __init__(self, *args, **kwargs):
        kwargs.update({'label_suffix': ''})

        super(EditUserForm, self).__init__(*args, **kwargs)

        twitter_ph = _('Your Twitter username')
        self.fields['twitter'].widget.attrs['placeholder'] = twitter_ph

        linkedin_ph = _('Your LinkedIn profile URL')
        self.fields['linkedin'].widget.attrs['placeholder'] = linkedin_ph

        website_ph = _('Your personal website/blog URL')
        self.fields['website'].widget.attrs['placeholder'] = website_ph

        bio_ph = _('Why are you part of our translation project? '
                   'Describe yourself, inspire others!')
        self.fields['bio'].widget.attrs['placeholder'] = bio_ph

    def clean_linkedin(self):
        url = self.cleaned_data['linkedin']
        if url != '':
            parsed = urlparse.urlparse(url)
            if 'linkedin.com' not in parsed.netloc or parsed.path == '/':
                raise forms.ValidationError(
                    _('Please enter a valid LinkedIn user profile URL.')
                )

        return url
