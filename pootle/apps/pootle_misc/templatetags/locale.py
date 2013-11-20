#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from django import template
from django.utils import dateformat
from django.utils.formats import get_format
from django.utils.translation import trans_real


register = template.Library()


@register.simple_tag
def locale_dir():
    """Returns current locale's direction."""
    return trans_real.get_language_bidi() and "rtl" or "ltr"


@register.simple_tag
def locale_align():
    """Returns current locale's default alignment."""
    return trans_real.get_language_bidi() and "right" or "left"


@register.simple_tag
def locale_reverse_align():
    """Returns current locale's reverse alignment."""
    return trans_real.get_language_bidi() and "left" or "right"


@register.filter(name='dateformat')
def do_dateformat(value, format='DATETIME_FORMAT'):
    """Formats a `value` date using `format`.

    :param value: a datetime object.
    :param format: a format string accepted by
        :func:`django.utils.formats.get_format` or
        :func:`django.utils.dateformat.format`. If none is set, the current
        locale's default format will be used.
    """
    try:
        use_format = get_format(format)
    except AttributeError:
        use_format = format

    return dateformat.format(value, use_format)
