#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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
from lxml.html import fromstring, rewrite_links, tostring
from lxml.html.clean import clean_html

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import escape, simple_email_re
from django.utils.safestring import mark_safe


register = template.Library()


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
    """Obfuscate the given text in case it is an email address.

    Based on the implementation used in addons.mozilla.org
    """
    if not simple_email_re.match(text):
        return text

    fallback = text[::-1]  # Reverse.
    # Inject junk somewhere.
    i = random.randint(0, len(text) - 1)
    fallback = u"%s%s%s" % (escape(fallback[:i]),
                            u'<span class="i">null</span>',
                            escape(fallback[i:]))
    # Replace '@' and '.'.
    fallback = fallback.replace('@', '&#x0040;').replace('.', '&#x002E;')

    title = '<span class="email">%s</span>' % fallback

    node = u'%s<span class="email hide">%s</span>' % (title, fallback)
    return mark_safe(node)


@register.filter
@stringfilter
def url_target_blank(text):
    """Set the target="_blank" for hyperlinks."""
    return mark_safe(text.replace('<a ', '<a target="_blank" '))


TRIM_URL_LENGTH = 70

def trim_url(link):
    """Trims `link` if it's longer than `TRIM_URL_LENGTH` chars.

    Trimming is done by always keeping the scheme part, and replacing
    everything up to the last path part with three dots. Example::

    https://www.evernote.com/shard/s12/sh/f6f3eb18-c11c/iPhone5_AppStore_01_Overview.png?resizeSmall&width=832
    becomes
    https://.../iPhone5_AppStore_01_Overview.png?resizeSmall&width=832
    """
    link_text = link

    if len(link_text) > TRIM_URL_LENGTH:
        scheme_index = link.rfind('://') + 3
        last_slash_index = link.rfind('/')
        text_to_replace = link[scheme_index:last_slash_index]
        link_text = link_text.replace(text_to_replace, '...')

    return link_text


@register.filter
@stringfilter
def url_trim(html):
    """Trims anchor texts that are longer than 70 chars."""
    fragment = fromstring(html)
    for el, attrib, link, pos in fragment.iterlinks():
        new_link_text = trim_url(el.text_content())
        el.text = new_link_text

    return mark_safe(tostring(fragment, encoding=unicode))


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
