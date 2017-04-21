# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.utils.datastructures import MultiValueDict

from pootle.core.dateparse import parse_datetime
from pootle_checks.constants import CATEGORY_IDS


class CommaSeparatedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):

    def value_from_datadict(self, data, files, name):
        # Accept `sfields` to be a comma-separated string of fields (#46)
        if "," in data.get(name, ""):
            return data.get(name).split(u',')
        if isinstance(data, MultiValueDict):
            return data.getlist(name)
        return data.get(name, None)


class MultipleValueWidget(forms.TextInput):

    def value_from_datadict(self, data, files, name):
        if hasattr(data, "getlist"):
            return data.getlist(name)
        return []


class MultipleArgsField(forms.Field):
    widget = MultipleValueWidget

    def __init__(self, *args, **kwargs):
        self.field = kwargs.pop("field")
        super(MultipleArgsField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if len(value) == 1 and "," in value[0]:
            value = value[0].split(",")
        return [self.field.clean(x) for x in value]


class ISODateTimeField(forms.DateTimeField):

    def to_python(self, value):
        if value is not None:
            return parse_datetime(value)


class CategoryChoiceField(forms.ChoiceField):

    def to_python(self, value):
        if value is not None:
            return CATEGORY_IDS.get(value)
