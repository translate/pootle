#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from unicodedata import bidirectional

from django.utils.encoding import force_unicode


_strong_types = ("L", "R", "AL")
_rtl_types = ("R", "AL")


def get_base_direction(text):
    """Find the base direction of a text string according to the first character
    with strong bidi type.

    Returns ``0`` for LTR, ``1`` for RTL and ``-1`` for undefined (no strong
    characters found).
    """
    text = force_unicode(text)

    # find first character with strong bidi type
    first = None
    for c in text:
        bidi_type = bidirectional(c)
        if bidi_type in _strong_types:
            first = bidi_type
            break

    if first:
        if first in _rtl_types:
            return 1
        else:
            return 0
    else:
        # text composed of weak bidi characters
        return -1


def insert_embeding(text):
    """Insert LRE (left-to-right embedding) or RLE (right-to-left
    embedding) marks around text according to its base direction, to ensure
    brackets and other weak bidi characters will be rendered correctly
    irrespective of the overall direction.

    Note: Unicode 6.3 will introduce FSI U+2068 (first strong isolate),
    which tells the bidi implementation to do all the magic we are doing
    here, so we should use it once it is widely available.
    """
    base = get_base_direction(text)
    if base == 0:
        return u"\u202a%s\u202c" % text
    elif base == 1:
        return u"\u202b%s\u202c" % text
    else:
        return text
