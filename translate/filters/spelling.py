#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
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

"""An API to provide spell checking for use in checks or elsewhere."""

# Let us see what is available in our preferred order
try:
    # Enchant
    from enchant import checker
    checkers = {}
    def check(text, lang):
        if not lang in checkers:
            checkers[lang] = checker.SpellChecker(lang)
        spellchecker = checkers[lang]
        spellchecker.set_text(text)
        for err in spellchecker:
            yield err.word, err.wordpos, err.suggest()

except ImportError:
    try:
        # jToolkit might be installed and might give access to aspell, for 
        # example
        from jToolkit import spellcheck
        check = spellcheck.check
    except ImportError:
        
        def check(text, lang):
            return []

