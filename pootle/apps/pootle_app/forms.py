#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, 2013 Zuza Software Foundation
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
from django.utils.translation import ugettext_lazy as _

from pootle_misc.siteconfig import load_site_config


class GeneralSettingsForm(forms.Form):
    TITLE = forms.CharField(
        label=_("Title"),
        help_text=_("The name for this Pootle server"),
        max_length=50,
        required=True,
    )
    DESCRIPTION = forms.CharField(
        label=_("Description"),
        help_text=_("The description and instructions shown on the front page "
                    "and about page. Be sure to use valid HTML."),
        max_length=8192,
        required=True,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        self.siteconfig = load_site_config()

        for field in self.fields:
            value = self.siteconfig.get(field, None)

            if value is not None:
                self.fields[field].initial = value

    def save(self):
        if not self.errors:
            for field, value in self.cleaned_data.iteritems():
                self.siteconfig.set(field, value)

            self.siteconfig.save()
