#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2005, 2006 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""a set of autocorrect functions that make resolving common problems more automatic..."""

from translate.filters import decoration

def simplecorrect(msgid, msgstr):
    """runs a set of easy automatic corrections"""
    if msgstr == "":
        return msgstr
    if "..." in msgid and u"…" in msgstr:
        return msgstr.replace(u"…", "...")
    if decoration.spacestart(msgid) != decoration.spacestart(msgstr) or decoration.spaceend(msgid) != decoration.spaceend(msgstr):
        return decoration.spacestart(msgid) + msgstr.strip() + decoration.spaceend(msgid)
    punctuation = (".", ":", ". ", ": ", "?")
    puncendid = decoration.puncend(msgid, punctuation)
    puncendstr = decoration.puncend(msgstr, punctuation)
    if puncendid != puncendstr:
        if not puncendstr:
            return msgstr + puncendid
    if msgid[:1].isalpha() and msgstr[:1].isalpha():
        if msgid[:1].isupper() and msgstr[:1].islower():
            return msgstr[:1].upper() + msgstr[1:]
        elif msgid[:1].islower() and msgstr[:1].isupper():
            return msgstr[:1].lower() + msgstr[1:]
    return None

def correct(msgid, msgstr):
    """runs a set of easy automatic corrections, handling unicode etc"""
    if isinstance(msgid, str):
        msgid = msgid.decode("utf-8")
    if isinstance(msgstr, str):
        msgstr = msgstr.decode("utf-8")
        wasstr = True
    else:
        wasstr = False
    correction = simplecorrect(msgid, msgstr)
    if correction and wasstr:
        return correction.encode("utf-8")
    return correction

