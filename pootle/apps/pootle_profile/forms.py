# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import urlparse

from django import forms
from django.contrib.auth import get_user_model

from pootle.i18n.gettext import ugettext_lazy as _


class EditUserForm(forms.ModelForm):
    class Meta(object):
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
