#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template
from django.utils.html import escapejs
from django.utils.safestring import mark_safe

from ..utils.json import jsonify


register = template.Library()


@register.filter
def to_js(value):
    """Returns a string which leaves the value readily available for JS
    consumption.
    """
    return mark_safe('JSON.parse("%s")' % escapejs(jsonify(value)))


@register.inclusion_tag('includes/formtable.html')
def formtable(formtable):
    return dict(formtable=formtable)
