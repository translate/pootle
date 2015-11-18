#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import random
import re

from lxml.etree import ParserError
from lxml.html import fromstring, tostring
from lxml.html.clean import clean_html

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import escape, simple_email_re as email_re
from django.utils.safestring import mark_safe

from pootle.core.utils.html import rewrite_links


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
