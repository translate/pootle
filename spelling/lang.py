#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Zuza Software Foundation, WordForge Foundation
#
# This is free software; you can redistribute it and/or modify
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Language management

Simple management of language related issues such as what languages 
are provided by all spell checkers.
"""

import spell

class LangResult:
    """The result from a language list request

    XML Lang result::
        <?xml version="1.0"?>
            <langresult count="2">
                <lang>af</lang>
                <lang>en_ZA</lang>
            </langresult>
    
    Attributes:
        - B{count} - the number of languages available

    Each <lang> entity contains the iso639 language code and iso country code if needed

    @todo: look at the option of::
        <langresult lang="af">
           <lang code="en_ZA" name="English (South Africa)" locale_name="Engels (Suid-Afrika)"/>
    @todo: make it a unique list
    """
    def __init__(self):
        self._langs = spell.GoogleChecker.langs() + spell.EnchantChecker.langs()
        self._langs.sort()

    def __str__(self):
        """
        @return: an XML packet with all supported languages
        @rtype: string
        """
        skeleton = '''<?xml version="1.0" ?>
    <langresult count="%i">
        %s
    </langrequest>'''
        xmllangs = []
        for lang in self._langs:
            xmllangs.append('<lang>%s</lang>' % lang)
        return skeleton % (len(self._langs), "\n        ".join(xmllangs))

