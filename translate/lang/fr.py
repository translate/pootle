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

"""This module represents French language.

For more information, see U{http://en.wikipedia.org/wiki/French_language}
"""

from translate.lang import common
import re

class fr(common.Common):
    """This class represents French."""
    code = "fr"
    fullname = "French"
    nplurals = 2
    pluralequation = "(n > 1)"

    # According to http://french.about.com/library/writing/bl-punctuation.htm, 
    # in French, a space is required both before and after all two- (or more) 
    # part punctuation marks and symbols, including : ; « » ! ? % $ # etc.
    puncdict = {}
    for c in u":;!?#":
        puncdict[c] = u" %s" % c
    # TODO: consider adding % and $, but think about the consequences of how 
    # they could be part of variables

    def punctranslate(cls, text):
        """Implement some extra features for quotation marks.
        
        Known shortcomings:
            - % and $ are not touched yet for fear of variables
            - Double spaces might be introduced
        """
        text = super(cls, cls).punctranslate(text)

        def convertquotation(match):
            prefix = match.group(1)
            # Let's see that we didn't perhaps match an XML tag property like
            # <a href="something">
            if prefix == u"=":
                return match.group(0)
            return u"%s« %s »" % (prefix, match.group(2))
        
        # Check that there is an even number of double quotes, otherwise it is
        # probably not safe to convert them.
        if text.count(u'"') % 2 == 0:
            text = re.sub('(.|^)"([^"]+)"', convertquotation, text)

        return text
    punctranslate = classmethod(punctranslate)
