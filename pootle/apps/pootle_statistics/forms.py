# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Form fields required for handling translation files."""

from django import forms


class StatsForm(forms.Form):

    offset = forms.IntegerField(required=False)
    path = forms.CharField(max_length=2048, required=True)

    def clean_path(self):
        return self.cleaned_data.get("path", "/") or "/"
