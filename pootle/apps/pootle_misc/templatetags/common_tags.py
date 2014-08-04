#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013-2104 Evernote Corporation
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

import datetime

from django import template
from django.contrib.auth import get_user_model


register = template.Library()


@register.inclusion_tag('browser/_table.html', takes_context=True)
def display_table(context, table):
    return {
        'table': table,
    }


@register.filter
def endswith(value, arg):
    return value.endswith(arg)


@register.filter
def count(value, arg):
    return value.count(arg)


@register.filter
def label_tag(field, suffix=None):
    """Returns the `label_tag` for a field.

    Optionally allows overriding the default `label_suffix` for the form
    this field belongs to.
    """
    if not hasattr(field, 'label_tag'):
        return ''

    return field.label_tag(label_suffix=suffix)


@register.inclusion_tag('core/_top_scorers.html')
def top_scorers(*args, **kwargs):
    User = get_user_model()
    allowed_kwargs = ('days', 'language', 'project', 'limit')
    lookup_kwargs = dict(
        (k, v) for (k, v) in kwargs.iteritems() if k in allowed_kwargs
    )

    return {
        'top_scorers': User.top_scorers(**lookup_kwargs),
    }


@register.simple_tag
def format_date_range(date_from, date_to, separator=" - ",
    format_str="%B %-d, %Y", year_f=", %Y", month_f="%B"):
    """ Takes a start date, end date, separator and formatting strings and
    returns a pretty date range string
    """
    if (isinstance(date_to, datetime.datetime) and
        isinstance(date_from, datetime.datetime)):
        date_to = date_to.date()
        date_from = date_from.date()

    if date_to and date_to != date_from:
        from_format = to_format = format_str
        if date_from.year == date_to.year:
            from_format = from_format.replace(year_f, '')
            if date_from.month == date_to.month:
                to_format = to_format.replace(month_f, '')
        return separator.join((date_from.strftime(from_format),
                               date_to.strftime(to_format)))

    return date_from.strftime(format_str)