#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from pootle_language.models import Language


LANGCODE_RE = re.compile("^[a-z]{2,}([_-][a-z]{2,})*(@[a-z0-9]+)?$",
                         re.IGNORECASE)


class LanguageAdminForm(forms.ModelForm):

    class Meta:
        model = Language

    def __init__(self, *args, **kwargs):
        super(LanguageAdminForm, self).__init__(*args, **kwargs)
        self.fields['nplurals'].widget.attrs['class'] = \
            "js-select2 select2-nplurals"

    def clean_code(self):
        if (self.cleaned_data['code'] != 'templates' and
            not LANGCODE_RE.match(self.cleaned_data['code'])):
            raise forms.ValidationError(
                _('Language code does not follow the ISO convention')
            )
        return self.cleaned_data["code"]
