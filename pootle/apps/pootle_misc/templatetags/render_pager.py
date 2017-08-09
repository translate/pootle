# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template
from django.utils.safestring import mark_safe

from pootle.i18n.gettext import ugettext as _


register = template.Library()


@register.filter
def render_pager(pager):
    """Render a pager block with next and previous links"""
    if not pager.has_other_pages():
        return ""

    result = '<ul class="pager">'
    if pager.has_previous():
        result += '<li><a href="?page=1" class="nth-link">%s</a></li>' % \
                  _('First')
        result += ('<li><a href="?page=%d" class="prevnext-link">%s</a>'
                   '</li>' % (pager.previous_page_number(), _('Previous')))

    start = max(1, pager.number - 4)
    end = min(pager.paginator.num_pages, pager.number + 4)
    if start > 1:
        result += '<li>...</li>'
    for i in range(start, end+1):
        if i == pager.number:
            result += '<li><span class="current-link">%s</span></li>' % i
        else:
            result += ('<li><a href="?page=%d" class="number-link">%d</a>'
                       '</li>' % (i, i))
    if end < pager.paginator.num_pages:
        result += '<li>...</li>'

    if pager.has_next():
        result += ('<li><a href="?page=%d" class="prevnext-link">%s</a>'
                   '</li>' % (pager.next_page_number(), _('Next')))
        result += '<li><a href="?page=%d" class="nth-link">%s</a></li>' % \
                  (pager.paginator.num_pages, _('Last (%d)',
                                                pager.paginator.num_pages))

    result += '</ul>'
    return mark_safe(result)
