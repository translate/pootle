#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
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

def try_language_code(code, test, f):
    """See if 'code' lets 'test' evaluate to true. If so, return
    'f(code)'.

    Otherwise, see if 'code' is a specialized language code
    (i.e. something like af-ZA or af_ZA, instead of just af) and strip
    away the specialization suffix (so change af-ZA to af or af_ZA to
    af) and again see if the new code lets 'test' evaluate to true.

    This utility function is useful in cases where we want to treat
    all sub-languages (i.e. af-ZA, af-NA) similar to the main language
    (af).

    We might want to make 'test' something like

        lambda code: code in dictionary

    and 'f' something like

        lambda code: dictionary[code]

    so that we can look up something in a dictionary which is only
    indexed by a plain language code like 'af' using a key such as
    'af-ZA'."""
    if test(code):
        return f(code)
    else:
        for dash in ('-', '_'):
            if dash in code:
                short_code = code[:code.find(dash)]
                if test(short_code):
                    return f(short_code)
        return None
