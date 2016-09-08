# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.utils.dateparse import parse_datetime
from django.utils.encoding import force_str


class ISODateTimeField(forms.DateTimeField):
    """A `DateTimeField` which understands timezone-aware ISO 8601 strings.

    Django's built-in `DateTimeField` relies on Python's `strptime`, and the
    format strings it parses against do not include the `%z` timezone marker.
    But even if they did (and one can always specify a `input_formats` parameter
    to the form field constructor), `%z` is not supported in Python 2:
    http://bugs.python.org/issue6641.

    Refs. https://code.djangoproject.com/ticket/11385.
    """

    def strptime(self, value, format):
        return parse_datetime(force_str(value))
