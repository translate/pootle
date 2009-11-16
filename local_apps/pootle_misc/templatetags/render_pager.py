#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

from django.utils.translation import ugettext as _
from django import template
from django.utils.safestring import mark_safe

def render_pager(pager):
    """Render a pager block with next and previous links"""
    if not pager.has_other_pages():
        return ""
    
    result = '<div class="pager">'
    if pager.has_previous():
        result += '<a href="?page=1" class="first-link">%s</a> | ' % _('First')
        result += '<a href="?page=%d" class="previous-link">%s</a> | ' % (pager.previous_page_number(), _('Previous'))

    start = max(1, pager.number - 4)
    end = min(pager.paginator.num_pages, pager.number + 4)
    if start > 1:
        result += '...'
    for i in range(start, end+1):
        if i == pager.number:
            result += '<span class="current-link">%s</span> | ' % i
        else:
            result += '<a href="?page=%d" class="number-link">%d</a> | ' % (i, i)
    if end < pager.paginator.num_pages:
        result += '...'

    if pager.has_next():
        result += '<a href="?page=%d" class="next-link">%s</a> | ' % (pager.next_page_number(),  _('Next'))
        result += '<a href="?page=%d" class="previous-link">%s</a>' % (pager.paginator.num_pages, _('Last'))

    result +='</div>'
    return mark_safe(result)

register = template.Library()
register.filter('render_pager', render_pager)

