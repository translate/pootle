# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms

from pootle.core.fields import ISODateTimeField

from .models import DueDate


class DueDateForm(forms.ModelForm):

    due_on = ISODateTimeField()

    class Meta:
        model = DueDate
        fields = ('due_on', 'pootle_path', 'modified_by', )
