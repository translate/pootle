#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template
from django.utils.formats import get_format
from django.utils.translation import trans_real

from pootle.core.utils import dateformat


register = template.Library()


@register.simple_tag
def locale_dir():
    """Returns current locale's direction."""
    return trans_real.get_language_bidi() and "rtl" or "ltr"


@register.filter(name='dateformat')
def do_dateformat(value, format='c'):
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


@register.simple_tag
def locale_align():
    """Returns current locale's default alignment."""
    return trans_real.get_language_bidi() and "right" or "left"
