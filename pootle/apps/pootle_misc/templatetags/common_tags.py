#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.inclusion_tag('browser/_table.html', takes_context=True)
def display_table(context, table):
    return {
        'table': table,
        'user': context.get('user', None),
        'request': context.get('request', None),
    }


@register.filter
@stringfilter
def makeid(value):
    """Replaces all '.' with '-'."""
    return value.replace(u'.', u'-')


@register.filter
def endswith(value, arg):
    return value.endswith(arg)


@register.filter
def count(value, arg):
    return value.count(arg)
