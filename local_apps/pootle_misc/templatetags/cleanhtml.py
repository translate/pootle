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

import re

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

try:
    from lxml.html.clean import clean_html
except ImportError:
    clean_html = lambda text: text

ESCAPE_RE = re.compile('<.*?>|\r\n|[\r\n\t&<>]')
def fancy_escape(text):
    """replace special chars with entities, and highlight xml tags and
    whitespaces"""
    def replace(match):
        escape_highlight = '<span class="translation-highlight-escape">%s</span>'
        html_highlight = '<span class="translation-highlight-html">&lt;%s&gt;</span>'
        submap = {
            '\r\n': (escape_highlight % '\\r\\n') + '<br/>\n',
            '\r': (escape_highlight % '\\r') + '<br/>\n',
            '\n': (escape_highlight % '\\n') + '<br/>\n',
            '\t': (escape_highlight % '\\t') + '\t',
            '&': escape_highlight % '&amp;',
            '<': escape_highlight % '&lt;',
            '>': escape_highlight % '&gt;',
            }
        try:
            return submap[match.group()]
        except KeyError:
            return html_highlight %  match.group()[1:-1]
    return ESCAPE_RE.sub(replace, text)

WHITESPACE_RE = re.compile('^ +| +$|[\r\n\t] +')
def fancy_spaces(text):
    """Highlight spaces to make them easily visible"""
    def replace(match):
        fancy_space = '<span class="translation-space"> </span>'
        if match.group().startswith(' '):
            return fancy_space * len(match.group())
        return match.group()[0] + fancy_space * (len(match.group()) - 1)
    return WHITESPACE_RE.sub(replace, text)

def clean_wrapper(text):
    """wrapper around lxml's html cleaner that returns SafeStrings for
    immediate rendering in templates"""
    return mark_safe(clean_html(text))

def fancy_highlight(text):
    return mark_safe(fancy_spaces(fancy_escape(text)))

register = template.Library()
register.filter('clean', stringfilter(clean_wrapper))
register.filter('fancy_highlight', stringfilter(fancy_highlight))

