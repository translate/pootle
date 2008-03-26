# -*- coding: utf-8 -*-
# 
# Copyright 2006 Zuza Software Foundation
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

"""A class that does terminology matching"""

import re

# We don't want to miss certain forms of words that only change a little
# at the end. Now we are tying this code to English, but it should serve
# us well. For example "category" should be found in "categories", 
# "copy" should be found in "copied"
#
# The tuples define a regular expression to search for, and what with
# what it should be replaced.
ignorepatterns = [("y\s*$", "ie"),          #category/categories, identify/identifies, apply/applied
                  ("[\s-]*", ""),           #down time / downtime, pre-order / preorder
                  ("-", " "),               #pre-order / pre order
                  (" ", "-"),               #pre order / pre-order
                 ]

#TODO: compile regexes

class TerminologyComparer:
    def __init__(self, max_len=500):
        self.MAX_LEN = max_len

    def similarity(self, a, b, stoppercentage=40):
        """returns the match quality of term b in the text a"""
        # We could segment the words, but mostly it will give less ideal 
        # results, since we'll miss plurals, etc. Then we also can't search for
        # multiword terms, such as "Free Software". Ideally we should use a 
        # stemmer, like the Porter stemmer.
        
        # So we just see if the word occurs anywhere. This is not perfect since
        # we might get more than we bargained for. The term "form" will be found
        # in the word "format", for example. A word like "at" will trigger too
        # many false positives. 

        # First remove a possible disambiguating bracket at the end
        b = re.sub("\s+\(.*\)\s*$", "", b)

        if len(b) <= 2:
            return 0
            
        pos = a[:self.MAX_LEN].find(b)
        if pos >= 0:
            return 100 - pos * 10 / len(a[:self.MAX_LEN])

        for ignorepattern in ignorepatterns:
            newb = re.sub(ignorepattern[0], ignorepattern[1], b)
            if newb in a[:self.MAX_LEN]:
                return 80
        return 0
    
