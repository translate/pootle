#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
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
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


register = template.Library()


@register.filter
def render_pager(pager):
    """Render a pager block with next and previous links"""
    if not pager.has_other_pages():
        return ""

    result = '<ul class="pager">'
    if pager.has_previous():
        result += '<li><a href="?page=1" class="nth-link">%s</a></li>' % _('First')
        result += '<li><a href="?page=%d" class="prevnext-link">%s</a></li>' % (pager.previous_page_number(),
                                                                                _('Previous'))

    start = max(1, pager.number - 4)
    end = min(pager.paginator.num_pages, pager.number + 4)
    if start > 1:
        result += '<li>...</li>'
    for i in range(start, end+1):
        if i == pager.number:
            result += '<li><span class="current-link">%s</span></li>' % i
        else:
            result += '<li><a href="?page=%d" class="number-link">%d</a></li>' % (i, i)
    if end < pager.paginator.num_pages:
        result += '<li>...</li>'

    if pager.has_next():
        result += '<li><a href="?page=%d" class="prevnext-link">%s</a></li>' % (pager.next_page_number(),
                                                                                _('Next'))
        result += '<li><a href="?page=%d" class="nth-link">%s</a></li>' % (pager.paginator.num_pages,
                                                                           _('Last (%d)', pager.paginator.num_pages))

    result += '</ul>'
    return mark_safe(result)
