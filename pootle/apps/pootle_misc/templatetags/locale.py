# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import calendar

from django import template
from django.utils.formats import get_format
from django.utils.translation import get_language, trans_real

from pootle.core.utils import dateformat
from pootle.i18n.dates import timesince


register = template.Library()


@register.simple_tag
def locale_dir():
    """Returns current locale's direction."""
    return trans_real.get_language_bidi() and "rtl" or "ltr"


@register.filter(name='dateformat')
def do_dateformat(value, use_format='c'):
    """Formats a `value` date using `format`.

    :param value: a datetime object.
    :param use_format: a format string accepted by
        :func:`django.utils.formats.get_format` or
        :func:`django.utils.dateformat.format`. If none is set, the current
        locale's default format will be used.
    """
    try:
        use_format = get_format(use_format)
    except AttributeError:
        pass

    return dateformat.format(value, use_format)


@register.filter(name='relative_datetime_format')
def do_relative_datetime_format(value):
    return timesince(
        calendar.timegm(value.timetuple()),
        locale=get_language())


@register.simple_tag
def locale_align():
    """Returns current locale's default alignment."""
    return trans_real.get_language_bidi() and "right" or "left"
