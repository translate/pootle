# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms


class PootleActivityForm(forms.Form):

    object_type = forms.ChoiceField(
        label="",
        choices=(
            ("user", "User"),
            ("language", "Language"),
            ("project", "Project"),
            ("store", "Store"),
            ("tp", "Translation Project")))
    object_name = forms.CharField(label="")
