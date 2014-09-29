#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

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
