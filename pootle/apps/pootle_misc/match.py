#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

import re

from translate.search import match, terminology

delimiters = re.compile(u"[\W]+", re.U)

class Matcher(match.terminologymatcher):
    def __init__(self, store, max_candidates=10, min_similarity=75,
                 max_length=500, comparer=None):
        comparer = TerminologyComparer(max_length)
        super(Matcher, self).__init__(store, max_candidates,
                                      min_similarity=10,
                                      max_length=max_length,
                                      comparer=comparer)

    def inittm(self, store):
        match.matcher.inittm(self, store)
        for cand in self.candidates.units:
            cand.source = cand.source.lower()


class TerminologyComparer(terminology.TerminologyComparer):

    def __init__(self, max_len=500):
        self.match_info = {}
        self.MAX_LEN = max_len

    def similarity(self, text, term, stoppercentage=40):
        text_list = delimiters.split(text)
        term_list = delimiters.split(term)
        #text_list = text.split()
        #term_list = term.split()
        match_info = {}
        matched_count = 0
        match_gap = 0
        pos = 0
        term_count = len(term_list)
        matched_index = 0

        for i, term_word in enumerate(term_list):
            for j, text_word in enumerate(text_list[matched_index:],
                                          start=matched_index):
                text_word_len = len(text_word)
                text_word = text_word[:len(term_word)]
                if text_word == term_word:
                    if matched_count == 0:
                        match_info = {'pos': pos}
                    matched_count += 1
                    matched_index = j + 1
                    break
                else:
                    if matched_count > 0:
                        match_gap += 1

                    if match_gap > 2:
                        matched_count = 0
                        match_gap = 0
                        matched_index = 0

                pos += text_word_len + 1

            if matched_count == 0:
                break

        if matched_count == term_count:
            self.match_info[term] = match_info
            return 100
        else:
            return 0
