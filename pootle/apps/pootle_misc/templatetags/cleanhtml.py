#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
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

import random
import re

from lxml.etree import ParserError
from lxml.html import rewrite_links
from lxml.html.clean import clean_html

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import escape, simple_email_re as email_re
from django.utils.safestring import mark_safe

from translate.storage.placeables import general


register = template.Library()


ESCAPE_RE = re.compile('<[^<]*?>|\\\\|\r\n|[\r\n\t&<>]')
def fancy_escape(text):
    """replace special chars with entities, and highlight xml tags and
    whitespaces"""
    def replace(match):
        escape_highlight = '<span class="highlight-escape ' \
                           'js-editor-copytext">%s</span>'
        html_highlight = '<span class="highlight-html js-editor-copytext">' \
                         '&lt;%s&gt;</span>'
        submap = {
            '\r\n': (escape_highlight % '\\r\\n') + '<br/>\n',
            '\r': (escape_highlight % '\\r') + '<br/>\n',
            '\n': (escape_highlight % '\\n') + '<br/>\n',
            '\t': (escape_highlight % '\\t'),
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '\\': (escape_highlight % '\\\\'),
            }

        try:
            return submap[match.group()]
        except KeyError:
            return html_highlight % fancy_escape(match.group()[1:-1])

    return ESCAPE_RE.sub(replace, text)


WHITESPACE_RE = re.compile('^ +| +$|[\r\n\t] +| {2,}')
def fancy_spaces(text):
    """Highlight spaces to make them easily visible"""
    def replace(match):
        fancy_space = '<span class="translation-space"> </span>'
        if match.group().startswith(' '):
            return fancy_space * len(match.group())
        return match.group()[0] + fancy_space * (len(match.group()) - 1)
    return WHITESPACE_RE.sub(replace, text)


PUNCTUATION_RE = general.PunctuationPlaceable().regex
def fancy_punctuation_chars(text):
    """Wraps punctuation chars found in the ``text`` around tags."""
    def replace(match):
        fancy_special_char = '<span class="highlight-punctuation ' \
                             'js-editor-copytext">%s</span>'
        return fancy_special_char % match.group()

    return PUNCTUATION_RE.sub(replace, text)


@register.filter
@stringfilter
def fancy_highlight(text):
    return mark_safe(fancy_punctuation_chars(fancy_spaces(fancy_escape(text))))


@register.filter
@stringfilter
def clean(text):
    """Wrapper around lxml's html cleaner that returns SafeStrings for
    immediate rendering in templates.
    """
    try:
        clean_text = clean_html(text)
    except ParserError:
        clean_text = u""

    return mark_safe(clean_text)


@register.filter
@stringfilter
def obfuscate(text):
    """Obfuscates the given text in case it is an email address.
    Based on the implementation used in addons.mozilla.org"""

    if not email_re.match(text):
        return text

    fallback = text[::-1]  # reverse
    # inject junk somewhere
    i = random.randint(0, len(text) - 1)
    fallback = u"%s%s%s" % (escape(fallback[:i]),
                            u'<span class="i">null</span>',
                            escape(fallback[i:]))
    # replace @ and .
    fallback = fallback.replace('@', '&#x0040;').replace('.', '&#x002E;')

    title = '<span class="email">%s</span>' % fallback

    node = u'%s<span class="email hide">%s</span>' % (title, fallback)
    return mark_safe(node)


@register.filter
@stringfilter
def url_target_blank(text):
    """Sets the target="_blank" for hyperlinks."""
    return mark_safe(text.replace('<a ', '<a target="_blank" '))


LANGUAGE_LINK_RE = re.compile(ur'/xx/', re.IGNORECASE)

@register.filter
@stringfilter
def rewrite_language_links(html, language_code):
    if language_code:
        html = rewrite_links(
            html,
            lambda lnk: LANGUAGE_LINK_RE.sub(u'/' + language_code + u'/', lnk)
        )

    return mark_safe(html)
